import { FastifyInstance } from 'fastify';
import { pgPool } from '../index.js';
import { authenticateJWT } from '../middleware/auth.js';
import { logger } from '../lib/logger.js';

export async function toolsRouter(app: FastifyInstance) {
  // GET /tools/:conversationId
  app.get(
    '/:conversationId',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId } = request.params;
      const userCompanyId = request.user.company_id;
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(404).send({ error: 'Conversation not found' });
      }
      
      const result = await pgPool.query(
        `SELECT id, tool_name, status, created_at FROM whatsapp.executed_tools 
         WHERE conversation_id = $1 
         ORDER BY created_at DESC`,
        [conversationId]
      );
      
      return { tools: result.rows };
    }
  );

  // POST /tools/pdf
  app.post(
    '/pdf',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId, title, sections, includeVisuals = true, includeFooter = true } = request.body;
      const userCompanyId = request.user.company_id;
      
      if (!conversationId || !title || !sections) {
        return reply.code(400).send({ error: 'Missing required fields' });
      }
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      try {
        const response = await fetch(`${process.env.SYNTEXA_API_BASE}/v1/multimodal/export/pdf`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.SYNTEXA_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ title, sections, include_visuals: includeVisuals, include_footer: includeFooter }),
        });
        
        if (!response.ok) throw new Error('PDF generation failed');
        
        const pdfBuffer = await response.arrayBuffer();
        
        await pgPool.query(
          `INSERT INTO whatsapp.executed_tools 
           (conversation_id, tool_name, input_data, status)
           VALUES ($1, 'pdf', $2, 'success')`,
          [conversationId, JSON.stringify({ title, sections, includeVisuals, includeFooter })]
        );
        
        logger.info(`PDF generated for conversation ${conversationId}`);
        reply.type('application/pdf');
        return Buffer.from(pdfBuffer);
      } catch (error) {
        logger.error('PDF generation error:', error);
        reply.code(500);
        return { error: 'PDF generation failed' };
      }
    }
  );

  // POST /tools/xlsx
  app.post(
    '/xlsx',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId, title, rows, header } = request.body;
      const userCompanyId = request.user.company_id;
      
      if (!conversationId || !title || !rows || !header) {
        return reply.code(400).send({ error: 'Missing required fields' });
      }
      
      // Validar ownership
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      try {
        // Validar e limpar dados para garantir formatação COMPLETA com somas
        const cleanRows = (rows || []).map((row: any) => {
          if (!row) return {};
          if (typeof row === 'object') {
            return Object.entries(row).reduce((acc, [k, v]) => {
              acc[k] = v === null || v === undefined ? '' : String(v).trim();
              return acc;
            }, {} as any);
          }
          return { value: String(row).trim() };
        });
        
        const cleanHeader = (header || []).map(h => typeof h === 'string' ? h.trim() : String(h));
        
        // Calcular somas por coluna (apenas números)
        const columnSums: any = {};
        cleanHeader.forEach((col: string) => {
          let sum = 0;
          let hasNumbers = false;
          cleanRows.forEach((row: any) => {
            const val = row[col];
            if (val && !isNaN(parseFloat(val))) {
              sum += parseFloat(val);
              hasNumbers = true;
            }
          });
          if (hasNumbers) {
            columnSums[col] = sum;
          }
        });
        
        // Adicionar linha de totais se houver cálculos
        const finalRows = [...cleanRows];
        if (Object.keys(columnSums).length > 0) {
          const totalRow: any = { '***TOTAL***': 'TOTAL' };
          cleanHeader.forEach((col: string) => {
            totalRow[col] = columnSums[col] || '';
          });
          finalRows.push(totalRow);
        }
        
        const response = await fetch(`${process.env.SYNTEXA_API_BASE}/v1/multimodal/export/xlsx`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.SYNTEXA_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            sheet_title: title || 'Export',
            rows: finalRows, 
            header: cleanHeader,
            formatting: {
              autowidth: true,
              bold_header: true,
              bold_total: true,
              borders: 'thin',
              freeze_header: true,
              alignment: 'left',
              number_format: '#,##0.00',
              highlight_total: true
            }
          }),
        });
        
        if (!response.ok) throw new Error('XLSX generation failed');
        
        const xlsxBuffer = await response.arrayBuffer();
        
        await pgPool.query(
          `INSERT INTO whatsapp.executed_tools 
           (conversation_id, tool_name, input_data, status)
           VALUES ($1, 'xlsx', $2, 'success')`,
          [conversationId, JSON.stringify({ title, rows, header })]
        );
        
        logger.info(`XLSX generated for conversation ${conversationId}`);
        reply.type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        return Buffer.from(xlsxBuffer);
      } catch (error) {
        logger.error('XLSX generation error:', error);
        reply.code(500);
        return { error: 'XLSX generation failed' };
      }
    }
  );

  // POST /tools/docx
  app.post(
    '/docx',
    { onRequest: [authenticateJWT] },
    async (request: any, reply) => {
      const { conversationId, title, sections } = request.body;
      const userCompanyId = request.user.company_id;
      
      if (!conversationId || !title || !sections) {
        return reply.code(400).send({ error: 'Missing required fields' });
      }
      
      const conversation = await pgPool.query(
        `SELECT id FROM whatsapp.conversations 
         WHERE id = $1 AND company_id = $2`,
        [conversationId, userCompanyId]
      );
      
      if (!conversation.rows[0]) {
        return reply.code(403).send({ error: 'Access denied' });
      }
      
      try {
        const response = await fetch(`${process.env.SYNTEXA_API_BASE}/v1/multimodal/export/docx`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.SYNTEXA_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ title, sections }),
        });
        
        if (!response.ok) throw new Error('DOCX generation failed');
        
        const docxBuffer = await response.arrayBuffer();
        
        await pgPool.query(
          `INSERT INTO whatsapp.executed_tools 
           (conversation_id, tool_name, input_data, status)
           VALUES ($1, 'docx', $2, 'success')`,
          [conversationId, JSON.stringify({ title, sections })]
        );
        
        logger.info(`DOCX generated for conversation ${conversationId}`);
        reply.type('application/vnd.openxmlformats-officedocument.wordprocessingml.document');
        return Buffer.from(docxBuffer);
      } catch (error) {
        logger.error('DOCX generation error:', error);
        reply.code(500);
        return { error: 'DOCX generation failed' };
      }
    }
  );
}
