import { z } from 'zod';

export const createPhoneNumberSchema = z.object({
  phone_number_id: z.string().min(3).max(50).regex(/^[a-zA-Z0-9_-]+$/),
  waba_id: z.string().min(3).max(50),
  access_token: z.string().min(10).max(500),
  display_number: z.string().optional()
});

export const createMessageSchema = z.object({
  conversationId: z.string().uuid(),
  content: z.string().min(1).max(4096)
});

export const createCompanySchema = z.object({
  name: z.string().min(1).max(255),
  email: z.string().email(),
  plan: z.enum(['free', 'pro', 'enterprise']).default('free')
});

export const updateConfigSchema = z.object({
  system_prompt: z.string().optional(),
  max_tokens_per_message: z.number().min(100).max(2000).optional(),
  temperature: z.number().min(0).max(2).optional(),
  welcome_message: z.string().optional(),
  auto_reply_enabled: z.boolean().optional()
});

export type CreatePhoneNumber = z.infer<typeof createPhoneNumberSchema>;
export type CreateMessage = z.infer<typeof createMessageSchema>;
export type CreateCompany = z.infer<typeof createCompanySchema>;
export type UpdateConfig = z.infer<typeof updateConfigSchema>;
