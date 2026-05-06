import { clsx } from "clsx";
import React from "react";

export function Input(props) {
  const { label, className, ...rest } = props;
  const cn = clsx(
    "syntexa-input w-full px-4 py-3 text-sm text-zinc-900 outline-none placeholder:text-zinc-500",
    className
  );
  return React.createElement(
    "label",
    { className: "flex w-full flex-col gap-1.5 text-xs text-zinc-400" },
    label ? React.createElement("span", null, label) : null,
    React.createElement("input", { className: cn, ...rest })
  );
}
