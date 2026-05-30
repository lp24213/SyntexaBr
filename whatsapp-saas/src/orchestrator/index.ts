/**
 * Orchestrator - Núcleo da IA
 * 
 * Coordena:
 * - Parsing de mensagens
 * - Memória curta/longa
 * - Chamadas à LLM
 * - Execução de tools
 * - Envio de respostas
 */

import axios from 'axios';
import { pgPool } from '../index.js';
import { logger } from '../lib/logger.js';

export interface Message {
  id: string;
  type: string;
  text?: { body: string };
  image?: { link: string };
  audio?: { link: string };
  document?: { link: string };
  timestamp: number;
  from: string;
}

export interface Contact {
  profile: { name: string };
  wa_id: string;
}

export async function orchestrateMessage(
  phoneNumberId: string,
  message: Message,
  contacts: Contact[]
) {
  try {
    logger.info(`🤖 Orchestrating message: ${message.id}`);

    // 1. Buscar configurações da empresa
    const phoneRecord = await pgPool.query(
      `SELECT companies.id as company_id, companies.name, whatsapp.phone_numbers.*,
              whatsapp.company_config.*
       FROM whatsapp.phone_numbers
       JOIN whatsapp.companies ON whatsapp.companies.id = whatsapp.phone_numbers.company_id
       LEFT JOIN whatsapp.company_config ON whatsapp.company_config.company_id = whatsapp.companies.id
       WHERE whatsapp.phone_numbers.phone_number_id = $1`,
      [phoneNumberId]
    );

    if (!phoneRecord.rows[0]) {
      logger.error(`Phone number not found: ${phoneNumberId}`);
      return;
    }

    const config = phoneRecord.rows[0];
    const contactName = contacts[0]?.profile?.name || message.from;
    const contactPhone = message.from;

    // 2. Buscar ou criar conversa
    let conversation = await pgPool.query(
      `SELECT * FROM whatsapp.conversations 
       WHERE phone_number_id = $1 AND contact_phone = $2`,
      [config.id, contactPhone]
    );

    let conversationId: string;
    if (conversation.rows.length > 0) {
      conversationId = conversation.rows[0].id;
    } else {
      const newConv = await pgPool.query(
        `INSERT INTO whatsapp.conversations 
         (company_id, phone_number_id, contact_phone, contact_name, status)
         VALUES ($1, $2, $3, $4, 'active')
         RETURNING id`,
        [config.company_id, config.id, contactPhone, contactName]
      );
      conversationId = newConv.rows[0].id;
    }

    // 3. Extrair conteúdo da mensagem
    let userText = '';
    let mediaUrl: string | null = null;

    if (message.type === 'text') {
      userText = message.text?.body || '';
    } else if (message.type === 'image') {
      mediaUrl = message.image?.link || null;
      userText = '(Imagem enviada)';
    } else if (message.type === 'audio') {
      mediaUrl = message.audio?.link || null;
      userText = '(Áudio enviado)';
    } else if (message.type === 'document') {
      mediaUrl = message.document?.link || null;
      userText = '(Documento enviado)';
    }

    // 4. Armazenar mensagem recebida
    await pgPool.query(
      `INSERT INTO whatsapp.messages 
       (conversation_id, direction, message_type, content, media_url, wa_message_id)
       VALUES ($1, 'inbound', $2, $3, $4, $5)`,
      [conversationId, message.type, userText, mediaUrl, message.id]
    );

    // 5. Buscar contexto da conversa (últimas 10 mensagens)
    const history = await pgPool.query(
      `SELECT direction, message_type, content FROM whatsapp.messages 
       WHERE conversation_id = $1 
       ORDER BY created_at DESC LIMIT 10`,
      [conversationId]
    );

    // 6. Montar prompt para LLM
    const systemPrompt = config.system_prompt || 
      'Você é um assistente IA profissional para WhatsApp Business.';

    const messages = [
      {
        role: 'system',
        content: systemPrompt,
      },
      ...history.rows.reverse().map((msg: any) => ({
        role: msg.direction === 'inbound' ? 'user' : 'assistant',
        content: msg.content,
      })),
      {
        role: 'user',
        content: userText,
      },
    ];

    // 7. Chamar LLM (Syntexa ou fallback)
    logger.info(`📤 Calling LLM with context of ${history.rows.length} messages`);

    const llmResponse = await callSyntexaLLM(messages, {
      maxTokens: config.max_tokens_per_message,
      temperature: config.temperature,
    });

    const aiResponse = llmResponse.content;

    // 8. Armazenar resposta
    await pgPool.query(
      `INSERT INTO whatsapp.messages 
       (conversation_id, direction, message_type, content)
       VALUES ($1, 'outbound', 'text', $2)`,
      [conversationId, aiResponse]
    );

    // 9. Enviar resposta via WhatsApp
    await sendWhatsAppMessage(
      config.access_token,
      config.phone_number_id,
      contactPhone,
      aiResponse
    );

    logger.info(`✅ Message sent to ${contactPhone}`);

  } catch (error) {
    logger.error('Orchestration error:', error);
  }
}

async function callSyntexaLLM(messages: any[], options: any) {
  try {
    const response = await axios.post(
      `${process.env.SYNTEXA_API_BASE}/v1/chat/completions`,
      {
        model: 'syntexa-native',
        messages,
        max_tokens: options.maxTokens,
        temperature: options.temperature,
        stream: false,
      },
      {
        headers: {
          Authorization: `Bearer ${process.env.SYNTEXA_API_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      }
    );

    return {
      content: response.data.choices[0].message.content,
      tokensUsed: response.data.usage?.total_tokens || 0,
    };
  } catch (error) {
    logger.error('LLM call failed:', error);
    throw error;
  }
}

async function sendWhatsAppMessage(
  accessToken: string,
  phoneNumberId: string,
  recipientPhone: string,
  message: string
) {
  try {
    await axios.post(
      `https://graph.facebook.com/v18.0/${phoneNumberId}/messages`,
      {
        messaging_product: 'whatsapp',
        to: recipientPhone.replace(/\D/g, ''),
        type: 'text',
        text: { body: message },
      },
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    logger.error('Failed to send WhatsApp message:', error);
    throw error;
  }
}
