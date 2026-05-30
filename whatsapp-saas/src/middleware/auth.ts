import { FastifyRequest, FastifyReply } from 'fastify';

export async function authenticateJWT(
  request: FastifyRequest,
  reply: FastifyReply
) {
  try {
    await request.jwtVerify();
  } catch (err) {
    reply.code(401).send({ 
      error: 'Unauthorized',
      message: 'Invalid or missing JWT token'
    });
  }
}

export async function validateCompanyOwnership(
  request: FastifyRequest,
  reply: FastifyReply
) {
  const user = (request as any).user;
  if (!user || !user.company_id) {
    return reply.code(401).send({ error: 'Unauthorized' });
  }

  // Extract company_id from params or body
  const companyId = (request.params as any)?.companyId || 
                   (request.body as any)?.company_id ||
                   (request.query as any)?.company_id;

  if (companyId && companyId !== user.company_id) {
    return reply.code(403).send({ 
      error: 'Forbidden',
      message: 'Access denied to this company'
    });
  }
}
