function cleanLine(line) {
  return String(line || "").replace(/\t/g, " ").replace(/\s+/g, " ").trim();
}

function isVisualNoiseLine(line) {
  var t = cleanLine(line);
  if (!t) return false;
  if (/^[|_\-*=~`^#%&$@!+.:;,\\/()\[\]{}<>?¨"'’`´]+$/.test(t)) return true;
  var alnum = (t.match(/[a-zA-Z0-9À-ÿ]/g) || []).length;
  var sym = (t.match(/[^a-zA-Z0-9À-ÿ\s]/g) || []).length;
  return sym >= 6 && alnum <= 2;
}

function isMdSeparatorLine(line) {
  var t = cleanLine(line);
  return /^\|?[\s:-]+\|[\s|:-]*$/.test(t);
}

function parsePipeRow(line) {
  var raw = String(line || "").trim();
  if (!raw.includes("|")) return null;
  var parts = raw.split("|").map(function (p) {
    return p.trim();
  });
  if (parts[0] === "") parts.shift();
  if (parts[parts.length - 1] === "") parts.pop();
  if (parts.length < 2) return null;
  return parts;
}

function detectTable(lines, start) {
  var first = parsePipeRow(lines[start]);
  if (!first) return null;
  var cursor = start + 1;
  if (cursor < lines.length && isMdSeparatorLine(lines[cursor])) cursor++;
  var rows = [first];
  while (cursor < lines.length) {
    var row = parsePipeRow(lines[cursor]);
    if (!row || row.length !== first.length) break;
    rows.push(row);
    cursor++;
  }
  if (rows.length < 2) return null;
  return { kind: "table", rows: rows, end: cursor - 1 };
}

function parseBlocks(raw) {
  var text = String(raw || "").replace(/\r\n/g, "\n");
  var lines = text.split("\n");
  var blocks = [];
  var i = 0;
  while (i < lines.length) {
    var line = lines[i];
    var trimmed = cleanLine(line);
    if (!trimmed) {
      i++;
      continue;
    }
    if (isVisualNoiseLine(trimmed)) {
      i++;
      continue;
    }
    var table = detectTable(lines, i);
    if (table) {
      blocks.push({ kind: "table", rows: table.rows });
      i = table.end + 1;
      continue;
    }
    if (/^#{1,3}\s+/.test(trimmed)) {
      blocks.push({ kind: "heading", level: (trimmed.match(/^#+/) || ["#"])[0].length, text: trimmed.replace(/^#{1,3}\s+/, "") });
      i++;
      continue;
    }
    if (/^(\d+[\.\)]|-|\*|•)\s+/.test(trimmed)) {
      var items = [];
      while (i < lines.length) {
        var li = cleanLine(lines[i]);
        if (!/^(\d+[\.\)]|-|\*|•)\s+/.test(li)) break;
        items.push(li.replace(/^(\d+[\.\)]|-|\*|•)\s+/, ""));
        i++;
      }
      blocks.push({ kind: "list", items: items });
      continue;
    }
    var para = [trimmed];
    i++;
    while (i < lines.length) {
      var next = cleanLine(lines[i]);
      if (!next) break;
      if (detectTable(lines, i) || /^#{1,3}\s+/.test(next) || /^(\d+[\.\)]|-|\*|•)\s+/.test(next)) break;
      para.push(next);
      i++;
    }
    blocks.push({ kind: "paragraph", text: para.join(" ") });
  }
  return blocks;
}

function detectFlavor(blocks) {
  var full = blocks
    .map(function (b) {
      if (b.kind === "paragraph" || b.kind === "heading") return b.text || "";
      if (b.kind === "list") return (b.items || []).join(" ");
      if (b.kind === "table") return (b.rows || []).flat().join(" ");
      return "";
    })
    .join(" ")
    .toLowerCase();
  if (/\b(seg|segunda|terça|quarta|quinta|sexta|sábado|domingo|treino|série|repeti)/.test(full)) return "workout";
  if (/\b(r\$|receita|despesa|saldo|lucro|invest|finance)/.test(full)) return "finance";
  if (/\b(cronograma|etapa|fase|prazo|semana|mês|mes|dia)\b/.test(full)) return "timeline";
  if (/\b(vs|versus|compar|diferença|diferenca|prós|contras)\b/.test(full)) return "comparison";
  return "text";
}

export function parseRichResponse(raw) {
  var blocks = parseBlocks(raw);
  var flavor = detectFlavor(blocks);
  return { blocks: blocks, flavor: flavor };
}

export function toExportReadyText(raw) {
  var parsed = parseRichResponse(raw);
  var out = [];
  for (var i = 0; i < parsed.blocks.length; i++) {
    var b = parsed.blocks[i];
    if (b.kind === "heading") out.push(b.text);
    else if (b.kind === "paragraph") out.push(b.text);
    else if (b.kind === "list") {
      for (var j = 0; j < b.items.length; j++) out.push((j + 1) + ". " + b.items[j]);
    } else if (b.kind === "table") {
      for (var r = 0; r < b.rows.length; r++) out.push(b.rows[r].join(" ; "));
    }
  }
  return out.join("\n").trim();
}
