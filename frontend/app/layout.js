import "./globals.css";
import React, { Suspense } from "react";
import Script from "next/script";
import { AppWrapper } from "../components/app-wrapper";

export const metadata = {
  metadataBase: new URL("https://syntexabr.com.br"),
  title: {
    default: "Syntexa AI",
    template: "%s | Syntexa AI",
  },
  description:
    "Plataforma de IA da Syntexa para chat, geração de conteúdo, exportação profissional e operações educacionais e institucionais.",
  keywords: [
    "Syntexa",
    "IA",
    "inteligência artificial",
    "chat com IA",
    "plataforma educacional",
    "automação de conteúdo",
    "exportação PDF DOCX XLSX",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: "https://syntexabr.com.br",
    title: "Syntexa AI",
    description:
      "Plataforma de IA para produtividade, educação e operações institucionais com foco em entrega prática.",
    siteName: "Syntexa AI",
    images: [{ url: "/LOGOTIPO.png", width: 1024, height: 1024, alt: "Syntexa AI" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Syntexa AI",
    description:
      "Plataforma de IA para chat, criação de materiais e exportação profissional.",
    images: ["/LOGOTIPO.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/LOGOTIPO.png",
    shortcut: "/LOGOTIPO.png",
    apple: "/LOGOTIPO.png",
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
};

const GOOGLE_TAG_ID = "G-4S5QPJQ2J8";
const isProduction = process.env.NODE_ENV === "production";

export default function RootLayout(props) {
  const { children } = props;
  return React.createElement(
    "html",
    { lang: "pt-BR" },
    React.createElement(
      "head",
      null,
      isProduction &&
        React.createElement(Script, {
          src: `https://www.googletagmanager.com/gtag/js?id=${GOOGLE_TAG_ID}`,
          strategy: "afterInteractive",
        }),
      isProduction &&
        React.createElement(
          Script,
          { id: "google-gtag", strategy: "afterInteractive" },
          "window.dataLayer = window.dataLayer || [];" +
            "function gtag(){dataLayer.push(arguments);}" +
            "window.gtag = gtag;" +
            "gtag('js', new Date());" +
            "gtag('consent', 'default', {" +
            "'analytics_storage': 'denied'," +
            "'ad_storage': 'denied'," +
            "'ad_user_data': 'denied'," +
            "'ad_personalization': 'denied'" +
            "});" +
            `gtag('config', '${GOOGLE_TAG_ID}', { 'anonymize_ip': true });` +
            "window.addEventListener('syntexa:cookie-consent', function(event) {" +
            "var mode = event && event.detail && event.detail.value === 'accepted' ? 'granted' : 'denied';" +
            "gtag('consent', 'update', {" +
            "'analytics_storage': mode," +
            "'ad_storage': 'denied'," +
            "'ad_user_data': 'denied'," +
            "'ad_personalization': 'denied'" +
            "});" +
            "});"
        )
    ),
    React.createElement(
      "body",
      { className: "antialiased bg-white text-[#0f172a]" },
      React.createElement(Suspense, { fallback: null }, React.createElement(AppWrapper, null, children))
    )
  );
}
