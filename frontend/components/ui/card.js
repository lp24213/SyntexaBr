import { clsx } from "clsx";
import React from "react";

export function Card(props) {
  const { title, description, className, children } = props;
  const header =
    title || description
      ? React.createElement(
          "header",
          { className: "mb-5 space-y-1.5" },
          title && React.createElement("h2", { className: "text-base font-semibold text-zinc-900" }, title),
          description && React.createElement("p", { className: "text-sm text-zinc-500" }, description)
        )
      : null;
  return React.createElement(
    "div",
    {
      className: clsx(
        "syntexa-card relative overflow-hidden p-8",
        className
      ),
    },
    header,
    children
  );
}
