"use client";

import React from "react";
import { CryptoBackground } from "./crypto-background";

export function AppWrapper(props) {
  const { children } = props;
  return React.createElement(
    React.Fragment,
    null,
    React.createElement(CryptoBackground, null),
    React.createElement("div", { className: "relative z-10 min-h-screen" }, children)
  );
}
