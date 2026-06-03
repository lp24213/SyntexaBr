import React from "react";
import PlanosPage from "../../../../app/planos/page";

export async function generateStaticParams() {
  return [
    { locale: "pt-BR" },
    { locale: "en-US" },
    { locale: "es-ES" },
    { locale: "zh-CN" },
  ];
}

export default function LocalePlansPage({ params }) {
  return React.createElement(PlanosPage);
}
