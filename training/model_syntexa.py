#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class SyntexaConfig:
    vocab_size: int = 32000
    hidden_size: int = 512
    num_layers: int = 8
    num_heads: int = 8
    max_seq_len: int = 1024
    dropout: float = 0.0


class DecoderBlock(nn.Module):
    def __init__(self, hidden: int, heads: int, dropout: float):
        super().__init__()
        self.ln1 = nn.LayerNorm(hidden)
        self.attn = nn.MultiheadAttention(
            embed_dim=hidden,
            num_heads=heads,
            dropout=dropout,
            batch_first=True,
        )
        self.ln2 = nn.LayerNorm(hidden)
        self.ff = nn.Sequential(
            nn.Linear(hidden, hidden * 4),
            nn.GELU(),
            nn.Linear(hidden * 4, hidden),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attn_mask: torch.Tensor | None = None) -> torch.Tensor:
        h = self.ln1(x)
        y, _ = self.attn(h, h, h, attn_mask=attn_mask, need_weights=False)
        x = x + self.dropout(y)
        x = x + self.dropout(self.ff(self.ln2(x)))
        return x


class SyntexaDecoderLM(nn.Module):
    def __init__(self, cfg: SyntexaConfig):
        super().__init__()
        self.cfg = cfg
        self.token_emb = nn.Embedding(cfg.vocab_size, cfg.hidden_size)
        self.pos_emb = nn.Embedding(cfg.max_seq_len, cfg.hidden_size)
        self.blocks = nn.ModuleList(
            [DecoderBlock(cfg.hidden_size, cfg.num_heads, cfg.dropout) for _ in range(cfg.num_layers)]
        )
        self.ln_f = nn.LayerNorm(cfg.hidden_size)
        self.head = nn.Linear(cfg.hidden_size, cfg.vocab_size, bias=False)
        self.head.weight = self.token_emb.weight

    def _causal_mask(self, t: int, device: torch.device) -> torch.Tensor:
        # True nos pontos bloqueados para MultiheadAttention
        return torch.triu(torch.ones(t, t, device=device, dtype=torch.bool), diagonal=1)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        b, t = idx.shape
        if t > self.cfg.max_seq_len:
            idx = idx[:, -self.cfg.max_seq_len :]
            b, t = idx.shape
        pos = torch.arange(0, t, device=idx.device).unsqueeze(0).expand(b, t)
        x = self.token_emb(idx) + self.pos_emb(pos)
        m = self._causal_mask(t, idx.device)
        for blk in self.blocks:
            x = blk(x, attn_mask=m)
        x = self.ln_f(x)
        return self.head(x)

    @torch.no_grad()
    def generate(
        self,
        input_ids: list[int],
        *,
        max_new_tokens: int = 128,
        temperature: float = 0.9,
        top_k: int = 40,
        eos_id: int = 3,
        device: str = "cpu",
    ) -> list[int]:
        self.eval()
        idx = torch.tensor([input_ids], dtype=torch.long, device=device)
        for _ in range(max_new_tokens):
            logits = self.forward(idx)[:, -1, :]
            if temperature <= 0:
                nxt = torch.argmax(logits, dim=-1, keepdim=True)
            else:
                logits = logits / max(1e-5, temperature)
                if top_k > 0:
                    vals, _ = torch.topk(logits, k=min(top_k, logits.size(-1)))
                    cutoff = vals[:, -1].unsqueeze(-1)
                    logits = torch.where(logits < cutoff, torch.full_like(logits, float("-inf")), logits)
                probs = F.softmax(logits, dim=-1)
                nxt = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, nxt], dim=1)
            if int(nxt.item()) == eos_id:
                break
        return idx[0].tolist()
