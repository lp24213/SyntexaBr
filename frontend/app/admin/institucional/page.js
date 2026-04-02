"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AppShell } from "../../../components/shell";
import {
  institutionalListClients,
  institutionalCreateClient,
  institutionalUpdateClient,
  institutionalDeactivateClient,
  institutionalRenewClient,
  institutionalRegenerateKey,
} from "../../../lib/api";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

// ─── Guard: apenas admin ────────────────────────────────────────────────────
function AdminGuard({ children }) {
  const [allowed, setAllowed] = React.useState(null);
  React.useEffect(() => {
    const isAdmin = typeof window !== "undefined" && window.localStorage.getItem("syntexa_is_admin") === "1";
    setAllowed(isAdmin);
  }, []);

  if (allowed === null) return React.createElement("div", { className: "flex min-h-screen items-center justify-center" },
    React.createElement("span", { className: "text-zinc-500 text-sm" }, "Verificando acesso..."));

  if (!allowed) return React.createElement(AppShell, null,
    React.createElement("div", { className: "flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center px-4" },
      React.createElement("div", { className: "flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10" },
        React.createElement(FuturisticIcon, { name: "lock", className: "h-10 w-10 text-violet-300" })),
      React.createElement("h1", { className: "text-xl font-bold text-white" }, "Acesso restrito"),
      React.createElement("p", { className: "text-zinc-400 text-sm max-w-sm" }, "Esta área é exclusiva para administradores do sistema."),
      React.createElement("a", { href: "/login", className: "mt-2 rounded-xl bg-zinc-700 hover:bg-zinc-600 px-6 py-2 text-sm text-white transition-colors" }, "Fazer login")));

  return children;
}

// ─── Utilidades ─────────────────────────────────────────────────────────────
const TYPE_LABEL = { escola: "Escola", municipio: "Município", estado: "Estado", universidade: "Universidade", federal: "Federal" };
const PLAN_LABEL = { basico: "Básico", avancado: "Avançado", enterprise: "Enterprise" };
const TYPE_COLOR = { escola: "bg-blue-500/15 text-blue-300", municipio: "bg-violet-500/15 text-violet-300", estado: "bg-amber-500/15 text-amber-300", universidade: "bg-emerald-500/15 text-emerald-300", federal: "bg-rose-500/15 text-rose-300" };
const PLAN_COLOR = { basico: "bg-zinc-700/60 text-zinc-300", avancado: "bg-sky-500/15 text-sky-300", enterprise: "bg-yellow-500/15 text-yellow-300" };

function fmtDate(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleDateString("pt-BR"); } catch { return iso; }
}

function isExpired(iso) {
  if (!iso) return false;
  return new Date(iso) < new Date();
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  return React.createElement("button", {
    onClick: () => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); },
    className: "ml-2 rounded px-2 py-0.5 text-xs bg-zinc-700 hover:bg-zinc-600 text-zinc-300 transition-colors",
  }, copied ? React.createElement("span", { className: "inline-flex items-center gap-1" }, React.createElement(FuturisticIcon, { name: "check", className: "h-3.5 w-3.5" }), "OK") : "Copiar");
}

// ─── Formulário de criação ───────────────────────────────────────────────────
const EMPTY_FORM = {
  name: "", cnpj: "", client_type: "escola", contact_name: "", contact_email: "",
  contact_phone: "", city: "", state: "", plan: "basico", notes: "", expires_days: 365,
};

