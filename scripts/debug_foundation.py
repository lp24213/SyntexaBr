#!/usr/bin/env python3
"""Debug script para investigar o treinamento da Foundation Model."""
import sys
sys.path.insert(0, r'c:\Users\luisp\OneDrive\Área de Trabalho\syntexabr')

from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer
from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig
import torch
from pathlib import Path

# 1) Verificar tokenizer
tok_dir = Path('checkpoints/foundation/tokenizer')
tok = SyntexaFoundationTokenizer.load(tok_dir)
print(f"Tokenizer vocab: {tok.vocab_size}")

prompt = 'Qual o valor aproximado de PI? Resposta:'
ids = tok.encode(prompt, add_special_tokens=True)
print(f"Prompt: {repr(prompt)}")
print(f"Tokens: {ids}")
print(f"Decode: {repr(tok.decode(ids))}")
for i in ids:
    print(f"  {i}: {repr(tok.inverse_vocab.get(i, '?'))}")

# 2) Verificar modelo
engine = SyntexaInferenceEngine()
engine.load_from_checkpoint('checkpoints/foundation/checkpoint_best.pt', tok_dir)
print(f"\nEngine ready: {engine.is_ready()}")

x = torch.tensor([ids], dtype=torch.long)
logits, _ = engine._model(x)
probs = torch.softmax(logits[0, -1], dim=-1)
top10 = torch.topk(probs, 10)
print("\nTop 10 next tokens:")
for i in range(10):
    tid = top10.indices[i].item()
    p = top10.values[i].item()
    t = tok.inverse_vocab.get(tid, '?')
    print(f"  {tid:4d} {p:.4f} {repr(t)}")

# 3) Gerar tokens
print("\nGeneration:")
for tid in engine._model.generate(x, max_new_tokens=10, temperature=0.7):
    t = tok.inverse_vocab.get(tid, '?')
    print(f"  {tid}: {repr(t)}")
