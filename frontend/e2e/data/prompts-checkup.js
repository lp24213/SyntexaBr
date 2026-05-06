/**
 * Gera N prompts distintos (PT-BR) para stress do chat: texto, pedidos de tabela/CSV,
 * imagem, raciocínio, código — para exercitar rotas do frontend + API.
 * @param {number} n — mínimo 1; por defeito 100 (env SYNTEXA_E2E_CHAT_ROUNDS).
 */
function buildCheckupPrompts(n) {
  var count = Math.max(1, Math.min(500, Math.floor(Number(n) || 100)));
  var concepts = [
    "fotossíntese",
    "ciclo de Krebs",
    "lei de Ohm",
    "teorema de Pitágoras",
    "derivada de x²",
    "o que é DNS",
    "diferença entre HTTP e HTTPS",
    "LGPD em uma frase",
    "o que é inflação",
    "Revolução Francesa (data aproximada)",
    "bioma Cerrado",
    "Camada de Ozono",
    "transformada de Laplace (ideia)",
    "rede neural (ideia)",
    "Docker vs VM",
    "Git merge vs rebase (resumo)",
    "complexidade O(n log n)",
    "normalização em BD",
    "ACID em transações",
    "o que é JWT",
    "CORS resumido",
    "REST vs GraphQL",
    "Unicode vs UTF-8",
    "recursão",
    "programação dinâmica",
    "álgebra linear: matriz identidade",
    "números primos",
    "série de Taylor (ideia)",
    "entropia em termodinâmica",
    "equação de Schrödinger (só contexto)",
    "CRISPR (ideia)",
    "mitocôndria",
    "DNA vs RNA",
    "sistema imunitário adaptativo",
    "vacina mRNA (ideia)",
    "aquecimento global",
    "Acordo de Paris (ideia)",
    "direitos humanos",
    "Constituição Federal do Brasil (estrutura)",
    "Marco Civil da Internet (ideia)",
    "economia comportamental",
  ];
  var out = [];
  var imgIdx = 0;
  var images = [
    "Crie uma imagem quadrada simples: um sol amarelo em céu azul.",
    "Gere uma imagem minimalista: uma xícara de café vista de cima.",
    "Crie uma imagem simples: ícone de folha verde em fundo branco.",
    "Gere uma imagem abstrata: gradiente roxo para azul.",
    "Crie uma imagem: silhueta de montanhas ao pôr do sol.",
    "Gere uma imagem: um gato estilizado em arte plana.",
    "Crie uma imagem: um robô amigável em estilo cartoon.",
    "Gere uma imagem: ondas do mar vistas de cima.",
  ];
  var k = 0;
  while (out.length < count) {
    var i = out.length;
    if (i > 0 && i % 11 === 0) {
      out.push(images[imgIdx % images.length]);
      imgIdx++;
      continue;
    }
    if (i > 0 && i % 19 === 0) {
      out.push(
        "Sem markdown: escreva 4 linhas de exemplo em formato CSV com cabeçalho nome,idade,cidade e três linhas fictícias."
      );
      continue;
    }
    if (i > 0 && i % 23 === 0) {
      out.push(
        "Liste em tópicos curtos: 3 vantagens de energia solar e 2 limitações."
      );
      continue;
    }
    var c = concepts[k % concepts.length];
    k++;
    out.push(
      "Pergunta " +
        (i + 1) +
        ": Explique em no máximo 4 frases, em português claro, o seguinte: " +
        c +
        "."
    );
  }
  return out.slice(0, count);
}

module.exports = { buildCheckupPrompts };
