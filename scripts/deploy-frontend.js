#!/usr/bin/env node
/**
 * Deploy Syntexa Frontend com URL fixa
 * 
 * Este script:
 * 1. Faz deploy para Cloudflare Pages
 * 2. Registra a URL em um arquivo .deployed
 * 3. Atualiza o gateway_worker.js com a nova URL
 * 4. Faz commit e push
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const DEPLOYED_FILE = path.join(REPO_ROOT, '.frontend-deployed.json');
const GATEWAY_FILE = path.join(REPO_ROOT, 'gateway_worker.js');

console.log('🚀 Deploying Syntexa Frontend to Cloudflare Pages...');

try {
  // 1. Deploy para Pages
  console.log('📦 Building and deploying to Pages...');
  const deployOutput = execSync(
    'cd frontend && npx wrangler pages deploy out --project-name syntexa-frontend',
    { encoding: 'utf-8', stdio: 'pipe' }
  );

  // 2. Extrair URL do output
  const urlMatch = deployOutput.match(/https:\/\/[\w-]+\.syntexa-frontend\.pages\.dev/);
  if (!urlMatch) {
    console.error('❌ Could not find deployment URL in output');
    console.error(deployOutput);
    process.exit(1);
  }

  const deploymentUrl = urlMatch[0];
  console.log(`✅ Deployed to: ${deploymentUrl}`);

  // 3. Registrar no arquivo .deployed
  const deployedInfo = {
    timestamp: new Date().toISOString(),
    url: deploymentUrl,
    commit: execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim(),
  };
  fs.writeFileSync(DEPLOYED_FILE, JSON.stringify(deployedInfo, null, 2));
  console.log(`📝 Registered deployment in ${DEPLOYED_FILE}`);

  // 4. Atualizar gateway_worker.js com a nova URL
  console.log('🔧 Updating gateway_worker.js...');
  let gatewayContent = fs.readFileSync(GATEWAY_FILE, 'utf-8');
  
  // Substituir a URL no gateway
  const oldUrlPattern = /const pagesDeployment = getPagesDeploymentUrl\(env, request\);/;
  if (!oldUrlPattern.test(gatewayContent)) {
    console.warn('⚠️  Could not find getPagesDeploymentUrl pattern - using fallback pattern');
  }

  // Atualizar a função para retornar o novo URL como padrão
  gatewayContent = gatewayContent.replace(
    /return "https:\/\/[\w-]+\.syntexa-frontend\.pages\.dev";/,
    `return "${deploymentUrl}";`
  );

  fs.writeFileSync(GATEWAY_FILE, gatewayContent);
  console.log(`✅ Updated gateway_worker.js with new deployment URL`);

  // 5. Atualizar wrangler.toml também
  console.log('🔧 Updating wrangler.toml...');
  let wranglerContent = fs.readFileSync(path.join(REPO_ROOT, 'wrangler.toml'), 'utf-8');
  wranglerContent = wranglerContent.replace(
    /FRONTEND_PAGES_URL = "https:\/\/[\w-]+\.syntexa-frontend\.pages\.dev"/,
    `FRONTEND_PAGES_URL = "${deploymentUrl}"`
  );
  fs.writeFileSync(path.join(REPO_ROOT, 'wrangler.toml'), wranglerContent);
  console.log(`✅ Updated wrangler.toml`);

  // 6. Commit e push
  console.log('📤 Committing and pushing...');
  execSync('git add -A', { cwd: REPO_ROOT });
  execSync(`git commit -m "Deploy: ${deployedInfo.commit} Frontend ${deploymentUrl.split('/')[2]}"`, {
    cwd: REPO_ROOT,
  });
  execSync('git push origin main', { cwd: REPO_ROOT });
  console.log('✅ Committed and pushed to main');

  // 7. Deploy gateway
  console.log('🚀 Deploying gateway...');
  execSync('npx wrangler deploy --name syntexa-gateway', { cwd: REPO_ROOT });
  console.log('✅ Gateway deployed');

  console.log('\n✨ Frontend deployment complete!');
  console.log(`📍 URL: ${deploymentUrl}`);
  console.log(`🔗 Public URL: https://syntexabr.com.br`);
} catch (error) {
  console.error('❌ Deployment failed:', error.message);
  process.exit(1);
}
