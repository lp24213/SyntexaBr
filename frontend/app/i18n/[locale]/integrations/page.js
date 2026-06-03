import React from "react";
import IntegrationsClient from "./IntegrationsClient";

export async function generateStaticParams() {
  return [
    { locale: "pt-BR" },
    { locale: "en-US" },
    { locale: "es-ES" },
    { locale: "zh-CN" },
  ];
}

export default function IntegrationsPage({ params }) {
  return React.createElement(IntegrationsClient, { locale: params.locale });
}

