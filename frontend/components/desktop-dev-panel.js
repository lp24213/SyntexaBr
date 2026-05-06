"use client";

import React, { useEffect, useMemo, useState } from "react";

function hasDesktopApi() {
  return typeof window !== "undefined" && window.syntexaDesktop;
}

export function DesktopDevPanel() {
  const [enabled, setEnabled] = useState(false);
  const [workspaceRoot, setWorkspaceRoot] = useState("");
  const [items, setItems] = useState([]);
  const [currentFile, setCurrentFile] = useState("");
  const [editorText, setEditorText] = useState("");
  const [newFilePath, setNewFilePath] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(function () {
    if (!hasDesktopApi()) return;
    setEnabled(true);
    let off = function () {};
    (async function () {
      try {
        const root = await window.syntexaDesktop.getWorkspaceRoot();
        if (root) {
          setWorkspaceRoot(root);
          const list = await window.syntexaDesktop.listDirectory(root);
          setItems(Array.isArray(list) ? list : []);
        }
      } catch (_) {}
      off = window.syntexaDesktop.onSelection(async function (payload) {
        if (!payload || !payload.path) return;
        if (payload.kind === "folder") {
          setWorkspaceRoot(payload.path);
          setCurrentFile("");
          setEditorText("");
          try {
            const list = await window.syntexaDesktop.listDirectory(payload.path);
            setItems(Array.isArray(list) ? list : []);
            setStatus("Pasta aberta.");
          } catch (e) {
            setStatus((e && e.message) || "Falha ao listar pasta.");
          }
          return;
        }
        if (payload.kind === "file") {
          try {
            const out = await window.syntexaDesktop.readFile(payload.path);
            setCurrentFile(out.path || payload.path);
            setEditorText(out.content || "");
            setStatus("Arquivo aberto.");
          } catch (e) {
            setStatus((e && e.message) || "Falha ao abrir arquivo.");
          }
        }
      });
    })();
    return function () {
      try {
        off();
      } catch (_) {}
    };
  }, []);

  const visibleItems = useMemo(function () {
    return items.slice(0, 300);
  }, [items]);

  async function openFolder() {
    if (!enabled) return;
    try {
      setBusy(true);
      await window.syntexaDesktop.openFolder();
    } catch (e) {
      setStatus((e && e.message) || "Falha ao abrir pasta.");
    } finally {
      setBusy(false);
    }
  }

  async function openFile() {
    if (!enabled) return;
    try {
      setBusy(true);
      await window.syntexaDesktop.openFile();
    } catch (e) {
      setStatus((e && e.message) || "Falha ao abrir arquivo.");
    } finally {
      setBusy(false);
    }
  }

  async function refreshList() {
    if (!workspaceRoot || !enabled) return;
    try {
      setBusy(true);
      const list = await window.syntexaDesktop.listDirectory(workspaceRoot);
      setItems(Array.isArray(list) ? list : []);
      setStatus("Lista atualizada.");
    } catch (e) {
      setStatus((e && e.message) || "Falha ao atualizar.");
    } finally {
      setBusy(false);
    }
  }

  async function saveCurrent() {
    if (!currentFile || !enabled) return;
    try {
      setBusy(true);
      await window.syntexaDesktop.writeFile(currentFile, editorText);
      setStatus("Arquivo salvo.");
    } catch (e) {
      setStatus((e && e.message) || "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  async function createFromEditor() {
    if (!newFilePath || !enabled) return;
    try {
      setBusy(true);
      await window.syntexaDesktop.createFile(newFilePath, editorText);
      setCurrentFile(newFilePath);
      setStatus("Arquivo criado.");
      await refreshList();
    } catch (e) {
      setStatus((e && e.message) || "Falha ao criar arquivo.");
    } finally {
      setBusy(false);
    }
  }

  async function openFromList(filePath) {
    if (!enabled || !filePath) return;
    try {
      setBusy(true);
      const out = await window.syntexaDesktop.readFile(filePath);
      setCurrentFile(out.path || filePath);
      setEditorText(out.content || "");
      setStatus("Arquivo carregado.");
    } catch (e) {
      setStatus((e && e.message) || "Falha ao abrir da lista.");
    } finally {
      setBusy(false);
    }
  }

  if (!enabled) return null;

  return React.createElement(
    "section",
    { className: "mx-auto mb-3 w-full max-w-3xl rounded-xl border border-zinc-200 bg-white p-3 shadow-sm" },
    React.createElement(
      "div",
      { className: "mb-2 flex flex-wrap items-center gap-2" },
      React.createElement(
        "button",
        { type: "button", onClick: openFolder, disabled: busy, className: "rounded-lg border border-zinc-300 bg-zinc-50 px-2 py-1 text-xs text-zinc-800 hover:bg-zinc-100 disabled:opacity-50" },
        "Open Folder"
      ),
      React.createElement(
        "button",
        { type: "button", onClick: openFile, disabled: busy, className: "rounded-lg border border-zinc-300 bg-zinc-50 px-2 py-1 text-xs text-zinc-800 hover:bg-zinc-100 disabled:opacity-50" },
        "Open File"
      ),
      React.createElement(
        "button",
        { type: "button", onClick: refreshList, disabled: busy || !workspaceRoot, className: "rounded-lg border border-zinc-300 bg-zinc-50 px-2 py-1 text-xs text-zinc-800 hover:bg-zinc-100 disabled:opacity-50" },
        "Refresh"
      ),
      React.createElement("span", { className: "ml-auto text-[11px] text-zinc-500" }, workspaceRoot || "Sem pasta selecionada")
    ),
    React.createElement(
      "div",
      { className: "grid gap-2 sm:grid-cols-[220px_1fr]" },
      React.createElement(
        "div",
        { className: "max-h-52 overflow-auto rounded-lg border border-zinc-200 bg-zinc-50 p-2" },
        visibleItems.length === 0
          ? React.createElement("p", { className: "text-[11px] text-zinc-500" }, "Abra uma pasta para listar arquivos.")
          : visibleItems.map(function (it) {
              const isDir = it.type === "directory";
              return React.createElement(
                "button",
                {
                  key: it.path,
                  type: "button",
                  disabled: busy || isDir,
                  onClick: function () {
                    if (!isDir) openFromList(it.path);
                  },
                  className:
                    "mb-1 flex w-full items-center justify-start rounded px-2 py-1 text-left text-[11px] " +
                    (isDir ? "text-zinc-500" : "text-zinc-800 hover:bg-zinc-100") +
                    " disabled:opacity-60",
                },
                isDir ? "[DIR] " : "[FILE] ",
                it.name
              );
            })
      ),
      React.createElement(
        "div",
        { className: "space-y-2" },
        React.createElement("input", {
          value: currentFile,
          readOnly: true,
          placeholder: "Arquivo atual",
          className: "w-full rounded-lg border border-zinc-200 bg-zinc-50 px-2 py-1 text-[11px] text-zinc-700",
        }),
        React.createElement("textarea", {
          value: editorText,
          onChange: function (e) {
            setEditorText(e.target.value);
          },
          rows: 8,
          className: "w-full resize-y rounded-lg border border-zinc-200 bg-white px-2 py-2 text-xs text-zinc-800",
          placeholder: "Conteudo do arquivo...",
        }),
        React.createElement(
          "div",
          { className: "flex flex-wrap items-center gap-2" },
          React.createElement("input", {
            value: newFilePath,
            onChange: function (e) {
              setNewFilePath(e.target.value);
            },
            placeholder: "Novo arquivo (caminho completo na pasta aberta)",
            className: "min-w-[240px] flex-1 rounded-lg border border-zinc-200 bg-zinc-50 px-2 py-1 text-[11px] text-zinc-700",
          }),
          React.createElement(
            "button",
            { type: "button", onClick: createFromEditor, disabled: busy || !newFilePath, className: "rounded-lg border border-emerald-300 bg-emerald-50 px-2 py-1 text-xs text-emerald-800 hover:bg-emerald-100 disabled:opacity-50" },
            "Criar arquivo"
          ),
          React.createElement(
            "button",
            { type: "button", onClick: saveCurrent, disabled: busy || !currentFile, className: "rounded-lg border border-violet-300 bg-violet-50 px-2 py-1 text-xs text-violet-800 hover:bg-violet-100 disabled:opacity-50" },
            "Salvar"
          )
        ),
        status && React.createElement("p", { className: "text-[11px] text-zinc-500" }, status)
      )
    )
  );
}
