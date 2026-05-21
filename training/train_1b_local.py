#!/usr/bin/env python3
"""
TREINO SYNTEXA 1B LOCAL
=======================
Treina ~1B parâmetros em CPU com ~7GB RAM.
Técnicas de economia de memória:
- FP16 modelo + gradientes
- Gradient checkpointing
- Batch size 1, seq_len 256
- SGD com momentum (estados FP16, mais leve que AdamW)
- Gradient accumulation (simula batch maior)
- Gradient clipping

Configuração (~1.03B params):
  vocab=32000, dim=1920, layers=24, heads=16, kv_heads=4, hidden=5120

Memória estimada:
  Modelo FP16:     ~2.1 GB
  Gradientes FP16: ~2.1 GB
  Momentum FP16:   ~2.1 GB
  Ativações (b=1,seq=256,cp): ~0.5 GB
  Overhead:        ~0.2 GB
  Total:           ~7.0 GB

Uso:
  python training/train_1b_local.py --data data/syntexa_corpus_real.jsonl \
    --tokenizer checkpoints/foundation/tokenizer --output-dir checkpoints/syntexa_1b
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from vereda_ai.syntexa_core.foundation_model import (
    SyntexaFoundationConfig,
    SyntexaFoundationModel,
)
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer


# ============================================================
# CONFIG 1B (~1.03B params)
# ============================================================

def get_50m_config(vocab_size: int = 32000) -> SyntexaFoundationConfig:
    """~50M params — cabe em ~0.8GB RAM."""
    return SyntexaFoundationConfig(
        vocab_size=vocab_size,
        dim=512,
        num_layers=10,
        num_heads=8,
        num_kv_heads=2,
        max_seq_len=1024,
        hidden_dim=1376,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float16,
    )


def get_100m_config(vocab_size: int = 32000) -> SyntexaFoundationConfig:
    """~100M params — cabe em ~1.5GB RAM."""
    return SyntexaFoundationConfig(
        vocab_size=vocab_size,
        dim=768,
        num_layers=12,
        num_heads=12,
        num_kv_heads=3,
        max_seq_len=1024,
        hidden_dim=2048,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float16,
    )


def get_500m_config(vocab_size: int = 32000) -> SyntexaFoundationConfig:
    """~500M params — cabe em ~4GB RAM para treino."""
    return SyntexaFoundationConfig(
        vocab_size=vocab_size,
        dim=1536,
        num_layers=20,
        num_heads=16,
        num_kv_heads=4,
        max_seq_len=2048,
        hidden_dim=4096,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float16,
    )


def get_1b_config(vocab_size: int = 32000) -> SyntexaFoundationConfig:
    """~1.03B params — requer ~6GB+ RAM."""
    return SyntexaFoundationConfig(
        vocab_size=vocab_size,
        dim=1920,
        num_layers=24,
        num_heads=16,
        num_kv_heads=4,
        max_seq_len=2048,
        hidden_dim=5120,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float16,
    )


# ============================================================
# DATASET
# ============================================================

class TextDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_len: int = 256):
        self.samples = []
        # Concatena textos para formar sequências longas o suficiente
        buffer = []
        eos_id = tokenizer.special_tokens.get("<eos>", 3)
        bos_id = tokenizer.special_tokens.get("<bos>", 2)
        for text in texts:
            toks = tokenizer.encode(text, add_special_tokens=False)
            if len(toks) < 5:
                continue
            # Adiciona BOS no início se buffer vazio
            if not buffer:
                buffer = [bos_id]
            buffer.extend(toks)
            buffer.append(eos_id)
            # Se buffer tem sequência suficiente, extrai chunks
            while len(buffer) >= max_len + 1:
                chunk = buffer[: max_len + 1]
                self.samples.append(chunk)
                buffer = buffer[max_len // 2 :]  # stride = 50% overlap
        # Se sobrar buffer grande o suficiente
        if len(buffer) >= max_len + 1:
            self.samples.append(buffer[: max_len + 1])
        print(f"[DATASET] {len(self.samples)} samples criados (seq_len={max_len})")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        toks = self.samples[idx]
        x = torch.tensor(toks[:-1], dtype=torch.long)
        y = torch.tensor(toks[1:], dtype=torch.long)
        return x, y


# ============================================================
# Otimizador memória-light: SGD + momentum em FP16
# ============================================================

class FP16SGD(torch.optim.Optimizer):
    """SGD com momentum, estados mantidos em FP16 para economia de RAM."""
    def __init__(self, params, lr=1e-3, momentum=0.9, weight_decay=0.1):
        defaults = dict(lr=lr, momentum=momentum, weight_decay=weight_decay)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self):
        for group in self.param_groups:
            lr = group["lr"]
            momentum = group["momentum"]
            wd = group["weight_decay"]
            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad
                if wd != 0:
                    grad = grad.add(p, alpha=wd)
                state = self.state[p]
                if "momentum_buffer" not in state:
                    state["momentum_buffer"] = torch.zeros_like(p, dtype=torch.float16)
                buf = state["momentum_buffer"]
                buf.mul_(momentum).add_(grad, alpha=1 - momentum)
                p.add_(buf, alpha=-lr)


# ============================================================
# TREINAMENTO
# ============================================================

def train(args):
    device = torch.device(args.device)
    print("=" * 60)
    print("  SYNTEXA LOCAL TRAINER")
    print("=" * 60)
    print(f"[DEVICE] {device}")

    # Tokenizer primeiro para saber vocab_size real
    tok_path = Path(args.tokenizer)
    if not tok_path.exists():
        print(f"[ERRO] Tokenizer não encontrado: {tok_path}")
        sys.exit(1)
    tokenizer = SyntexaFoundationTokenizer.load(tok_path)
    vocab_size = tokenizer.vocab_size
    print(f"[OK] Tokenizer: vocab_size={vocab_size}")

    # Detecta RAM e escolhe config
    try:
        import psutil
        ram_gb = psutil.virtual_memory().available / 1024**3
    except ImportError:
        ram_gb = 4.0  # assume 4GB se não conseguir detectar
        print("[AVISO] psutil não instalado — assumindo 4GB RAM")

    print(f"[RAM DISPONIVEL] {ram_gb:.1f} GB")

    # Escolhe config baseada na RAM
    if args.config == "1b":
        cfg = get_1b_config(vocab_size=vocab_size)
        config_name = "1B"
    elif args.config == "500m":
        cfg = get_500m_config(vocab_size=vocab_size)
        config_name = "500M"
    elif args.config == "100m":
        cfg = get_100m_config(vocab_size=vocab_size)
        config_name = "100M"
    elif args.config == "50m":
        cfg = get_50m_config(vocab_size=vocab_size)
        config_name = "50M"
    elif ram_gb >= 6.0:
        cfg = get_1b_config(vocab_size=vocab_size)
        config_name = "1B"
    elif ram_gb >= 3.5:
        cfg = get_500m_config(vocab_size=vocab_size)
        config_name = "500M"
    elif ram_gb >= 1.0:
        cfg = get_100m_config(vocab_size=vocab_size)
        config_name = "100M"
    else:
        print(f"[ERRO] RAM insuficiente: {ram_gb:.1f}GB. Mínimo 0.5GB para 50M.")
        sys.exit(1)

    print(f"[CONFIG] {config_name}: dim={cfg.dim}, layers={cfg.num_layers}, heads={cfg.num_heads}, kv={cfg.num_kv_heads}")

    # Estimativa de parâmetros
    vocab = cfg.vocab_size * cfg.dim
    head_dim = cfg.dim // cfg.num_heads
    attn_per_layer = (
        cfg.dim * (cfg.num_heads * head_dim)          # Q
        + cfg.dim * (cfg.num_kv_heads * head_dim)     # K
        + cfg.dim * (cfg.num_kv_heads * head_dim)     # V
        + cfg.dim * (cfg.num_heads * head_dim)         # O
    )
    ffn_per_layer = 3 * cfg.dim * cfg.hidden_dim
    total_params = vocab + cfg.num_layers * (attn_per_layer + ffn_per_layer)
    print(f"[PARAMS] ~{total_params / 1e9:.2f}B params")

    mem_model = total_params * 2 / 1024**3
    mem_total = mem_model * 3.5  # modelo + grad + opt + overhead
    print(f"[MEM EST] ~{mem_total:.1f} GB necessários")
    if mem_total > ram_gb * 0.95:
        print(f"[AVISO] RAM pode ser insuficiente ({ram_gb:.1f}GB disponível).")
        if not args.force:
            input("Pressione ENTER para continuar mesmo assim...")

    # Dataset
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"[ERRO] Dados não encontrados: {data_path}")
        sys.exit(1)

    print(f"[DATA] Carregando {data_path}...")
    texts = []
    with open(data_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                t = str(obj.get("text", obj.get("instruction", "") + " " + obj.get("output", ""))).strip()
                if len(t) >= 20:
                    texts.append(t)
            except json.JSONDecodeError:
                continue
    print(f"[DATA] {len(texts)} textos carregados")

    if len(texts) < 100:
        print(f"[ERRO] Dataset muito pequeno: {len(texts)} textos (min 100)")
        sys.exit(1)

    dataset = TextDataset(texts, tokenizer, max_len=args.seq_len)
    if len(dataset) == 0:
        print("[ERRO] Nenhum sample gerado. Aumente --seq-len ou verifique os dados.")
        sys.exit(1)

    loader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=0)

    # Modelo
    print("[MODEL] Criando modelo 1B...")
    model = SyntexaFoundationModel(cfg)
    model = model.to(device)
    model = model.half()  # FP16
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[MODEL] {n_params:,} params ({n_params / 1e9:.2f}B)")

    # Ativa gradient checkpointing se disponível
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
        print("[OK] Gradient checkpointing ativado")
    else:
        print("[INFO] Gradient checkpointing não disponível nesta arquitetura")

    # Otimizador memória-light
    optimizer = FP16SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=0.1)
    print("[OPT] FP16 SGD + momentum (estados em FP16)")

    scaler = torch.cuda.amp.GradScaler() if device.type == "cuda" else None

    # Loop
    model.train()
    step = 0
    total_loss = 0.0
    start_time = time.time()
    accumulation_counter = 0

    print("=" * 60)
    print("TREINAMENTO INICIADO")
    print(f"  Steps alvo: {args.max_steps}")
    print(f"  Accumulation: {args.accumulation_steps}")
    print(f"  Seq len: {args.seq_len}")
    print("=" * 60)

    for epoch in range(args.epochs):
        for batch_idx, (x, y) in enumerate(loader):
            x, y = x.to(device), y.to(device)

            # Forward com autocast para FP16
            with torch.cuda.amp.autocast(enabled=(scaler is not None)):
                logits, _ = model(x)
                loss = nn.functional.cross_entropy(
                    logits.view(-1, cfg.vocab_size), y.view(-1)
                )
                loss = loss / args.accumulation_steps

            if scaler is not None:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            total_loss += loss.item() * args.accumulation_steps
            accumulation_counter += 1

            # Step apenas após accumulation
            if accumulation_counter >= args.accumulation_steps:
                # Clip grad
                if scaler is not None:
                    scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

                if scaler is not None:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()

                optimizer.zero_grad(set_to_none=True)
                accumulation_counter = 0
                step += 1

                if step % args.log_every == 0:
                    avg_loss = total_loss / args.log_every
                    elapsed = time.time() - start_time
                    tok_per_sec = (step * args.accumulation_steps * args.seq_len) / elapsed
                    print(f"  step {step:>6} | loss {avg_loss:.4f} | {tok_per_sec:.0f} tok/s | {elapsed:.0f}s")
                    total_loss = 0.0

                if step % args.save_every == 0:
                    _save_checkpoint(model, cfg, tokenizer, args.output_dir, step)

                if step >= args.max_steps:
                    break

        if step >= args.max_steps:
            break

    # Finaliza accumulation pendente
    if accumulation_counter > 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    # Salva final
    final_dir = _save_checkpoint(model, cfg, tokenizer, args.output_dir, "final")

    print("=" * 60)
    print("TREINAMENTO CONCLUIDO")
    print(f"  Steps: {step}")
    print(f"  Params: {n_params:,} ({n_params/1e9:.2f}B)")
    print(f"  Checkpoint: {final_dir / 'model.pt'}")
    print("=" * 60)


def _save_checkpoint(model, cfg, tokenizer, output_dir, step_or_name):
    ckpt_dir = Path(output_dir) / (f"step_{step_or_name}" if isinstance(step_or_name, int) else str(step_or_name))
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    # Salva em FP16 para economia de disco
    torch.save(model.state_dict(), ckpt_dir / "model.pt")
    # Salva config sem torch.dtype (não serializável em JSON)
    cfg_dict = {k: v for k, v in cfg.__dict__.items() if k != "dtype"}
    cfg_dict["dtype"] = "float16"
    (ckpt_dir / "config.json").write_text(json.dumps(cfg_dict, indent=2))
    tokenizer.save(ckpt_dir / "tokenizer")

    # Manifest
    n_params = sum(p.numel() for p in model.parameters())
    manifest = {
        "name": "syntexa_1b",
        "params": n_params,
        "params_b": round(n_params / 1e9, 2),
        "config": "1b",
        "steps": str(step_or_name) if isinstance(step_or_name, int) else step_or_name,
        "checkpoint": str(ckpt_dir / "model.pt"),
        "tokenizer": str(ckpt_dir / "tokenizer"),
    }
    (ckpt_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"  [CKPT] Salvo: {ckpt_dir}")
    return ckpt_dir


def main():
    ap = argparse.ArgumentParser(description="Treino Syntexa em PC local")
    ap.add_argument("--config", default="auto", choices=["auto", "50m", "100m", "500m", "1b"], help="Configuração (auto detecta pela RAM)")
    ap.add_argument("--data", default="data/syntexa_corpus_real.jsonl", help="JSONL com campo text/instruction/output")
    ap.add_argument("--tokenizer", default="checkpoints/tokenizer_1b", help="Diretório do tokenizer")
    ap.add_argument("--output-dir", default="checkpoints/syntexa_local", help="Diretório de checkpoints")
    ap.add_argument("--epochs", type=int, default=10, help="Épocas (default: 10)")
    ap.add_argument("--batch-size", type=int, default=1, help="Batch size (mantenha 1)")
    ap.add_argument("--seq-len", type=int, default=256, help="Comprimento da sequência (default: 256)")
    ap.add_argument("--lr", type=float, default=5e-4, help="Learning rate (default: 5e-4)")
    ap.add_argument("--max-steps", type=int, default=10000, help="Steps máximos (default: 10000)")
    ap.add_argument("--accumulation-steps", type=int, default=4, help="Gradient accumulation (default: 4)")
    ap.add_argument("--log-every", type=int, default=50, help="Log a cada N steps")
    ap.add_argument("--save-every", type=int, default=1000, help="Salva a cada N steps")
    ap.add_argument("--device", default="cpu", help="cpu (única opção no seu PC)")
    ap.add_argument("--force", action="store_true", help="Ignora aviso de RAM")
    args = ap.parse_args()
    train(args)


if __name__ == "__main__":
    main()