function CreateForm({ onCreated, onCancel }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function submit(e) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const created = await institutionalCreateClient({ ...form, expires_days: Number(form.expires_days) || 365 });
      onCreated(created);
    } catch (err) { setError(err.message || "Erro ao criar cliente."); }
    finally { setLoading(false); }
  }

  const inp = "w-full rounded-lg border border-zinc-700 bg-zinc-800/60 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none";
  const lbl = "block text-xs text-zinc-400 mb-1";

  return React.createElement("form", { onSubmit: submit, className: "space-y-4" },
    React.createElement("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2" },
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Nome da instituição *"),
        React.createElement("input", { className: inp, required: true, value: form.name, onChange: e => set("name", e.target.value), placeholder: "Ex: Escola Estadual João XXIII" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "CNPJ"),
        React.createElement("input", { className: inp, value: form.cnpj, onChange: e => set("cnpj", e.target.value), placeholder: "00.000.000/0000-00" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Tipo *"),
        React.createElement("select", { className: inp, value: form.client_type, onChange: e => set("client_type", e.target.value) },
          Object.entries(TYPE_LABEL).map(([k, v]) => React.createElement("option", { key: k, value: k }, v)))),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Plano *"),
        React.createElement("select", { className: inp, value: form.plan, onChange: e => set("plan", e.target.value) },
          Object.entries(PLAN_LABEL).map(([k, v]) => React.createElement("option", { key: k, value: k }, v)))),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Nome do contato"),
        React.createElement("input", { className: inp, value: form.contact_name, onChange: e => set("contact_name", e.target.value), placeholder: "Diretor / Secretário" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "E-mail do contato"),
        React.createElement("input", { type: "email", className: inp, value: form.contact_email, onChange: e => set("contact_email", e.target.value), placeholder: "contato@escola.gov.br" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Telefone"),
        React.createElement("input", { className: inp, value: form.contact_phone, onChange: e => set("contact_phone", e.target.value), placeholder: "(11) 9 9999-9999" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Validade (dias a partir de hoje)"),
        React.createElement("input", { type: "number", min: 1, max: 3650, className: inp, value: form.expires_days, onChange: e => set("expires_days", e.target.value) })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Cidade"),
        React.createElement("input", { className: inp, value: form.city, onChange: e => set("city", e.target.value), placeholder: "São Paulo" })),
      React.createElement("div", null,
        React.createElement("label", { className: lbl }, "Estado"),
        React.createElement("input", { className: inp, value: form.state, onChange: e => set("state", e.target.value), placeholder: "SP" }))),
    React.createElement("div", null,
      React.createElement("label", { className: lbl }, "Observações / Notas internas"),
      React.createElement("textarea", { className: inp + " resize-none h-20", value: form.notes, onChange: e => set("notes", e.target.value), placeholder: "Ex: Contrato assinado em 01/04/2026, 3 laboratórios, 480 alunos." })),
    error && React.createElement("p", { className: "text-rose-400 text-xs" }, error),
    React.createElement("div", { className: "flex gap-3 justify-end" },
      React.createElement("button", { type: "button", onClick: onCancel, className: "rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-400 hover:text-white hover:border-zinc-500 transition-colors" }, "Cancelar"),
      React.createElement("button", { type: "submit", disabled: loading, className: "inline-flex items-center justify-center gap-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-50 px-5 py-2 text-sm font-medium text-white transition-colors" },
        loading ? "Criando..." : React.createElement(React.Fragment, null, React.createElement(FuturisticIcon, { name: "plus", className: "h-4 w-4" }), "Criar licença"))));
}

// ─── Card de cliente ─────────────────────────────────────────────────────────
function ClientCard({ client, onUpdate }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState("");
  const expired = isExpired(client.expires_at);
  const seenRecently = client.last_seen_at && (Date.now() - new Date(client.last_seen_at).getTime()) < 24 * 3600 * 1000;

  async function act(fn, label) {
    setLoading(label);
    try { const updated = await fn(); onUpdate(updated || { ...client, active: false }); }
    catch (e) { alert(e.message || "Erro"); }
    finally { setLoading(""); }
  }

  return React.createElement("div", {
    className: `rounded-xl border ${client.active && !expired ? "border-zinc-700/60" : "border-rose-800/40"} bg-zinc-900/50 p-4 space-y-3`,
  },
    // Header
    React.createElement("div", { className: "flex flex-wrap items-start gap-2 justify-between" },
      React.createElement("div", { className: "flex-1 min-w-0" },
        React.createElement("div", { className: "flex flex-wrap items-center gap-2 mb-1" },
          React.createElement("span", { className: `rounded-full px-2 py-0.5 text-xs font-medium border-0 ${TYPE_COLOR[client.client_type] || "bg-zinc-700 text-zinc-300"}` }, TYPE_LABEL[client.client_type] || client.client_type),
          React.createElement("span", { className: `rounded-full px-2 py-0.5 text-xs font-medium ${PLAN_COLOR[client.plan] || "bg-zinc-700 text-zinc-300"}` }, PLAN_LABEL[client.plan] || client.plan),
          !client.active && React.createElement("span", { className: "rounded-full px-2 py-0.5 text-xs bg-zinc-800 text-zinc-500" }, "Inativo"),
          expired && client.active && React.createElement("span", { className: "rounded-full px-2 py-0.5 text-xs bg-rose-900/50 text-rose-400" }, "Expirado"),
          seenRecently && React.createElement("span", { className: "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs bg-emerald-900/40 text-emerald-400" },
            React.createElement(FuturisticIcon, { name: "online", className: "h-3 w-3 text-emerald-400" }), "Online")),
        React.createElement("h3", { className: "font-semibold text-white text-sm truncate" }, client.name),
        client.city && React.createElement("p", { className: "text-xs text-zinc-500" }, `${client.city}${client.state ? ` — ${client.state}` : ""}`)),
      React.createElement("button", {
        onClick: () => setExpanded(x => !x),
        className: "text-zinc-500 hover:text-zinc-300 text-xs transition-colors shrink-0",
      }, expanded ? "▲ Fechar" : "▼ Detalhes")),

    // Chave de licença
    React.createElement("div", { className: "rounded-lg bg-zinc-800/80 px-3 py-2 flex items-center gap-2 flex-wrap" },
      React.createElement("span", { className: "text-xs text-zinc-500 shrink-0" }, "Licença:"),
      React.createElement("code", { className: "font-mono text-xs text-amber-300 flex-1 break-all" }, client.license_key),
      React.createElement(CopyBtn, { text: client.license_key })),

    // Detalhes expandidos
    expanded && React.createElement("div", { className: "space-y-2 text-xs text-zinc-400" },
      client.cnpj && React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "CNPJ: "), client.cnpj),
      client.contact_name && React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "Contato: "), client.contact_name),
      client.contact_email && React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "E-mail: "), client.contact_email, React.createElement(CopyBtn, { text: client.contact_email })),
      client.contact_phone && React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "Telefone: "), client.contact_phone),
      React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "Criado em: "), fmtDate(client.created_at)),
      React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "Expira em: "), React.createElement("span", { className: expired ? "text-rose-400" : "text-zinc-300" }, fmtDate(client.expires_at))),
      client.last_seen_at && React.createElement("p", null, React.createElement("span", { className: "text-zinc-500" }, "Último sinal: "), fmtDate(client.last_seen_at)),
      client.notes && React.createElement("p", { className: "mt-1 rounded bg-zinc-800/60 px-2 py-1 text-zinc-400 italic" }, client.notes),

      // Ações
      React.createElement("div", { className: "flex flex-wrap gap-2 mt-3 pt-3 border-t border-zinc-800" },
        client.active && !expired && React.createElement("button", {
          disabled: !!loading,
          onClick: () => act(() => institutionalDeactivateClient(client.id), "desativar"),
          className: "rounded-lg border border-rose-800/60 px-3 py-1.5 text-xs text-rose-400 hover:bg-rose-900/20 transition-colors disabled:opacity-50",
        }, loading === "desativar" ? "..." : React.createElement("span", { className: "inline-flex items-center gap-1.5" }, React.createElement(FuturisticIcon, { name: "ban", className: "h-3.5 w-3.5" }), "Desativar")),

        (!client.active || expired) && React.createElement("button", {
          disabled: !!loading,
          onClick: () => act(() => institutionalRenewClient(client.id, 365), "renovar"),
          className: "rounded-lg border border-emerald-700/60 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-900/20 transition-colors disabled:opacity-50",
        }, loading === "renovar" ? "..." : React.createElement("span", { className: "inline-flex items-center gap-1.5" }, React.createElement(FuturisticIcon, { name: "refresh", className: "h-3.5 w-3.5" }), "Renovar +365 dias")),

        React.createElement("button", {
          disabled: !!loading,
          onClick: () => { if (confirm("Gerar nova chave? A chave atual deixará de funcionar.")) act(() => institutionalRegenerateKey(client.id), "regen"); },
          className: "rounded-lg border border-amber-700/60 px-3 py-1.5 text-xs text-amber-400 hover:bg-amber-900/20 transition-colors disabled:opacity-50",
        }, loading === "regen" ? "..." : React.createElement("span", { className: "inline-flex items-center gap-1.5" }, React.createElement(FuturisticIcon, { name: "key", className: "h-3.5 w-3.5" }), "Nova chave")),

        React.createElement("button", {
          onClick: () => {
            const guide = [
              `=== GUIA DE INSTALAÇÃO — ${client.name} ===`,
              ``,
              `1. Baixe o pacote em: https://syntexabr.com.br/download`,
              `2. Execute o instalador na máquina/servidor da instituição.`,
              `3. Quando solicitado, insira a chave de licença:`,
              ``,
              `   ${client.license_key}`,
              ``,
              `4. O sistema irá validar a licença em: https://api.syntexabr.com.br/v1/institutional/validate/${client.license_key}`,
              `5. Configure o DNS local para apontar para este servidor.`,
              `6. Plano ativo: ${PLAN_LABEL[client.plan] || client.plan}`,
              `7. Expira em: ${fmtDate(client.expires_at)}`,
              ``,
              `Suporte: contato@syntexabr.com.br`,
            ].join("\n");
            const blob = new Blob([guide], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a"); a.href = url;
            a.download = `instrucoes-${client.name.replace(/\s+/g, "-").toLowerCase()}.txt`;
            a.click(); URL.revokeObjectURL(url);
          },
          className: "rounded-lg border border-sky-700/60 px-3 py-1.5 text-xs text-sky-400 hover:bg-sky-900/20 transition-colors",
        }, React.createElement("span", { className: "inline-flex items-center gap-1.5" }, React.createElement(FuturisticIcon, { name: "doc", className: "h-3.5 w-3.5" }), "Guia de instalação")))),
  );
}

