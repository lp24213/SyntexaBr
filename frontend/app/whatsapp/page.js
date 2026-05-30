"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { WhatsAppConnect } from "../../components/whatsapp-connect";
import { WhatsAppDashboard } from "../../components/whatsapp-dashboard";

export default function WhatsAppPage() {
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkConnection();
  }, []);

  async function checkConnection() {
    try {
      const token = localStorage.getItem("syntexa_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/companies`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConnected(data.length > 0);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#25D366]" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-[#1a1c1e] mb-2">
              WhatsApp Business
            </h1>
            <p className="text-[#64748b] text-sm">
              Conecte seu WhatsApp Business e gerencie conversas com IA
            </p>
          </div>

          {connected ? (
            <WhatsAppDashboard />
          ) : (
            <WhatsAppConnect onConnect={() => setConnected(true)} />
          )}
        </motion.div>
      </div>
    </AppShell>
  );
}
