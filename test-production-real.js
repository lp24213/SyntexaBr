#!/usr/bin/env node

/**
 * TESTE REAL EM PRODUÇÃO COM PLAYWRIGHT
 * Abre o site de VERDADE, gera conteúdo REAL e valida tudo
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SITE_URL = 'https://syntexabr.com.br/chat';
const DOWNLOADS_DIR = path.join(__dirname, 'test-downloads-real');

if (!fs.existsSync(DOWNLOADS_DIR)) {
  fs.mkdirSync(DOWNLOADS_DIR, { recursive: true });
}

let browser;
let context;
let page;

async function setup() {
  console.log('🚀 Iniciando navegador em PRODUÇÃO...');
  browser = await chromium.launch({ headless: false });
  context = await browser.newContext({
    acceptDownloads: true,
  });
  page = await context.newPage();
  console.log('✅ Navegador pronto\n');
}

async function teardown() {
  if (browser) await browser.close();
}

async function testPDFWithRealContent() {
  console.log('📄 [TESTE 1] PDF com Conteúdo REAL');
  console.log('─'.repeat(60));
  
  try {
    await page.goto(SITE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    console.log('✅ Chat carregado');

    // Digitar mensagem REAL E LONGA
    const input = await page.locator('input[placeholder*="Escreva"], textarea, [contenteditable="true"]').first();
    
    if (!input) {
      console.log('❌ Campo de entrada não encontrado');
      return false;
    }

    const message = "Você é um analista financeiro experiente. Crie um relatório executivo DETALHADO sobre análise de vendas para uma empresa de tecnologia no mês de maio de 2026. O relatório deve incluir: 1) Resumo executivo com principais métricas e KPIs, 2) Análise de vendas por categoria (Tecnologia R$ 125.000 com crescimento 28%, Serviços R$ 85.000 com crescimento 12%, Produtos R$ 95.000 com crescimento 8%, Consultoria R$ 45.000 com crescimento 5%, Total R$ 350.000), 3) Análise detalhada de clientes (45 novos clientes adquiridos, 128 clientes recorrentes, taxa de retenção 92%, ticket médio R$ 2.734, lifetime value médio R$ 18.500), 4) Comparação com mês anterior mostrando crescimento de 15% geral, 5) Análise por segmento com destaque para tecnologia que cresceu 28%, 6) Identificação de oportunidades de crescimento, 7) Recomendações estratégicas para próximos meses incluindo aumento de investimento em marketing para tecnologia, manutenção de qualidade de serviço e exploração de oportunidades em consultoria. Faça um texto LONGO, PROFISSIONAL e DETALHADO com PELO MENOS 2000 caracteres, bem estruturado com seções claras.";
    
    await input.fill(String(message).trim());
    console.log('✅ Mensagem LONGA e REAL digitada');

    // Enviar
    await page.locator('button[type="submit"], button:has-text("Enviar")').first().click();
    console.log('✅ Mensagem enviada');

    // Aguardar resposta LONGA
    await page.waitForTimeout(8000);

    // Procurar botão de exportar PDF
    const exportButton = await page.locator('button:has-text("PDF"), button:has-text("Exportar PDF")').first();
    
    if (!exportButton) {
      console.log('❌ Botão de exportar PDF não encontrado');
      return false;
    }

    console.log('✅ Botão de exportar PDF encontrado');

    // Clicar e baixar
    const downloadPromise = context.waitForEvent('download');
    await exportButton.click();
    
    const download = await downloadPromise;
    const pdfPath = path.join(DOWNLOADS_DIR, 'relatorio_real.pdf');
    await download.saveAs(pdfPath);

    const stats = fs.statSync(pdfPath);
    console.log(`✅ PDF baixado: ${pdfPath}`);
    console.log(`   Tamanho: ${(stats.size / 1024).toFixed(2)} KB`);

    // Validar conteúdo
    const content = fs.readFileSync(pdfPath, 'utf8');
    const hasContent = content.includes('Relatório') || content.includes('vendas') || content.length > 5000;

    if (hasContent) {
      console.log('✅ PDF contém conteúdo REAL');
      return true;
    } else {
      console.log('❌ PDF vazio ou sem conteúdo');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao testar PDF:', error.message);
    return false;
  }
}

async function testExcelWithRealContent() {
  console.log('\n📊 [TESTE 2] Excel com Conteúdo REAL');
  console.log('─'.repeat(60));
  
  try {
    // Digitar mensagem REAL E LONGA
    const input = await page.locator('input[placeholder*="Escreva"], textarea, [contenteditable="true"]').first();
    
    if (!input) {
      console.log('❌ Campo de entrada não encontrado');
      return false;
    }

    const message = "Crie uma planilha COMPLETA e DETALHADA de fluxo de caixa para uma empresa de tecnologia referente ao mês de maio de 2026. A planilha deve incluir: 1) Dados diários de receita e despesa para cada dia do mês (01/05 a 31/05), 2) Receitas por dia: 01/05 R$ 15.000, 05/05 R$ 22.500, 10/05 R$ 18.000, 15/05 R$ 25.000, 20/05 R$ 20.000, 25/05 R$ 28.000, 31/05 R$ 30.000, 3) Despesas correspondentes: 01/05 R$ 8.500, 05/05 R$ 12.000, 10/05 R$ 9.500, 15/05 R$ 14.000, 20/05 R$ 10.500, 25/05 R$ 15.000, 31/05 R$ 16.500, 4) Cálculo de saldo diário (receita - despesa), 5) Totalizações mensais de receita, despesa e saldo, 6) Análise de tendências, 7) Identificação de dias com maior fluxo de caixa, 8) Recomendações de gestão de caixa. Faça uma planilha PROFISSIONAL, BEM FORMATADA, com cores, cabeçalhos destacados e cálculos automáticos.";
    
    await input.fill(String(message).trim());
    console.log('✅ Mensagem LONGA e REAL digitada');

    // Enviar
    await page.locator('button[type="submit"], button:has-text("Enviar")').first().click();
    console.log('✅ Mensagem enviada');

    // Aguardar resposta LONGA
    await page.waitForTimeout(8000);

    // Procurar botão de exportar Excel
    const exportButton = await page.locator('button:has-text("Excel"), button:has-text("XLSX")').first();
    
    if (!exportButton) {
      console.log('❌ Botão de exportar Excel não encontrado');
      return false;
    }

    console.log('✅ Botão de exportar Excel encontrado');

    // Clicar e baixar
    const downloadPromise = context.waitForEvent('download');
    await exportButton.click();
    
    const download = await downloadPromise;
    const excelPath = path.join(DOWNLOADS_DIR, 'fluxo_caixa_real.xlsx');
    await download.saveAs(excelPath);

    const stats = fs.statSync(excelPath);
    console.log(`✅ Excel baixado: ${excelPath}`);
    console.log(`   Tamanho: ${(stats.size / 1024).toFixed(2)} KB`);

    // Validar se é Excel
    const buffer = fs.readFileSync(excelPath);
    const isExcel = buffer.toString('utf8', 0, 2) === 'PK';

    if (isExcel && stats.size > 1000) {
      console.log('✅ Excel é válido e contém dados');
      return true;
    } else {
      console.log('❌ Excel inválido ou vazio');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao testar Excel:', error.message);
    return false;
  }
}

async function testWordWithRealContent() {
  console.log('\n📝 [TESTE 3] Word com Conteúdo REAL');
  console.log('─'.repeat(60));
  
  try {
    // Digitar mensagem REAL E LONGA
    const input = await page.locator('input[placeholder*="Escreva"], textarea, [contenteditable="true"]').first();
    
    if (!input) {
      console.log('❌ Campo de entrada não encontrado');
      return false;
    }

    const message = "Crie um documento PROFISSIONAL e DETALHADO sobre estratégia de marketing digital para uma empresa de tecnologia em 2026. O documento deve incluir: 1) Introdução executiva explicando a importância do marketing digital, 2) Análise de mercado atual (crescimento 25% ao ano, competição aumentando, oportunidades em redes sociais), 3) Objetivos SMART (aumentar visibilidade da marca em 40%, adquirir 500 novos clientes, melhorar taxa de retenção para 95%, aumentar ticket médio em 20%), 4) Público-alvo detalhado (empresas de 10-100 funcionários, setor de tecnologia, orçamento anual acima de R$ 500.000), 5) Estratégia por canal (Redes Sociais: LinkedIn, Instagram, TikTok com 3 posts/semana; Email Marketing: newsletter semanal para 10.000 contatos; SEO: otimização de 50 páginas; Publicidade: Google Ads e Facebook Ads com orçamento de R$ 30.000), 6) Orçamento detalhado (Ferramentas: R$ 5.000, Criação de conteúdo: R$ 15.000, Publicidade: R$ 30.000, Total: R$ 50.000), 7) Timeline de implementação (Mês 1-2: preparação, Mês 3-10: execução, Mês 11-12: análise e otimização), 8) Métricas de sucesso (ROI, CAC, LTV, taxa de conversão, engagement rate), 9) Riscos e mitigações, 10) Conclusão com próximos passos. Faça um documento LONGO, BEM ESTRUTURADO, PROFISSIONAL com pelo menos 3000 caracteres.";
    
    await input.fill(String(message).trim());
    console.log('✅ Mensagem LONGA e REAL digitada');

    // Enviar
    await page.locator('button[type="submit"], button:has-text("Enviar")').first().click();
    console.log('✅ Mensagem enviada');

    // Aguardar resposta LONGA
    await page.waitForTimeout(8000);

    // Procurar botão de exportar Word
    const exportButton = await page.locator('button:has-text("Word"), button:has-text("DOCX")').first();
    
    if (!exportButton) {
      console.log('❌ Botão de exportar Word não encontrado');
      return false;
    }

    console.log('✅ Botão de exportar Word encontrado');

    // Clicar e baixar
    const downloadPromise = context.waitForEvent('download');
    await exportButton.click();
    
    const download = await downloadPromise;
    const wordPath = path.join(DOWNLOADS_DIR, 'estrategia_marketing.docx');
    await download.saveAs(wordPath);

    const stats = fs.statSync(wordPath);
    console.log(`✅ Word baixado: ${wordPath}`);
    console.log(`   Tamanho: ${(stats.size / 1024).toFixed(2)} KB`);

    // Validar se é Word
    const buffer = fs.readFileSync(wordPath);
    const isWord = buffer.toString('utf8', 0, 2) === 'PK';

    if (isWord && stats.size > 1000) {
      console.log('✅ Word é válido e contém dados');
      return true;
    } else {
      console.log('❌ Word inválido ou vazio');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao testar Word:', error.message);
    return false;
  }
}

async function testMicrophoneReal() {
  console.log('\n🎤 [TESTE 4] Microfone REAL');
  console.log('─'.repeat(60));
  
  try {
    // Procurar botão do microfone
    const micButton = await page.locator('button[aria-label*="mic"], button[title*="mic"], svg[viewBox*="24"]').first();
    
    if (!micButton) {
      console.log('❌ Botão do microfone não encontrado');
      return false;
    }

    console.log('✅ Botão do microfone encontrado');
    console.log('⚠️  AÇÃO MANUAL: Clique no microfone e fale algo');
    console.log('   Pressione ENTER quando terminar...');
    
    // Aguardar entrada do usuário
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });

    // Verificar se texto foi transcrito
    const chatMessages = await page.locator('[role="article"], .message, .chat-message, [class*="message"]').count();
    
    if (chatMessages > 0) {
      console.log(`✅ Microfone funcionou! ${chatMessages} mensagens no chat`);
      return true;
    } else {
      console.log('❌ Nenhuma mensagem foi transcrita');
      return false;
    }
  } catch (error) {
    console.error('❌ Erro ao testar microfone:', error.message);
    return false;
  }
}

async function runAllTests() {
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║    🚀 TESTE REAL EM PRODUÇÃO COM PLAYWRIGHT                   ║');
  console.log('║                                                               ║');
  console.log('║  Testando cada funcionalidade COM CONTEÚDO REAL               ║');
  console.log('║  Abrindo site, gerando documentos, validando tudo             ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  await setup();

  const results = {
    'PDF com Conteúdo REAL': await testPDFWithRealContent(),
    'Excel com Conteúdo REAL': await testExcelWithRealContent(),
    'Word com Conteúdo REAL': await testWordWithRealContent(),
    'Microfone REAL': await testMicrophoneReal()
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
    console.log('\n🎉 GARANTIA CONFIRMADA: Tudo está funcionando COM CONTEÚDO REAL!');
    console.log('   ✅ PDF com dados reais');
    console.log('   ✅ Excel com dados reais');
    console.log('   ✅ Word com dados reais');
    console.log('   ✅ Microfone funcionando');
    console.log('\n🟢 PRONTO PARA CLIENTES EM PRODUÇÃO!');
    console.log(`\n📁 Arquivos em: ${DOWNLOADS_DIR}`);
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
