"use client";

import React, { useMemo } from "react";
import { marked } from "marked";

marked.setOptions({
  gfm: true,
  breaks: true,
  async: false,
});

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function sanitizeBeforeParse(raw) {
  let s = String(raw || "");
  s = s.replace(/\\{2,}\s*$/gm, "");
  s = s.replace(/\\{2,}/g, "\n");
  s = s.replace(/~~([^~]*)~~/g, "$1");
  s = s.replace(/~~+/g, "");
  return s;
}

/**
 * Renders Markdown (including GFM tables) safely as HTML using marked.
 * Used exclusively for assistant messages.
 */
export function MarkdownMessage({ content }) {
  const html = useMemo(function () {
    if (!content) return "";
    const clean = sanitizeBeforeParse(content);
    let parsed = "";
    try {
      const result = marked.parse(clean);
      parsed = typeof result === "string" ? result : "<p>" + escapeHtml(clean) + "</p>";
    } catch {
      parsed = "<p>" + escapeHtml(clean) + "</p>";
    }
    return parsed;
  }, [content]);

  return React.createElement("div", {
    className: "syntexa-md prose prose-sm max-w-none text-sm leading-relaxed",
    dangerouslySetInnerHTML: { __html: html },
  });
}
