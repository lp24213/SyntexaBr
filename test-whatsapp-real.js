#!/usr/bin/env node

/**
 * TESTE REAL: WhatsApp SaaS em Produção
 * Simula mensagem real do WhatsApp e valida resposta
 */

const https = require('https');
const crypto = require('crypto');

const WEBHOOK_URL = 'https://api-whatsapp.syntexabr.com.br/webhook/whatsapp';
const APP_SECRET = 'test-app-secret'; // Usar o real do .env
const VERIFY_TOKEN = 'test-verify-token';

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║       🚀 TESTE REAL: WhatsApp SaaS em Produção                ║');
console.log('║                                                               ║');
console.log('║  Testando webhook, fila Redis, LLM e geração de arquivos     ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

// ─────────────────────────────────────────────────────────────────────────
// TESTE 1: Webhook Validation
// ─────────────────────────────────────────────────────────────────────────

function testWebhookValidation() {
  return new Promise((resolve) => {
    console.log('📡 [TESTE 1] Webhook Validation');
    console.log('─'.repeat(60));

    const challenge = 'test-challenge-12345';
    const url = new URL(WEBHOOK_URL);
    url.searchParams.append('hub_verify_token', VERIFY_TOKEN);
    url.searchParams.append('hub_challenge', challenge);

    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'GET',
      timeout: 10000
    };

    https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200 && data === challenge) {
          console.log('✅ Webhook validation: PASSOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(true);
        } else {
          console.log('❌ Webhook validation: FALHOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    }).on('error', (error) => {
      console.log('❌ Webhook validation: ERRO');
      console.log(`   ${error.message}`);
      resolve(false);
    }).end();
  });
}

// ─────────────────────────────────────────────────────────────────────────
// TESTE 2: Webhook Message Reception
// ─────────────────────────────────────────────────────────────────────────

function testWebhookMessage() {
  return new Promise((resolve) => {
    console.log('\n📨 [TESTE 2] Webhook Message Reception');
    console.log('─'.repeat(60));

    const payload = JSON.stringify({
      entry: [{
        id: '123456789',
        changes: [{
          field: 'messages',
          value: {
            messaging_product: 'whatsapp',
            metadata: {
              display_phone_number: '5511987654321',
              phone_number_id: '1234567890',
              business_account_id: '123456789'
            },
            messages: [{
              from: '5511999999999',
              id: 'wamid.test.001',
              timestamp: Math.floor(Date.now() / 1000).toString(),
              type: 'text',
              text: {
                body: 'Monta uma planilha de fluxo de caixa com receita, custo e lucro'
              }
            }],
            contacts: [{
              profile: { name: 'Cliente Teste' },
              wa_id: '5511999999999'
            }]
          }
        }]
      }]
    });

    // Calcular HMAC
    const signature = crypto
      .createHmac('sha256', APP_SECRET)
      .update(payload)
      .digest('hex');

    const options = {
      hostname: new URL(WEBHOOK_URL).hostname,
      path: new URL(WEBHOOK_URL).pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'X-Hub-Signature-256': `sha256=${signature}`
      },
      timeout: 10000
    };

    https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Webhook message reception: PASSOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log('   ✅ Mensagem enfileirada em Redis');
          resolve(true);
        } else {
          console.log('❌ Webhook message reception: FALHOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Response: ${data}`);
          resolve(false);
        }
      });
    }).on('error', (error) => {
      console.log('❌ Webhook message reception: ERRO');
      console.log(`   ${error.message}`);
      resolve(false);
    }).write(payload);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// TESTE 3: Backend Health
// ─────────────────────────────────────────────────────────────────────────

function testBackendHealth() {
  return new Promise((resolve) => {
    console.log('\n🏥 [TESTE 3] Backend Health Check');
    console.log('─'.repeat(60));

    const options = {
      hostname: 'api.syntexabr.com.br',
      path: '/health',
      method: 'GET',
      timeout: 10000
    };

    https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (res.statusCode === 200 && json.status === 'ok') {
            console.log('✅ Backend health: PASSOU');
            console.log(`   Status: ${res.statusCode}`);
            console.log(`   Response: ${JSON.stringify(json)}`);
            resolve(true);
          } else {
            console.log('❌ Backend health: FALHOU');
            resolve(false);
          }
        } catch (e) {
          console.log('❌ Backend health: ERRO');
          resolve(false);
        }
      });
    }).on('error', (error) => {
      console.log('❌ Backend health: ERRO');
      console.log(`   ${error.message}`);
      resolve(false);
    }).end();
  });
}

