const fs = require("fs");
const path = require("path");

const target = path.join(__dirname, "..", "components", "cookie-consent.js");

const content = `"use client";

import React, { useEffect, useState } from "react";

const TERMS_KEY = "syntexa_terms_accepted_v1";
const CONSENT_KEY = "syntexa_cookie_consent_v1";
const GEO_KEY = "syntexa_geo_v1";

function notifyConsent(value) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent("syntexa:cookie-consent", { detail: { value } })
  );
}

function requestOptionalGeolocation() {
  if (typeof window === "undefined" || !navigator.geolocation) return;
  try {
    if (window.localStorage.getItem(GEO_KEY)) return;
  } catch {
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      try {
        window.localStorage.setItem(
          GEO_KEY,
          JSON.stringify({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            at: new Date().toISOString(),
          })
        );
      } catch {}
    },
    () => {},
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
  );
}

export function CookieConsent() {
  const [phase, setPhase] = useState(null);

  useEffect(() => {
    try {
      const terms = window.localStorage.getItem(TERMS_KEY);
      if (!terms) {
        setPhase("terms");
        return;
      }
      const saved = window.localStorage.getItem(CONSENT_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        notifyConsent(parsed?.value === "accepted" ? "accepted" : "essential_only");
        setPhase(null);
        return;
      }
      const t = setTimeout(() => setPhase("cookies"), 400);
      return () => clearTimeout(t);
    } catch {
      setPhase("terms");
    }
  }, []);

  function acceptTerms() {
    try {
      window.localStorage.setItem(TERMS_KEY, JSON.stringify({ at: new Date().toISOString() }));
    } catch {}
    try {
      if (window.localStorage.getItem(CONSENT_KEY)) {
        setPhase(null);
        return;
      }
    } catch {}
    setPhase("cookies");
  }

  function saveConsent(value) {
    try {
      window.localStorage.setItem(
        CONSENT_KEY,
        JSON.stringify({ value, at: new Date().toISOString() })
      );
    } catch {}
    notifyConsent(value);
    if (value === "accepted") requestOptionalGeolocation();
    setPhase(null);
  }

  if (!phase) return null;

  if (phase === "terms") {
    return (
      <div
        className="fixed inset-0 z-[100] flex items-end justify-center bg-[rgba(15,23,42,0.25)] p-4 backdrop-blur-[2px] sm:items-center"
        role="dialog"
        aria-modal="true"
        aria-label="Termos e condições"
      >
        <div className="w-full max-w-lg rounded-2xl border border-[rgba(15,23,42,0.08)] bg-white p-5 shadow-[0_20px_50px_rgba(15,23,42,0.12)] sm:p-6">
          <h2 className="text-base font-semibold text-[#0f172a]">Antes de continuar</h2>
          <p className="mt-2 text-sm leading-relaxed text-[#475569]">
            Para usar o console da Syntexa, confirme que leu e aceita nossos{" "}
            <a href="/termos" className="font-medium text-[#0f172a] underline-offset-2 hover:underline">
              Termos e Condições
            </a>{" "}
            e a{" "}
            <a href="/privacidade" className="font-medium text-[#0f172a] underline-offset-2 hover:underline">
              Política de Privacidade
            </a>
            .
          </p>
          <TAG_MT5>
            <button
              type="button"
              onClick={acceptTerms}
              className="rounded-lg bg-[#0f172a] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#1e293b]"
            >
              Li e aceito
            </button>
          </TAG_MT5>
        </TAG_CARD>
      </TAG_OVERLAY>
    );
  }

  return (
    <TAG_ROOT
      role="dialog"
      aria-label="Consentimento de cookies"
      className="fixed bottom-4 left-4 right-4 z-[100] mx-auto max-w-md sm:left-auto sm:right-4"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <TAG_PANEL>
        <TAG_ROW>
          <TAG_DOT className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[#475569]" aria-hidden="true" />
          <p className="text-[12px] leading-relaxed text-[#475569]">
            Usamos cookies para manter sua sessão segura e melhorar a experiência. Consulte{" "}
            <a href="/privacidade" className="font-medium text-[#0f172a] underline-offset-2 hover:underline">
              Privacidade
            </a>{" "}
            e{" "}
            <a href="/cookies" className="font-medium text-[#0f172a] underline-offset-2 hover:underline">
              Cookies
            </a>
            .
          </p>
        </TAG_ROW>
        <TAG_ACTIONS>
          <button
            type="button"
            onClick={() => saveConsent("essential_only")}
            className="rounded-lg px-3 py-1.5 text-[11px] font-medium text-[#64748b] transition-colors hover:bg-[rgba(15,23,42,0.04)] hover:text-[#0f172a]"
          >
            Apenas essenciais
          </button>
          <button
            type="button"
            onClick={() => saveConsent("accepted")}
            className="rounded-lg bg-[#0f172a] px-3 py-1.5 text-[11px] font-medium text-white transition-colors hover:bg-[#1e293b]"
          >
            Aceitar
          </button>
        </motionless>
      </motionless>
    </motionless>
  );
}
`;

fs.writeFileSync(target, content.replace(/motionless/g, "div"), "utf8");
console.log("written", target);