// ─── Página principal ────────────────────────────────────────────────────────
function InstitucionalAdminPage() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("all");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setClients(await institutionalListClients()); }
    catch (e) { setError(e.message || "Erro ao carregar clientes."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function handleCreated(client) {
    setClients(prev => [client, ...prev]);
    setShowCreate(false);
  }

  function handleUpdate(updated) {
    setClients(prev => prev.map(c => c.id === updated.id ? updated : c));
  }

  const filtered = clients.filter(c => {
    const matchSearch = !search || c.name.toLowerCase().includes(search.toLowerCase()) || (c.license_key || "").toLowerCase().includes(search.toLowerCase()) || (c.city || "").toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === "all" || c.client_type === filterType;
    return matchSearch && matchType;
  });

  const stats = {
    total: clients.length,
    active: clients.filter(c => c.active && !isExpired(c.expires_at)).length,
    expired: clients.filter(c => c.active && isExpired(c.expires_at)).length,
    inactive: clients.filter(c => !c.active).length,
    online: clients.filter(c => c.last_seen_at && (Date.now() - new Date(c.last_seen_at).getTime()) < 24 * 3600 * 1000).length,
  };

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "max-w-5xl mx-auto px-4 py-8 space-y-6" },

      // Header
      React.createElement("div", { className: "flex flex-wrap items-center justify-between gap-4" },
        React.createElement("div", null,
          React.createElement("h1", { className: "text-2xl font-bold text-white flex items-center gap-2" },
            React.createElement(FuturisticIcon, { name: "building", className: "h-7 w-7 text-violet-300 shrink-0" }),
            "Painel Institucional"),
          React.createElement("p", { className: "text-sm text-zinc-400 mt-1" }, "Gerencie licenças para escolas, municípios e governos.")),
        React.createElement("button", {
          onClick: () => setShowCreate(true),
          className: "rounded-xl bg-violet-600 hover:bg-violet-500 px-5 py-2.5 text-sm font-medium text-white transition-colors shadow-lg shadow-violet-900/30",
        }, React.createElement("span", { className: "inline-flex items-center gap-2" }, React.createElement(FuturisticIcon, { name: "plus", className: "h-4 w-4" }), "Nova licença"))),

      // KPIs
      React.createElement("div", { className: "grid grid-cols-2 sm:grid-cols-5 gap-3" },
        [
          ["Total", stats.total, "text-zinc-300"],
          ["Ativas", stats.active, "text-emerald-400"],
          ["Expiradas", stats.expired, "text-rose-400"],
          ["Inativas", stats.inactive, "text-zinc-500"],
          ["Online (24h)", stats.online, "text-sky-400"],
        ].map(([label, val, color]) =>
          React.createElement("div", { key: label, className: "rounded-xl border border-zinc-700/50 bg-zinc-900/50 p-3 text-center" },
            React.createElement("div", { className: `text-2xl font-bold ${color}` }, val),
            React.createElement("div", { className: "text-xs text-zinc-500 mt-0.5" }, label)))),

      // Formulário de criação
      showCreate && React.createElement("div", { className: "rounded-xl border border-violet-800/50 bg-zinc-900/70 p-5 shadow-xl" },
        React.createElement("h2", { className: "text-base font-semibold text-white mb-4" }, "Nova licença institucional"),
        React.createElement(CreateForm, { onCreated: handleCreated, onCancel: () => setShowCreate(false) })),

      // Filtros
      React.createElement("div", { className: "flex flex-wrap gap-3" },
        React.createElement("input", {
          className: "flex-1 min-w-48 rounded-lg border border-zinc-700 bg-zinc-800/60 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none",
          placeholder: "Buscar por nome, cidade ou chave…",
          value: search,
          onChange: e => setSearch(e.target.value),
        }),
        React.createElement("select", {
          className: "rounded-lg border border-zinc-700 bg-zinc-800/60 px-3 py-2 text-sm text-zinc-300 focus:outline-none",
          value: filterType,
          onChange: e => setFilterType(e.target.value),
        },
          React.createElement("option", { value: "all" }, "Todos os tipos"),
          Object.entries(TYPE_LABEL).map(([k, v]) => React.createElement("option", { key: k, value: k }, v)))),

      // Lista
      loading
        ? React.createElement("div", { className: "text-center text-zinc-500 py-16 text-sm" }, "Carregando clientes…")
        : error
          ? React.createElement("div", { className: "rounded-xl bg-rose-900/20 border border-rose-800/40 p-4 text-rose-400 text-sm" }, error)
          : filtered.length === 0
            ? React.createElement("div", { className: "text-center text-zinc-500 py-16 text-sm" }, clients.length === 0 ? "Nenhum cliente cadastrado ainda. Crie a primeira licença acima." : "Nenhum resultado para os filtros aplicados.")
            : React.createElement("div", { className: "space-y-3" },
                filtered.map(c => React.createElement(ClientCard, { key: c.id, client: c, onUpdate: handleUpdate }))),

      // Guia rápido
      React.createElement("div", { className: "rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 space-y-3" },
        React.createElement("h3", { className: "text-sm font-semibold text-white flex items-center gap-2" },
          React.createElement(FuturisticIcon, { name: "book", className: "h-4 w-4 text-zinc-400" }),
          "Como funciona"),
        React.createElement("ol", { className: "list-decimal list-inside space-y-1.5 text-xs text-zinc-400" },
          React.createElement("li", null, "Crie uma nova licença acima informando o nome da instituição, tipo e plano."),
          React.createElement("li", null, "Copie a chave de licença gerada (formato ", React.createElement("code", { className: "text-amber-300" }, "SYNTEXA-XXXX-XXXX-XXXX"), ")."),
          React.createElement("li", null, "Instale o pacote offline (disponível em ", React.createElement("a", { href: "/download", className: "text-sky-400 hover:underline" }, "/download"), ") nos computadores da escola/prefeitura."),
          React.createElement("li", null, "Durante a instalação, insira a chave de licença quando solicitado."),
          React.createElement("li", null, "O sistema validará a chave em: ", React.createElement("code", { className: "text-zinc-400 text-xs" }, "api.syntexabr.com.br/v1/institutional/validate/<chave>")),
          React.createElement("li", { className: "flex flex-wrap items-center gap-1" }, "O sistema instalado enviará heartbeats periódicos — você verá ",
            React.createElement("span", { className: "inline-flex items-center gap-1 text-emerald-400" },
              React.createElement(FuturisticIcon, { name: "online", className: "h-3 w-3" }), "Online"), " quando ativo."),
          React.createElement("li", null, "Para vender ao governo: crie licenças do tipo ", React.createElement("span", { className: "text-amber-300" }, "estado"), " ou ", React.createElement("span", { className: "text-amber-300" }, "federal"), " com plano ", React.createElement("span", { className: "text-yellow-300" }, "Enterprise"), "."),
          React.createElement("li", { className: "flex flex-wrap items-center gap-1" }, "Use ",
            React.createElement("strong", { className: "inline-flex items-center gap-1 text-zinc-200" },
              React.createElement(FuturisticIcon, { name: "doc", className: "h-3.5 w-3.5 text-zinc-300" }), "Guia de instalação"),
            " para baixar um arquivo .txt com todas as instruções para entregar ao TI da instituição.")))));
}

export default function Page() {
  return React.createElement(AdminGuard, null, React.createElement(InstitucionalAdminPage));
}
