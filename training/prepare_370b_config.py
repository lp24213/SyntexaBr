#!/usr/bin/env python3
"""Gera config, manifest e estatísticas do modelo Syntexa 370B.
NÃO instancia o modelo na RAM (meta-device apenas)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vereda_ai.syntexa_core.foundation_model import get_370b_config


def calc_params(cfg) -> dict:
    """Calcula parâmetros teóricos sem instanciar na RAM."""
    d = cfg.dim
    n_layers = cfg.num_layers
    n_heads = cfg.num_heads
    n_kv = cfg.num_kv_heads
    v = cfg.vocab_size
    h = cfg.hidden_dim

    # Embedding
    embed = v * d

    # Per layer
    head_dim = d // n_heads
    # Q: d * (n_heads * head_dim) = d*d
    # K: d * (n_kv * head_dim) = d * d * n_kv/n_heads
    # V: d * (n_kv * head_dim) = d * d * n_kv/n_heads
    # O: (n_heads * head_dim) * d = d*d
    attn_params = d * d + 2 * (d * d * n_kv / n_heads) + d * d
    # FFN: w1(d*h), w3(d*h), w2(h*d) = 3*d*h
    ffn_params = 3 * d * h
    # Norms: 2 * d (negligível)
    layer_params = attn_params + ffn_params

    total = embed + n_layers * layer_params
    # lm_head tied -> não conta extra

    return {
        "vocab_size": v,
        "dim": d,
        "num_layers": n_layers,
        "num_heads": n_heads,
        "num_kv_heads": n_kv,
        "head_dim": head_dim,
        "hidden_dim": h,
        "max_seq_len": cfg.max_seq_len,
        "rope_theta": cfg.rope_theta,
        "embedding_params": int(embed),
        "attention_params_per_layer": int(attn_params),
        "ffn_params_per_layer": int(ffn_params),
        "layer_params": int(layer_params),
        "total_params": int(total),
        "total_params_b": round(total / 1e9, 2),
    }


def calc_memory(params: int, dtype_bits: int = 16) -> dict:
    """Calcula requisitos de memória."""
    bytes_per_param = dtype_bits / 8
    model_gb = params * bytes_per_param / (1024 ** 3)
    # Optimizer states (AdamW): 2x params (momentum + variance)
    optimizer_gb = params * 4 * 2 / (1024 ** 3)  # float32
    # Gradients: float32
    grad_gb = params * 4 / (1024 ** 3)
    # Activations (batch=1, seq=4096, roughly)
    activation_gb = model_gb * 0.5
    total_train_gb = model_gb + optimizer_gb + grad_gb + activation_gb

    return {
        "dtype_bits": dtype_bits,
        "model_only_gb": round(model_gb, 1),
        "optimizer_gb": round(optimizer_gb, 1),
        "gradients_gb": round(grad_gb, 1),
        "activations_est_gb": round(activation_gb, 1),
        "total_training_gb": round(total_train_gb, 1),
        "inference_bf16_gb": round(model_gb, 1),
        "inference_fp8_gb": round(model_gb / 2, 1),
        "inference_int4_gb": round(model_gb / 4, 1),
    }


def calc_hardware(req_gb: float) -> dict:
    """Recomendação de hardware."""
    # H100 80GB
    h100_80 = math.ceil(req_gb / 80)
    # H100 96GB (SXM5)
    h100_96 = math.ceil(req_gb / 96)
    # H200 141GB
    h200 = math.ceil(req_gb / 141)
    # B200 (Blackwell, ~180GB est.)
    b200 = math.ceil(req_gb / 180)

    return {
        "h100_80gb_needed": h100_80,
        "h100_96gb_needed": h100_96,
        "h200_141gb_needed": h200,
        "b200_est_needed": b200,
    }


def main() -> None:
    cfg = get_370b_config()
    stats = calc_params(cfg)
    mem = calc_memory(stats["total_params"], dtype_bits=16)
    hw_bf16 = calc_hardware(mem["inference_bf16_gb"])
    hw_fp8 = calc_hardware(mem["inference_fp8_gb"])
    hw_int4 = calc_hardware(mem["inference_int4_gb"])

    out_dir = Path("checkpoints/foundation_370b")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": "syntexa_370b",
        "family": "decoder_transformer",
        "stage": "foundation_config",
        "parameters": stats["total_params"],
        "parameters_b": stats["total_params_b"],
        "vocab_size": stats["vocab_size"],
        "dim": stats["dim"],
        "num_layers": stats["num_layers"],
        "num_heads": stats["num_heads"],
        "num_kv_heads": stats["num_kv_heads"],
        "head_dim": stats["head_dim"],
        "hidden_dim": stats["hidden_dim"],
        "max_seq_len": stats["max_seq_len"],
        "rope_theta": stats["rope_theta"],
        "rope_scaling": cfg.rope_scaling,
        "dtype": str(cfg.dtype),
        "memory_requirements": mem,
        "hardware_recommendations": {
            "bf16_inference": hw_bf16,
            "fp8_inference": hw_fp8,
            "int4_inference": hw_int4,
        },
        "config_path": str((out_dir / "config.json").resolve()),
        "status": "config_ready",
    }

    (out_dir / "config.json").write_text(
        json.dumps(cfg.__dict__, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "stats.json").write_text(
        json.dumps({"params": stats, "memory": mem, "hardware": {"bf16": hw_bf16, "fp8": hw_fp8, "int4": hw_int4}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("SYNTEXA FOUNDATION MODEL 370B")
    print("=" * 60)
    print(f"  Total params:     {stats['total_params']:,} ({stats['total_params_b']}B)")
    print(f"  Vocab size:       {stats['vocab_size']:,}")
    print(f"  Dim:              {stats['dim']}")
    print(f"  Layers:           {stats['num_layers']}")
    print(f"  Heads:            {stats['num_heads']} (Q) / {stats['num_kv_heads']} (KV)")
    print(f"  Head dim:         {stats['head_dim']}")
    print(f"  Hidden dim:       {stats['hidden_dim']}")
    print(f"  Max seq len:      {stats['max_seq_len']}")
    print(f"  RoPE theta:       {stats['rope_theta']}")
    print()
    print("MEMORY REQUIREMENTS")
    print(f"  BF16 model only:  {mem['inference_bf16_gb']} GB")
    print(f"  FP8  model only:  {mem['inference_fp8_gb']} GB")
    print(f"  INT4 model only:  {mem['inference_int4_gb']} GB")
    print(f"  Training total:   {mem['total_training_gb']} GB")
    print()
    print("HARDWARE RECOMMENDATIONS (INFERENCE)")
    print(f"  BF16: {hw_bf16['h100_80gb_needed']}x H100 80GB | {hw_bf16['h200_141gb_needed']}x H200 141GB")
    print(f"  FP8:  {hw_fp8['h100_80gb_needed']}x H100 80GB | {hw_fp8['h200_141gb_needed']}x H200 141GB")
    print(f"  INT4: {hw_int4['h100_80gb_needed']}x H100 80GB | {hw_int4['h200_141gb_needed']}x H200 141GB")
    print()
    print("HARDWARE RECOMMENDATIONS (TRAINING BF16)")
    print(f"  Est. {mem['total_training_gb']} GB total (model + optimizer + grad + activ)")
    print(f"  ~{math.ceil(mem['total_training_gb'] / 80)}x H100 80GB ou ~{math.ceil(mem['total_training_gb'] / 141)}x H200 141GB")
    print()
    print("OUTPUT")
    print(f"  Config:   {out_dir / 'config.json'}")
    print(f"  Manifest: {out_dir / 'manifest.json'}")
    print(f"  Stats:    {out_dir / 'stats.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
