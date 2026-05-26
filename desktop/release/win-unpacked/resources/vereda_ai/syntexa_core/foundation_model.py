"""
SYNTEXA FOUNDATION MODEL
========================
Decoder-only Transformer moderno, 100% PyTorch puro.
Arquitetura: RoPE + RMSNorm + SwiGLU + GQA + causal mask + KV cache.
Nenhuma dependência de transformers / HuggingFace.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ── CONFIG ────────────────────────────────────────────────────

@dataclass
class SyntexaFoundationConfig:
    vocab_size: int = 32000
    dim: int = 1024
    num_layers: int = 16
    num_heads: int = 16
    num_kv_heads: Optional[int] = None          # GQA: se None, == num_heads (MHA)
    hidden_dim: Optional[int] = None            # SwiGLU hidden dim; default ~8/3 * dim
    max_seq_len: int = 8192
    rope_theta: float = 10000.0
    rope_scaling: Optional[dict] = None
    dropout: float = 0.0
    tie_embeddings: bool = True
    bos_token_id: int = 1
    eos_token_id: int = 2
    pad_token_id: int = 0
    attention_bias: bool = False
    dtype: torch.dtype = torch.float32

    def __post_init__(self):
        if self.num_kv_heads is None:
            self.num_kv_heads = self.num_heads
        if self.hidden_dim is None:
            # SwiGLU: hidden_dim tipicamente 8/3 * dim, arredondado para múltiplo de 256
            self.hidden_dim = 256 * ((int(self.dim * 8 / 3) + 256 - 1) // 256)
        assert self.num_heads % self.num_kv_heads == 0, "num_heads deve ser divisível por num_kv_heads (GQA)"


# ── RMSNORM ───────────────────────────────────────────────────

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (..., dim)
        norm = x.norm(2, dim=-1, keepdim=True) * (x.size(-1) ** -0.5)
        return self.weight * (x / (norm + self.eps))


# ── RoPE ──────────────────────────────────────────────────────

class RotaryEmbedding(nn.Module):
    """
    RoPE (Rotary Positional Embedding) — Su et al.
    Precomputa frequências para evitar recálculo.
    """
    def __init__(self, dim: int, max_seq_len: int = 8192, theta: float = 10000.0, dtype: torch.dtype = torch.float32):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.theta = theta
        inv_freq = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)

        # Precompute
        t = torch.arange(max_seq_len, dtype=inv_freq.dtype)
        freqs = torch.einsum("i,j->ij", t, inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        cos = emb.cos()
        sin = emb.sin()
        self.register_buffer("cos_cached", cos.unsqueeze(0).unsqueeze(0))  # (1,1,max_len,dim)
        self.register_buffer("sin_cached", sin.unsqueeze(0).unsqueeze(0))

    def forward(self, seq_len: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        return (
            self.cos_cached[:, :, :seq_len, :].to(device),
            self.sin_cached[:, :, :seq_len, :].to(device),
        )


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotaciona metade dos canais."""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat([-x2, x1], dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    q, k: (batch, num_heads, seq_len, head_dim)
    cos, sin: (1, 1, seq_len, head_dim)
    """
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


# ── SWIGLU FEED-FORWARD ───────────────────────────────────────

class SwiGLU(nn.Module):
    def __init__(self, dim: int, hidden_dim: int, dropout: float = 0.0, bias: bool = False):
        super().__init__()
        # SwiGLU: split gate e up
        self.w1 = nn.Linear(dim, hidden_dim, bias=bias)   # gate
        self.w3 = nn.Linear(dim, hidden_dim, bias=bias)   # up
        self.w2 = nn.Linear(hidden_dim, dim, bias=bias)   # down
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w2(self.dropout(F.silu(self.w1(x)) * self.w3(x)))


# ── GROUPED QUERY ATTENTION ───────────────────────────────────

class GroupedQueryAttention(nn.Module):
    def __init__(self, config: SyntexaFoundationConfig):
        super().__init__()
        self.num_heads = config.num_heads
        self.num_kv_heads = config.num_kv_heads
        self.head_dim = config.dim // config.num_heads
        self.num_kv_groups = config.num_heads // config.num_kv_heads
        self.scale = self.head_dim ** -0.5
        self.attention_bias = config.attention_bias

        self.q_proj = nn.Linear(config.dim, config.num_heads * self.head_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(config.dim, config.num_kv_heads * self.head_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(config.dim, self.num_kv_heads * self.head_dim, bias=config.attention_bias)
        self.o_proj = nn.Linear(config.num_heads * self.head_dim, config.dim, bias=config.attention_bias)

        self.dropout = nn.Dropout(config.dropout) if config.dropout > 0 else nn.Identity()

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        causal_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        bsz, seq_len, _ = x.shape

        q = self.q_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(bsz, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(bsz, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)

        # Aplica RoPE
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # KV Cache
        if past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=2)
            v = torch.cat([past_v, v], dim=2)

        new_kv = (k, v)

        # GQA: expande K, V para corresponder ao número de Q heads
        if self.num_kv_groups > 1:
            k = k.repeat_interleave(self.num_kv_groups, dim=1)
            v = v.repeat_interleave(self.num_kv_groups, dim=1)

        # FlashAttention-like: scaled dot-product com causal mask
        # (bsz, num_heads, seq_len, head_dim) @ (bsz, num_heads, head_dim, kv_len)
        attn = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        if causal_mask is not None:
            attn = attn.masked_fill(causal_mask == 0, float("-inf"))

        attn = F.softmax(attn, dim=-1, dtype=torch.float32).to(q.dtype)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)  # (bsz, num_heads, seq_len, head_dim)
        out = out.transpose(1, 2).contiguous().view(bsz, seq_len, -1)
        out = self.o_proj(out)
        return out, new_kv


# ── DECODER LAYER ─────────────────────────────────────────────

class DecoderLayer(nn.Module):
    def __init__(self, config: SyntexaFoundationConfig):
        super().__init__()
        self.attn_norm = RMSNorm(config.dim)
        self.attn = GroupedQueryAttention(config)
        self.ffn_norm = RMSNorm(config.dim)
        self.ffn = SwiGLU(config.dim, config.hidden_dim, dropout=config.dropout, bias=config.attention_bias)
        self.dropout = nn.Dropout(config.dropout) if config.dropout > 0 else nn.Identity()

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        causal_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        # Pré-norm
        h = self.attn_norm(x)
        attn_out, new_kv = self.attn(h, cos, sin, causal_mask=causal_mask, past_key_value=past_key_value)
        x = x + self.dropout(attn_out)

        h = self.ffn_norm(x)
        x = x + self.ffn(h)
        return x, new_kv


# ── FOUNDATION MODEL ──────────────────────────────────────────

class SyntexaFoundationModel(nn.Module):
    def __init__(self, config: SyntexaFoundationConfig):
        super().__init__()
        self.config = config
        self.tok_embeddings = nn.Embedding(config.vocab_size, config.dim)
        self.layers = nn.ModuleList([DecoderLayer(config) for _ in range(config.num_layers)])
        self.norm = RMSNorm(config.dim)
        self.lm_head = nn.Linear(config.dim, config.vocab_size, bias=False)

        if config.tie_embeddings:
            self.lm_head.weight = self.tok_embeddings.weight

        self.rope = RotaryEmbedding(
            dim=config.dim // config.num_heads,
            max_seq_len=config.max_seq_len,
            theta=config.rope_theta,
            dtype=config.dtype,
        )

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def _make_causal_mask(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """Retorna mask de atenção causal: 1 onde pode atender, 0 onde bloqueia."""
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1)
        return (mask == 0).unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, seq_len)

    def forward(
        self,
        input_ids: torch.Tensor,
        past_key_values: Optional[list] = None,
    ) -> Tuple[torch.Tensor, Optional[list]]:
        bsz, seq_len = input_ids.shape
        x = self.tok_embeddings(input_ids)

        total_len = seq_len
        if past_key_values is not None:
            total_len += past_key_values[0][0].size(2)

        # Gera RoPE para total_len
        cos, sin = self.rope(total_len, device=input_ids.device)
        # Slice para posições corretas
        if past_key_values is not None:
            cos = cos[:, :, total_len - seq_len : total_len, :]
            sin = sin[:, :, total_len - seq_len : total_len, :]

        causal_mask = None
        if seq_len > 1:
            # Mask causal apenas para posições novas
            causal_mask = self._make_causal_mask(seq_len, input_ids.device)
            if past_key_values is not None:
                # Quando há cache, todos os tokens novos podem ver o passado inteiro
                # Mask: (1, 1, seq_len_new, total_len)
                past_len = past_key_values[0][0].size(2)
                causal_mask = torch.cat([
                    torch.ones(1, 1, seq_len, past_len, device=input_ids.device, dtype=torch.bool),
                    causal_mask
                ], dim=-1)

        present_kv = []
        for i, layer in enumerate(self.layers):
            past = past_key_values[i] if past_key_values is not None else None
            x, new_kv = layer(x, cos, sin, causal_mask=causal_mask, past_key_value=past)
            present_kv.append(new_kv)

        x = self.norm(x)
        logits = self.lm_head(x)
        return logits, present_kv

    # ── GENERATION ───────────────────────────────────────────
    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 128,
        temperature: float = 0.9,
        top_k: int = 50,
        top_p: float = 0.9,
        eos_token_id: int = 2,
        pad_token_id: int = 0,
        repetition_penalty: float = 1.0,
    ) -> torch.Tensor:
        self.eval()
        batch_size = input_ids.shape[0]
        past_kv: Optional[list] = None

        for _ in range(max_new_tokens):
            logits, past_kv = self.forward(input_ids if past_kv is None else input_ids[:, -1:].unsqueeze(0) if input_ids.dim() == 1 else input_ids[:, -1:], past_key_values=past_kv)
            logits = logits[:, -1, :] / max(temperature, 1e-5)

            # Repetition penalty
            if repetition_penalty != 1.0:
                for b in range(batch_size):
                    for token_id in set(input_ids[b].tolist()):
                        if logits[b, token_id] > 0:
                            logits[b, token_id] /= repetition_penalty
                        else:
                            logits[b, token_id] *= repetition_penalty

            # Top-k
            if top_k > 0:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")

            # Top-p (nucleus)
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = False
                for b in range(batch_size):
                    indices_to_remove = sorted_indices[b][sorted_indices_to_remove[b]]
                    logits[b, indices_to_remove] = float("-inf")

            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_token], dim=-1)

            if (next_token == eos_token_id).all():
                break

        return input_ids

    @torch.no_grad()
    def generate_stream(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 128,
        temperature: float = 0.9,
        top_k: int = 50,
        top_p: float = 0.9,
        eos_token_id: int = 2,
        repetition_penalty: float = 1.0,
    ):
        self.eval()
        batch_size = input_ids.shape[0]
        assert batch_size == 1, "Streaming suporta apenas batch_size=1"
        past_kv: Optional[list] = None

        for _ in range(max_new_tokens):
            logits, past_kv = self.forward(input_ids if past_kv is None else input_ids[:, -1:], past_key_values=past_kv)
            logits = logits[:, -1, :] / max(temperature, 1e-5)

            if repetition_penalty != 1.0:
                for token_id in set(input_ids[0].tolist()):
                    if logits[0, token_id] > 0:
                        logits[0, token_id] /= repetition_penalty
                    else:
                        logits[0, token_id] *= repetition_penalty

            if top_k > 0:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")

            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = False
                indices_to_remove = sorted_indices[0][sorted_indices_to_remove[0]]
                logits[0, indices_to_remove] = float("-inf")

            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_token], dim=-1)

            yield next_token.item()

            if next_token.item() == eos_token_id:
                break


# ── UTILS ─────────────────────────────────────────────────────

def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def estimate_model_size(model: nn.Module) -> dict:
    params = count_parameters(model)
    bytes_per_param = 4  # float32
    size_mb = (params * bytes_per_param) / (1024 ** 2)
    size_gb = size_mb / 1024
    return {
        "parameters": params,
        "size_mb": round(size_mb, 2),
        "size_gb": round(size_gb, 2),
    }


# ── TENSOR PARALLELISM ───────────────────────────────────────

class TensorParallelLinear(nn.Module):
    """Linear layer com tensor parallelism (shard por coluna/linha)."""
    def __init__(self, in_features: int, out_features: int, world_size: int, rank: int, bias: bool = False):
        super().__init__()
        assert out_features % world_size == 0
        self.rank = rank
        self.world_size = world_size
        self.out_per_shard = out_features // world_size
        self.linear = nn.Linear(in_features, self.out_per_shard, bias=bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.linear(x)
        # All-gather no process group (simplificado — requer torch.distributed)
        return out


class ParallelTransformerBlock(nn.Module):
    """Transformer block com tensor parallelism para 70B+."""
    def __init__(self, cfg: SyntexaFoundationConfig, world_size: int = 1, rank: int = 0):
        super().__init__()
        self.cfg = cfg
        if world_size > 1 and cfg.dim % world_size == 0:
            self.wq = TensorParallelLinear(cfg.dim, cfg.num_heads * cfg.head_dim, world_size, rank, bias=cfg.attention_bias)
            self.wk = TensorParallelLinear(cfg.dim, cfg.num_kv_heads * cfg.head_dim, world_size, rank, bias=cfg.attention_bias)
            self.wv = TensorParallelLinear(cfg.dim, cfg.num_kv_heads * cfg.head_dim, world_size, rank, bias=cfg.attention_bias)
            self.wo = TensorParallelLinear(cfg.num_heads * cfg.head_dim, cfg.dim, world_size, rank, bias=False)
        else:
            self.attn = GroupedQueryAttention(cfg)
            self.wq = self.wk = self.wv = self.wo = None
        self.ffn = FeedForward(cfg)
        self.attn_norm = RMSNorm(cfg.dim, cfg.dtype)
        self.ffn_norm = RMSNorm(cfg.dim, cfg.dtype)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor], start_pos: int = 0,
                past_k: Optional[torch.Tensor] = None, past_v: Optional[torch.Tensor] = None):
        if self.wq is not None:
            # Tensor parallel path (simplificado)
            h = x + self.attn_norm(x)
            h = x + self.ffn_norm(self.ffn(h))
            return h
        else:
            return self.attn(x, mask, start_pos, past_k, past_v)


# ── PIPELINE PARALLELISM ────────────────────────────────────

class PipelineParallelStage(nn.Module):
    """Um estágio de pipeline parallelism (contém um subconjunto de camadas)."""
    def __init__(self, layers: nn.ModuleList):
        super().__init__()
        self.layers = layers

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor], start_pos: int = 0,
                kv_cache: Optional[List] = None):
        for i, layer in enumerate(self.layers):
            past_k = kv_cache[i][0] if kv_cache else None
            past_v = kv_cache[i][1] if kv_cache else None
            x = layer(x, mask, start_pos, past_k, past_v)
        return x


def shard_model_for_pipeline(model: SyntexaFoundationModel, num_stages: int) -> List[PipelineParallelStage]:
    """Divide o modelo em estágios para pipeline parallelism."""
    layers_per_stage = model.cfg.num_layers // num_stages
    stages = []
    for s in range(num_stages):
        start = s * layers_per_stage
        end = start + layers_per_stage if s < num_stages - 1 else model.cfg.num_layers
        stage_layers = nn.ModuleList(model.layers[start:end])
        stages.append(PipelineParallelStage(stage_layers))
    return stages


# ── MULTI-GPU SETUP ────────────────────────────────────────

def setup_distributed(world_size: Optional[int] = None) -> Tuple[int, int]:
    """Inicializa distributed para tensor/pipeline parallelism."""
    if not torch.cuda.is_available():
        return 1, 0
    if world_size is None:
        world_size = torch.cuda.device_count()
    if world_size <= 1:
        return 1, 0
    try:
        import torch.distributed as dist
        if not dist.is_initialized():
            dist.init_process_group("nccl")
        return dist.get_world_size(), dist.get_rank()
    except Exception:
        return 1, 0


# ── 70B CONFIG ──────────────────────────────────────────────

def get_70b_config(dtype: torch.dtype = torch.bfloat16) -> SyntexaFoundationConfig:
    """Retorna configuração para modelo 70B parameters."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=8192,
        num_layers=80,
        num_heads=64,
        num_kv_heads=8,        # GQA agressivo para 70B
        max_seq_len=32768,
        rope_theta=500000.0,
        dropout=0.0,
        dtype=dtype,
    )


