"use client";

import React from "react";
import { CryptoBackground } from "./crypto-background";
import { CookieConsent } from "./cookie-consent";

export function AppWrapper(props) {
  const { children } = props;
  return React.createElement(
    React.Fragment,
    null,
    React.createElement(CryptoBackground, null),
    React.createElement("div", { id: "root", className: "relative z-10 min-h-[100dvh] w-full max-w-[100vw] overflow-x-hidden bg-[#f8f9fb] text-zinc-900" }, children),
    React.createElement(CookieConsent, null)
  );
}
