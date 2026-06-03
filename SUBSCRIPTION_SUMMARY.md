# Sistema de Subscription Automatizado - Syntexa
## ✅ IMPLEMENTADO E PRONTO PARA USO

---

## 🎯 Resumo

Sistema completo de subscription automatizado com **30 dias grátis** de trial para todos os usuários.

---

## 📁 Arquivos Implementados

### Backend (vereda_backend)

| Arquivo | Descrição |
|---------|-----------|
| `core/subscription.py` | Core do sistema - trial, ativação, verificação, limites |
| `api/v1/endpoints/subscription.py` | API REST para gerenciar subscription |
| `api/v1/endpoints/webhooks_billing.py` | Webhooks Stripe, Pagar.me, PagBank, Coinbase |
| `api/deps/subscription.py` | Dependencies para proteger rotas |
| `middleware/subscription.py` | Middleware global de proteção |
| `db/models.py` | Campos de subscription no User |

---

## 🔄 Fluxo Automatizado

```
1. Usuário cadastra conta
   ↓
2. Verifica email
   ↓
3. ✅ TRIAL 30 DIAS ATIVADO AUTOMATICAMENTE
   ↓
4. Usuário usa todas as features normalmente
   ↓
5. Trial expira (30 dias)
   ↓
6. ⚠️ SISTEMA BLOQUEIA AUTOMATICAMENTE
   - Redireciona para /plans
   - Mostra paywall
   - Mantém login/dashboard básico
   ↓
7. Usuário faz pagamento
   ↓
8. 💰 Webhook recebe confirmação AUTOMATICAMENTE
   ↓
9. ✅ Subscription ativada AUTOMATICAMENTE
   ↓
10. 🚀 Acesso liberado IMEDIATAMENTE
```

**SEM INTERVENÇÃO MANUAL!**

---

## 💳 Planos e Preços

| Plano | Preço | Mensagens | WhatsApp | Agentes | Automações |
|-------|-------|-----------|----------|---------|------------|
| **FREE** | Grátis | 200/mês | 0 | 0 | 0 |
| **BASIC** | R$ 39/mês | 500/mês | 1 | 2 | 5 |
| **MEDIUM** | R$ 99/mês | Ilimitado | 3 | 10 | 50 |
| **MASTER** | R$ 199/mês | Ilimitado | Ilimitado | Ilimitado | Ilimitado |

---

## 🔒 Como Proteger Rotas

### Método 1: Dependency (Recomendado)

```python
from vereda_backend.api.deps import require_active_subscription, require_feature

# Requer subscription ativa
@router.post("/chat/completions")
async def chat(
    user: User = Depends(require_active_subscription),
):
    pass

# Requer feature específica
@router.post("/whatsapp/send")
async def whatsapp(
    user: User = Depends(require_feature("whatsapp_saas")),
):
    pass
```

### Método 2: Verificação Manual

```python
from vereda_backend.core.subscription import require_subscription

@router.post("/export/pdf")
async def export_pdf(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = require_subscription(db, user, feature="export_pdf")
    if not result["allowed"]:
        return {
            "error": result["error"],
            "redirect": result["redirect_url"]
        }
    # Processa...
```

### Método 3: Middleware Global

```python
from vereda_backend.middleware.subscription import SubscriptionMiddleware

app.add_middleware(SubscriptionMiddleware)
```

---

## 🔗 URLs de Webhook (Configure nos Dashboards)

| Gateway | URL |
|---------|-----|
| **Stripe** | `https://api.syntexabr.com.br/v1/webhooks/stripe` |
| **Pagar.me** | `https://api.syntexabr.com.br/v1/webhooks/pagarme` |
| **PagBank** | `https://api.syntexabr.com.br/v1/webhooks/pagbank` |
| **Coinbase** | `https://api.syntexabr.com.br/v1/webhooks/coinbase` |

---

## 🌐 Endpoints da API

| Endpoint | Descrição |
|----------|-----------|
| `GET /subscription/status` | Status completo da subscription |
| `GET /subscription/plans` | Lista de planos disponíveis |
| `GET /subscription/usage` | Uso atual do usuário |
| `POST /subscription/cancel` | Cancelar subscription |
| `POST /subscription/reactivate` | Reativar subscription |
| `POST /subscription/upgrade` | Upgrade de plano |
| `GET /subscription/check-access?feature=X` | Verificar acesso a feature |
| `GET /subscription/paywall-url` | URL do paywall |

---

## 🗄️ Migração do Banco

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

---

## ✅ Status de Implementação

- ✅ Modelo de dados completo
- ✅ Trial 30 dias automático
- ✅ Ativação após pagamento
- ✅ Bloqueio automático ao expirar
- ✅ Reativação automática
- ✅ Webhooks para 4 gateways
- ✅ Controle de limites por plano
- ✅ API REST completa
- ✅ Dependencies de proteção
- ✅ Middleware global
- ✅ Período de carência (3 dias)

---

## 🚀 PRONTO PARA DEPLOY!

O sistema está **100% funcional** e automatizado.

**Nenhuma intervenção manual necessária!**

Usuários ganham **30 dias grátis** automaticamente ao verificar email.
Pagamentos são reconhecidos automaticamente via webhooks.
Acesso é liberado imediatamente sem equipe manual.
