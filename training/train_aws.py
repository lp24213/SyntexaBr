#!/usr/bin/env python3
"""Treino progressivo Syntexa na AWS t3.medium (4GB RAM)."""
import json
import os
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, "/opt/syntexa")
from foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from foundation_tokenizer import SyntexaFoundationTokenizer

DATA_FILE = "/opt/syntexa/data.jsonl"
CKPT_DIR = Path("/opt/syntexa/checkpoints")
CKPT_DIR.mkdir(exist_ok=True)

# Configs progressivas: 30M -> 60M -> 100M -> 200M -> 300M -> 500M
CONFIGS = [
    ("30M", 512, 8, 8, 2, 1024, 1376),
    ("60M", 768, 10, 12, 3, 1024, 2048),
    ("100M", 768, 14, 12, 3, 1024, 2048),
    ("200M", 1024, 16, 16, 4, 2048, 2816),
    ("300M", 1280, 18, 20, 5, 2048, 3520),
    ("500M", 1536, 22, 24, 6, 2048, 4096),
]

def count_params(model):
    return sum(p.numel() for p in model.parameters())

def load_data(tokenizer, seq_len=256):
    texts = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                texts.append(json.loads(line).get("text", ""))
    
    # Concatena tudo e splita em sequencias
    all_ids = []
    for t in texts:
        all_ids.extend(tokenizer.encode(t, add_special_tokens=False))
    
    samples = []
    for i in range(0, len(all_ids) - seq_len, seq_len):
        samples.append(all_ids[i:i+seq_len+1])
    
    print(f"[DATA] {len(samples)} samples (seq_len={seq_len})")
    return samples

def train_model(name, dim, layers, heads, kv, max_seq, hidden, tokenizer, data, epochs=3):
    vocab_size = tokenizer.vocab_size
    cfg = SyntexaFoundationConfig(
        vocab_size=vocab_size,
        dim=dim,
        num_layers=layers,
        num_heads=heads,
        num_kv_heads=kv,
        max_seq_len=max_seq,
        hidden_dim=hidden,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )
    
    device = torch.device("cpu")
    model = SyntexaFoundationModel(cfg).to(device)
    params = count_params(model)
    print(f"\n[TRAIN] {name}: {params:,} params ({params/1e6:.1f}M)")
    
    # Verifica se cabe na RAM
    model_mem = params * 4 / 1024**3  # FP32
    print(f"[TRAIN] Mem modelo: {model_mem:.2f}GB")
    if model_mem > 2.5:
        print(f"[SKIP] {name} nao cabe na RAM (limite ~2.5GB)")
        return None
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4)
    model.train()
    
    total_steps = len(data) * epochs
    step = 0
    start_time = time.time()
    
    for epoch in range(epochs):
        random.shuffle(data)
        epoch_loss = 0.0
        
        for sample in data:
            x = torch.tensor([sample[:-1]], dtype=torch.long, device=device)
            y = torch.tensor([sample[1:]], dtype=torch.long, device=device)
            
            logits, _ = model(x)
            loss = F.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            step += 1
            
            if step % 500 == 0:
                elapsed = time.time() - start_time
                print(f"  [STEP {step}/{total_steps}] loss={loss.item():.4f} | {elapsed:.1f}s")
        
        avg_loss = epoch_loss / len(data)
        print(f"[EPOCH {epoch+1}/{epochs}] avg_loss={avg_loss:.4f}")
    
    # Salva
    ckpt_path = CKPT_DIR / f"model_{name}.pt"
    torch.save(model.state_dict(), ckpt_path)
    
    # Salva config
    cfg_dict = {
        "vocab_size": vocab_size,
        "dim": dim,
        "num_layers": layers,
        "num_heads": heads,
        "num_kv_heads": kv,
        "max_seq_len": max_seq,
        "hidden_dim": hidden,
        "rope_theta": 10000.0,
        "dropout": 0.1,
        "dtype": "float32",
    }
    (CKPT_DIR / f"config_{name}.json").write_text(json.dumps(cfg_dict))
    
    print(f"[SAVE] {ckpt_path}")
    return model

def main():
    print("=" * 50)
    print("SYNTEXA AWS TRAINER")
    print("=" * 50)
    
    # Carrega tokenizer
    print("[LOAD] Tokenizer...")
    tokenizer = SyntexaFoundationTokenizer.load("/opt/syntexa/tokenizer")
    print(f"[LOAD] Vocab: {tokenizer.vocab_size}")
    
    # Carrega dados
    print("[LOAD] Dados...")
    data = load_data(tokenizer, seq_len=256)
    
    if len(data) < 100:
        print("[ERRO] Poucos dados!")
        sys.exit(1)
    
    # Treina progressivamente
    for name, dim, layers, heads, kv, max_seq, hidden in CONFIGS:
        train_model(name, dim, layers, heads, kv, max_seq, hidden, tokenizer, data)
    
    print("\n[DONE] Treino concluido!")

if __name__ == "__main__":
    main()
