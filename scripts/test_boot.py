#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Users\luisp\OneDrive\Área de Trabalho\syntexabr')

from desktop.backend.boot_validator import run_boot_validation
from vereda_ai.syntexa_core.foundation_runtime import SyntexaFoundationRuntime

rt = SyntexaFoundationRuntime('checkpoints/foundation')
rt.load()
validator = run_boot_validation(rt, checkpoint_dir='checkpoints/foundation')
print('Bootable:', validator.is_bootable())
for r in validator.results:
    status = 'PASS' if r.passed else 'FAIL'
    print(f'  [{status}] {r.name}: {r.error}')
