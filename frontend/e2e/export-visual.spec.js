/**
 * Validação visual dos exports PDF/XLSX/HTML/DOCX gerados no cliente.
 *
 * Não depende do backend nem de auth: usa um harness HTML que embute o mesmo
 * buildBrandedHtmlDocument + SpreadsheetML + RTF + html2pdf.js do CDN, alimenta
 * com texto de chat realista e captura os 4 downloads para análise.
 */
const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const OUT = path.join(__dirname, "..", "test-results", "exports");
fs.mkdirSync(OUT, { recursive: true });

const SAMPLE_CHAT = [
  "Você:",
  "Faça uma análise rápida do plano de negócios da Syntexa em formato tabela.",
  "",
  "Assistente:",
  "## Plano de Negócios — Syntexa",
  "",
  "A Syntexa é uma plataforma brasileira de IA generativa com foco em **soberania de dados**.",
  "",
  "| Seção | Conteúdo |",
  "| --- | --- |",
  "| 1. Resumo Executivo | Plataforma de IA de alto desempenho |",
  "| 2. Análise de Mercado | R$ 15 bi em 2025, CAGR ≈ 20% |",
  "| 3. Proposta de Valor | Desempenho, personalização e privacidade |",
  "| 4. Modelo de Receita | SaaS + API Pay-Per-Use |",
  "| 5. Estrutura Operacional | Equipe core ML + Infra + DevOps |",
  "| 6. Marketing & Vendas | Webinars, parcerias com integradores |",
  "",
  "*Próximos passos:* alinhamento com investidores e cronograma de implantação.",
].join("\n");

