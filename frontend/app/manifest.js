export const dynamic = "force-static";

export default function manifest() {
  return {
    name: "Syntexa AI",
    short_name: "Syntexa",
    description: "Plataforma Syntexa instalada como app web em desktop e mobile.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#f8f9fb",
    theme_color: "#6d28d9",
    lang: "pt-BR",
    icons: [
      {
        src: "/LOGOTIPO.png",
        sizes: "1024x1024",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}

