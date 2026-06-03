# Sistema de Subscription Automatizado - Syntexa

## Implementação Completa

### 1. Modelo de Dados (models.py)

Campos adicionados ao modelo `User`:
- `subscription_status`: trial | active | overdue | suspended | cancelled | expired
- `trial_start`, `trial_end`: Período de trial
- `subscription_start`, `subscription_end`: Período da assinatura
- `renewal_date`: Data de renovação
- `payment_status`: pending | paid | failed | overdue | refunded
- `payment_gateway`: stripe | pagarme | pagbank | coinbase
- `payment_gateway_customer_id`: ID do cliente no gateway
- `payment_gateway_subscription_id`: ID da assinatura no gateway
- `last_payment_date`, `last_payment_amount`: Último pagamento
- `payment_failure_count`: Contador de falhas
- `usage_limits`: Limites de uso (JSON)
- `feature_flags`: Features habilitadas (JSON)
- `billing_email`, `billing_name`, `billing_document`: Dados de faturamento
- `grace_period_until`: Período de carência após vencimento

### 2. Core Subscription (core/subscription.py)

Funções principais:
- `init_trial_for_user()`: Inicializa trial de 7 dias
- `check_subscription_status()`: Verifica status atual
- `activate_subscription()`: Ativa após pagamento
- `handle_payment_failure()`: Processa falha de pagamento
- `cancel_subscription()`: Cancela assinatura
- `can_use_feature()`: Verifica acesso a features
- `require_subscription()`: Validação completa
- `increment_usage()`: Incrementa contadores de uso
- `get_usage_stats()`: Retorna estatísticas de uso

### 3. Webhooks de Billing (api/v1/endpoints/webhooks_billing.py)

Webhooks implementados:
- **Stripe**: checkout.session.completed, invoice.paid, invoice.payment_failed, subscription.deleted
- **Pagar.me**: transaction.paid, transaction.refused
- **PagBank**: PAYMENT_CONFIRMED, PAYMENT_DECLINED
- **Coinbase**: charge:confirmed, charge:failed

### 4. API de Subscription (api/v1/endpoints/subscription.py)

Endpoints:
- `GET /subscription/status`: Status completo
- `GET /subscription/plans`: Planos disponíveis
- `GET /subscription/usage`: Uso atual
- `POST /subscription/cancel`: Cancelar
- `POST /subscription/reactivate`: Reativar
- `POST /subscription/upgrade`: Upgrade de plano
- `GET /subscription/check-access`: Verificar acesso a feature
- `GET /subscription/paywall-url`: URL do paywall

### 5. Dependencies (api/deps/subscription.py)

Decorators para proteger rotas:

```python
# Requer subscription ativa
@router.post("/feature")
async def feature(
    user: User = Depends(require_active_subscription),
):
    pass

# Requer feature específica
@router.post("/whatsapp")
async def whatsapp(
    user: User = Depends(require_feature("whatsapp_saas")),
):
    pass

# Requer subscription com redirect
@router.post("/premium")
async def premium(
    user: User = Depends(SubscriptionRequired(feature="premium_ai", redirect=True)),
):
    pass
```

### 6. Trial Automático

Ao verificar email (`/auth/verify-email`):
- Usuário ativado
- Trial de 7 dias iniciado automaticamente
- Status: `trial`
- Notificação enviada

### 7. Fluxo Automatizado

```
1. Cadastro → Email verificado
2. Trial iniciado automaticamente (7 dias)
3. Usuário usa sistema normalmente
4. Trial expira → Status: expired
5. Sistema bloqueia features premium
6. Redireciona para /plans
7. Usuário paga
8. Webhook recebe confirmação
9. Subscription ativada automaticamente
10. Acesso liberado imediatamente
```

### 8. Planos e Limites

| Plano | Mensagens | WhatsApp | Agentes | Automações |
|-------|-----------|----------|---------|------------|
| free | 200/mês | 0 | 0 | 0 |
| basic | 500/mês | 1 | 2 | 5 |
| medium | Ilimitado | 3 | 10 | 50 |
| master | Ilimitado | Ilimitado | Ilimitado | Ilimitado |

### 9. Variáveis de Ambiente

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Pagar.me
PAGARME_API_KEY=ak_live_...
PAGARME_WEBHOOK_SECRET=...

# PagBank
PAGBANK_TOKEN=...
PAGBANK_WEBHOOK_SECRET=...

# Coinbase
COINBASE_API_KEY=...
COINBASE_WEBHOOK_SECRET=...
```

### 10. URLs de Webhook

Configure nos dashboards:

- Stripe: `https://api.syntexabr.com.br/v1/webhooks/stripe`
- Pagar.me: `https://api.syntexabr.com.br/v1/webhooks/pagarme`
- PagBank: `https://api.syntexabr.com.br/v1/webhooks/pagbank`
- Coinbase: `https://api.syntexabr.com.br/v1/webhooks/coinbase`

### 11. Como Proteger Rotas Existentes

```python
from vereda_backend.api.deps import require_active_subscription, require_feature

# Proteger rota de IA
@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    # Só executa se tiver subscription válida
    pass

# Proteger feature específica
@router.post("/whatsapp/send")
async def whatsapp_send(
    message: MessageRequest,
    user: User = Depends(require_feature("whatsapp_saas")),
):
    # Só executa se tiver plano Medium ou superior
    pass

# Verificação manual
@router.post("/export/pdf")
async def export_pdf(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = require_subscription(db, user, feature="export_pdf")
    if not result["allowed"]:
        return {"error": result["error"], "redirect": result["redirect_url"]}
    # Processa exportação
```

### 12. Migração do Banco

Execute no PostgreSQL:

```sql
-- Adicionar colunas de subscription
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(32) DEFAULT 'trial';
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_start TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS renewal_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_status VARCHAR(32) DEFAULT 'pending';
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_gateway VARCHAR(32);
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_gateway_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_gateway_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_payment_amount FLOAT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_failure_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS usage_limits JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS feature_flags JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_document VARCHAR(32);
ALTER TABLE users ADD COLUMN IF NOT EXISTS grace_period_until TIMESTAMP;

-- Atualizar usuários existentes
UPDATE users SET 
    subscription_status = 'free',
    payment_status = 'pending'
WHERE subscription_status IS NULL;
```

### 13. Cron Jobs Recomendados

```bash
# Verificar subscriptions vencidas a cada hora
0 * * * * curl -X POST https://api.syntexabr.com.br/v1/admin/check-expired-subscriptions

# Resetar uso mensal no 1º dia de cada mês
0 0 1 * * curl -X POST https://api.syntexabr.com.br/v1/admin/reset-monthly-usage

# Notificar usuários com trial expirando
0 9 * * * curl -X POST https://api.syntexabr.com.br/v1/admin/notify-expiring-trials
```

## Sistema Completo e Funcional

O sistema está pronto para uso com:
- ✅ Trial automático (7 dias)
- ✅ Controle de acesso por plano
- ✅ Webhooks para 4 gateways
- ✅ Reativação automática
- ✅ Bloqueio automático
- ✅ Período de carência (3 dias)
- ✅ Controle de uso/features
- ✅ API completa
- ✅ Dependencies para proteção de rotas

Sem intervenção manual necessária!
