"use client";

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
    function (pos) {
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
      } catch (_) {}
    },
    function () {},
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
  );
}

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [needsTerms, setNeedsTerms] = useState(false);

  useEffect(function () {
    try {
      var terms = window.localStorage.getItem(TERMS_KEY);
      var saved = window.localStorage.getItem(CONSENT_KEY);
      if (saved) {
        var parsed = JSON.parse(saved);
        notifyConsent(parsed && parsed.value === "accepted" ? "accepted" : "essential_only");
        setVisible(false);
        return;
      }
      setNeedsTerms(!terms);
      var t = setTimeout(function () { setVisible(true); }, 300);
      return function () { clearTimeout(t); };
    } catch {
      setNeedsTerms(true);
      setVisible(true);
    }
  }, []);

  function acceptAll() {
    try {
      window.localStorage.setItem(TERMS_KEY, JSON.stringify({ at: new Date().toISOString() }));
      window.localStorage.setItem(
        CONSENT_KEY,
        JSON.stringify({ value: "accepted", at: new Date().toISOString() })
      );
    } catch (_) {}
    notifyConsent("accepted");
    requestOptionalGeolocation();
    setVisible(false);
  }

  function acceptEssential() {
    try {
      window.localStorage.setItem(TERMS_KEY, JSON.stringify({ at: new Date().toISOString() }));
      window.localStorage.setItem(
        CONSENT_KEY,
        JSON.stringify({ value: "essential_only", at: new Date().toISOString() })
      );
    } catch (_) {}
    notifyConsent("essential_only");
    setVisible(false);
  }

  if (!visible) return null;

  return React.createElement(
    "div",
    {
      className:
        "fixed bottom-0 left-0 right-0 z-[80] pointer-events-none px-4 pb-4 sm:px-6",
      style: { paddingBottom: "max(1rem, env(safe-area-inset-bottom))" },
      role: "dialog",
      "aria-label": needsTerms ? "Termos e cookies" : "Cookies",
    },
    React.createElement(
      "div",
      {
        className:
          "pointer-events-auto mx-auto w-full max-w-xl rounded-2xl border border-[rgba(15,23,42,0.08)] bg-white p-4 shadow-[0_12px_40px_rgba(15,23,42,0.14)]",
      },
      React.createElement(
        "p",
        { className: "text-sm leading-relaxed text-[#475569]" },
        needsTerms
          ? "Para usar o chat, aceite os "
          : "Usamos cookies para manter sua sessão. Veja ",
        React.createElement(
          "a",
          { href: "/termos", className: "font-medium text-[#0f172a] underline-offset-2 hover:underline" },
          "Termos"
        ),
        " e ",
        React.createElement(
          "a",
          { href: "/privacidade", className: "font-medium text-[#0f172a] underline-offset-2 hover:underline" },
          "Privacidade"
        ),
        needsTerms ? "." : "."
      ),
      React.createElement(
        "div",
        { className: "mt-3 flex flex-wrap items-center justify-end gap-2" },
        React.createElement(
          "button",
          {
            type: "button",
            onClick: acceptEssential,
            className:
              "rounded-lg px-3 py-2 text-xs font-medium text-[#64748b] hover:bg-[rgba(15,23,42,0.04)]",
          },
          "Só o essencial"
        ),
        React.createElement(
          "button",
          {
            type: "button",
            onClick: acceptAll,
            className:
              "rounded-lg bg-[#334155] px-4 py-2 text-xs font-medium text-white hover:bg-[#1e293b]",
          },
          "Aceitar e continuar"
        )
      )
    )
  );
}
