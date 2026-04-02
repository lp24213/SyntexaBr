import "./globals.css";
import React from "react";
import { AppWrapper } from "../components/app-wrapper";

export const metadata = {
  title: "Syntexa AI",
  description: "Plataforma de IA de próxima geração.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
};

export default function RootLayout(props) {
  const { children } = props;
  return React.createElement(
    "html",
    { lang: "pt-BR", className: "dark" },
    React.createElement(
      "body",
      { className: "bg-black text-white antialiased" },
      React.createElement(AppWrapper, null, children)
    )
  );
}
