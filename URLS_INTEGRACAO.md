# 🔗 URLs de Integração - Syntexa

## Frontend com i18n

### URLs Principais
- **Home**: `https://syntexabr.com.br/i18n/pt-BR/`
- **Chat**: `https://syntexabr.com.br/i18n/pt-BR/chat`
- **Planos**: `https://syntexabr.com.br/i18n/pt-BR/plans`
- **Integrações**: `https://syntexabr.com.br/i18n/pt-BR/integrations`

### Idiomas Suportados
- 🇧🇷 **Português**: `/i18n/pt-BR/`
- 🇺🇸 **English**: `/i18n/en-US/`
- 🇪🇸 **Español**: `/i18n/es-ES/`
- 🇨🇳 **中文**: `/i18n/zh-CN/`

---

## Integrações Meta (WhatsApp, Instagram, Facebook)

### WhatsApp Business
- **Página**: `https://syntexabr.com.br/i18n/pt-BR/integrations`
- **Aba**: WhatsApp Business
- **Ação**: Conectar WhatsApp

### Instagram
- **Página**: `https://syntexabr.com.br/i18n/pt-BR/integrations`
- **Aba**: Instagram
- **Ação**: Conectar Instagram

### Facebook
- **Página**: `https://syntexabr.com.br/i18n/pt-BR/integrations`
- **Aba**: Facebook
- **Ação**: Conectar Facebook

---

## TikTok Business

### URL de Redirecionamento (Callback)
```
https://syntexabr.com.br/i18n/pt-BR/integrations/tiktok/callback
```

### Fluxo de Autenticação
1. Usuário clica em "Conectar TikTok Business"
2. Redireciona para: `https://ads.tiktok.com/i18n/signup?redirect=https%3A%2F%2Fbusiness-api.tiktok.com%2Fportal%2Fapps%2F&_source_=marketing_api`
3. TikTok redireciona de volta para: `https://syntexabr.com.br/i18n/pt-BR/integrations/tiktok/callback?code=XXX&state=YYY`
4. Backend processa o código e retorna token
5. Usuário é redirecionado para integrations com sucesso

### Configuração no TikTok Business API
- **Redirect URI**: `https://syntexabr.com.br/i18n/pt-BR/integrations/tiktok/callback`
- **Scopes**: `business_management`, `ads_management`, `analytics`

---

## Backend APIs

### Integração TikTok Callback
```
POST /v1/integrations/tiktok/callback
Headers:
  Authorization: Bearer {token}
  Content-Type: application/json

Body:
{
  "code": "authorization_code_from_tiktok",
  "state": "state_parameter"
}

Response:
{
  "success": true,
  "message": "TikTok integrado com sucesso",
  "company_id": "xxx",
  "tiktok_account_id": "yyy"
}
```

### Listar Integrações
```
GET /v1/integrations
Headers:
  Authorization: Bearer {token}

Response:
{
  "integrations": [
    {
      "type": "whatsapp",
      "status": "connected",
      "account_id": "xxx"
    },
    {
      "type": "tiktok",
      "status": "connected",
      "account_id": "yyy"
    }
  ]
}
```

---

## Resumo

✅ **Frontend**: Totalmente integrado com i18n em URL
✅ **Integrações**: WhatsApp, Instagram, Facebook, TikTok
✅ **URLs**: Padrão `/i18n/{locale}/{page}`
✅ **TikTok**: Callback handler implementado
✅ **Pronto para Produção**
