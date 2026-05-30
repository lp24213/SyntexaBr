"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";

export function WhatsAppDashboard() {
  const [stats, setStats] = useState({
    conversations: 0,
    messages: 0,
    companies: 0,
    activeNumbers: 0,
  });
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const token = localStorage.getItem("syntexa_token");
      const headers = { Authorization: `Bearer ${token}` };

      const [companiesRes, convRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/companies`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/messages`, { headers }),
      ]);

      const companies = await companiesRes.json();
      const messages = await convRes.json();

      setStats({
        companies: companies.length || 0,
        conversations: messages.length || 0,
        messages: messages.reduce((acc, c) => acc + (c.message_count || 0), 0),
        activeNumbers: companies.reduce((acc, c) => acc + (c.phone_numbers?.length || 0), 0),
      });
      setConversations(messages.slice(0, 10));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-[#25D366]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Empresas" value={stats.companies} icon="building" />
        <StatCard label="Números Ativos" value={stats.activeNumbers} icon="phone" />
        <StatCard label="Conversas" value={stats.conversations} icon="chat" />
        <StatCard label="Mensagens" value={stats.messages} icon="message" />
      </div>

      <div className="syntexa-card rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-6">
        <h3 className="text-lg font-semibold text-[#0f172a] mb-4">
          Conversas Recentes
        </h3>
        {conversations.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-12 h-12 text-[#cbd5e1] mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
            <p className="text-[#64748b] text-sm">Nenhuma conversa ainda</p>
            <p className="text-[#94a3b8] text-xs mt-1">
              As conversas aparecerão quando mensagens forem recebidas
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {conversations.map((conv) => (
              <ConversationRow key={conv.id} conversation={conv} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon }) {
  const icons = {
    building: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5" />
      </svg>
    ),
    phone: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
      </svg>
    ),
    chat: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
    message: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="syntexa-card rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-5"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-[#f8fafc] text-[#475569] flex items-center justify-center">
          {icons[icon]}
        </div>
      </div>
      <div className="text-2xl font-bold text-[#0f172a]">{value}</div>
      <div className="text-sm text-[#64748b]">{label}</div>
    </motion.div>
  );
}

function ConversationRow({ conversation }) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl hover:bg-[#f8fafc] transition-colors cursor-pointer border border-transparent hover:border-[rgba(15,23,42,0.04)]">
      <div className="w-10 h-10 rounded-full bg-[#25D366]/10 flex items-center justify-center shrink-0">
        <svg className="w-5 h-5 text-[#25D366]" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-[#0f172a] text-sm truncate">
            {conversation.contact_name || conversation.contact_phone || "Contato"}
          </span>
          {conversation.status === "active" && (
            <span className="w-2 h-2 rounded-full bg-[#25D366]" />
          )}
        </div>
        <p className="text-xs text-[#8e9094] truncate mt-0.5">
          {conversation.last_message || "Nenhuma mensagem"}
        </p>
      </div>
      <div className="text-xs text-[#8e9094]">
        {conversation.updated_at
          ? new Date(conversation.updated_at).toLocaleDateString("pt-BR")
          : ""}
      </div>
    </div>
  );
}
