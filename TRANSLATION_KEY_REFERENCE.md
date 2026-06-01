# Translation Key Reference by Category

This document groups all hardcoded Portuguese strings by semantic category for efficient translation management.

## 1. AUTHENTICATION & LOGIN
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| loginTitle | Entrar | Sign In |
| loginDescription | Acesse sua conta para o chat e as ferramentas. | Access your account for chat and tools. |
| loginButton | Entrar | Sign In |
| enteringStatus | Entrando... | Signing in... |
| loginFailed | Falha ao entrar. Tente novamente. | Failed to sign in. Try again. |
| invalidLoginResponse | Resposta de login inválida. | Invalid login response. |
| emailLabel | E-mail | Email |
| passwordLabel | Senha | Password |
| createAccount | Criar conta | Create Account |
| forgotPassword | Esqueci minha senha | Forgot Password |
| loginWithGithub | Entrar com GitHub | Sign in with GitHub |
| githubNoEmailError | Entre com e-mail e senha ou deixe um e-mail visível na sua conta do GitHub. | Sign in with email/password or make your GitHub email public. |
| githubOAuthError | GitHub não respondeu de primeira — tente de novo. | GitHub didn't respond. Please try again. |
| turnstileWaitMessage | Aguarde a verificação de segurança carregar. | Please wait for security verification to load. |
| securityErrorPrefix | Erro de segurança: | Security Error: |

---

## 2. REGISTRATION & ACCOUNT CREATION
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| createAccountTitle | Criar conta | Create Account |
| createAccountDescription | Comece a usar a plataforma de IA Syntexa em poucos segundos. | Start using Syntexa AI platform in seconds. |
| registerButton | Criar conta | Register |
| creatingAccount | Criando conta... | Creating account... |
| fullNameLabel | Nome completo | Full Name |
| documentLabel | CPF/CNPJ | Document ID |
| cepLabel | CEP | Postal Code |
| stateLabel | Estado (UF) | State |
| cityLabel | Cidade | City |
| addressLabel | Endereço (rua/avenida) | Address |
| numberLabel | Número | Number |
| complementLabel | Complemento | Complement |
| confirmPasswordLabel | Confirmar senha | Confirm Password |
| passwordsMismatch | As senhas não coincidem. | Passwords do not match. |
| termsNotAccepted | Você precisa aceitar os Termos e Condições para continuar. | You must accept the Terms and Conditions to continue. |
| termsAcceptanceText | Li e aceito os Termos e Condições e a Política de Privacidade. | I accept the Terms and Conditions and Privacy Policy. |
| accountCreationFailed | Falha ao criar conta. | Account creation failed. |
| accountCreatedVerificationSent | Conta criada. Enviamos um código de verificação para seu e-mail. | Account created. We sent a verification code to your email. |
| unexpectedAccountError | Erro inesperado ao criar conta. | Unexpected error creating account. |
| alreadyHaveAccount | Já tem conta? | Already have an account? |
| backToLogin | Voltar para login | Back to Login |

---

## 3. PASSWORD RECOVERY & RESET
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| recoveryTitle | Recuperar senha | Recover Password |
| recoveryDescription | Use seu e-mail e o código recebido para redefinir sua senha. | Use your email and the received code to reset your password. |
| sendResetCode | Enviar código de redefinição | Send Reset Code |
| sendingEmail | Enviando... | Sending... |
| passwordResetEmailSent | Se o e-mail existir, um código de redefinição será enviado. | If email exists, a reset code will be sent. |
| recoveryCodeLabel | Código recebido | Recovery Code |
| newPasswordLabel | Nova senha | New Password |
| resetButton | Redefinir senha | Reset Password |
| resettingPassword | Redefinindo... | Resetting... |
| passwordResetSuccess | Senha redefinida com sucesso. Você já pode fazer login. | Password reset successfully. You can now sign in. |
| passwordResetFailed | Falha ao redefinir senha. | Password reset failed. |
| passwordResetError | Erro ao redefinir senha. | Error resetting password. |
| passwordResetRequestError | Erro ao solicitar redefinição. | Error requesting password reset. |
| rememberPassword | Lembrou da senha? | Remember your password? |

---

