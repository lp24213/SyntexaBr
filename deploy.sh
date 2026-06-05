#!/bin/bash

# Deployment Script - SyntexaBR Frontend + Backend
# Deploy para Wrangler Pages + Railway

set -e

echo "🚀 Iniciando deploy SyntexaBR..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Frontend Build
echo -e "${YELLOW}[1] Building Frontend...${NC}"
cd frontend
npm run build
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Frontend built${NC}"
else
  echo -e "${RED}✗ Frontend build failed${NC}"
  exit 1
fi

# 2. Deploy Frontend to Wrangler Pages
echo -e "${YELLOW}[2] Deploying to Wrangler Pages...${NC}"
npx wrangler pages deploy out/ --project-name syntexa-frontend
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Wrangler Pages deployed${NC}"
else
  echo -e "${RED}✗ Wrangler deployment failed${NC}"
  exit 1
fi

# 3. Deploy Backend to Railway
echo -e "${YELLOW}[3] Deploying Backend to Railway...${NC}"
cd ../
railroad up --environment production
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Railway deployed${NC}"
else
  echo -e "${RED}✗ Railway deployment failed${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Deploy Complete!${NC}"
echo ""
echo "Frontend: https://syntexa-frontend.pages.dev"
echo "Backend: https://syntexabr-backend.up.railway.app"
echo ""
