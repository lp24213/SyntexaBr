import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';

export async function toolsRouter(app: FastifyInstance) {
  // GET /tools/:conversationId - listar tools executadas
  app.get('/:conversationId', async (request: any, reply) => {
    const { conversationId } = request.params;
    
    const result = await pgPool.query(
      `SELECT * FROM whatsapp.executed_tools 
       WHERE conversation_id = $1 
       ORDER BY created_at DESC`,
      [conversationId]
    );
    
    return { tools: result.rows };
  });

  // POST /tools/pdf - gerar PDF
  app.post('/pdf', async (request: any, reply) => {
    const { conversationId, title, sections } = request.body;
    
    try {
      // Chamar API de PDF da Syntexa
      const response = await fetch(`${process.env.SYNTEXA_API_BASE}/v1/multimodal/export/pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.SYNTEXA_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, sections }),
      });
      
      if (!response.ok) throw new Error('PDF generation failed');
      
      const pdfBuffer = await response.arrayBuffer();
      
      // Armazenar na DB
      const result = await pgPool.query(
        `INSERT INTO whatsapp.executed_tools 
         (conversation_id, tool_name, input_data, status)
         VALUES ($1, 'pdf', $2, 'success')
         RETURNING *`,
        [conversationId, JSON.stringify({ title, sections })]
      );
      
      reply.type('application/pdf');
      return Buffer.from(pdfBuffer);
    } catch (error) {
      reply.code(500);
      return { error: 'PDF generation failed' };
    }
  });

  // POST /tools/xlsx - gerar Excel
  app.post('/xlsx', async (request: any, reply) => {
    const { conversationId, title, rows, header } = request.body;
    
    try {
      // Chamar API de XLSX da Syntexa
      const response = await fetch(`${process.env.SYNTEXA_API_BASE}/v1/multimodal/export/xlsx`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.SYNTEXA_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sheet_title: title, rows, header }),
      });
      
      if (!response.ok) throw new Error('XLSX generation failed');
      
      const xlsxBuffer = await response.arrayBuffer();
      
      await pgPool.query(
        `INSERT INTO whatsapp.executed_tools 
         (conversation_id, tool_name, input_data, status)
         VALUES ($1, 'xlsx', $2, 'success')`,
        [conversationId, JSON.stringify({ title, rows, header })]
      );
      
      reply.type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      return Buffer.from(xlsxBuffer);
    } catch (error) {
      reply.code(500);
      return { error: 'XLSX generation failed' };
    }
  });
}
