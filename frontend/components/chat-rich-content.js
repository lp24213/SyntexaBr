"use client";
import React from "react";
import { parseRichResponse } from "../lib/chat-rich-format";

function flavorMeta(flavor) {
  if (flavor === "workout") return { tag: "Treino", tone: "from-emerald-50 to-emerald-100 border-emerald-200" };
  if (flavor === "finance") return { tag: "Financeiro", tone: "from-[#f1f5f9] to-[#f8fafc] border-[#e2e8f0]" };
  if (flavor === "timeline") return { tag: "Cronograma", tone: "from-[#f1f5f9] to-[#f8fafc] border-[#e2e8f0]" };
  if (flavor === "comparison") return { tag: "Comparação", tone: "from-amber-50 to-amber-100 border-amber-200" };
  return { tag: "Resposta", tone: "from-zinc-50 to-zinc-100 border-zinc-200" };
}

function TableView(props) {
  var rows = props.rows || [];
  if (!rows.length) return null;
  var header = rows[0];
  var body = rows.slice(1);
  return React.createElement(
    "div",
    { className: "mt-2 overflow-hidden rounded-xl border border-zinc-200 bg-white" },
    React.createElement(
      "div",
      { className: "hidden sm:block overflow-x-auto" },
      React.createElement(
        "table",
        { className: "w-full min-w-[460px] text-left text-xs sm:text-sm" },
        React.createElement(
          "thead",
          { className: "bg-zinc-900 text-zinc-100" },
          React.createElement(
            "tr",
            null,
            header.map(function (h, i) {
              return React.createElement("th", { key: "h-" + i, className: "px-3 py-2 font-semibold" }, h);
            })
          )
        ),
        React.createElement(
          "tbody",
          null,
          body.map(function (row, r) {
            return React.createElement(
              "tr",
              { key: "r-" + r, className: r % 2 ? "bg-zinc-50" : "bg-white" },
              row.map(function (cell, c) {
                return React.createElement("td", { key: "c-" + c, className: "px-3 py-2 text-zinc-700 border-t border-zinc-100" }, cell);
              })
            );
          })
        )
      )
    ),
    React.createElement(
      "div",
      { className: "sm:hidden space-y-2 p-2" },
      body.map(function (row, idx) {
        return React.createElement(
          "div",
          { key: "m-" + idx, className: "rounded-lg border border-zinc-200 bg-zinc-50 p-2" },
          row.map(function (cell, c) {
            return React.createElement(
              "div",
              { key: "mc-" + c, className: "flex items-start justify-between gap-3 py-0.5 text-xs" },
              React.createElement("span", { className: "font-semibold text-zinc-600" }, header[c] || "Campo"),
              React.createElement("span", { className: "text-zinc-800 text-right" }, cell)
            );
          })
        );
      })
    )
  );
}

export function ChatRichContent(props) {
  var text = String(props.text || "");
  var parsed = parseRichResponse(text);
  var blocks = parsed.blocks;
  var flavor = parsed.flavor;
  var meta = flavorMeta(flavor);
  return React.createElement(
    "div",
    { className: "space-y-2.5" },
    React.createElement(
      "div",
      { className: "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold text-zinc-700 bg-gradient-to-r " + meta.tone },
      meta.tag + " estruturado"
    ),
    blocks.map(function (b, idx) {
      if (b.kind === "heading") {
        return React.createElement("h4", { key: "h-" + idx, className: "text-sm sm:text-base font-bold text-zinc-900 mt-1" }, b.text);
      }
      if (b.kind === "table") return React.createElement(TableView, { key: "t-" + idx, rows: b.rows });
      if (b.kind === "list") {
        var listClass = flavor === "timeline" ? "space-y-2" : "space-y-1";
        return React.createElement(
          "ol",
          { key: "l-" + idx, className: listClass + " list-decimal pl-5 text-zinc-800" },
          b.items.map(function (item, n) {
            return React.createElement(
              "li",
              { key: "li-" + n, className: "rounded-md " + (flavor === "timeline" ? "bg-zinc-100 px-2 py-1" : "") },
              item
            );
          })
        );
      }
      return React.createElement(
        "p",
        { key: "p-" + idx, className: "whitespace-pre-wrap text-zinc-800 leading-relaxed rounded-lg bg-white/85 border border-zinc-200 px-3 py-2" },
        b.text
      );
    })
  );
}
