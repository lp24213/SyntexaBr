"use client";

import React from "react";
import { sanitizeOutput, escapeHTML } from "../lib/sanitizeOutput";

/**
 * Exporta conversa para múltiplos formatos.
 */

function escapeCsv(text) {
  if (!text) return "";
  var t = String(text).replace(/"/g, '""');
  if (/[\r\n",]/.test(t)) t = '"' + t + '"';
  return t;
}

export function exportConversation(messages, format) {
  var visible = messages.filter(function (m) { return m.role !== "system"; });
  var dateStr = new Date().toISOString().slice(0, 10);

  if (format === "txt") {
    var txt = visible.map(function (msg) {
      var time = msg.timestamp ? new Date(msg.timestamp).toLocaleString("pt-BR") : "";
      var header = (msg.role === "user" ? "[Você]" : "[Syntexa]") + (time ? " " + time : "");
      return header + "\n" + sanitizeOutput(msg.content || "") + "\n";
    }).join("\n---\n\n");
    downloadBlob(txt, "text/plain;charset=utf-8", "syntexa-conversa-" + dateStr + ".txt");
    return;
  }

  if (format === "md") {
    var md = "# Conversa Syntexa\n\n";
    md += "_Exportado em " + new Date().toLocaleString("pt-BR") + "_\n\n";
    visible.forEach(function (msg) {
      var time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
      var role = msg.role === "user" ? "**Você**" : "**Syntexa**";
      md += role + (time ? " _" + time + "_" : "") + "\n\n";
      md += sanitizeOutput(msg.content || "") + "\n\n---\n\n";
    });
    downloadBlob(md, "text/markdown;charset=utf-8", "syntexa-conversa-" + dateStr + ".md");
    return;
  }

  if (format === "csv") {
    var csv = "timestamp,role,content\n";
    visible.forEach(function (msg) {
      var time = msg.timestamp ? new Date(msg.timestamp).toISOString() : "";
      csv += escapeCsv(time) + "," + escapeCsv(msg.role) + "," + escapeCsv(sanitizeOutput(msg.content || "")) + "\n";
    });
    downloadBlob(csv, "text/csv;charset=utf-8", "syntexa-conversa-" + dateStr + ".csv");
    return;
  }

  if (format === "json") {
    var jsonData = visible.map(function (msg) {
      return {
        timestamp: msg.timestamp || new Date().toISOString(),
        role: msg.role,
        content: sanitizeOutput(msg.content || ""),
      };
    });
    downloadBlob(JSON.stringify(jsonData, null, 2), "application/json;charset=utf-8", "syntexa-conversa-" + dateStr + ".json");
    return;
  }

  if (format === "html") {
    var html = "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Conversa Syntexa</title>";
    html += "<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#333}";
    html += ".msg{margin:16px 0;padding:16px;border-radius:12px}";
    html += ".user{background:#f1f5f9;margin-left:40px}";
    html += ".assistant{background:#f8fafc;border:1px solid #e2e8f0}";
    html += ".meta{font-size:11px;color:#94a3b8;margin-bottom:4px}";
    html += ".content{white-space:pre-wrap;line-height:1.6}";
    html += "h1{color:#1e293b;font-size:24px;margin-bottom:8px}";
    html += ".date{color:#64748b;font-size:14px;margin-bottom:32px}";
    html += "</style></head><body>";
    html += "<h1>Conversa Syntexa</h1>";
    html += "<div class=\"date\">Exportado em " + new Date().toLocaleString("pt-BR") + "</div>";
    visible.forEach(function (msg) {
      var time = msg.timestamp ? new Date(msg.timestamp).toLocaleString("pt-BR") : "";
      var roleClass = msg.role === "user" ? "user" : "assistant";
      var roleLabel = msg.role === "user" ? "Você" : "Syntexa";
      html += "<div class=\"msg " + roleClass + "\">";
      html += "<div class=\"meta\">" + roleLabel + (time ? " &middot; " + time : "") + "</div>";
      html += "<div class=\"content\">" + escapeHTML(sanitizeOutput(msg.content || "")) + "</div>";
      html += "</div>";
    });
    html += "</body></html>";
    downloadBlob(html, "text/html;charset=utf-8", "syntexa-conversa-" + dateStr + ".html");
    return;
  }
}

function downloadBlob(content, mimeType, fileName) {
  var blob = new Blob([content], { type: mimeType });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExportMenu({ messages }) {
  var [open, setOpen] = React.useState(false);

  return React.createElement(
    "div",
    { className: "relative" },
    React.createElement(
      "button",
      {
        type: "button",
        onClick: function () { setOpen(!open); },
        className: "shrink-0 h-9 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-3 text-xs text-[#475569] hover:bg-[#f1f5f9] inline-flex items-center gap-1.5",
      },
      React.createElement("svg", { className: "h-3.5 w-3.5", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.5" },
        React.createElement("path", { d: "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3", strokeLinecap: "round", strokeLinejoin: "round" })
      ),
      "Exportar"
    ),
    open && React.createElement(
      "div",
      { className: "absolute bottom-full right-0 mb-2 w-40 rounded-xl border border-[#e2e8f0] bg-white shadow-lg py-1 z-50" },
      [
        { label: "Texto (.txt)", format: "txt" },
        { label: "Markdown (.md)", format: "md" },
        { label: "CSV (.csv)", format: "csv" },
        { label: "JSON (.json)", format: "json" },
        { label: "HTML (.html)", format: "html" },
      ].map(function (item) {
        return React.createElement(
          "button",
          {
            key: item.format,
            type: "button",
            onClick: function () { exportConversation(messages, item.format); setOpen(false); },
            className: "w-full px-4 py-2 text-left text-xs text-[#475569] hover:bg-[#f1f5f9] transition-colors",
          },
          item.label
        );
      })
    )
  );
}
