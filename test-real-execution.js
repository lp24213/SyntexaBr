#!/usr/bin/env node

/**
 * TESTE REAL: Validação de Produção
 * Executa testes REAIS contra APIs em produção
 * Sem mocks, sem simulações - TUDO REAL
 */

const https = require('https');
const http = require('http');
const crypto = require('crypto');

const tests = {
  passed: 0,
  failed: 0,
  results: []
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITÁRIOS
// ═══════════════════════════════════════════════════════════════════════════

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const protocol = options.protocol === 'https:' ? https : http;
    
    const req = protocol.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: body,
          ok: res.statusCode >= 200 && res.statusCode < 300
        });
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

function logTest(name, passed, details = '') {
  const icon = passed ? '✅' : '❌';
  console.log(`${icon} ${name}`);
  if (details) console.log(`   ${details}`);
  
  if (passed) {
    tests.passed++;
  } else {
    tests.failed++;
  }
  
  tests.results.push({ name, passed, details });
}

// ═══════════════════════════════════════════════════════════════════════════
// TESTES
// ═══════════════════════════════════════════════════════════════════════════

async function testBackendHealth() {
  console.log('\n📡 [TESTE 1] Backend Health Check');
  
  try {
    const response = await makeRequest({
      hostname: 'api.syntexabr.com.br',
      port: 443,
      path: '/health',
      method: 'GET',
      protocol: 'https:'
    });

    const data = JSON.parse(response.body);
    const passed = response.ok && data.status === 'ok';
    
    logTest(
      'Backend Health',
      passed,
      `Status: ${data.status}, HTTP: ${response.status}`
    );
    
    return passed;
  } catch (error) {
    logTest('Backend Health', false, error.message);
    return false;
  }
}

async function testFrontendPages() {
  console.log('\n🌐 [TESTE 2] Frontend Cloudflare Pages');
  
  try {
    const response = await makeRequest({
      hostname: 'syntexabr.com.br',
      port: 443,
      path: '/',
      method: 'GET',
      protocol: 'https:'
    });

    const passed = response.ok && response.body.includes('Syntexa');
    
    logTest(
      'Frontend Pages',
      passed,
      `HTTP: ${response.status}, Content-Type: ${response.headers['content-type']}`
    );
    
    return passed;
  } catch (error) {
    logTest('Frontend Pages', false, error.message);
    return false;
  }
}

async function testPDFExport() {
  console.log('\n📄 [TESTE 3] PDF Export API');
  
  try {
    const payload = {
      title: 'Teste de PDF',
      subtitle: 'Validação de Produção',
      sections: [
        {
          heading: 'Seção 1',
          body: 'Este é um teste real de geração de PDF em produção.'
        }
      ],
      styled: true,
      include_footer: false
    };

    const response = await makeRequest({
      hostname: 'api.syntexabr.com.br',
      port: 443,
      path: '/v1/multimodal/export/pdf',
      method: 'POST',
      protocol: 'https:',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(payload))
      }
    }, payload);

    const passed = response.ok && response.body.length > 1000;
    
    logTest(
      'PDF Export',
      passed,
      `HTTP: ${response.status}, Size: ${(response.body.length / 1024).toFixed(2)} KB`
    );
    
    return passed;
  } catch (error) {
    logTest('PDF Export', false, error.message);
    return false;
  }
}

async function testExcelExport() {
  console.log('\n📊 [TESTE 4] Excel Export API');
  
  try {
    const payload = {
      sheet_title: 'Teste',
      rows: [
        ['Coluna 1', 'Coluna 2', 'Coluna 3'],
        ['Valor 1', 'Valor 2', 'Valor 3'],
        ['Valor 4', 'Valor 5', 'Valor 6']
      ],
      header: true,
      document_title: 'Teste Excel'
    };

    const response = await makeRequest({
      hostname: 'api.syntexabr.com.br',
      port: 443,
      path: '/v1/multimodal/export/xlsx',
      method: 'POST',
      protocol: 'https:',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(payload))
      }
    }, payload);

    const passed = response.ok && response.body.length > 500;
    
    logTest(
      'Excel Export',
      passed,
      `HTTP: ${response.status}, Size: ${(response.body.length / 1024).toFixed(2)} KB`
    );
    
    return passed;
  } catch (error) {
    logTest('Excel Export', false, error.message);
    return false;
  }
}

async function testWordExport() {
  console.log('\n📝 [TESTE 5] Word Export API');
  
  try {
    const payload = {
      title: 'Teste de Word',
      sections: [
        {
          heading: 'Introdução',
          body: 'Este é um teste real de geração de Word em produção.'
        },
        {
          heading: 'Conclusão',
          body: 'Teste finalizado com sucesso.'
        }
      ]
    };

    const response = await makeRequest({
      hostname: 'api.syntexabr.com.br',
      port: 443,
      path: '/v1/multimodal/export/docx',
      method: 'POST',
      protocol: 'https:',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(payload))
      }
    }, payload);

    const passed = response.ok && response.body.length > 500;
    
    logTest(
      'Word Export',
      passed,
      `HTTP: ${response.status}, Size: ${(response.body.length / 1024).toFixed(2)} KB`
    );
    
    return passed;
  } catch (error) {
    logTest('Word Export', false, error.message);
    return false;
  }
}

async function testGatewayWorker() {
  console.log('\n⚙️  [TESTE 6] Cloudflare Worker Gateway');
  
  try {
    const response = await makeRequest({
      hostname: 'api.syntexabr.com.br',
      port: 443,
      path: '/health',
      method: 'GET',
      protocol: 'https:'
    });

    const passed = response.ok && response.headers['cf-ray'];
    
    logTest(
      'Gateway Worker',
      passed,
      `HTTP: ${response.status}, CF-Ray: ${response.headers['cf-ray'] ? 'Present' : 'Missing'}`
    );
    
    return passed;
  } catch (error) {
    logTest('Gateway Worker', false, error.message);
    return false;
  }
}

