# Nós de API (referência)

| Nó | Região | IP público | vCPU & SKU | Notas |
|----|--------|------------|------------|--------|
| **1** (original) | Brazil South | `74.163.97.52` | E4s_v3 (4) | Carga em `/opt/syntexa` — lista `config/syntexa-prod-nodes.txt` |
| **2** (replica) | West Europe | `51.124.194.42` | D4s_v5 (4) | Idem; mesma **base PostgreSQL** na Azure (não SQLite) |

- **brasil south** atingiu a quota de vCPUs (4/4) — não dá para outra VM grande aí; o nó 2 foi em **westeurope** (quota livre 4/4 aí).
- **Duas regiões, um estado:** **Azure Database for PostgreSQL (Flexible Server)** com `DATABASE_URL=...@....postgres.database.azure.com:5432/...?sslmode=require` **idêntico** em `/opt/syntexa/.env` nas duas máquinas. **Firewall do servidor PG:** regra(s) com o IP de saída pública de cada VM (cada nó o seu) ou 0.0.0.0-255 se a política o permitir.
- Sem essa partilha, sobra SQLite / estado partido e as duas VMs **não** alinham como um único back-end. Não fazer commit de `DATABASE_URL` com password.
- **Tráfego em `api.syntexabr.com.br`:** Load Balancing (Cloudflare com 2 origens, ou outro) em frente destes nós. Certificados e `health` em ambos.
- **Redis (fila / cache):** serviço compartilhado acessível de todas as VMs; ver `.env.example`.

## 1) A mesma URL PostgreSQL nas duas VMs + deploy de código

1. Azure Portal: Flexible Server → **Networking** → regras para o IP de cada VM.
2. No PC, após o deploy ter criado base em ambas, exportar a **mesma** URL (só 1.ª linha) pode usar ficheiro local: `config/syntexa-pg.url.local` (ignorado pelo git):

```bash
# export directo:
export SYNTEXA_AZURE_DATABASE_URL='postgresql+psycopg2://...?sslmode=require'
# ou: export SYNTEXA_AZURE_DATABASE_URL_FILE=config/syntexa-pg.url.local

bash scripts/push-pg-url-to-syntexa-vms.sh
bash scripts/migrate-db-on-syntexa-vm.sh
```

3. Atualizar código n ambas (tar + `remote_deploy_back`):

```bash
bash scripts/deploy-backend-both-nodes.sh
```

## Deploy nó 2 (PowerShell, alternativa a um nó de cada vez)

```powershell
$env:SYNTEXA_REMOTE_HOST = "51.124.194.42"
cd <repo>
.\deploy-syntexa.ps1 deploy-back
```

## Aumentar quota (mais nós / SKUs no Brasil)

Portal → Subscrição → **Usage + quotas** → **Request increase** (Total Regional vCPUs) em `brazilsouth`.
