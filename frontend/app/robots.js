export const dynamic = "force-static";

export default function robots() {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
      },
    ],
    sitemap: "https://syntexabr.com.br/sitemap.xml",
    host: "https://syntexabr.com.br",
  };
}
