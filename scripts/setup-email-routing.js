#!/usr/bin/env node

/**
 * Setup Email Routing no Cloudflare
 * Encaminha contato@syntexabr.com.br → syntexabr@hotmail.com
 * 
 * Uso:
 *   CLOUDFLARE_API_TOKEN=xxx CLOUDFLARE_ZONE_ID=yyy node scripts/setup-email-routing.js
 */

const https = require("https");

const CF_API_TOKEN = process.env.CLOUDFLARE_API_TOKEN;
const CF_ZONE_ID = process.env.CLOUDFLARE_ZONE_ID || "88bb8377dc5b75793f667b8f0752053f";
const CF_ACCOUNT_ID = process.env.CLOUDFLARE_ACCOUNT_ID;

const DOMAIN = "syntexabr.com.br";
const SOURCE_EMAIL = "contato@syntexabr.com.br";
const DESTINATION_EMAIL = "syntexabr@hotmail.com";

if (!CF_API_TOKEN) {
  console.error("❌ ERRO: CLOUDFLARE_API_TOKEN não definido");
  console.error("Defina: export CLOUDFLARE_API_TOKEN=seu_token");
  process.exit(1);
}

function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: "api.cloudflare.com",
      port: 443,
      path: `/client/v4${path}`,
      method: method,
      headers: {
        "Authorization": `Bearer ${CF_API_TOKEN}`,
        "Content-Type": "application/json",
      },
    };

    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on("error", reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

async function main() {
  console.log("📧 Configurando Email Routing no Cloudflare...\n");

  // 1. Verificar zona
  console.log(`🔍 1️⃣ Verificando zona ${DOMAIN} (${CF_ZONE_ID})...`);
  const zoneRes = await makeRequest("GET", `/zones/${CF_ZONE_ID}`);
  if (!zoneRes.data.success) {
    console.error("❌ Zona não encontrada:", zoneRes.data.errors);
    process.exit(1);
  }
  console.log(`✅ Zona ativa: ${zoneRes.data.result.name}\n`);

  // 2. Verificar Email Routing habilitado
  console.log(`📬 2️⃣ Verificando se Email Routing está habilitado...`);
  const enableRes = await makeRequest("GET", `/zones/${CF_ZONE_ID}/email/routing/enable`);
  if (!enableRes.data.success && enableRes.status !== 404) {
    console.error("❌ Erro ao verificar Email Routing:", enableRes.data.errors);
    process.exit(1);
  }

  if (enableRes.status === 404 || !enableRes.data.result?.enabled) {
    console.log(`⚠️ Email Routing não está habilitado. Ativando...`);
    const activateRes = await makeRequest("POST", `/zones/${CF_ZONE_ID}/email/routing/enable`);
    if (!activateRes.data.success) {
      console.error("❌ Erro ao ativar Email Routing:", activateRes.data.errors);
      process.exit(1);
    }
    console.log(`✅ Email Routing ativado\n`);
  } else {
    console.log(`✅ Email Routing já ativo\n`);
  }

  // 3. Listar regras existentes
  console.log(`📋 3️⃣ Listando regras existentes...`);
  const rulesRes = await makeRequest("GET", `/zones/${CF_ZONE_ID}/email/routing/rules`);
  if (!rulesRes.data.success) {
    console.error("❌ Erro ao listar regras:", rulesRes.data.errors);
    process.exit(1);
  }

  const existingRule = rulesRes.data.result?.find(
    (r) => r.matchers?.[0]?.value === SOURCE_EMAIL
  );

  if (existingRule) {
    console.log(`ℹ️ Regra já existe para ${SOURCE_EMAIL}`);
    console.log(`   ID: ${existingRule.id}`);
    console.log(`   Destino: ${existingRule.actions?.[0]?.value || "?"}\n`);
  } else {
    console.log(`ℹ️ Nenhuma regra existente para ${SOURCE_EMAIL}\n`);
  }

  // 4. Criar regra
  if (!existingRule) {
    console.log(`➕ 4️⃣ Criando regra para ${SOURCE_EMAIL} → ${DESTINATION_EMAIL}...`);
    
    const createRes = await makeRequest("POST", `/zones/${CF_ZONE_ID}/email/routing/rules`, {
      matchers: [
        {
          type: "literal",
          field: "to",
          value: SOURCE_EMAIL,
        },
      ],
      actions: [
        {
          type: "forward",
          value: [DESTINATION_EMAIL],
        },
      ],
      enabled: true,
    });

    if (!createRes.data.success) {
      console.error("❌ Erro ao criar regra:", createRes.data.errors);
      process.exit(1);
    }

    const rule = createRes.data.result;
    console.log(`✅ Regra criada com sucesso!`);
    console.log(`   ID: ${rule.id}`);
    console.log(`   Origem: ${rule.matchers[0].value}`);
    console.log(`   Destino: ${rule.actions[0].value[0]}`);
    console.log(`   Status: ${rule.enabled ? "ATIVO" : "INATIVO"}\n`);
  } else {
    console.log(`4️⃣ Regra já existe, pulando criação...\n`);
  }

  // 5. Verificar configuração final
  console.log(`🔍 5️⃣ Verificando configuração final...`);
  const finalRes = await makeRequest("GET", `/zones/${CF_ZONE_ID}/email/routing/rules`);
  const contorule = finalRes.data.result?.find(
    (r) => r.matchers?.[0]?.value === SOURCE_EMAIL
  );

  if (contorule && contorule.actions?.[0]?.value?.includes(DESTINATION_EMAIL)) {
    console.log(`✅ Email Routing configurado corretamente!`);
    console.log(`   ${SOURCE_EMAIL} → ${DESTINATION_EMAIL}\n`);
  } else {
    console.error(`❌ Falha ao confirmar roteamento`);
    process.exit(1);
  }

  console.log("✨ Concluído!");
  console.log("\n📝 Próximos passos:");
  console.log(`   1. Aguarde até 24h para emails chegarem em ${DESTINATION_EMAIL}`);
  console.log(`   2. Teste enviando email para ${SOURCE_EMAIL}`);
  console.log(`   3. Verifique o inbox/spam de ${DESTINATION_EMAIL}`);
}

main().catch((err) => {
  console.error("❌ Erro:", err.message);
  process.exit(1);
});
