#!/usr/bin/env node
/**
 * Produção primeiro: não executar Next.js nem servidor local.
 * Build e deploy: Cloudflare Pages (ver deploy-syntexa.ps1 deploy-front).
 */
console.error(
  "\n[syntexa] Comando desativado: execução local de servidor não é suportada.\n" +
    "  • Frontend: npm run build → wrangler pages deploy (ou .\\deploy-syntexa.ps1 deploy-front)\n" +
    "  • API pública: https://api.syntexabr.com.br\n"
);
process.exit(1);
