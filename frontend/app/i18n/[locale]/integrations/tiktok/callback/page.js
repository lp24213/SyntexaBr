import { Suspense } from "react";
import TikTokCallbackClient from "./TikTokCallbackClient";

export async function generateStaticParams() {
  return [
    { locale: "pt-BR" },
    { locale: "en-US" },
    { locale: "es-ES" },
    { locale: "zh-CN" },
  ];
}

export default function TikTokCallbackPage({ params }) {
  const { locale } = params;
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000]" /></div>}>
      <TikTokCallbackClient locale={locale} />
    </Suspense>
  );
}

