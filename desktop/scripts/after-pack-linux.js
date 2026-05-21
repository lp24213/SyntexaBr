/**
 * SYNTEXA DESKTOP — Linux After-Pack Hook
 * Ajustes pós-empacotamento para AppImage, .deb e tar.gz
 */
const fs = require("fs");
const path = require("path");

module.exports = async function (context) {
  const { electronPlatformName, outDir, arch } = context;

  console.log("[after-pack-linux] Plataforma:", electronPlatformName, "Arch:", arch);

  // Para AppImage: ajusta permissões se necessário
  if (electronPlatformName === "linux") {
    const appImage = fs.readdirSync(outDir).find((f) => f.endsWith(".AppImage"));
    if (appImage) {
      const p = path.join(outDir, appImage);
      try {
        fs.chmodSync(p, 0o755);
        console.log("[after-pack-linux] Permissão 755 aplicada em", appImage);
      } catch (e) {
        console.warn("[after-pack-linux] Não foi possível ajustar permissões:", e.message);
      }
    }
  }

  // Gera .desktop entry para tar.gz
  const tarGz = fs.readdirSync(outDir).find((f) => f.endsWith(".tar.gz"));
  if (tarGz) {
    const desktopEntry = `[Desktop Entry]
Name=Syntexa AI
Comment=Foundation Model Soberana Desktop (Offline)
Exec=./SyntexaAI
Icon=syntexa
Type=Application
Categories=Office;Utility;ArtificialIntelligence;
Keywords=ai;llm;chat;multimodal;offline;soberano;
StartupNotify=true
Terminal=false
`;
    const desktopFile = path.join(outDir, "syntexa-ai.desktop");
    fs.writeFileSync(desktopFile, desktopEntry, "utf8");
    console.log("[after-pack-linux] .desktop entry gerado para tar.gz");
  }
};
