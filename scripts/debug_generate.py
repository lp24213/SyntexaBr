#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Users\luisp\OneDrive\Área de Trabalho\syntexabr')

from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
import torch

engine = SyntexaInferenceEngine()
engine.load_from_checkpoint('checkpoints/foundation/syntexa_foundation_weights.pt', 'checkpoints/foundation/tokenizer')
print('Ready:', engine.is_ready())

tok = engine._tokenizer
prompt = 'Qual o valor aproximado de PI? Resposta:'
ids = tok.encode(prompt, add_special_tokens=True)
print(f'Prompt: {repr(prompt)}')
print(f'Tokens: {ids}')
for i in ids:
    print(f'  {i}: {repr(tok.inverse_vocab.get(i, "?"))}')

x = torch.tensor([ids], dtype=torch.long)

# Generate one token at a time
model = engine._model
model.eval()
with torch.no_grad():
    for step in range(15):
        logits, _ = model(x)
        next_logits = logits[0, -1, :]
        probs = torch.softmax(next_logits, dim=-1)
        top5 = torch.topk(probs, 5)
        next_id = top5.indices[0].item()
        print(f'Step {step}: next_id={next_id} ({repr(tok.inverse_vocab.get(next_id, "?"))}), prob={top5.values[0].item():.4f}')
        print(f'  Top5: {[(tid.item(), repr(tok.inverse_vocab.get(tid.item(), "?")), p.item()) for tid, p in zip(top5.indices, top5.values)]}')
        if next_id == tok.special_tokens['<eos>']:
            print('  <eos> reached')
            break
        x = torch.cat([x, torch.tensor([[next_id]], dtype=torch.long)], dim=1)

print('Final:', repr(tok.decode(x[0].tolist())))
