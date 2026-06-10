import { NextResponse } from "next/server";

export const dynamic = "force-static";

/**
 * API ROUTE: POST /api/contact
 * 
 * Processa formulário de contato:
 * 1. Valida dados
 * 2. Envia email para contato@syntexabr.com.br
 * 3. Salva no banco de dados (Railway)
 * 4. Retorna resposta
 */

// Email service (usando Resend ou nodemailer)
async function sendEmail(contactData) {
  try {
    // Usar Resend (recomendado) ou sua solução de email
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "noreply@syntexabr.com.br",
        to: "contato@syntexabr.com.br",
        replyTo: contactData.email,
        subject: `[${contactData.tipo.toUpperCase()}] ${contactData.assunto}`,
        html: `
          <h2>Novo Contato Recebido</h2>
          <p><strong>Nome:</strong> ${contactData.nome}</p>
          <p><strong>Email:</strong> ${contactData.email}</p>
          <p><strong>Empresa:</strong> ${contactData.empresa || "N/A"}</p>
          <p><strong>Telefone:</strong> ${contactData.telefone || "N/A"}</p>
          <p><strong>Tipo:</strong> ${contactData.tipo}</p>
          <p><strong>Assunto:</strong> ${contactData.assunto}</p>
          <hr />
          <p><strong>Mensagem:</strong></p>
          <pre>${contactData.mensagem}</pre>
        `,
      }),
    });

    if (!response.ok) {
      throw new Error("Falha ao enviar email");
    }

    return await response.json();
  } catch (error) {
    console.error("Email error:", error);
    throw error;
  }
}

// Database service (Railway/PostgreSQL)
async function saveToDatabase(contactData) {
  try {
    // Conectar ao Railway backend
    const railwayResponse = await fetch(
      `${process.env.RAILWAY_BACKEND_URL}/api/contacts`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.RAILWAY_API_TOKEN}`,
        },
        body: JSON.stringify({
          nome: contactData.nome,
          email: contactData.email,
          empresa: contactData.empresa,
          telefone: contactData.telefone,
          tipo: contactData.tipo,
          assunto: contactData.assunto,
          mensagem: contactData.mensagem,
          createdAt: new Date().toISOString(),
          status: "novo",
        }),
      }
    );

    if (!railwayResponse.ok) {
      throw new Error("Falha ao salvar no banco de dados");
    }

    return await railwayResponse.json();
  } catch (error) {
    console.error("Database error:", error);
    throw error;
  }
}

// Main handler
export async function POST(request) {
  try {
    const contactData = await request.json();

    // Validação básica
    if (!contactData.nome || !contactData.email || !contactData.mensagem) {
      return NextResponse.json(
        { error: "Campos obrigatórios faltando" },
        { status: 400 }
      );
    }

    // Validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(contactData.email)) {
      return NextResponse.json(
        { error: "Email inválido" },
        { status: 400 }
      );
    }

    // Enviar email e salvar no banco (em paralelo)
    const [emailResult, dbResult] = await Promise.all([
      sendEmail(contactData),
      saveToDatabase(contactData),
    ]);

    return NextResponse.json(
      {
        success: true,
        message: "Mensagem enviada com sucesso",
        contactId: dbResult.id,
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Contact form error:", error);

    return NextResponse.json(
      { error: "Erro ao processar sua solicitação. Tente novamente." },
      { status: 500 }
    );
  }
}

// Health check
export async function GET() {
  return NextResponse.json({ status: "ok", endpoint: "/api/contact" });
}
