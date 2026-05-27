const sharp = require('sharp');
const path = require('path');

const buildDir = path.join(__dirname, '..', 'build');

// Converter icon.png (com fundo preto) para PNG com fundo transparente
async function generateTransparentIcon() {
  try {
    console.log('Gerando ícone transparente...');
    
    const iconPath = path.join(buildDir, 'icon.png');
    const outputPath = path.join(buildDir, 'icon.png');
    
    // Ler a imagem
    const image = sharp(iconPath);
    const metadata = await image.metadata();
    
    console.log(`Ícone original: ${metadata.width}x${metadata.height}`);
    
    // Converter para RGBA e remover fundo preto
    const buffer = await image
      .ensureAlpha() // Garantir canal alpha
      .floodfill({
        x: 0,
        y: 0,
        out: 'rgb',
        tolerance: 10
      })
      .toBuffer();
    
    // Salvar como PNG transparente
    await sharp(buffer)
      .png()
      .toFile(outputPath);
    
    console.log('✅ Ícone transparente gerado com sucesso!');
    
    // Gerar versões menores
    await sharp(outputPath)
      .resize(256, 256, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(path.join(buildDir, 'icon-256.png'));
    
    console.log('✅ Ícone 256x256 gerado com sucesso!');
    
    // Gerar ICO a partir do PNG transparente (se possível com imagemin-ico)
    console.log('✅ Ícones regenerados');
    
  } catch (err) {
    console.error('❌ Erro ao gerar ícone:', err.message);
    process.exit(1);
  }
}

generateTransparentIcon();
