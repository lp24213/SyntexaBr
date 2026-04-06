# Arquitetura Syntexa — escala massiva (milhões de usuários)

**Objetivo:** suportar crescimento horizontal, segurança reforçada e tráfego global **sem** quebrar o que já funciona hoje (FastAPI monolítico, Cloudflare Pages, Hetzner).

**Princípio:** evolução **incremental** — cada fase entrega valor e pode ser revertida; o monólito atual permanece a “fonte da verdade” até a extração gradual de serviços.

---

## 1. Visão em 4 camadas

| Camada | Tecnologia | Função |
|--------|------------|--------|
| **1 — Frontend** | Cloudflare Pages | UI estática/SSR export, cache global de assets, baixa latência |
| **2 — Edge** | Cloudflare Workers + WAF + Rate Limiting (Cloudflare) | Terminação TLS, roteamento `/api`, políticas, cache seletivo |
| **3 — Core API** | Hetzner (VM ou futuro K8s) **só rede privada** | Auth, chat, educação, mídia, negócio — sem IP público na app |
| **4 — AI / processamento** | Hetzner nós dedicados (CPU leve / GPU pesado) | Inferência, geração de imagem, jobs longos — isolados da API síncrona |

**Regra de ouro:** o backend de aplicação **não** precisa de IP público se o **Cloudflare Tunnel** (cloudflared) ou **Load Balancer privado** encaminha tráfego apenas a partir da edge Cloudflare (origem confiável + mTLS opcional).

---

## 2. Edge (Cloudflare) — crítico

### Hoje (provável)
- DNS `api.*` apontando para IP público do Hetzner ou túnel.
- Worker de gateway (`gateway_worker.js`) faz proxy para `BACKEND_BASE_URL`.

### Meta
- **Cloudflare Tunnel** do Hetzner → `*.cfargotunnel.com` ou hostname dedicado, **sem** abrir 443 na VPS para o mundo (apenas saída para Cloudflare).
- **Rate limiting** na edge: regras por rota (`/v1/auth/login`, `/public-chat`), por IP e por token (via Workers KV ou Rate Limiting API).
- **WAF**: regras OWASP, bloqueio de países se necessário, challenge em abuso.
- **Cache GET**: apenas rotas idempotentes e com `Cache-Control` explícito (`/health`, documentação pública, assets); **nunca** cachear respostas autenticadas por padrão.
- **Validação na edge**: assinatura de JWT opaca ou verificação de `Authorization` com chave pública (JWKS) no Worker — reduz carga no core (implementação gradual).

### Roteamento inteligente
- Worker escolhe **pool** de origens (API A/B, região) com base em header, cookie ou geolocalização.
- Health checks no Worker → fallback para nó secundário.

---

## 3. Backend no Hetzner (core)

### Estado atual
- Monólito FastAPI (`vereda_backend`) — adequado para escalar **verticalmente** e depois **horizontalmente** com várias réplicas idênticas.

### Meta (sem big-bang)
1. **Duas ou mais instâncias** do mesmo app atrás de **NGINX** ou **HAProxy** (sticky session opcional para SSE).
2. **Rede privada Hetzner** (`10.x`): apenas LB/Tunnel fala com as VMs API.
3. **Separação lógica** (primeiro por **módulos** no código, depois por **serviços**):
   - `auth` → pode virar serviço quando houver fila de eventos e SSO.
   - `chat` / `media` → candidatos a escalar GPU separado.

**Microserviços completos** (Auth, Chat, Education, Gov, Media) são **fase tardia**: exigem contratos API versionados, observabilidade e CI/CD por serviço. Até lá: **monólito modular** + **workers assíncronos** para peso.

---

## 4. Nós de IA (escala)

- **CPU:** Ollama / LLM leve em VMs separadas, rede interna apenas.
- **GPU:** instâncias `g*` Hetzner ou provedor compatível para Stable Diffusion / modelos grandes.
- **Padrão:** API recebe pedido → enfileira job → cliente recebe `job_id` → polling ou WebSocket/SSE para resultado.

---

## 5. Filas (crítico para não bloquear)

### Stack recomendada
- **Redis** (Hetzner privado ou Redis Cloud com VPC peering).
- **Celery** (Python, integra com FastAPI) **ou** **ARQ** (async, mais leve) **ou** fila Redis simples com workers dedicados.

### O que vai para fila
- Geração de imagem / vídeo longo.
- Relatórios governamentais pesados (`gov/report`).
- Tarefas de embedding / indexação da base de conhecimento.

### Garantias
- Retries com backoff, DLQ (dead-letter), idempotência por `job_id`.
- Timeouts e limites de memória por worker.

---

## 6. Cache

| Onde | O quê |
|------|--------|
| Cloudflare | Assets estáticos, respostas GET públicas com TTL curto |
| Redis | Resultados de queries frequentes, rate-limit counters, sessões |
| Aplicação | Cache em memória só para dados ultra-estáveis (com TTL) |

**IA:** cachear respostas **somente** com chave hash(prompt+modelo+versão) e política clara de privacidade (opt-in para dados sensíveis).

