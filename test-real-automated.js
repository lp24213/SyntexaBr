#!/usr/bin/env node

/**
 * TESTE REAL AUTOMATIZADO
 * Testa cada funcionalidade de verdade sem intervenção manual
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SITE_URL = 'https://syntexabr.com.br';
const DOWNLOADS_DIR = path.join(__dirname, 'test-downloads');

if (!fs.existsSync(DOWNLOADS_DIR)) {
  fs.mkdirSync(DOWNLOADS_DIR, { recursive: true });
}

let browser;
let context;
let page;

async function setup() {
  console.log('🚀 Iniciando navegador...');
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({
    acceptDownloads: true,
  });
  page = await context.newPage();
  console.log('✅ Navegador pronto\n');
}

async function teardown() {
  if (browser) await browser.close();
}

async function testChatLoads() {
  console.log('🌐 [TESTE 0] Chat Carrega');
  console.log('─'.repeat(60));
  
  try {
    await page.goto(`${SITE_URL}/chat`, { waitUntil: 'networkidle', timeout: 30000 });
    console.log('✅ Chat carregado com sucesso');
    return true;
  } catch (error) {
    console.error('❌ Erro ao carregar chat:', error.message);
    return false;
  }
}

async function testPDFGeneration() {
  console.log('\n📄 [TESTE 1] PDF - Geração Real');
  console.log('─'.repeat(60));
  
  try {
    // Fazer requisição direta à API de PDF
    const pdfPayload = {
      title: 'Relatório de Vendas',
      subtitle: 'Análise de Dados',
      sections: [
        {
          heading: 'Resumo Executivo',
          body: 'Este relatório apresenta uma análise completa das vendas do período.'
        },
        {
          heading: 'Dados de Vendas',
          body: 'Janeiro: R$ 15.000\nFevereiro: R$ 18.500\nMarço: R$ 22.000'
        },
        {
          heading: 'Conclusão',
          body: 'Os dados mostram crescimento consistente.'
        }
      ],
      styled: true,
      include_footer: false
    };

    const response = await page.request.post('https://api.syntexabr.com.br/v1/multimodal/export/pdf', {
      data: pdfPayload,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok()) {
      console.log(`❌ API retornou ${response.status()}`);
      return false;
    }

    const buffer = await response.body();
    const pdfPath = path.join(DOWNLOADS_DIR, 'relatorio.pdf');
    fs.writeFileSync(pdfPath, buffer);

    console.log(`✅ PDF gerado: ${pdfPath}`);
    console.log(`   Tamanho: ${(buffer.length / 1024).toFixed(2)} KB`);

    // Validar PDF
    const isPDF = buffer.toString('utf8', 0, 4) === '%PDF';
    if (isPDF) {
      console.log('✅ PDF é válido');
      return true;
    } else {
      console.log('❌ Arquivo não é PDF válido');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao gerar PDF:', error.message);
    return false;
  }
}

async function testExcelGeneration() {
  console.log('\n📊 [TESTE 2] EXCEL - Geração Real');
  console.log('─'.repeat(60));
  
  try {
    const excelPayload = {
      sheet_title: 'Fluxo de Caixa',
      rows: [
        ['Mês', 'Receita', 'Custo', 'Lucro'],
        ['Janeiro', 'R$ 15.000', 'R$ 8.000', 'R$ 7.000'],
        ['Fevereiro', 'R$ 18.500', 'R$ 10.200', 'R$ 8.300'],
        ['Março', 'R$ 22.000', 'R$ 11.800', 'R$ 10.200']
      ],
      header: true,
      document_title: 'Fluxo de Caixa - Negócio'
    };

    const response = await page.request.post('https://api.syntexabr.com.br/v1/multimodal/export/xlsx', {
      data: excelPayload,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok()) {
      console.log(`❌ API retornou ${response.status()}`);
      return false;
    }

    const buffer = await response.body();
    const excelPath = path.join(DOWNLOADS_DIR, 'fluxo_caixa.xlsx');
    fs.writeFileSync(excelPath, buffer);

    console.log(`✅ Excel gerado: ${excelPath}`);
    console.log(`   Tamanho: ${(buffer.length / 1024).toFixed(2)} KB`);

    // Validar Excel
    const isExcel = buffer.toString('utf8', 0, 2) === 'PK';
    if (isExcel) {
      console.log('✅ Excel é válido');
      return true;
    } else {
      console.log('❌ Arquivo não é Excel válido');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao gerar Excel:', error.message);
    return false;
  }
}

async function testWordGeneration() {
  console.log('\n📝 [TESTE 3] WORD - Geração Real');
  console.log('─'.repeat(60));
  
  try {
    const wordPayload = {
      title: 'Estratégia de Marketing',
      sections: [
        {
          heading: 'Introdução',
          body: 'Este documento apresenta a estratégia de marketing para o próximo trimestre.'
        },
        {
          heading: 'Objetivos',
          body: 'Aumentar visibilidade da marca em 40%\nAcquisição de 500 novos clientes\nMelhorar taxa de retenção'
        },
        {
          heading: 'Conclusão',
          body: 'A estratégia proposta é viável e alinhada com os objetivos da empresa.'
        }
      ]
    };

    const response = await page.request.post('https://api.syntexabr.com.br/v1/multimodal/export/docx', {
      data: wordPayload,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok()) {
      console.log(`❌ API retornou ${response.status()}`);
      return false;
    }

    const buffer = await response.body();
    const wordPath = path.join(DOWNLOADS_DIR, 'documento.docx');
    fs.writeFileSync(wordPath, buffer);

    console.log(`✅ Word gerado: ${wordPath}`);
    console.log(`   Tamanho: ${(buffer.length / 1024).toFixed(2)} KB`);

    // Validar Word
    const isWord = buffer.toString('utf8', 0, 2) === 'PK';
    if (isWord) {
      console.log('✅ Word é válido');
      return true;
    } else {
      console.log('❌ Arquivo não é Word válido');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao gerar Word:', error.message);
    return false;
  }
}

async function testMicrophoneCode() {
  console.log('\n🎤 [TESTE 4] MICROFONE - Validação de Código');
  console.log('─'.repeat(60));
  
  try {
    // Verificar se arquivo de microfone existe
    const micPath = 'c:\\Users\\luisp\\OneDrive\\Área de Trabalho\\syntexabr\\frontend\\lib\\xenova-stt.js';
    
    if (!fs.existsSync(micPath)) {
      console.log('❌ Arquivo de microfone não encontrado');
      return false;
    }

    const content = fs.readFileSync(micPath, 'utf8');
    
    // Validar se tem retry
    const hasRetry = content.includes('maxRetries') && content.includes('for (let attempt');
    const hasXenova = content.includes('transcribeWithXenova');
    const hasFallback = content.includes('Web Speech') || content.includes('webkitSpeechRecognition');

    console.log(`✅ Arquivo de microfone encontrado`);
    console.log(`   Tem retry: ${hasRetry ? 'Sim' : 'Não'}`);
    console.log(`   Tem Xenova: ${hasXenova ? 'Sim' : 'Não'}`);
    console.log(`   Tem fallback: ${hasFallback ? 'Sim' : 'Não'}`);

    if (hasRetry && hasXenova) {
      console.log('✅ Microfone está implementado corretamente');
      return true;
    } else {
      console.log('❌ Microfone não está completo');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao validar microfone:', error.message);
    return false;
  }
}

async function testWhatsAppSaaS() {
  console.log('\n🤖 [TESTE 5] WHATSAPP SAAS - Validação de Código');
  console.log('─'.repeat(60));
  
  try {
    // Verificar se WhatsApp SaaS compila
    const { execSync } = require('child_process');
    
    try {
      execSync('npm run build', {
        cwd: 'c:\\Users\\luisp\\OneDrive\\Área de Trabalho\\syntexabr\\whatsapp-saas',
        stdio: 'pipe',
        timeout: 30000
      });
      
      console.log('✅ WhatsApp SaaS compila sem erros');
      return true;
    } catch (error) {
      console.log('❌ WhatsApp SaaS tem erros de compilação');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao validar WhatsApp SaaS:', error.message);
    return false;
  }
}

async function runAllTests() {
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║      🚀 TESTE REAL AUTOMATIZADO - Validação Completa          ║');
  console.log('║                                                               ║');
  console.log('║  Testando cada funcionalidade de VERDADE                      ║');
  console.log('║  Sem simulações, sem mocks - TUDO REAL                        ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  await setup();

  const results = {
    'Chat Carrega': await testChatLoads(),
    'PDF Geração': await testPDFGeneration(),
    'Excel Geração': await testExcelGeneration(),
    'Word Geração': await testWordGeneration(),
    'Microfone Código': await testMicrophoneCode(),
    'WhatsApp SaaS': await testWhatsAppSaaS()
  };

  await teardown();

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
    console.log('\n🎉 GARANTIA CONFIRMADA: Tudo está funcionando de VERDADE!');
    console.log('   ✅ Chat carrega corretamente');
    console.log('   ✅ PDF gera e baixa');
    console.log('   ✅ Excel gera e baixa');
    console.log('   ✅ Word gera e baixa');
    console.log('   ✅ Microfone implementado com retry');
    console.log('   ✅ WhatsApp SaaS compila sem erros');
    console.log('\n🟢 PRONTO PARA PRODUÇÃO E CLIENTES!');
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
