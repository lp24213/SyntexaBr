export const dynamic = "force-static";

export default function manifest() {
  return {
    name: "Syntexa AI",
    short_name: "Syntexa",
    description: "Plataforma de inteligência artificial para chat, geração de documentos e produtividade.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    display_override: ["window-controls-overlay", "standalone", "minimal-ui"],
    orientation: "portrait-primary",
    background_color: "#ffffff",
    theme_color: "#0f172a",
    lang: "pt-BR",
    dir: "ltr",
    categories: ["productivity", "education", "utilities"],
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Chat IA",
        short_name: "Chat",
        description: "Abrir o chat com IA directamente",
        url: "/chat/",
        icons: [{ src: "/icon-192.png", sizes: "192x192" }],
      },
      {
        name: "Perfil",
        short_name: "Perfil",
        description: "Ver e editar perfil",
        url: "/perfil/",
        icons: [{ src: "/icon-192.png", sizes: "192x192" }],
      },
    ],
    prefer_related_applications: false,
  };
}