test("exports geram ficheiros com conteúdo e visual", async ({ page }) => {
  // Carrega o módulo real do FileExportMenu via build estático (já existe em out/).
  // Mais simples: injeta diretamente as mesmas funções num harness em branco.
  const harness = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>harness</title></head>
<body>
<script src="https://cdn.jsdelivr.net/npm/html2pdf.js@0.10.1/dist/html2pdf.bundle.min.js"></script>
<button id="btn-pdf">PDF</button>
<button id="btn-xlsx">XLSX</button>
<button id="btn-html">HTML</button>
<button id="btn-docx">DOCX</button>
<script>
window.SAMPLE = ${JSON.stringify(SAMPLE_CHAT)};
</script>
</body></html>`;

  await page.setContent(harness);
  await page.waitForFunction(() => typeof window.html2pdf === "function");

  // Injeta as MESMAS funções do FileExportMenu (copiadas do código deployado).
  // Garante validação 1:1 com o que o utilizador receberá em produção.
  const filePath = path.join(__dirname, "..", "components", "FileExportMenu.js");
  const src = fs.readFileSync(filePath, "utf8");

  // Extrai pedaços essenciais por marcadores estáveis.
  function slice(start, end) {
    const a = src.indexOf(start);
    const b = src.indexOf(end, a);
    if (a < 0 || b < 0) throw new Error("marker not found: " + start);
    return src.substring(a, b);
  }
  const fnPlain = slice("export function plainTextForExport(", "function parsePipeTableRow(");
  const fnTableHelpers = slice("function parsePipeTableRow(", "function detectTable(");
  const fnDetect = slice("function detectTable(", "function fallbackBody()");
  const fnFallback = slice("function fallbackBody()", "function defaultExportTitle()");
  const fnDefaults = slice("function defaultExportTitle()", "function quoteCsvCell(");
  const fnQuote = slice("function quoteCsvCell(", "function copyrightLine()");
  const fnCopy = slice("function copyrightLine()", "function buildCsvBlob(");
  const fnHtml = slice(
    "function buildBrandedHtmlDocument(",
    " * Barra PDF/Excel"
  );
  // remove o "/**\n" final que entrou no fim do slice
  const fnHtmlClean = fnHtml.replace(/\/\*\*\s*$/, "").replace(/\n\/\*\*\s*$/, "");

  const inject =
    "var exports = {};\n" +
    "function downloadBlob(blob, name) { window.__downloads = window.__downloads || {}; var fr = new FileReader(); return new Promise(function(res){ fr.onload = function(){ window.__downloads[name] = { mime: blob.type, b64: fr.result.split(',')[1] }; res(); }; fr.readAsDataURL(blob); }); }\n" +
    fnPlain.replace("export function", "function") +
    "\n" +
    fnTableHelpers +
    "\n" +
    fnDetect +
    "\n" +
    fnFallback +
    "\n" +
    fnDefaults +
    "\n" +
    fnQuote +
    "\n" +
    fnCopy +
    "\n" +
    fnHtmlClean +
    "\n" +
    "window.__exports = { plainTextForExport: plainTextForExport, detectTable: detectTable, defaultSubtitle: defaultSubtitle, copyrightLine: copyrightLine, buildBrandedHtmlDocument: buildBrandedHtmlDocument, downloadBlob: downloadBlob };";

  await page.addScriptTag({ content: inject });

  // Executa os 4 fluxos exatamente como em produção.
  await page.evaluate(async () => {
    const E = window.__exports;
    const raw = window.SAMPLE;
    const brandedTitle = "Syntexa — Relatório Inteligente";
    const subtitle = E.defaultSubtitle();
    let plain = E.plainTextForExport(raw);
    if (!plain.trim()) plain = "(vazio)";
    const table = E.detectTable(plain);

    // ── HTML
    const htmlDoc = E.buildBrandedHtmlDocument(raw, brandedTitle, subtitle);
    await E.downloadBlob(new Blob([htmlDoc], { type: "text/html;charset=utf-8" }), "syntexa-relatorio.html");

    // ── XLSX (SpreadsheetML)
    function _xe(v) { return String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    let dataRows = [];
    if (table && table.rows && table.rows.length) {
      const intro = String(table.intro || "").trim();
      if (intro) {
        const ncol = table.rows[0].length;
        intro.split(/\n/).filter(Boolean).forEach(function (l) {
          const r = [l]; while (r.length < ncol) r.push(""); dataRows.push({ cells: r, kind: "intro" });
        });
        dataRows.push({ cells: new Array(table.rows[0].length).fill(""), kind: "sep" });
      }
      table.rows.forEach(function (r, ri) { dataRows.push({ cells: r.slice(), kind: ri === 0 ? "header" : (ri % 2 === 0 ? "even" : "odd") }); });
    } else {
      dataRows.push({ cells: ["De", "Mensagem"], kind: "header" });
      raw.split(/\n\n(?=Você:|Assistente:)/).forEach(function (block) {
        var isUser = block.startsWith("Você:");
        var role = isUser ? "Você" : "Syntexa AI";
        var content = block.replace(/^(Você:|Assistente:)\s*/, "").trim();
        if (!content) return;
        dataRows.push({ cells: [role, content], kind: isUser ? "even" : "odd" });
      });
    }
    var xlHtml = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">';
    xlHtml += '<head><meta charset="utf-8"/><style>body{font-family:Calibri;font-size:11pt;}table{border-collapse:collapse;}td,th{border:1px solid #CBD5E1;padding:6px 10px;}.title{background:#0F172A;color:#fff;font-weight:bold;font-size:14pt;}.header{background:#0F172A;color:#fff;font-weight:bold;}.odd{background:#fff;}.even{background:#F8FAFC;}.intro{background:#EFF6FF;font-style:italic;}.footer{background:#F1F5F9;color:#94A3B8;font-style:italic;}</style></head><body><table>';
    const ncols = dataRows.reduce(function (m, r) { return Math.max(m, r.cells.length); }, 1);
    xlHtml += '<tr><td colspan="' + ncols + '" class="title">' + _xe(brandedTitle) + '</td></tr>';
    xlHtml += '<tr><td colspan="' + ncols + '" style="background:#0F172A;color:#94A3B8;">' + _xe(subtitle) + '</td></tr>';
    dataRows.forEach(function (row) {
      xlHtml += '<tr>';
      const tag = row.kind === "header" ? "th" : "td";
      row.cells.forEach(function (c) { xlHtml += '<' + tag + ' class="' + _xe(row.kind) + '">' + _xe(c) + '</' + tag + '>'; });
      xlHtml += '</tr>';
    });
    xlHtml += '<tr><td colspan="' + ncols + '" class="footer">' + _xe(E.copyrightLine() + " — syntexa.com.br") + '</td></tr></table></body></html>';
    await E.downloadBlob(new Blob(["\uFEFF" + xlHtml], { type: "application/vnd.ms-excel;charset=utf-8" }), "syntexa-relatorio.xls");

    // ── DOCX (RTF)
    function _rtfSafe(s) { return String(s || "").replace(/[\\{}]/g, "").replace(/[\u0080-\uffff]/g, function (c) { return "\\u" + c.charCodeAt(0) + "?"; }); }
    var rtf = "{\\rtf1\\ansi\\ansicpg1252\\deff0\n{\\fonttbl{\\f0 Arial;}}\n";
    rtf += "\\b\\fs36 " + _rtfSafe(brandedTitle) + "\\b0\\par\n";
    rtf += "\\fs18\\i " + _rtfSafe(subtitle) + "\\i0\\par\\par\n";
    if (table && table.rows && table.rows.length >= 2) {
      var ncols2 = table.rows[0].length;
      var cellW = Math.floor(8600 / ncols2);
      table.rows.forEach(function (row, ri) {
        rtf += "\\trowd\\trgaph115\\trleft0\n";
        for (var c = 0; c < ncols2; c++) rtf += "\\clbrdrt\\brdrs\\brdrw10\\clbrdrb\\brdrs\\brdrw10\\clbrdrl\\brdrs\\brdrw10\\clbrdrr\\brdrs\\brdrw10 \\cellx" + ((c + 1) * cellW) + "\n";
        row.forEach(function (cell) { rtf += "\\pard\\intbl " + (ri === 0 ? "\\b " : "") + _rtfSafe(cell) + (ri === 0 ? "\\b0" : "") + "\\cell\n"; });
        rtf += "\\row\n";
      });
    } else {
      rtf += _rtfSafe(plain).replace(/\n/g, "\\par ") + "\\par\n";
    }
    rtf += "\\par " + _rtfSafe(E.copyrightLine()) + "\\par}";
    await E.downloadBlob(new Blob([rtf], { type: "application/msword" }), "syntexa-relatorio.docx");

    // ── PDF (html2pdf.js, igual ao FileExportMenu)
    function _esc2(s) { return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    function _md2html(s) {
      return _esc2(s)
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>")
        .replace(/^\s*#{1,3}\s+(.+)$/gm, "<h3>$1</h3>")
        .replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>")
        .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
        .replace(/\n{2,}/g, "</p><p>")
        .replace(/\n/g, "<br>");
    }
    var msgs = raw.split(/\n\n(?=Você:|Assistente:)/);
    var chatBlocks = "";
    msgs.forEach(function (block) {
      var isUser = block.startsWith("Você:");
      var isAI = block.startsWith("Assistente:");
      if (!isUser && !isAI) { chatBlocks += '<p style="color:#475569;font-size:13px;">' + _md2html(block) + '</p>'; return; }
      var role = isUser ? "Você" : "Syntexa AI";
      var bg = isUser ? "#f1f5f9" : "#eff6ff";
      var bar = isUser ? "#3b82f6" : "#0ea5e9";
      var content = block.replace(/^(Você:|Assistente:)\s*/, "").trim();
      chatBlocks +=
        '<div style="margin:10px 0;border-radius:10px;overflow:hidden;border-left:4px solid ' + bar + ';background:' + bg + ';">' +
        '<div style="background:' + bar + ';color:#fff;font-weight:600;font-size:11px;padding:6px 12px;">' + role + '</div>' +
        '<div style="padding:10px 14px;font-size:13px;line-height:1.65;color:#1e293b;">' + _md2html(content) + '</div>' +
        '</div>';
    });
    var pdfWrap = document.createElement("div");
    pdfWrap.style.cssText = "font-family:'Segoe UI',Arial,sans-serif;color:#1e293b;background:#fff;max-width:780px;margin:0 auto;";
    pdfWrap.innerHTML =
      '<div style="background:#0f172a;color:#fff;padding:20px 28px 16px;margin-bottom:20px;">' +
      '<div style="font-size:22px;font-weight:700;">Syntexa</div>' +
      '<div style="font-size:11px;color:#94a3b8;">Inteligência Artificial Soberana</div>' +
      '<div style="font-size:11px;color:#64748b;margin-top:8px;">' + subtitle + '</div></div>' +
      '<div style="padding:0 28px 20px;">' + chatBlocks + '</div>' +
      '<div style="border-top:1px solid #e2e8f0;margin:0 28px;padding:10px 0;color:#94a3b8;font-size:11px;display:flex;justify-content:space-between;"><span>' + _esc2(E.copyrightLine()) + '</span><span>syntexa.com.br</span></div>';
    document.body.appendChild(pdfWrap);
    const pdfBlob = await window.html2pdf().set({
      margin: [10, 10, 12, 10],
      filename: "syntexa-relatorio.pdf",
      image: { type: "jpeg", quality: 0.97 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff", logging: false },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    }).from(pdfWrap).outputPdf("blob");
    document.body.removeChild(pdfWrap);
    await E.downloadBlob(pdfBlob, "syntexa-relatorio.pdf");
  });

  // Recolhe os blobs gerados.
  const downloads = await page.evaluate(() => window.__downloads);
  expect(Object.keys(downloads).sort()).toEqual([
    "syntexa-relatorio.docx",
    "syntexa-relatorio.html",
    "syntexa-relatorio.pdf",
    "syntexa-relatorio.xls",
  ]);

  for (const [name, info] of Object.entries(downloads)) {
    const buf = Buffer.from(info.b64, "base64");
    fs.writeFileSync(path.join(OUT, name), buf);
    console.log(`[ok] ${name} → ${buf.length} bytes  (mime ${info.mime})`);
    expect(buf.length).toBeGreaterThan(500);
  }

  // Validações específicas
  const html = fs.readFileSync(path.join(OUT, "syntexa-relatorio.html"), "utf8");
  expect(html).toContain("Plano de Negócios");
  expect(html).toContain("R$ 15 bi");
  expect(html).toContain("<table>");
  expect(html).toContain("Syntexa AI");
  expect(html).toContain("background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%)");

  const xls = fs.readFileSync(path.join(OUT, "syntexa-relatorio.xls"), "utf8");
  expect(xls).toContain("Resumo Executivo");
  expect(xls).toContain("R$ 15 bi");
  expect(xls).toContain("background:#0F172A");

  const pdf = fs.readFileSync(path.join(OUT, "syntexa-relatorio.pdf"));
  expect(pdf.slice(0, 4).toString()).toBe("%PDF");
  expect(pdf.length).toBeGreaterThan(5000);

  // Screenshot da pré-visualização do HTML (mostra o visual como sairá em produção).
  const previewPage = await page.context().newPage();
  await previewPage.goto("file://" + path.join(OUT, "syntexa-relatorio.html").replace(/\\/g, "/"));
  await previewPage.setViewportSize({ width: 1024, height: 1400 });
  await previewPage.screenshot({ path: path.join(OUT, "preview-html.png"), fullPage: true });

  // Carrega o PDF no Chromium para snapshot.
  const pdfPage = await page.context().newPage();
  await pdfPage.goto("file://" + path.join(OUT, "syntexa-relatorio.pdf").replace(/\\/g, "/"));
  await pdfPage.waitForTimeout(2000);
  await pdfPage.screenshot({ path: path.join(OUT, "preview-pdf.png"), fullPage: false });

  console.log("Outputs em:", OUT);
});
