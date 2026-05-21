"use client";

import React from "react";
import { CookieConsent } from "./cookie-consent";

export function AppWrapper(props) {
  const { children } = props;
  return React.createElement(
    React.Fragment,
    null,
    React.createElement("div", { id: "root", className: "syntexa-os-shell relative z-10 min-h-[100dvh] w-full overflow-x-hidden text-[#0f172a] bg-white" }, children),
    React.createElement(CookieConsent, null)
  );
}