## 4. EMAIL VERIFICATION
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| verifyEmailTitle | Verificar e-mail | Verify Email |
| verifyEmailDescription | Informe seu e-mail e o código que recebeu para ativar sua conta. | Enter your email and verification code to activate your account. |
| verificationCodeLabel | Código de verificação | Verification Code |
| verifyButton | Verificar | Verify |
| verifyingEmail | Verificando... | Verifying... |
| emailVerificationSuccess | E-mail verificado com sucesso. Você já pode fazer login. | Email verified successfully. You can now sign in. |
| emailVerificationFailed | Falha ao verificar e-mail. | Email verification failed. |
| unexpectedVerificationError | Erro inesperado ao verificar e-mail. | Unexpected error verifying email. |

---

## 5. USER PROFILE & SETTINGS
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| profileTitle | Perfil do usuário | User Profile |
| profileDescription | Edite seus dados de conta e personalize sua identificação na Syntexa. | Edit your account data and customize your Syntexa profile. |
| loadingProfile | Carregando perfil... | Loading profile... |
| nameLabel | Nome | Name |
| namePlaceholder | Seu nome | Your name |
| usernameLabel | Username | Username |
| usernamePlaceholder | usuario.exemplo | user.example |
| cepPlaceholder | 00000-000 | Postal Code |
| statePlaceholder | SP | State |
| cityPlaceholder | São Paulo | City |
| addressPlaceholder | Rua / Avenida | Street / Avenue |
| addressNumberLabel | Número | Number |
| noPhoto | Sem foto | No photo |
| selectImageError | Selecione um ficheiro de imagem. | Select an image file. |
| profileUpdatedSuccess | Perfil atualizado com sucesso. | Profile updated successfully. |
| profileSaveError | Não foi possível salvar perfil. | Could not save profile. |
| saveProfileButton | Salvar perfil | Save Profile |

---

## 6. TWO-FACTOR AUTHENTICATION (2FA)
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| securityTitle | Segurança de conta (2FA) | Account Security (2FA) |
| securityDescription | Ative autenticação em dois fatores (TOTP) para reforçar o acesso. Use apps como Google Authenticator, Authy ou Microsoft Authenticator. | Enable two-factor authentication (TOTP) to strengthen access. Use apps like Google Authenticator, Authy, or Microsoft Authenticator. |
| twoFaAvailabilityNote | Para sua conta, a disponibilidade do 2FA depende da política do backend (admin/governo). Se não estiver habilitado, a API retorna mensagem de permissão. | For your account, 2FA availability depends on backend policy (admin/government). If not enabled, the API returns a permission message. |
| generateTwoFaButton | Gerar setup 2FA | Generate 2FA Setup |
| generatingStatus | Gerando... | Generating... |
| twoFaCodeLabel | Código 2FA | 2FA Code |
| twoFaPrompt | Digite o código do autenticador (2FA) para concluir o login. | Enter your authenticator code (2FA) to complete sign in. |
| validateTwoFaButton | Validar 2FA | Validate 2FA |
| validatingTwoFa | Validando... | Validating... |
| twoFaSetupGenerated | Setup 2FA gerado. Cadastre no app autenticador e confirme o código abaixo. | 2FA setup generated. Register in authenticator app and confirm code below. |
| twoFaSetupError | Não foi possível iniciar o setup 2FA. | Could not start 2FA setup. |
| twoFaEnabled | 2FA ativado com sucesso. | 2FA enabled successfully. |
| twoFaActivationFailed | Falha ao ativar 2FA. | Failed to activate 2FA. |
| twoFaValidationFailed | Não foi possível validar o código 2FA. | Could not validate 2FA code. |
| invalidTwoFaCode | Código 2FA inválido. | Invalid 2FA code. |

---

## 7. ADMIN & CONFIGURATION
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| accountSettingsTitle | Configurações da conta | Account Settings |
| accountSettingsDescription | Preferências e dados da sua conta Syntexa. | Your Syntexa account preferences and data. |
| accountSettingsHelpText | Use Planos para assinatura e Perfil para dados pessoais e segurança. | Use Plans for subscription and Profile for personal data and security. |
| ipListLoadError | Não foi possível carregar a lista (verifique login admin e API). | Could not load list (verify admin login and API). |
| ipSavedSuccess | Salvo. {count} IP(s). | Saved. {count} IP(s). |
| errorSaving | Erro ao salvar. | Error saving. |

---