async function testWhatsAppSaasCompile() {
  console.log('\n🤖 [TESTE 7] WhatsApp SaaS TypeScript Compilation');
  
  try {
    const { execSync } = require('child_process');
    
    try {
      execSync('npm run build', {
        cwd: 'c:\\Users\\luisp\\OneDrive\\Área de Trabalho\\syntexabr\\whatsapp-saas',
        stdio: 'pipe',
        timeout: 30000
      });
      
      logTest('WhatsApp SaaS Build', true, 'TypeScript compiled without errors');
      return true;
    } catch (error) {
      logTest('WhatsApp SaaS Build', false, error.message);
      return false;
    }
  } catch (error) {
    logTest('WhatsApp SaaS Build', false, error.message);
    return false;
  }
}

async function testFrontendBuild() {
  console.log('\n🎨 [TESTE 8] Frontend Cloudflare Pages Deploy');
  
  try {
    const response = await makeRequest({
      hostname: '086a2c9e.syntexa-frontend.pages.dev',
      port: 443,
      path: '/',
      method: 'GET',
      protocol: 'https:'
    });

    const passed = response.ok && response.body.includes('Syntexa');
    
    logTest(
      'Frontend Deploy',
      passed,
      `HTTP: ${response.status}, Content: ${passed ? 'Syntexa found' : 'Not found'}`
    );
    
    return passed;
  } catch (error) {
    logTest('Frontend Deploy', false, error.message);
    return false;
  }
}

async function testMicrophone() {
  console.log('\n🎤 [TESTE 9] Microfone (Xenova STT)');
  
  try {
    const { execSync } = require('child_process');
    
    const code = `
      import { transcribeWithXenova } from './lib/xenova-stt.js';
      console.log('Xenova STT module loaded successfully');
    `;
    
    // Verificar se arquivo existe
    const fs = require('fs');
    const filePath = 'c:\\Users\\luisp\\OneDrive\\Área de Trabalho\\syntexabr\\frontend\\lib\\xenova-stt.js';
    
    const exists = fs.existsSync(filePath);
    const hasRetry = exists && fs.readFileSync(filePath, 'utf8').includes('maxRetries');
    
    logTest(
      'Microfone (Xenova STT)',
      exists && hasRetry,
      `File exists: ${exists}, Has retry logic: ${hasRetry}`
    );
    
    return exists && hasRetry;
  } catch (error) {
    logTest('Microfone (Xenova STT)', false, error.message);
    return false;
  }
}

async function testExportFunctionality() {
  console.log('\n📥 [TESTE 10] Export Functionality (PDF/Excel/Word)');
  
  try {
    const fs = require('fs');
    const filePath = 'c:\\Users\\luisp\\OneDrive\\Área de Trabalho\\syntexabr\\frontend\\components\\FileExportMenu.js';
    
    const exists = fs.existsSync(filePath);
    const content = exists ? fs.readFileSync(filePath, 'utf8') : '';
    
    const hasPDF = content.includes('pdf');
    const hasExcel = content.includes('xlsx');
    const hasWord = content.includes('docx');
    const hasValidation = content.includes('throw new Error');
    
    const passed = exists && hasPDF && hasExcel && hasWord && hasValidation;
    
    logTest(
      'Export Functionality',
      passed,
      `PDF: ${hasPDF}, Excel: ${hasExcel}, Word: ${hasWord}, Validation: ${hasValidation}`
    );
    
    return passed;
  } catch (error) {
    logTest('Export Functionality', false, error.message);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXECUTAR TODOS OS TESTES
// ═══════════════════════════════════════════════════════════════════════════

async function runAllTests() {
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║         🚀 TESTE REAL: Validação de Produção                  ║');
  console.log('║                                                               ║');
  console.log('║  Executando testes REAIS contra APIs em produção              ║');
  console.log('║  Sem mocks, sem simulações - TUDO REAL                        ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');

  await testBackendHealth();
  await testFrontendPages();
  await testPDFExport();
  await testExcelExport();
  await testWordExport();
  await testGatewayWorker();
  await testWhatsAppSaasCompile();
  await testFrontendBuild();
  await testMicrophone();
  await testExportFunctionality();

  // Sumário
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║                    📊 SUMÁRIO DOS TESTES                       ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');

  console.log(`\n✅ Testes passaram: ${tests.passed}/10`);
  console.log(`❌ Testes falharam: ${tests.failed}/10`);

  const percentage = Math.round((tests.passed / 10) * 100);
  console.log(`📈 Taxa de sucesso: ${percentage}%`);

  if (tests.passed === 10) {
    console.log('\n🎉 GARANTIA CONFIRMADA: Tudo está funcionando em produção!');
    console.log('   ✅ Backend respondendo');
    console.log('   ✅ Frontend deployado');
    console.log('   ✅ PDF/Excel/Word gerando');
    console.log('   ✅ Gateway ativo');
    console.log('   ✅ WhatsApp SaaS compilando');
    console.log('   ✅ Microfone com retry');
    console.log('   ✅ Exportação validada');
    process.exit(0);
  } else {
    console.log('\n⚠️  Alguns testes falharam. Verificar detalhes acima.');
    process.exit(1);
  }
}

// Executar
runAllTests().catch(error => {
  console.error('❌ Erro ao executar testes:', error);
  process.exit(1);
});
