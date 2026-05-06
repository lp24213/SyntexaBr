import React from "react";

export default function TermosPage() {
  return React.createElement(
    "main",
    { className: "mx-auto max-w-4xl px-4 py-10 text-zinc-800" },
    React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, "Termos e Condições"),
    React.createElement(
      "p",
      { className: "mt-4 text-sm leading-relaxed" },
      "Ao utilizar a Syntexa, você concorda em usar a plataforma conforme a legislação brasileira e as políticas de segurança. "
      + "É proibido uso abusivo, fraudulento ou que viole direitos de terceiros."
    ),
    React.createElement(
      "p",
      { className: "mt-3 text-sm leading-relaxed" },
      "A conta e as credenciais são de responsabilidade do usuário. Podemos atualizar estes termos para adequação legal e operacional."
    )
  );
}