## 8. PRICING & SUBSCRIPTIONS
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| plansPageTitle | Planos Syntexa | Syntexa Plans |
| plansPageDescription | Escolha o plano que faz sentido para você. Estudante com e-mail .edu paga metade em qualquer plano pago. | Choose the plan that makes sense for you. Students with .edu email get 50% off any paid plan. |
| planFreeTitle | Gratuito | Free |
| planFreeTag | Sem cartão | No Card Required |
| planFreePrice | R$ 0 | $0 |
| perMonth | /mês | /month |
| forEver | para sempre | Forever |
| planFreeDescription | 120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão. | 120 messages per day to try. Chat, web search, and smart answers—no card needed. |
| planBasicTitle | Básico | Basic |
| planBasicTag | Para começar | To Get Started |
| planBasicPrice | R$ 39 | $39 |
| perStudentMonth | estudante/mês | student/month |
| planBasicDescription | 500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers. | 500 messages/month, file uploads, and complete answers. Perfect for students and freelancers. |
| planMediumTitle | Médio | Medium |
| planMediumTag | Mais usado | Most Popular |
| planMediumPrice | R$ 99 | $99 |
| planMediumDescription | Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais. | Unlimited messages, image/video/audio generation, code, extended context. For professionals. |
| planMasterTitle | Master | Master |
| planMasterTag | Empresas | Enterprise |
| planMasterPrice | R$ 199 | $199 |
| planMasterDescription | Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais. | Everything unlimited + advanced agents, priority support, multiple users, enterprise tools. |

---

## 9. WHATSAPP INTEGRATION
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| whatsappPageTitle | WhatsApp Business | WhatsApp Business |
| whatsappPageDescription | Conecte seu WhatsApp Business e gerencie conversas com IA | Connect your WhatsApp Business and manage conversations with AI |
| oauthAuthorizationDenied | Autorização negada ou cancelada. | Authorization denied or canceled. |
| oauthCodeNotReceived | Código de autorização não recebido. | Authorization code not received. |
| metaConnecting | Conectando ao Meta... | Connecting to Meta... |
| metaAwaitIntegration | Aguarde enquanto finalizamos a integração. | Please wait while we complete the integration. |
| connectedSuccess | Conectado com sucesso! | Connected successfully! |
| autoCloseWindow | Esta janela fechará automaticamente. | This window will close automatically. |
| redirecting | Redirecionando... | Redirecting... |
| connectionFailed | Falha na conexão | Connection Failed |
| backToWhatsApp | Voltar para WhatsApp | Back to WhatsApp |

---

## 10. PWA & INSTALLATION
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| downloadPageTitle | Instalar Syntexa AI | Install Syntexa AI |
| downloadPageDescription | App completo com atalho no desktop, menu Iniciar e abertura directa no chat. | Full app with desktop shortcut, Start menu entry, and direct chat opening. |
| installPwaOption | Instalar como app (PWA) | Install as App (PWA) |
| platformsSupported | Windows · macOS · Linux · Android · iOS | Windows · macOS · Linux · Android · iOS |
| pwaFeature1 | Atalho no desktop e menu Iniciar | Desktop shortcut and Start menu entry |
| pwaFeature2 | Abre como janela própria, sem barra do browser | Opens as standalone window, no browser bar |
| pwaFeature3 | Funciona offline para páginas já visitadas | Works offline for previously visited pages |
| pwaFeature4 | Abre directamente no chat da IA | Opens directly in AI chat |
| pwaInstalledSuccess | ✓ App instalado com sucesso! | ✓ App installed successfully! |
| installAppNow | Instalar app agora | Install App Now |
| installApp | Instalar app | Install App |
| installAppFallbackInstructions | Se o botão não funcionar: clique no ícone ⋮ ou ⊕ na barra de endereço do Chrome/Edge e escolha «Instalar Syntexa AI». | If button doesn't work: click ⋮ or ⊕ icon in Chrome/Edge address bar and choose "Install Syntexa AI". |
| orSeparator | ou | or |
| openInBrowserButton | Abrir no browser sem instalar | Open in Browser Without Installing |
| iosInstructions | iPhone / iPad (Safari) | iPhone / iPad (Safari) |
| iosInstallSteps | Toque em Compartilhar → «Adicionar à Tela de Início». O app aparece no ecrã inicial como qualquer outro. | Tap Share → "Add to Home Screen". App appears on home screen like any other. |
| androidInstructions | Android (Chrome) | Android (Chrome) |
| androidInstallSteps | Toque no menu ⋮ → «Adicionar à tela inicial» ou aguarde o banner automático de instalação. | Tap ⋮ menu → "Add to Home Screen" or wait for auto install banner. |

---

