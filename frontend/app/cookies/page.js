import React from "react";

export default function CookiesPage() {
  return React.createElement(
    "main",
    { className: "mx-auto max-w-4xl px-4 py-10 text-zinc-800" },
    React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, "Política de Cookies"),
    React.createElement(
      "p",
      { className: "mt-4 text-sm leading-relaxed" },
      "Utilizamos cookies essenciais para login, segurança de sessão e funcionamento da aplicação. "
      + "Cookies de medição podem ser usados para melhorar desempenho e experiência."
    ),
    React.createElement(
      "p",
      { className: "mt-3 text-sm leading-relaxed" },
      "No banner de consentimento, você pode escolher aceitar todos os cookies ou manter apenas os essenciais."
    )
  );
}
