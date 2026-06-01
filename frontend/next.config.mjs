/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  distDir: "out",
  images: { unoptimized: true },
  turbopack: {},
  env: {
    NEXT_PUBLIC_TURNSTILE_SITE_KEY: "0x4AAAAAADXPQoicsnfeZhcl",
    NEXT_PUBLIC_WHATSAPP_API: "https://api-whatsapp.syntexabr.com.br",
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.externals = [...(config.externals || []), "@xenova/transformers"];
    }
    // Do NOT bundle heavy ONNX WASM files — Xenova loads them from CDN at runtime
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    config.module.rules.push({
      test: /\.wasm$/,
      type: "asset/resource",
      generator: { emit: false },
    });
    return config;
  },
};

export default nextConfig;

