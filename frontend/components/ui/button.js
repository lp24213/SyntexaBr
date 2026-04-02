import { cva } from "class-variance-authority";
import { clsx } from "clsx";
import React from "react";

const buttonStyles = cva(
  "inline-flex items-center justify-center rounded-[14px] text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(59,130,246,0.4)] focus-visible:ring-offset-2 focus-visible:ring-offset-[#050506] disabled:opacity-60 disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        primary: "syntexa-btn-primary bg-[var(--text-primary)] text-[var(--bg-root)]",
        outline: "syntexa-btn-outline",
        ghost: "bg-transparent text-zinc-400 hover:bg-white/5 border border-transparent hover:text-white",
      },
      size: {
        sm: "px-3 py-1.5 text-xs",
        md: "px-4 py-2",
        lg: "px-5 py-2.5 text-base",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export function Button(props) {
  const { children, className, variant, size, ...rest } = props;
  return React.createElement(
    "button",
    { className: clsx(buttonStyles({ variant, size }), className), ...rest },
    children
  );
}
