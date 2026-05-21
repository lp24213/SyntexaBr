#!/usr/bin/env python3
"""Train tokenizer and model with SFT only (no pretrain), focused on PI."""
import sys
sys.path.insert(0, r'c:\Users\luisp\OneDrive\Área de Trabalho\syntexabr')

from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer
from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig
import torch
from pathlib import Path
import json

# 1) Train tokenizer with PI-focused + some general corpus
texts = []
for path in ['data/syntexa_corpus.jsonl', 'data/syntexa_sft.jsonl']:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                t = str(obj.get('text', obj.get('instruction','') + ' ' + obj.get('output',''))).strip()
                if len(t) >= 5:
                    texts.append(t)

tok = SyntexaFoundationTokenizer.train(texts, vocab_size=5000)
tok_dir = Path('checkpoints/foundation/tokenizer')
tok.save(tok_dir)
print(f'Tokenizer: {tok.vocab_size} tokens')

# 2) Generate checkpoint
cfg = SyntexaFoundationConfig(vocab_size=tok.vocab_size, dim=128, num_layers=2, num_heads=2, num_kv_heads=1, max_seq_len=256)
model = SyntexaFoundationModel(cfg)
info = sum(p.numel() for p in model.parameters())
out_dir = Path('checkpoints/foundation')
torch.save({'model_state': model.state_dict(), 'config': cfg.__dict__}, out_dir / 'syntexa_foundation_weights.pt')
with (out_dir/'manifest.json').open('w',encoding='utf-8') as fh:
    json.dump({'name':'syntexa_foundation','vocab_size':cfg.vocab_size,'dim':cfg.dim,'num_layers':cfg.num_layers,'num_heads':cfg.num_heads,'num_kv_heads':cfg.num_kv_heads,'max_seq_len':cfg.max_seq_len,'checkpoint_path':str((out_dir/'syntexa_foundation_weights.pt').resolve()),'tokenizer_dir':str(tok_dir.resolve()),'parameters':info}, fh, ensure_ascii=False, indent=2)
print(f'Checkpoint: {info:,} params')

# 3) SFT only (no pretrain) on PI data
trainer_cfg = TrainingConfig(
    data_path='data/syntexa_corpus.jsonl',
    output_dir='checkpoints/foundation',
    tokenizer_dir=str(tok_dir),
    model_config=cfg,
    epochs=1,
    batch_size=4,
    max_seq_len=14,
    learning_rate=3e-4,
    checkpoint_every_steps=0,
    use_amp=False,
    dtype=torch.float32,
    device='cpu',
    log_every=25,
)
trainer = SyntexaFoundationTrainer(trainer_cfg)

# SFT on PI data for many epochs
print('Starting SFT training...')
trainer.train_sft('data/syntexa_sft.jsonl', epochs=30, steps_per_epoch=100)
print('SFT done')

trainer.save_final(name='syntexa_foundation')
print('Saved final')

# 4) Test
from vereda_ai.syntexa_core.foundation_runtime import SyntexaFoundationRuntime
rt = SyntexaFoundationRuntime('checkpoints/foundation')
rt.load()
msgs = [{'role':'user','content':'Qual o valor aproximado de PI?'}]
resp = rt.chat(msgs, max_new_tokens=32, temperature=0.3)
print('Response:', repr(resp))
