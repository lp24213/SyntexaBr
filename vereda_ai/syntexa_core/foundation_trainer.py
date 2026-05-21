"""
SYNTEXA FOUNDATION TRAINER
==========================
Pipeline de treinamento soberano: pretraining + SFT + checkpointing.
Sem dependência de transformers, DeepSpeed, Megatron (opcional futuro).
Suporta: mixed precision (torch.autocast), gradient clipping, lr scheduling,
distributed training stub, checkpoint sharding.
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig, estimate_model_size
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

log = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    # Data
    data_path: str
    output_dir: str = "checkpoints/foundation"
    tokenizer_dir: str = "checkpoints/foundation/tokenizer"
    # Model
    model_config: SyntexaFoundationConfig = field(default_factory=SyntexaFoundationConfig)
    # Training hyperparameters
    epochs: int = 3
    batch_size: int = 8
    max_seq_len: int = 2048
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    betas: tuple[float, float] = (0.9, 0.95)
    max_grad_norm: float = 1.0
    warmup_steps: int = 100
    # Checkpointing
    checkpoint_every_steps: int = 500
    keep_last_n_checkpoints: int = 3
    # Mixed precision
    use_amp: bool = True
    dtype: torch.dtype = torch.float16
    # Device
    device: Optional[str] = None
    # Logging
    log_every: int = 10

    def __post_init__(self):
        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"


class SyntexaFoundationTrainer:
    """
    Treinador autoregressivo para a Foundation Model Syntexa.
    """

    def __init__(self, config: TrainingConfig):
        self.cfg = config
        self.device = torch.device(config.device)
        self.model: Optional[SyntexaFoundationModel] = None
        self.tokenizer: Optional[SyntexaFoundationTokenizer] = None
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.scheduler: Optional[Any] = None
        self.scaler = torch.cuda.amp.GradScaler() if config.use_amp and torch.cuda.is_available() else None

        self.global_step = 0
        self.epoch = 0
        self.loss_history: list[float] = []
        self.best_loss = float("inf")

        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    # ── DATA LOADING ──────────────────────────────────────────

    def _load_texts(self) -> list[str]:
        texts: list[str] = []
        p = Path(self.cfg.data_path)
        if not p.is_file():
            raise FileNotFoundError(f"Dataset não encontrado: {p}")
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = str(obj.get("text", "")).strip()
                    if len(text) >= 10:
                        texts.append(text)
                except json.JSONDecodeError:
                    continue
        log.info("[Trainer] Carregados %d textos", len(texts))
        return texts

    def _prepare_data(self) -> list[list[int]]:
        texts = self._load_texts()
        log.info("[Trainer] Treinando tokenizer BPE (vocab_size=%d)...", self.cfg.model_config.vocab_size)
        self.tokenizer = SyntexaFoundationTokenizer.train(texts, vocab_size=self.cfg.model_config.vocab_size)
        self.tokenizer.save(self.cfg.tokenizer_dir)
        log.info("[Trainer] Tokenizer salvo em %s", self.cfg.tokenizer_dir)

        tokenized = []
        for t in texts:
            ids = self.tokenizer.encode(t, add_special_tokens=True)
            if len(ids) > 4:
                tokenized.append(ids)
        log.info("[Trainer] %d amostras após tokenização", len(tokenized))
        return tokenized

    def _sample_batch(
        self,
        all_ids: list[list[int]],
        batch_size: int,
        seq_len: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        # Filtra amostras que cabem no seq_len; se não houver, faz padding
        valid_ids = [s for s in all_ids if len(s) >= 2]
        if not valid_ids:
            raise RuntimeError("Nenhuma amostra válida após tokenização.")
        xs, ys = [], []
        for _ in range(batch_size):
            seq = random.choice(valid_ids)
            if len(seq) >= seq_len + 1:
                start = random.randint(0, len(seq) - seq_len - 1)
                chunk = seq[start : start + seq_len + 1]
            else:
                # Padding com <pad> (id=0) para amostras curtas
                chunk = seq + [0] * (seq_len + 1 - len(seq))
            xs.append(chunk[:-1][:seq_len])
            ys.append(chunk[1:][:seq_len])
        x = torch.tensor(xs, dtype=torch.long, device=self.device)
        y = torch.tensor(ys, dtype=torch.long, device=self.device)
        return x, y

    # ── MODEL SETUP ─────────────────────────────────────────

    def _build_model(self) -> None:
        log.info("[Trainer] Construindo modelo...")
        self.model = SyntexaFoundationModel(self.cfg.model_config).to(self.device)
        if self.cfg.dtype == torch.float16 and self.device.type == "cuda":
            self.model = self.model.half()
        info = estimate_model_size(self.model)
        log.info("[Trainer] Parâmetros: %s | Tamanho: %s MB", f"{info['parameters']:,}", info["size_mb"])

        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            betas=self.cfg.betas,
            weight_decay=self.cfg.weight_decay,
        )

    # ── CHECKPOINTING ─────────────────────────────────────────

    def save_checkpoint(self, tag: str) -> Path:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Modelo ou tokenizer não inicializado.")
        out = Path(self.cfg.output_dir) / f"checkpoint_{tag}.pt"
        torch.save({
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict() if self.optimizer else None,
            "config": self.cfg.model_config.__dict__,
            "global_step": self.global_step,
            "epoch": self.epoch,
            "loss_history": self.loss_history,
        }, out)
        log.info("[Trainer] Checkpoint salvo: %s", out)
        self._prune_checkpoints()
        return out

    def load_checkpoint(self, path: str) -> None:
        ckpt = torch.load(path, map_location=self.device)
        if self.model is None:
            self._build_model()
        self.model.load_state_dict(ckpt["model_state"])
        if self.optimizer and ckpt.get("optimizer_state"):
            self.optimizer.load_state_dict(ckpt["optimizer_state"])
        self.global_step = ckpt.get("global_step", 0)
        self.epoch = ckpt.get("epoch", 0)
        self.loss_history = ckpt.get("loss_history", [])
        log.info("[Trainer] Checkpoint carregado: %s (step=%d)", path, self.global_step)

    def _prune_checkpoints(self) -> None:
        ckpts = sorted(
            Path(self.cfg.output_dir).glob("checkpoint_*.pt"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(ckpts) > self.cfg.keep_last_n_checkpoints:
            ckpts[0].unlink()
            ckpts.pop(0)

    def save_final(self, name: str = "syntexa_foundation") -> dict[str, Path]:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Modelo ou tokenizer não inicializado.")
        out_dir = Path(self.cfg.output_dir)
        weights_path = out_dir / f"{name}_weights.pt"
        torch.save({
            "model_state": self.model.state_dict(),
            "config": self.cfg.model_config.__dict__,
        }, weights_path)
        self.tokenizer.save(out_dir / "tokenizer")
        manifest = {
            "name": name,
            "family": "decoder_transformer",
            "stage": "foundation",
            "vocab_size": self.cfg.model_config.vocab_size,
            "dim": self.cfg.model_config.dim,
            "num_layers": self.cfg.model_config.num_layers,
            "num_heads": self.cfg.model_config.num_heads,
            "num_kv_heads": self.cfg.model_config.num_kv_heads,
            "max_seq_len": self.cfg.model_config.max_seq_len,
            "checkpoint_path": str(weights_path.resolve()),
            "tokenizer_dir": str((out_dir / "tokenizer").resolve()),
            "parameters": sum(p.numel() for p in self.model.parameters()),
        }
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("[Trainer] Modelo final salvo em %s", out_dir)
        return {"weights": weights_path, "manifest": manifest_path, "tokenizer": out_dir / "tokenizer"}

    # ── TRAINING LOOP ─────────────────────────────────────────

    def train(self, steps_per_epoch: Optional[int] = None) -> None:
        if self.model is None:
            self._build_model()
        if self.tokenizer is None:
            self._prepare_data()

        all_ids = []
        texts = self._load_texts()
        for t in texts:
            ids = self.tokenizer.encode(t, add_special_tokens=True)  # type: ignore[union-attr]
            if len(ids) > 4:
                all_ids.append(ids)

        if not all_ids:
            raise RuntimeError("Dataset vazio após tokenização.")

        if steps_per_epoch is None:
            steps_per_epoch = max(1, len(all_ids) // self.cfg.batch_size)

        total_steps = self.cfg.epochs * steps_per_epoch
        if self.scheduler is None:
            # Warmup + cosine decay
            self.scheduler = self._build_scheduler(total_steps)

        log.info("[Trainer] Iniciando treino: %d epochs, %d steps/epoch, lr=%.2e", self.cfg.epochs, steps_per_epoch, self.cfg.learning_rate)
        self.model.train()

        for ep in range(self.cfg.epochs):
            self.epoch = ep
            epoch_loss = 0.0
            t0 = time.time()

            for step in range(steps_per_epoch):
                x, y = self._sample_batch(all_ids, self.cfg.batch_size, self.cfg.max_seq_len)

                self.optimizer.zero_grad(set_to_none=True)  # type: ignore[union-attr]

                with torch.autocast(device_type=self.device.type, enabled=self.cfg.use_amp and self.scaler is not None):
                    logits, _ = self.model(x)
                    loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1), reduction='none')
                    mask = (y != 0).float()
                    loss = (loss * mask.reshape(-1)).sum() / mask.sum().clamp(min=1)

                if self.scaler:
                    self.scaler.scale(loss).backward()  # type: ignore[arg-type]
                    self.scaler.unscale_(self.optimizer)  # type: ignore[arg-type]
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                    self.scaler.step(self.optimizer)  # type: ignore[arg-type]
                    self.scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                    self.optimizer.step()  # type: ignore[union-attr]

                if self.scheduler is not None:
                    self.scheduler.step()

                self.global_step += 1
                epoch_loss += float(loss.item())
                self.loss_history.append(float(loss.item()))

                if (step + 1) % self.cfg.log_every == 0:
                    lr = self.optimizer.param_groups[0]["lr"]  # type: ignore[union-attr]
                    avg_loss = epoch_loss / (step + 1)
                    log.info(
                        "[ep %d/%d | step %d/%d] loss=%.4f lr=%.2e time=%.1fs",
                        ep + 1, self.cfg.epochs, step + 1, steps_per_epoch, avg_loss, lr, time.time() - t0,
                    )

                if self.cfg.checkpoint_every_steps > 0 and self.global_step % self.cfg.checkpoint_every_steps == 0:
                    self.save_checkpoint(f"step_{self.global_step}")

            avg_loss = epoch_loss / steps_per_epoch
            log.info("[Trainer] Epoch %d/%d concluída. Loss médio: %.4f", ep + 1, self.cfg.epochs, avg_loss)
            if avg_loss < self.best_loss:
                self.best_loss = avg_loss
                self.save_checkpoint("best")

        log.info("[Trainer] Treinamento concluído. Melhor loss: %.4f", self.best_loss)

    def _build_scheduler(self, total_steps: int):
        """Warmup linear + cosine annealing."""
        warmup = LinearLR(
            self.optimizer,  # type: ignore[arg-type]
            start_factor=0.01,
            end_factor=1.0,
            total_iters=self.cfg.warmup_steps,
        )
        cosine = CosineAnnealingLR(
            self.optimizer,  # type: ignore[arg-type]
            T_max=max(1, total_steps - self.cfg.warmup_steps),
            eta_min=self.cfg.learning_rate * 0.1,
        )
        from torch.optim.lr_scheduler import SequentialLR
        return SequentialLR(
            self.optimizer,  # type: ignore[arg-type]
            schedulers=[warmup, cosine],
            milestones=[self.cfg.warmup_steps],
        )

    # ── SFT (Supervised Fine-Tuning) ──────────────────────────

    def train_sft(
        self,
        instruction_data_path: str,
        epochs: int = 2,
        steps_per_epoch: Optional[int] = None,
    ) -> None:
        """
        Instruction tuning a partir de JSONL com campos 'instruction', 'input', 'output'.
        """
        if self.model is None:
            raise RuntimeError("Carregue ou treine o modelo base antes de SFT.")
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer não carregado.")

        texts: list[str] = []
        p = Path(instruction_data_path)
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    instruction = str(obj.get("instruction", "")).strip()
                    inp = str(obj.get("input", "")).strip()
                    out = str(obj.get("output", "")).strip()
                    prompt = instruction
                    if inp:
                        prompt += f"\nEntrada: {inp}"
                    prompt += f"\nResposta: {out}"
                    texts.append(prompt)
                except json.JSONDecodeError:
                    continue

        all_ids = []
        for t in texts:
            ids = self.tokenizer.encode(t, add_special_tokens=True)
            if len(ids) > 4:
                all_ids.append(ids)

        if not all_ids:
            raise RuntimeError("Dataset SFT vazio.")

        if steps_per_epoch is None:
            steps_per_epoch = max(1, len(all_ids) // self.cfg.batch_size)

        log.info("[Trainer] Iniciando SFT: %d epochs, %d amostras", epochs, len(all_ids))
        self.model.train()
        for ep in range(epochs):
            epoch_loss = 0.0
            for step in range(steps_per_epoch):
                x, y = self._sample_batch(all_ids, self.cfg.batch_size, self.cfg.max_seq_len)
                self.optimizer.zero_grad(set_to_none=True)  # type: ignore[union-attr]

                with torch.autocast(device_type=self.device.type, enabled=self.cfg.use_amp and self.scaler is not None):
                    logits, _ = self.model(x)
                    loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1), reduction='none')
                    mask = (y != 0).float()
                    loss = (loss * mask.reshape(-1)).sum() / mask.sum().clamp(min=1)

                if self.scaler:
                    self.scaler.scale(loss).backward()  # type: ignore[arg-type]
                    self.scaler.unscale_(self.optimizer)  # type: ignore[arg-type]
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                    self.scaler.step(self.optimizer)  # type: ignore[arg-type]
                    self.scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                    self.optimizer.step()  # type: ignore[union-attr]

                self.global_step += 1
                epoch_loss += float(loss.item())
                if (step + 1) % self.cfg.log_every == 0:
                    log.info("[SFT ep %d/%d step %d/%d] loss=%.4f", ep + 1, epochs, step + 1, steps_per_epoch, epoch_loss / (step + 1))

            self.save_checkpoint(f"sft_ep{ep+1}")

        log.info("[Trainer] SFT concluído.")
