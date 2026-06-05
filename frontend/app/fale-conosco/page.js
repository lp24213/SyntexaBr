"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import {
  NeonDivider,
  GlassPanel,
  FloatingCTA,
} from "../../components/premium";

/**
 * PÁGINA /fale-conosco — Formulário de Contato Premium
 * Integrado com API para envio de email e banco de dados
 */

export default function ContatoPage() {
  const [formData, setFormData] = useState({
    nome: "",
    email: "",
    empresa: "",
    assunto: "",
    mensagem: "",
    telefone: "",
    tipo: "geral",
  });

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Erro ao enviar mensagem");
      }

      const result = await response.json();
      setStatus("success");
      setFormData({
        nome: "",
        email: "",
        empresa: "",
        assunto: "",
        mensagem: "",
        telefone: "",
        tipo: "geral",
      });

      setTimeout(() => setStatus(null), 5000);
    } catch (err) {
      setError(err.message || "Erro ao enviar mensagem. Tente novamente.");
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const assuntos = [
    { value: "parceria", label: "Parcerias" },
    { value: "integracao", label: "Integração API" },
    { value: "suporte", label: "Suporte" },
    { value: "vendas", label: "Vendas" },
    { value: "geral", label: "Outro" },
  ];

  return (
    <AppShell>
      <main className="relative w-full overflow-x-hidden bg-white text-[#0f172a]">
        {/* ===== HERO ===== */}
        <section className="relative min-h-screen flex items-center justify-center px-5 py-24">
          <div className="mx-auto w-full max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="mb-6 inline-flex rounded-full border border-[rgba(5,150,105,0.2)] bg-[rgba(5,150,105,0.05)] px-4 py-1.5"
            >
              <svg
                className="w-4 h-4 text-[#059669] mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
              </svg>
              <span className="text-sm font-medium text-[#059669]">
                Entre em Contato
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              className="text-4xl md:text-5xl font-medium leading-tight"
            >
              Fale Conosco
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-xl text-[#64748b] max-w-2xl mx-auto"
            >
              Tem uma pergunta? Quer parcerias? Precisa de suporte? Estamos aqui para ajudar. Envie sua mensagem e responderemos em breve.
            </motion.p>
          </div>
        </section>

        {/* ===== FORMULÁRIO ===== */}
        <section className="relative py-24 px-5">
          <NeonDivider variant="medium" />

          <div className="mx-auto max-w-2xl">
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              onSubmit={handleSubmit}
              className="space-y-6"
            >
              {/* Status Messages */}
              {status === "success" && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg bg-[rgba(5,150,105,0.1)] border border-[rgba(5,150,105,0.3)] p-4"
                >
                  <p className="text-sm font-medium text-[#059669]">
                    Mensagem enviada com sucesso! Entraremos em contato em breve.
                  </p>
                </motion.div>
              )}

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg bg-[rgba(220,38,38,0.1)] border border-[rgba(220,38,38,0.3)] p-4"
                >
                  <p className="text-sm font-medium text-red-600">{error}</p>
                </motion.div>
              )}

              {/* Tipo de Contato */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Assunto
                </label>
                <select
                  name="tipo"
                  value={formData.tipo}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                >
                  {assuntos.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Nome Completo
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  placeholder="Seu nome"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  placeholder="seu@email.com"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                />
              </div>

              {/* Empresa */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Empresa
                </label>
                <input
                  type="text"
                  name="empresa"
                  value={formData.empresa}
                  onChange={handleChange}
                  placeholder="Nome da sua empresa"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                />
              </div>

              {/* Telefone */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Telefone (Opcional)
                </label>
                <input
                  type="tel"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleChange}
                  placeholder="+55 (11) 99999-9999"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                />
              </div>

              {/* Assunto */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Título da Mensagem
                </label>
                <input
                  type="text"
                  name="assunto"
                  value={formData.assunto}
                  onChange={handleChange}
                  required
                  placeholder="Resumo da sua mensagem"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all"
                />
              </div>

              {/* Mensagem */}
              <div>
                <label className="block text-sm font-medium text-[#0f172a] mb-2">
                  Mensagem
                </label>
                <textarea
                  name="mensagem"
                  value={formData.mensagem}
                  onChange={handleChange}
                  required
                  placeholder="Escreva sua mensagem aqui..."
                  rows="6"
                  className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white px-4 py-2.5 text-[#0f172a] placeholder-[#94a3b8] focus:border-[rgba(5,150,105,0.3)] focus:outline-none focus:ring-1 focus:ring-[rgba(5,150,105,0.2)] transition-all resize-none"
                />
              </div>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full rounded-lg bg-[#059669] px-6 py-3 font-medium text-white transition-colors hover:bg-[#047857] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Enviando..." : "Enviar Mensagem"}
              </motion.button>
            </motion.form>
          </div>
        </section>

        {/* ===== INFO CARDS ===== */}
        <section className="relative py-24 px-5 bg-[#f8fafc]">
          <div className="mx-auto max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="mb-12 text-center"
            >
              <h2 className="text-3xl font-medium">Outras Formas de Contato</h2>
            </motion.div>

            <div className="grid gap-6 md:grid-cols-4">
              {[
                {
                  title: "Email",
                  value: "contato@syntexabr.com.br",
                  icon: (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                      <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                    </svg>
                  ),
                },
                {
                  title: "Parcerias",
                  value: "parceiros@syntexabr.com.br",
                  icon: (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                    </svg>
                  ),
                },
                {
                  title: "Telefone",
                  value: "+55 (66) 99236-3830",
                  icon: (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773c.418 1.291 1.207 2.532 2.202 3.526a8.3 8.3 0 003.526 2.202l.773-1.548a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1H4a1 1 0 01-1-1V3z" />
                    </svg>
                  ),
                },
                {
                  title: "Agendar",
                  value: "Abrir Calendly",
                  link: "https://calendly.com/syntexabr",
                  icon: (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v2h16V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zM4 8h16v9a2 2 0 01-2 2H6a2 2 0 01-2-2V8zm2 3a1 1 0 100 2h1a1 1 0 100-2H6zm4-1a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                  ),
                },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                >
                  {item.link ? (
                    <a href={item.link} target="_blank" rel="noopener noreferrer" className="block h-full">
                      <GlassPanel
                        icon={() => (
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)] text-[#059669]">
                            {item.icon}
                          </div>
                        )}
                        title={item.title}
                        subtitle={item.value}
                      />
                    </a>
                  ) : (
                    <GlassPanel
                      icon={() => (
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(5,150,105,0.08)] text-[#059669]">
                          {item.icon}
                        </div>
                      )}
                      title={item.title}
                      subtitle={item.value}
                    />
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== FLOATING CTA ===== */}
        <FloatingCTA
          title="Mensagem Enviada?"
          subtitle="Obrigado por entrar em contato"
          primaryText="Voltar"
          primaryHref="/"
        />
      </main>
    </AppShell>
  );
}
