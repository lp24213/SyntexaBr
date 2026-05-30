import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT } from '../middleware/auth.js';
import { logger } from '../lib/logger.js';

export async function authRouter(app: FastifyInstance) {
  // POST /auth/meta/callback — troca code por token e salva
  app.post(
    '/meta/callback',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { code, redirectUri } = request.body;
      const user = (request as any).user;
      const companyId = user?.company_id;

      if (!code || !redirectUri) {
        return reply.code(400).send({ error: 'Missing code or redirectUri' });
      }
      if (!companyId) {
        return reply.code(401).send({ error: 'Company not associated' });
      }

      try {
        const appId = process.env.META_APP_ID;
        const appSecret = process.env.META_APP_SECRET;

        if (!appId || !appSecret) {
          return reply.code(500).send({ error: 'Meta app credentials not configured' });
        }

        const exchangeUrl = `https://graph.facebook.com/v18.0/oauth/access_token?client_id=${appId}&client_secret=${appSecret}&code=${code}&redirect_uri=${encodeURIComponent(redirectUri)}`;
        const exchangeRes = await fetch(exchangeUrl);
        const exchangeData: any = await exchangeRes.json();

        if (!exchangeData.access_token) {
          logger.error('Meta token exchange failed:', exchangeData);
          return reply.code(400).send({ error: 'Failed to exchange code for token', details: exchangeData });
        }

        const accessToken = exchangeData.access_token;

        // Obter WABA info
        const wabaRes = await fetch(`https://graph.facebook.com/v18.0/me?access_token=${accessToken}`);
        const wabaData: any = await wabaRes.json();

        // Salvar token no banco (criptografado em produção)
        await pgPool.query(
          `UPDATE whatsapp.companies 
           SET meta_access_token = $1, 
               meta_waba_id = $2,
               updated_at = NOW()
           WHERE id = $3`,
          [accessToken, wabaData.id || null, companyId]
        );

        logger.info(`Meta OAuth success for company ${companyId}`);
        return { success: true, connected: true };
      } catch (error: any) {
        logger.error('Meta OAuth callback error:', error);
        return reply.code(500).send({ error: 'OAuth processing failed' });
      }
    }
  );
}
