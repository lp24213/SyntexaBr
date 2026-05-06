# Own Model Scripts

Scripts operacionais para a IA própria Syntexa.

## Start runtime

- Linux: `bash scripts/own-model/start-own-model.sh`
- Windows: `powershell -File scripts/own-model/start-own-model.ps1`

## Train + activate

- Linux: `bash scripts/own-model/train-full.sh`
- Windows: `powershell -File scripts/own-model/train-full.ps1`

## Benchmark

- Linux: `bash scripts/own-model/benchmark.sh`
- Windows: `powershell -File scripts/own-model/benchmark.ps1`

## Healthcheck

- Linux: `bash scripts/own-model/healthcheck.sh`
- Windows: `powershell -File scripts/own-model/healthcheck.ps1`

## Switch active model

- Linux: `bash scripts/own-model/switch_active_model.sh http://127.0.0.1:8000 <TOKEN> syntexa_small`
- Windows: `powershell -File scripts/own-model/switch_active_model.ps1 -Api http://127.0.0.1:8000 -Token <TOKEN> -Model syntexa_small`

## One-shot VM provisioning

- Linux (na VM): `bash scripts/own-model/provision_vm_full.sh`
- Windows (remoto via SSH): `powershell -File scripts/own-model/provision_vm_full.ps1 -Host <IP>`

## Blue/Green deploy (com rollback automático)

- Linux:
  - `bash scripts/own-model/deploy_blue_green.sh http://127.0.0.1:8000 <TOKEN> syntexa_small true`
- Windows:
  - `powershell -File scripts/own-model/deploy_blue_green.ps1 -Api http://127.0.0.1:8000 -Token <TOKEN> -Candidate syntexa_small -RollbackOnFail $true`

## Canary promotion (janela de estabilidade)

- Linux:
  - `bash scripts/own-model/promote_canary.sh http://127.0.0.1:8000 <TOKEN> syntexa_small 5 2.0 true`
- Windows:
  - `powershell -File scripts/own-model/promote_canary.ps1 -Api http://127.0.0.1:8000 -Token <TOKEN> -Candidate syntexa_small -Checks 5 -IntervalSec 2.0 -RollbackOnFail $true`

Canário com gate de SLO:
- Linux:
  - `bash scripts/own-model/promote_canary.sh http://127.0.0.1:8000 <TOKEN> syntexa_small 5 2.0 true true 0.08 3500 50`
- Windows:
  - `powershell -File scripts/own-model/promote_canary.ps1 -Api http://127.0.0.1:8000 -Token <TOKEN> -Candidate syntexa_small -Checks 5 -IntervalSec 2.0 -RollbackOnFail $true -EnforceSlo $true -MaxErrorRate 0.08 -MaxP95LatencyMs 3500 -MinRequestsForSlo 50`

## Preflight enterprise

- Linux:
  - `bash scripts/own-model/preflight_enterprise.sh http://127.0.0.1:8000 http://127.0.0.1:9010 <TOKEN_OPCIONAL>`
- Windows:
  - `powershell -File scripts/own-model/preflight_enterprise.ps1 -Api http://127.0.0.1:8000 -Gateway http://127.0.0.1:9010 -Token <TOKEN_OPCIONAL>`

## Backup / restore de registry

- Linux:
  - `bash scripts/own-model/backup_registry.sh`
  - `bash scripts/own-model/restore_registry.sh backups/own-model/syntexa_model_registry-YYYYMMDD-HHMMSS.json`
- Windows:
  - `powershell -File scripts/own-model/backup_registry.ps1`
  - `powershell -File scripts/own-model/restore_registry.ps1 -BackupFile backups/own-model/syntexa_model_registry-YYYYMMDD-HHMMSS.json`

## Assinatura e validação de bundle

- Gerar assinatura:
  - `python scripts/own-model/sign_runtime_bundle.py --bundle-dir dist/own-model-bundle`
- Validar assinatura:
  - `python scripts/own-model/verify_runtime_bundle.py --bundle-dir dist/own-model-bundle`
- Export com assinatura em uma etapa:
  - `python training/export_runtime_bundle.py --manifest checkpoints/syntexa_small/manifest.json --out-dir dist/own-model-bundle --sign`

## Disaster recovery backup (completo)

- Linux:
  - `bash scripts/own-model/disaster_recovery_backup.sh`
- Windows:
  - `powershell -File scripts/own-model/disaster_recovery_backup.ps1`

## Monitor pós deploy (auto rollback por SLO)

- Linux:
  - `bash scripts/own-model/monitor_post_deploy.sh http://127.0.0.1:8000 <TOKEN> syntexa_native 300 15 0.10 4000`
- Windows:
  - `powershell -File scripts/own-model/monitor_post_deploy.ps1 -Api http://127.0.0.1:8000 -Token <TOKEN> -PreviousModel syntexa_native -WindowSec 300 -PollSec 15 -MaxErrorRate 0.10 -MaxP95Ms 4000`