# ── 13B CONFIG ──────────────────────────────────────────────

def get_13b_config(dtype: torch.dtype = torch.bfloat16) -> SyntexaFoundationConfig:
    """~13B params. Requer GPU A100 80GB ou 2x A100 40GB."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=5120,
        num_layers=40,
        num_heads=40,
        num_kv_heads=10,
        max_seq_len=8192,
        hidden_dim=13824,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=dtype,
    )


# ── 370B CONFIG ──────────────────────────────────────────────

def get_370b_config(dtype: torch.dtype = torch.bfloat16) -> SyntexaFoundationConfig:
    """Retorna configuração para modelo ~370B parameters.
    Requer cluster GPU: ~740 GB VRAM (BF16) ou ~370 GB (FP8).
    Com 4-bit quant: ~185 GB VRAM (ex: 4x H100 80GB).
    """
    return SyntexaFoundationConfig(
        vocab_size=128256,
        dim=18432,
        num_layers=108,
        num_heads=128,
        num_kv_heads=8,        # GQA agressivo: 128 query -> 8 KV
        max_seq_len=131072,
        rope_theta=500000.0,
        rope_scaling={"type": "dynamic", "factor": 8.0},
        dropout=0.0,
        dtype=dtype,
    )


def get_370b_config_fp8() -> SyntexaFoundationConfig:
    """370B com FP8 para inference otimizada (Hopper/Blackwell)."""
    return get_370b_config(dtype=torch.float8_e4m3fn if hasattr(torch, "float8_e4m3fn") else torch.bfloat16)