## 11. HOMEPAGE/MARKETING
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| aiMadeBrazilBadge | Inteligência Artificial Brasileira | Brazilian Artificial Intelligence |
| mainHeading | Sua Assistente de IA, Feita no Brasil | Your AI Assistant, Made in Brazil |
| mainDescription | Uma assistente que entende português de verdade. Pode pesquisar na internet, gerar imagens, escrever códigos e ajudar em qualquer área — tudo de forma segura. | An assistant that truly understands Portuguese. Can search the web, generate images, write code, and help in any area—all securely. |
| accessConsole | Acessar Console | Access Console |
| exploreArchitecture | Explorar Arquitetura | Explore Architecture |
| architectureLabel | Arquitetura | Architecture |
| platformModules | Módulos da Plataforma | Platform Modules |
| platformModulesDescription | Tudo o que você precisa em um só lugar: chat inteligente, criação de conteúdo, análise de documentos e assistência técnica — sempre em português. | Everything you need in one place: smart chat, content creation, document analysis, and technical assistance—always in Portuguese. |

---

## 12. PRODUCT FEATURES (Homepage Modules)
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| moduleChatTitle | Chat Inteligente | Smart Chat |
| moduleChatDesc | Converse sobre qualquer assunto. A Syntexa entende contexto, memória e pode pesquisar na web em tempo real. | Chat about anything. Syntexa understands context, memory, and can search the web in real time. |
| moduleSpeedTitle | Respostas na Velocidade da Luz | Lightning-Fast Responses |
| moduleSpeedDesc | Processamento distribuído em servidores de alta performance para que você não espere por nada. | Distributed processing on high-performance servers so you never wait. |
| moduleAgentsTitle | Agentes Inteligentes | Smart Agents |
| moduleAgentsDesc | Crie assistentes especializados que executam tarefas complexas sozinhos, do planejamento à execução. | Create specialized assistants that execute complex tasks independently, from planning to execution. |
| moduleCreateTitle | Crie com IA | Create with AI |
| moduleCreateDesc | Gere imagens, vídeos, músicas e áudio com descrições em português. Sua criatividade é o limite. | Generate images, videos, music, and audio with Portuguese descriptions. Your creativity is the limit. |
| moduleMemoryTitle | Memória e Contexto | Memory and Context |
| moduleMemoryDesc | A Syntexa lembra das conversas, entende nuances e mantém o fio da meada em diálogos longos. | Syntexa remembers conversations, understands nuances, and maintains context in long dialogues. |
| moduleSpeechTitle | Fale com Ela | Speak to Her |
| moduleSpeechDesc | Dite suas perguntas e ouça as respostas. Reconhecimento e síntese de voz em português brasileiro. | Dictate your questions and hear the answers. Voice recognition and synthesis in Brazilian Portuguese. |
| moduleDocumentsTitle | Leitura de Documentos | Document Reading |
| moduleDocumentsDesc | Envie PDFs, planilhas e textos. A Syntexa resume, extrai informações e responde sobre o conteúdo. | Upload PDFs, spreadsheets, and text. Syntexa summarizes, extracts info, and answers about content. |
| modulePowerTitle | Potência Real | Real Power |
| modulePowerDesc | Infraestrutura de última geração com GPUs dedicadas para processar bilhões de parâmetros em segundos. | Next-gen infrastructure with dedicated GPUs to process billions of parameters in seconds. |
| moduleSecurityTitle | Segurança & Privacidade | Security & Privacy |
| moduleSecurityDesc | Seus dados ficam com você. Criptografia completa e nada enviado para empresas estrangeiras. | Your data stays with you. Full encryption and nothing sent to foreign companies. |
| moduleResearchTitle | Pesquisa Avançada | Advanced Research |
| moduleResearchDesc | Ferramentas de pesquisa científica e otimização para projetos complexos e inovação. | Scientific research tools and optimization for complex projects and innovation. |
| moduleExecutionTitle | Execução Rápida | Fast Execution |
| moduleExecutionDesc | Respostas instantâneas onde você estiver, com tecnologia de ponta em servidores distribuídos. | Instant answers wherever you are, with cutting-edge distributed server technology. |
| moduleBusinessTitle | Para Empresas | For Enterprises |
| moduleBusinessDesc | Contratos com garantia de funcionamento, relatórios completos e conformidade com a LGPD. | Contracts with uptime guarantees, complete reporting, and LGPD compliance. |
| statusOperational | Operacional | Operational |
| statusStandby | Standby | Standby |

---