---

## 7. Autenticação e 2FA

### Hoje
- JWT stateless (access token), sem refresh formal obrigatório em todos os fluxos.

### Meta
- **Access token** curto (15–30 min).
- **Refresh token** rotativo, armazenado com hash no DB, revogável.
- **Sessões** com `jti`, IP e user-agent para auditoria.
- **2FA TOTP** (RFC 6238) para: admin, governo, professores/pesquisadores — com **códigos de backup** hasheados.
- SMS/e-mail como **recuperação**, não substituto permanente do TOTP em contas de alto privilégio.

Implementação **incremental:** tabelas `user_totp_secret`, `backup_codes`, feature flag por papel.

---

## 8. Endurecimento de segurança

- **HTTPS** ponta a ponta (Cloudflare Full Strict + certificado de origem).
- **RBAC** já parcialmente presente (`is_admin`, planos) — expandir para permissões granulares (`gov:read`, `edu:write`).
- **Cabeçalhos** já no FastAPI (`security_headers_middleware`) — manter e endurecer CSP conforme frontend.
- **Zero trust** entre serviços: mTLS ou tokens de serviço de curta duração na rede interna.
- **Segredos:** Vault ou variáveis por ambiente nunca no Git.

---

## 9. Performance global

- Pages já entrega estático na edge.
- **HTTP/3** e **0-RTT** (com cuidado em dados sensíveis).
- **Imagens:** formato moderno (WebP/AVIF), dimensões corretas no upload.
- **API:** paginação obrigatória em listas; evitar N+1 no ORM (SQLAlchemy `selectinload`).

---

## 10. Banco de dados

### Hoje
- SQLite/Postgres possível conforme deploy.

### Meta produção
- **PostgreSQL** como primário.
- **PgBouncer** para pool de conexões.
- **Réplicas de leitura** para dashboards e relatórios somente leitura.
- Migrações versionadas (Alembic).

**Nunca** exposição pública da porta 5432; só rede privada + bastion SSH se necessário.

---

## 11. Estratégia de escala horizontal

| Sinal | Ação |
|-------|------|
| CPU API > 70% sustentado | + réplicas do monólito atrás do LB |
| Latência p95 subindo em `/v1/chat` | + nós API, revisar pool DB |
| Fila de jobs > SLA | + workers ou + GPU |
| GPU 100% em horários de pico | + nó GPU ou fila com prioridade gov |

Auto-scaling: Hetzner não tem AS nativo como AWS; usar **scripts** + **métricas** (Prometheus) ou migrar orquestração para **Nomad/Kubernetes** em fase madura.

---

## 12. Falhas e confiabilidade

- Health checks: `/health` liveness; `/ready` com DB e Redis.
- **Circuit breaker** chamadas a LLM externo (OpenAI, Replicate).
- **Degradação graciosa:** fila cheia → mensagem clara + retry_after.
- **Backups** PostgreSQL PITR + teste de restore trimestral.

---

## 13. Acesso tipo governo

- **IP allowlist** na edge (Cloudflare Firewall Rules) + lista no backend (já há base para IPs admin em arquivo).
- **Fila prioritária** para tenants `gov` / licenças institucionais (tag no job).
- **Dedicated** reservado para contratos específicos (nós ou cluster separado).

---

## O que está **faltando** para “milhões” (honesto)

1. **Túnel Cloudflare** fechando entrada direta na VPS — maior ganho de superfície de ataque.
2. **PostgreSQL + pool + backups** automatizados.
3. **Redis + fila** para todo trabalho pesado (hoje parte ainda é síncrono).
4. **Refresh tokens + 2FA** para contas privilegiadas.
5. **Observabilidade:** OpenTelemetry, logs estruturados, tracing entre Worker → API → worker.
6. **Testes de carga** (k6, Locust) com SLAs definidos.
7. **Separação legal/compliance** LGPD: retenção, anonimização, DPA com subprocessadores.

---

## Roadmap sugerido (sem quebrar o existente)

| Fase | Entrega | Risco |
|------|---------|-------|
| **0** | Documentar APIs, SLAs, limites atuais | Baixo |
| **1** | Cloudflare Tunnel + fechar 443 direto na origem | Baixo |
| **2** | PostgreSQL + PgBouncer; migrar dados | Médio |
| **3** | Redis + fila; mover só **mídia pesada** e **gov report** | Médio |
| **4** | Refresh tokens + sessões | Médio |
| **5** | 2FA obrigatório admin/gov | Médio |
| **6** | Extrair **Media Service** se gargalo comprovado | Alto |
| **7** | Réplicas de leitura + cache query | Médio |

---

## Conclusão

A arquitetura alvo é **sólida e padrão de mercado**. O sistema atual pode **crescer** com réplicas do monólito, banco gerenciado/poolado, fila para trabalhos pesados e edge Cloudflare bem configurado — **antes** de fragmentar em microserviços. O relatório acima serve como **north star**; a implementação deve seguir as **fases** para não interromper a operação nem a funcionalidade já entregue aos usuários.