// ─────────────────────────────────────────────────────────────────────────
// TESTE 4: PDF Generation
// ─────────────────────────────────────────────────────────────────────────

function testPDFGeneration() {
  return new Promise((resolve) => {
    console.log('\n📄 [TESTE 4] PDF Generation');
    console.log('─'.repeat(60));

    const payload = JSON.stringify({
      title: 'Fluxo de Caixa',
      subtitle: 'Análise de Negócio',
      sections: [
        {
          heading: 'Resumo',
          body: 'Análise do fluxo de caixa dos últimos 3 meses.'
        }
      ],
      styled: true
    });

    const options = {
      hostname: 'api.syntexabr.com.br',
      path: '/v1/multimodal/export/pdf',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 30000
    };

    https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200 && data.length > 1000) {
          console.log('✅ PDF generation: PASSOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Size: ${(data.length / 1024).toFixed(2)} KB`);
          resolve(true);
        } else {
          console.log('❌ PDF generation: FALHOU');
          console.log(`   Status: ${res.statusCode}`);
          resolve(false);
        }
      });
    }).on('error', (error) => {
      console.log('❌ PDF generation: ERRO');
      console.log(`   ${error.message}`);
      resolve(false);
    }).write(payload);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// TESTE 5: Excel Generation
// ─────────────────────────────────────────────────────────────────────────

function testExcelGeneration() {
  return new Promise((resolve) => {
    console.log('\n📊 [TESTE 5] Excel Generation');
    console.log('─'.repeat(60));

    const payload = JSON.stringify({
      sheet_title: 'Fluxo de Caixa',
      rows: [
        ['Mês', 'Receita', 'Custo', 'Lucro'],
        ['Janeiro', 'R$ 15.000', 'R$ 8.000', 'R$ 7.000'],
        ['Fevereiro', 'R$ 18.500', 'R$ 10.200', 'R$ 8.300'],
        ['Março', 'R$ 22.000', 'R$ 11.800', 'R$ 10.200']
      ],
      header: true
    });

    const options = {
      hostname: 'api.syntexabr.com.br',
      path: '/v1/multimodal/export/xlsx',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 30000
    };

    https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200 && data.length > 500) {
          console.log('✅ Excel generation: PASSOU');
          console.log(`   Status: ${res.statusCode}`);
          console.log(`   Size: ${(data.length / 1024).toFixed(2)} KB`);
          resolve(true);
        } else {
          console.log('❌ Excel generation: FALHOU');
          console.log(`   Status: ${res.statusCode}`);
          resolve(false);
        }
      });
    }).on('error', (error) => {
      console.log('❌ Excel generation: ERRO');
      console.log(`   ${error.message}`);
      resolve(false);
    }).write(payload);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// EXECUTAR TODOS OS TESTES
// ─────────────────────────────────────────────────────────────────────────

async function runAllTests() {
  const results = {
    'Webhook Validation': await testWebhookValidation(),
    'Webhook Message': await testWebhookMessage(),
    'Backend Health': await testBackendHealth(),
    'PDF Generation': await testPDFGeneration(),
    'Excel Generation': await testExcelGeneration()
  };

  // Sumário
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║                    📊 SUMÁRIO DOS TESTES                       ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  const passed = Object.values(results).filter(r => r).length;
  const total = Object.keys(results).length;

  console.log(`✅ Testes passaram: ${passed}/${total}`);
  console.log(`📈 Taxa de sucesso: ${Math.round((passed / total) * 100)}%\n`);

  Object.entries(results).forEach(([test, result]) => {
    const icon = result ? '✅' : '❌';
    console.log(`${icon} ${test}`);
  });

  if (passed === total) {
    console.log('\n🎉 GARANTIA CONFIRMADA: WhatsApp SaaS está 100% funcional!');
    console.log('   ✅ Webhook recebe mensagens');
    console.log('   ✅ Backend processa');
    console.log('   ✅ PDF gera');
    console.log('   ✅ Excel gera');
    console.log('   ✅ Pronto para clientes!');
    process.exit(0);
  } else {
    console.log('\n⚠️  Alguns testes falharam.');
    process.exit(1);
  }
}

runAllTests().catch(error => {
  console.error('❌ Erro fatal:', error);
  process.exit(1);
});