## 13. PRODUCT ROADMAP
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| roadmapPhase1Window | 0-30 dias | 0-30 days |
| roadmapPhase1Focus | Lançamento e conversão inicial | Launch and Initial Conversion |
| roadmapPhase1Item1 | Refino de onboarding e redução de abandono no primeiro uso | Refine onboarding and reduce first-use abandonment |
| roadmapPhase1Item2 | CTAs comerciais em páginas estratégicas para acelerar upgrade | Commercial CTAs on strategic pages to accelerate upgrades |
| roadmapPhase1Item3 | Ajustes de SEO técnico (metadata, sitemap, docs e rota roadmap) | Technical SEO adjustments (metadata, sitemap, docs and roadmap route) |
| roadmapPhase2Window | 31-60 dias | 31-60 days |
| roadmapPhase2Focus | Monetização e retenção | Monetization and Retention |
| roadmapPhase2Item1 | Aumento da conversão de usuário ativo para pagante | Increase active user to paying customer conversion |
| roadmapPhase2Item2 | Aprimoramento dos planos e proposta de valor por perfil | Enhance plans and value proposition by profile |
| roadmapPhase2Item3 | Instrumentação de coortes de retenção semanal/mensal | Implement weekly/monthly retention cohort tracking |
| roadmapPhase3Window | 61-90 dias | 61-90 days |
| roadmapPhase3Focus | Escala com previsibilidade | Scaling with Predictability |
| roadmapPhase3Item1 | Repetição de canal de aquisição vencedor com CAC controlado | Repeat winning acquisition channel with controlled CAC |
| roadmapPhase3Item2 | Hardening operacional e monitorização contínua de estabilidade | Operational hardening and continuous stability monitoring |
| roadmapPhase3Item3 | Evidência de tração para expansão comercial e institucional | Evidence of traction for commercial and institutional expansion |
| roadmapPhase4Window | 4-12 meses | 4-12 months |
| roadmapPhase4Focus | Expansão orientada a dados | Data-Driven Expansion |
| roadmapPhase4Item1 | Evolução gradual da capacidade até referência de 100 mil simultâneos | Gradual capacity evolution up to 100k concurrent reference |
| roadmapPhase4Item2 | Contratação por marcos de receita, retenção e confiabilidade | Contracting by revenue, retention, and reliability milestones |
| roadmapPhase4Item3 | Escala nacional mantendo custo operacional previsível | National scale while maintaining predictable operational cost |

---

## 14. POLICIES & LEGAL
| Key | Portuguese | English (Suggested) |
|-----|------------|-------------------|
| termsPageTitle | Termos e Condições | Terms and Conditions |
| termsContent1 | Ao utilizar a Syntexa, você concorda em usar a plataforma conforme a legislação brasileira e as políticas de segurança. É proibido uso abusivo, fraudulento ou que viole direitos de terceiros. | By using Syntexa, you agree to use the platform in accordance with Brazilian law and security policies. Abusive, fraudulent, or rights-infringing use is prohibited. |
| termsContent2 | A conta e as credenciais são de responsabilidade do usuário. Podemos atualizar estes termos para adequação legal e operacional. | Account and credentials are user responsibility. We may update these terms for legal and operational compliance. |
| cookiesPolicyTitle | Política de Cookies | Cookie Policy |
| cookiesPolicyContent1 | Utilizamos cookies essenciais para login, segurança de sessão e funcionamento da aplicação. Cookies de medição podem ser usados para melhorar desempenho e experiência. | We use essential cookies for login, session security, and application functionality. Measurement cookies may be used to improve performance and experience. |
| cookiesPolicyContent2 | No banner de consentimento, você pode escolher aceitar todos os cookies ou manter apenas os essenciais. | In the consent banner, you can choose to accept all cookies or keep only essential ones. |
| privacyPageTitle | Política de Privacidade | Privacy Policy |
| privacyContent1 | Tratamos dados pessoais conforme a LGPD, com finalidade de autenticação, segurança, prestação do serviço e melhoria contínua da plataforma. | We handle personal data per LGPD for authentication, security, service provision, and continuous platform improvement. |
| privacyContent2 | Você pode solicitar atualização ou exclusão de dados nos canais oficiais de suporte, observadas obrigações legais de retenção. | You can request data updates or deletion through official support channels, subject to legal retention obligations. |

---

## Notes
- All keys use camelCase for consistency
- Prices should be parameterized where possible (e.g., use `${price}` or `{price}` format)
- Regional variations: Some text uses "directamente" (Portuguese) vs "diretamente" - standardize based on target locale
- Currency: All prices currently in BRL (R$) - consider locale-specific currency conversion
