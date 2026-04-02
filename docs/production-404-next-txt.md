# Correção 404 para recursos `__next.*.txt` em produção

Em produção (plans, chat, login, register etc.) podem aparecer 404 para requisições a URLs como `__next.*.txt`. Esses recursos **não são gerados** pelo Next.js no export estático; o app usa apenas `/_next/static/...` (JS/CSS).

## Causa provável

- Ferramenta de monitoramento, extensão ou script que pede `__next.*.txt`.
- CDN/proxy que faz health check em caminhos que não existem.

## Solução: regra na borda (host)

Configure o servidor que serve o frontend para **não retornar 404** para esses caminhos (resposta vazia ou 204).

### Nginx

No `server` que serve o frontend (ex.: `syntexabr.com.br`):

```nginx
# Silenciar 404 para __next.*.txt (evitar ruído em logs e métricas)
location ~* ^/__next.*\.txt$ {
    add_header Content-Type text/plain;
    return 204;
}
```

### Cloudflare Pages (Wrangler)

Se usar **Functions** (ex.: `functions/[[path]].ts`), pode tratar:

- `request.url` contendo `__next` e `.txt` → responder com status 204 e body vazio.

Se usar apenas **static** (pasta `out`), não dá para alterar resposta por path; a opção é:

- No **Cloudflare Dashboard** → Workers & Pages → seu projeto → Settings → **Builds & deployments** → ignorar ou
- Criar um **Worker** na zona que intercepte `*__next*.txt` e responda 204.

### Vercel

Em `vercel.json` (na raiz do frontend):

```json
{
  "rewrites": [
    { "source": "/__next/:path*.txt", "destination": "/api/empty" }
  ]
}
```

e um route handler que retorna 204 (ou servir um `.txt` vazio em `public`).

---

Depois de aplicar a regra no seu host, os 404 de `__next.*.txt` deixam de aparecer nas páginas públicas.
