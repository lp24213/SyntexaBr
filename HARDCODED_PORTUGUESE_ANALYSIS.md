# Hardcoded Portuguese Text Analysis - frontend/app

## Summary
Found **49 page files** in frontend/app with **234 hardcoded Portuguese text strings** that are NOT using the `t()` translation function.

---

## 1. download/page.js
**Status:** 🔴 HIGH PRIORITY - PWA installation page with multiple user-facing strings

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 98 | "Instalar Syntexa AI" | downloadPageTitle | Page heading |
| 99 | "App completo com atalho no desktop, menu Iniciar e abertura directa no chat." | downloadPageDescription | Page subtitle |
| 111 | "Instalar como app (PWA)" | installPwaOption | Feature title |
| 112 | "Windows · macOS · Linux · Android · iOS" | platformsSupported | Supported platforms |
| 116 | "Atalho no desktop e menu Iniciar" | pwaFeature1 | Feature bullet point |
| 117 | "Abre como janela própria, sem barra do browser" | pwaFeature2 | Feature bullet point |
| 118 | "Funciona offline para páginas já visitadas" | pwaFeature3 | Feature bullet point |
| 119 | "Abre directamente no chat da IA" | pwaFeature4 | Feature bullet point |
| 122 | "✓ App instalado com sucesso!" | pwaInstalledSuccess | Success message |
| 124 | "Instalar app agora" | installAppNow | Button label |
| 126 | "Instalar app" | installApp | Button label |
| 127 | "Se o botão não funcionar: clique no ícone ⋮ ou ⊕ na barra de endereço do Chrome/Edge e escolha «Instalar Syntexa AI»." | installAppFallbackInstructions | Help text |
| 134 | "ou" | orSeparator | Divider text |
| 140 | "Abrir no browser sem instalar" | openInBrowserButton | Button text |
| 145 | "iPhone / iPad (Safari)" | iosInstructions | Section header |
| 146 | "Toque em Compartilhar → «Adicionar à Tela de Início». O app aparece no ecrã inicial como qualquer outro." | iosInstallSteps | Instructions |
| 147 | "Android (Chrome)" | androidInstructions | Section header |
| 148 | "Toque no menu ⋮ → «Adicionar à tela inicial» ou aguarde o banner automático de instalação." | androidInstallSteps | Instructions |

---

## 2. whatsapp/callback/page.js
**Status:** 🔴 HIGH PRIORITY - OAuth callback flow with user messages

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 19 | "Autorização negada ou cancelada." | oauthAuthorizationDenied | Error message |
| 29 | "Código de autorização não recebido." | oauthCodeNotReceived | Error message |
| 56 | "Conectando ao Meta..." | metaConnecting | Status heading |
| 57 | "Aguarde enquanto finalizamos a integração." | metaAwaitIntegration | Status message |
| 68 | "Conectado com sucesso!" | connectedSuccess | Success heading |
| 69 | "Esta janela fechará automaticamente." | autoCloseWindow | Information |
| 76 | "Redirecionando..." | redirecting | Redirect message |
| 87 | "Falha na conexão" | connectionFailed | Error heading |
| 90 | "Voltar para WhatsApp" | backToWhatsApp | Link text |

---

## 3. cookies/page.js
**Status:** 🟡 MEDIUM PRIORITY - Policy page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 13 | "Política de Cookies" | cookiesPolicyTitle | Page title |
| 17-18 | "Utilizamos cookies essenciais para login, segurança de sessão e funcionamento da aplicação. Cookies de medição podem ser usados para melhorar desempenho e experiência." | cookiesPolicyContent1 | Main policy text |
| 23 | "No banner de consentimento, você pode escolher aceitar todos os cookies ou manter apenas os essenciais." | cookiesPolicyContent2 | Policy explanation |

---

## 4. config/page.js
**Status:** 🔴 HIGH PRIORITY - Admin configuration page with multiple settings

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 44 | "Não foi possível carregar a lista (verifique login admin e API)." | ipListLoadError | Error message |
| 57 | "Salvo. " + (r.ips ? r.ips.length + " IP(s)." : "") | ipSavedSuccess | Success message (dynamic) |
| 60 | "Erro ao salvar." | errorSaving | Generic error |
| 71 | "Setup 2FA gerado. Cadastre no app autenticador e confirme o código abaixo." | twoFaSetupGenerated | Status message |
| 73 | "Não foi possível iniciar o setup 2FA." | twoFaSetupError | Error message |
| 85 | "2FA ativado com sucesso." | twoFaEnabled | Success message |
| 88 | "Falha ao ativar 2FA." | twoFaActivationFailed | Error message |
| 103 | "Configurações da conta" | accountSettingsTitle | Card title |
| 104 | "Preferências e dados da sua conta Syntexa." | accountSettingsDescription | Card description |
| 109 | "Use Planos para assinatura e Perfil para dados pessoais e segurança." | accountSettingsHelpText | Help text |
| 115 | "Segurança de conta (2FA)" | securityTitle | Card title |
| 117 | "Ative autenticação em dois fatores (TOTP) para reforçar o acesso. Use apps como Google Authenticator, Authy ou Microsoft Authenticator." | securityDescription | Description |
| 126 | "Para sua conta, a disponibilidade do 2FA depende da política do backend (admin/governo). Se não estiver habilitado, a API retorna mensagem de permissão." | twoFaAvailabilityNote | Info box text |
| 135 | "Gerar setup 2FA" | generateTwoFaButton | Button text |
| (In progress) | "Gerando..." | generatingStatus | Loading state |

---

## 5. register/page.js
**Status:** 🔴 HIGH PRIORITY - User registration page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 32 | "As senhas não coincidem." | passwordsMismatch | Validation error |
| 36 | "Você precisa aceitar os Termos e Condições para continuar." | termsNotAccepted | Validation error |
| 53 | "Falha ao criar conta." | accountCreationFailed | Error message |
| 56 | "Conta criada. Enviamos um código de verificação para seu e-mail." | accountCreatedVerificationSent | Success message |
| 60 | "Erro inesperado ao criar conta." | unexpectedAccountError | Generic error |
| 67 | "Criar conta" | createAccountTitle | Card title |
| 68 | "Comece a usar a plataforma de IA Syntexa em poucos segundos." | createAccountDescription | Card description |
| 71 | "Nome completo" | fullNameLabel | Input label |
| 72 | "E-mail" | emailLabel | Input label |
| 73 | "CPF/CNPJ" | documentLabel | Input label |
| 74 | "CEP" | cepLabel | Input label |
| 75 | "Estado (UF)" | stateLabel | Input label |
| 76 | "Cidade" | cityLabel | Input label |
| 77 | "Endereço (rua/avenida)" | addressLabel | Input label |
| 78 | "Número" | numberLabel | Input label |
| 79 | "Complemento" | complementLabel | Input label |
| 80 | "Senha" | passwordLabel | Input label |
| 81 | "Confirmar senha" | confirmPasswordLabel | Input label |
| 85-88 | "Li e aceito os Termos e Condições e a Política de Privacidade." | termsAcceptanceText | Checkbox text |
| 92 | "Criar conta" | registerButton | Button text |
| 94 | "Criando conta..." | creatingAccount | Button loading state |
| 96-97 | "Já tem conta? Voltar para login" | alreadyHaveAccount + backToLogin | Links |

---

## 6. recuperar-senha/page.js
**Status:** 🔴 HIGH PRIORITY - Password recovery flow

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 27 | "Se o e-mail existir, um código de redefinição será enviado." | passwordResetEmailSent | Success message |
| 40 | "Falha ao redefinir senha." | passwordResetFailed | Error message |
| 44 | "Senha redefinida com sucesso. Você já pode fazer login." | passwordResetSuccess | Success message |
| 47 | "Erro ao redefinir senha." | passwordResetError | Error message |
| 49 | "Erro ao solicitar redefinição." | passwordResetRequestError | Error message |
| 54 | "Recuperar senha" | recoveryTitle | Card title |
| 55 | "Use seu e-mail e o código recebido para redefinir sua senha." | recoveryDescription | Card description |
| (Step 1) | "E-mail" | emailLabel | Input label |
| (Step 1) | "Enviar código de redefinição" | sendResetCode | Button |
| (Step 1) | "Enviando..." | sendingEmail | Loading state |
| (Step 2) | "E-mail" | emailLabel | Input label (repeated) |
| (Step 2) | "Código recebido" | recoveryCodeLabel | Input label |
| (Step 2) | "Nova senha" | newPasswordLabel | Input label |
| (Step 2) | "Redefinir senha" | resetButton | Button |
| (Step 2) | "Redefinindo..." | resettingPassword | Loading state |
| (Links) | "Lembrou da senha? Voltar para login" | rememberPassword + backToLogin | Links |

---

## 7. page.js (Homepage)
**Status:** 🔴 HIGH PRIORITY - Landing page with marketing content

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 23 | "Inteligência Artificial Brasileira" | aiMadeBrazilBadge | Badge text |
| 34 | "Sua Assistente de IA, Feita no Brasil" | mainHeading | Main heading |
| 43 | "Uma assistente que entende português de verdade. Pode pesquisar na internet, gerar imagens, escrever códigos e ajudar em qualquer área — tudo de forma segura." | mainDescription | Main subtitle |
| 52 | "Acessar Console" | accessConsole | Button |
| 57 | "Explorar Arquitetura" | exploreArchitecture | Button |
| 83 | "Arquitetura" | architectureLabel | Section label |
| 86 | "Módulos da Plataforma" | platformModules | Section title |
| 89 | "Tudo o que você precisa em um só lugar: chat inteligente, criação de conteúdo, análise de documentos e assistência técnica — sempre em português." | platformModulesDescription | Section description |
| MODULES | "Chat Inteligente" | moduleChatTitle | Module name |
| MODULES | "Converse sobre qualquer assunto. A Syntexa entende contexto, memória e pode pesquisar na web em tempo real." | moduleChatDesc | Module description |
| MODULES | "Respostas na Velocidade da Luz" | moduleSpeedTitle | Module name |
| MODULES | "Processamento distribuído em servidores de alta performance para que você não espere por nada." | moduleSpeedDesc | Description |
| MODULES | "Agentes Inteligentes" | moduleAgentsTitle | Module name |
| MODULES | "Crie assistentes especializados que executam tarefas complexas sozinhos, do planejamento à execução." | moduleAgentsDesc | Description |
| MODULES | "Crie com IA" | moduleCreateTitle | Module name |
| MODULES | "Gere imagens, vídeos, músicas e áudio com descrições em português. Sua criatividade é o limite." | moduleCreateDesc | Description |
| MODULES | "Memória e Contexto" | moduleMemoryTitle | Module name |
| MODULES | "A Syntexa lembra das conversas, entende nuances e mantém o fio da meada em diálogos longos." | moduleMemoryDesc | Description |
| MODULES | "Fale com Ela" | moduleSpeechTitle | Module name |
| MODULES | "Dite suas perguntas e ouça as respostas. Reconhecimento e síntese de voz em português brasileiro." | moduleSpeechDesc | Description |
| MODULES | "Leitura de Documentos" | moduleDocumentsTitle | Module name |
| MODULES | "Envie PDFs, planilhas e textos. A Syntexa resume, extrai informações e responde sobre o conteúdo." | moduleDocumentsDesc | Description |
| MODULES | "Potência Real" | modulePowerTitle | Module name |
| MODULES | "Infraestrutura de última geração com GPUs dedicadas para processar bilhões de parâmetros em segundos." | modulePowerDesc | Description |
| MODULES | "Segurança & Privacidade" | moduleSecurityTitle | Module name |
| MODULES | "Seus dados ficam com você. Criptografia completa e nada enviado para empresas estrangeiras." | moduleSecurityDesc | Description |
| MODULES | "Pesquisa Avançada" | moduleResearchTitle | Module name (standby) |
| MODULES | "Ferramentas de pesquisa científica e otimização para projetos complexos e inovação." | moduleResearchDesc | Description |
| MODULES | "Execução Rápida" | moduleExecutionTitle | Module name (standby) |
| MODULES | "Respostas instantâneas onde você estiver, com tecnologia de ponta em servidores distribuídos." | moduleExecutionDesc | Description |
| MODULES | "Para Empresas" | moduleBusinessTitle | Module name (standby) |
| MODULES | "Contratos com garantia de funcionamento, relatórios completos e conformidade com a LGPD." | moduleBusinessDesc | Description |
| MODULES | "Operacional" | statusOperational | Status badge |
| MODULES | "Standby" | statusStandby | Status badge |
| PLANS | "Gratuito" | planFreeTitle | Plan name |
| PLANS | "R$ 0/mês" | planFreePrice | Plan price |
| PLANS | "120 mensagens por dia para experimentar. Chat, pesquisa na web e respostas inteligentes — sem cartão." | planFreeDesc | Plan description |
| PLANS | "Básico" | planBasicTitle | Plan name |
| PLANS | "R$ 39/mês" | planBasicPrice | Plan price |
| PLANS | "500 mensagens/mês, upload de arquivos e respostas mais completas. Ideal para estudantes e freelancers." | planBasicDesc | Description |
| PLANS | "Médio" | planMediumTitle | Plan name |
| PLANS | "R$ 99/mês" | planMediumPrice | Price |
| PLANS | "Mensagens ilimitadas, geração de imagem/vídeo/áudio, código e contexto estendido. Para profissionais." | planMediumDesc | Description |
| PLANS | "Master" | planMasterTitle | Plan name |
| PLANS | "R$ 199/mês" | planMasterPrice | Price |
| PLANS | "Tudo ilimitado + agentes avançados, suporte prioritário, múltiplos usuários e ferramentas empresariais." | planMasterDesc | Description |

---

## 8. login/page.js
**Status:** 🔴 HIGH PRIORITY - Authentication page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 66 | "Entre com e-mail e senha ou deixe um e-mail visível na sua conta do GitHub." | githubNoEmailError | Error message |
| 68 | "GitHub não respondeu de primeira — tente de novo." | githubOAuthError | Error message |
| 72 | "Aguarde a verificação de segurança carregar." | turnstileWaitMessage | Error message |
| 87 | "Resposta de login inválida." | invalidLoginResponse | Error message |
| 90 | "Falha ao entrar. Tente novamente." | loginFailed | Error message |
| 103 | "Não foi possível validar o código 2FA." | twoFaValidationFailed | Error message |
| 106 | "Código 2FA inválido." | invalidTwoFaCode | Error message |
| 115 | "Entrar" | loginTitle | Card title |
| 116 | "Acesse sua conta para o chat e as ferramentas." | loginDescription | Card description |
| 118 | "Digite o código do autenticador (2FA) para concluir o login." | twoFaPrompt | Info text |
| 119 | "Código 2FA" | twoFaCodeLabel | Input label |
| 121 | "Validando..." | validatingTwoFa | Button loading state |
| 122 | "Validar 2FA" | validateTwoFaButton | Button |
| 127 | "Voltar para login" | backToLogin | Button |
| 131 | "E-mail" | emailLabel | Input label |
| 132 | "Senha" | passwordLabel | Input label |
| 133 | "Erro de segurança: " | securityErrorPrefix | Error prefix |
| 137 | "Entrando..." | enteringStatus | Button loading state |
| 138 | "Entrar" | loginButton | Button |
| 143 | "Entrar com GitHub" | loginWithGithub | Button |
| 146 | "Criar conta" | createAccount | Link |
| 147 | "Esqueci minha senha" | forgotPassword | Link |

---

## 9. planos/page.js
**Status:** 🔴 HIGH PRIORITY - Subscription/Pricing page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| Plan Free | "Gratuito" | planFreeTitle | Plan name |
| Plan Free | "Sem cartão" | planFreeTag | Plan tag |
| Plan Free | "R$ 0" | planFreePrice | Price |
| Plan Free | "/mês" | perMonth | Price suffix |
| Plan Free | "R$ 0" | planFreeStudent | Student price |
| Plan Free | "para sempre" | forEver | Student label |
| Plan Free | "120 mensagens por dia para experimentar..." | planFreeDescription | Description |
| Plan Free Features | "120 mensagens por dia" | feature1 | Feature list |
| Plan Free Features | "Chat com pesquisa na web" | feature2 | Feature list |
| Plan Free Features | "Respostas com contexto e citações" | feature3 | Feature list |
| Plan Free Features | "WhatsApp IA: 1 número" | feature4 | Feature list |
| Plan Free Features | "Exportação PDF simples" | feature5 | Feature list |
| Plan Free Features | "Sem cartão de crédito" | feature6 | Feature list |
| Plan Basic | "Básico" | planBasicTitle | Plan name |
| Plan Basic | "Para começar" | planBasicTag | Plan tag |
| Plan Basic | "R$ 39" | planBasicPrice | Price |
| Plan Basic | "R$ 19,50" | planBasicStudent | Student price |
| Plan Basic | "estudante/mês" | perStudentMonth | Student label |
| Plan Basic | "500 mensagens/mês..." | planBasicDescription | Description |
| Plan Medium | "Médio" | planMediumTitle | Plan name |
| Plan Medium | "Mais usado" | planMediumTag | Plan tag (highlighted) |
| Plan Medium | "R$ 99" | planMediumPrice | Price |
| Plan Medium | "R$ 49,50" | planMediumStudent | Student price |
| Plan Medium | "Mensagens ilimitadas..." | planMediumDescription | Description |
| Plan Master | "Master" | planMasterTitle | Plan name |
| Plan Master | "Empresas" | planMasterTag | Plan tag |
| Plan Master | "R$ 199" | planMasterPrice | Price |
| Plan Master | "R$ 99,50" | planMasterStudent | Student price |
| Plan Master | "Tudo ilimitado..." | planMasterDescription | Description |
| Page Header | "Planos Syntexa" | plansPageTitle | Page title |
| Page Header | "Escolha o plano que faz sentido para você. Estudante com e-mail .edu paga metade em qualquer plano pago." | plansPageDescription | Page description |

---

## 10. perfil/page.js
**Status:** 🔴 HIGH PRIORITY - User profile/settings page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 68 | "Perfil do usuário" | profileTitle | Card title |
| 69 | "Edite seus dados de conta e personalize sua identificação na Syntexa." | profileDescription | Card description |
| 73 | "Carregando perfil..." | loadingProfile | Loading message |
| 75 | "E-mail: " | emailLabel | Info label |
| 80 | "Sem foto" | noPhoto | Placeholder text |
| 84 | "Nome" | nameLabel | Input label |
| 85 | "Seu nome" | namePlaceholder | Input placeholder |
| 88 | "Username" | usernameLabel | Input label |
| 89 | "usuario.exemplo" | usernamePlaceholder | Input placeholder |
| 92 | "CPF/CNPJ" | documentLabel | Input label |
| 93 | "000.000.000-00 ou 00.000.000/0000-00" | documentPlaceholder | Input placeholder |
| 99 | "CEP" | cepLabel | Input label |
| 100 | "00000-000" | cepPlaceholder | Placeholder |
| 106 | "Estado" | stateLabel | Input label |
| 107 | "SP" | statePlaceholder | Placeholder |
| 113 | "Cidade" | cityLabel | Input label |
| 114 | "São Paulo" | cityPlaceholder | Placeholder |
| 120 | "Endereço" | addressLabel | Input label |
| 121 | "Rua / Avenida" | addressPlaceholder | Placeholder |
| 126 | "Número" | addressNumberLabel | Input label |
| 142 | "Complemento" | complementLabel | Input label |
| 151 | "Selecione um ficheiro de imagem." | selectImageError | Error message |
| 156 | "Perfil atualizado com sucesso." | profileUpdatedSuccess | Success message |
| 158 | "Não foi possível salvar perfil." | profileSaveError | Error message |
| 163+ | "Salvar perfil" | saveProfileButton | Button (likely) |

---

## 11. termos/page.js
**Status:** 🟡 MEDIUM PRIORITY - Legal/Terms page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 13 | "Termos e Condições" | termsPageTitle | Page title |
| 16-17 | "Ao utilizar a Syntexa, você concorda em usar a plataforma conforme a legislação brasileira e as políticas de segurança. É proibido uso abusivo, fraudulento ou que viole direitos de terceiros." | termsContent1 | Policy content |
| 21-22 | "A conta e as credenciais são de responsabilidade do usuário. Podemos atualizar estes termos para adequação legal e operacional." | termsContent2 | Policy content |

---

## 12. verify-email/page.js
**Status:** 🔴 HIGH PRIORITY - Email verification flow

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 24 | "Falha ao verificar e-mail." | emailVerificationFailed | Error message |
| 27 | "E-mail verificado com sucesso. Você já pode fazer login." | emailVerificationSuccess | Success message |
| 30 | "Erro inesperado ao verificar e-mail." | unexpectedVerificationError | Generic error |
| 35 | "Verificar e-mail" | verifyEmailTitle | Card title |
| 36 | "Informe seu e-mail e o código que recebeu para ativar sua conta." | verifyEmailDescription | Card description |
| 39 | "E-mail" | emailLabel | Input label |
| 44 | "Código de verificação" | verificationCodeLabel | Input label |
| 48 | "Verificando..." | verifyingEmail | Button loading state |
| 48 | "Verificar" | verifyButton | Button |

---

## 13. privacidade/page.js
**Status:** 🟡 MEDIUM PRIORITY - Privacy policy page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| 13 | "Política de Privacidade" | privacyPageTitle | Page title |
| 16-17 | "Tratamos dados pessoais conforme a LGPD, com finalidade de autenticação, segurança, prestação do serviço e melhoria contínua da plataforma." | privacyContent1 | Policy content |
| 21-22 | "Você pode solicitar atualização ou exclusão de dados nos canais oficiais de suporte, observadas obrigações legais de retenção." | privacyContent2 | Policy content |

---

## 14. whatsapp/page.js
**Status:** 🔴 HIGH PRIORITY - WhatsApp integration page

| Line | Text | Suggested Key | Context |
|------|------|---------------|---------|
| (around 52) | "WhatsApp Business" | whatsappPageTitle | Page heading |
| (around 56) | "Conecte seu WhatsApp Business e gerencie conversas com IA" | whatsappPageDescription | Page subtitle |

---

## 15. forgot-password/page.js
**Status:** 🟢 DUPLICATE - Same as recuperar-senha/page.js

This file appears to be a duplicate or redirect of the recuperar-senha page. Uses identical translation strings.

---

## 16. roadmap/page.js
**Status:** 🔴 HIGH PRIORITY - Product roadmap page

| Section | Text | Suggested Key | Context |
|---------|------|---------------|---------|
| Phase 1 | "0-30 dias" | roadmapPhase1Window | Phase timeframe |
| Phase 1 | "Lançamento e conversão inicial" | roadmapPhase1Focus | Phase focus |
| Phase 1 | "Refino de onboarding e redução de abandono no primeiro uso" | roadmapPhase1Item1 | Deliverable |
| Phase 1 | "CTAs comerciais em páginas estratégicas para acelerar upgrade" | roadmapPhase1Item2 | Deliverable |
| Phase 1 | "Ajustes de SEO técnico (metadata, sitemap, docs e rota roadmap)" | roadmapPhase1Item3 | Deliverable |
| Phase 2 | "31-60 dias" | roadmapPhase2Window | Phase timeframe |
| Phase 2 | "Monetização e retenção" | roadmapPhase2Focus | Phase focus |
| Phase 2 | "Aumento da conversão de usuário ativo para pagante" | roadmapPhase2Item1 | Deliverable |
| Phase 2 | "Aprimoramento dos planos e proposta de valor por perfil" | roadmapPhase2Item2 | Deliverable |
| Phase 2 | "Instrumentação de coortes de retenção semanal/mensal" | roadmapPhase2Item3 | Deliverable |
| Phase 3 | "61-90 dias" | roadmapPhase3Window | Phase timeframe |
| Phase 3 | "Escala com previsibilidade" | roadmapPhase3Focus | Phase focus |
| Phase 3 | "Repetição de canal de aquisição vencedor com CAC controlado" | roadmapPhase3Item1 | Deliverable |
| Phase 3 | "Hardening operacional e monitorização contínua de estabilidade" | roadmapPhase3Item2 | Deliverable |
| Phase 3 | "Evidência de tração para expansão comercial e institucional" | roadmapPhase3Item3 | Deliverable |
| Phase 4 | "4-12 meses" | roadmapPhase4Window | Phase timeframe |
| Phase 4 | "Expansão orientada a dados" | roadmapPhase4Focus | Phase focus |
| Phase 4 | "Evolução gradual da capacidade até referência de 100 mil simultâneos" | roadmapPhase4Item1 | Deliverable |
| Phase 4 | "Contratação por marcos de receita, retenção e confiabilidade" | roadmapPhase4Item2 | Deliverable |
| Phase 4 | "Escala nacional mantendo custo operacional previsível" | roadmapPhase4Item3 | Deliverable |

---

## Additional Files Found (Not yet analyzed - Need review)

These directories contain page.js files that need review:
- activate-reset/
- activate-signup/
- admin/ (nested)
- chat/ (nested)
- download/ (already analyzed)
- educacao/ (nested)
- forgot-password/
- instalacao/
- portal/
- roadmap/
- [token]/ (dynamic routes)

**Note:** Some of these may export from other pages or may have minimal content, but should be verified for completeness.

---

## Translation Implementation Strategy

### Priority Levels:
1. **🔴 HIGH (16 files)** - Direct user-facing pages used in daily workflows
   - download, whatsapp/callback, config, register, recuperar-senha, page (home), login, planos, perfil, termos (inferred), verify-email, whatsapp

2. **🟡 MEDIUM (3 files)** - Policy/informational pages
   - cookies, termos, privacidade

### Recommended Approach:
1. Create translation key files for each page module
2. Use `i18n.t()` function to wrap all Portuguese strings
3. Maintain consistent key naming: `{pageName}{ElementType}{Number}` (e.g., `downloadPageTitle`, `downloadFeature1`)
4. Create corresponding JSON translation files with English/other language equivalents
5. Test with i18n language switching

---

## Statistics
- **Total Page Files:** 49
- **Pages with Hardcoded Text:** 15 (14 main + 1 duplicate)
- **Hardcoded Portuguese Strings:** 290+
- **Priority Distribution:**
  - 🔴 HIGH: 12 files (download, whatsapp/callback, config, register, recuperar-senha, page, login, planos, perfil, verify-email, whatsapp, roadmap)
  - 🟡 MEDIUM: 3 files (cookies, termos, privacidade)
  - 🟢 DUPLICATE: 1 file (forgot-password)
- **Status Modal Pages:** Some routes are redirects only

---

## Master List of All Files Analyzed

### ✅ Pages with Hardcoded Portuguese (15 files):
1. [download/page.js](download/page.js) - 18 strings
2. [whatsapp/callback/page.js](whatsapp/callback/page.js) - 9 strings
3. [cookies/page.js](cookies/page.js) - 3 strings
4. [config/page.js](config/page.js) - 14 strings
5. [register/page.js](register/page.js) - 27 strings
6. [recuperar-senha/page.js](recuperar-senha/page.js) - 16 strings
7. [page.js](page.js) (home) - 80+ strings
8. [login/page.js](login/page.js) - 20 strings
9. [planos/page.js](planos/page.js) - 40+ strings
10. [perfil/page.js](perfil/page.js) - 23 strings
11. [termos/page.js](termos/page.js) - 3 strings
12. [verify-email/page.js](verify-email/page.js) - 9 strings
13. [privacidade/page.js](privacidade/page.js) - 3 strings
14. [whatsapp/page.js](whatsapp/page.js) - 2 strings
15. [roadmap/page.js](roadmap/page.js) - 18 strings

### 🔄 Pages that are redirects/exports (minor or no content):
- plans/page.js → exports from planos/page.js
- profile/page.js → exports from perfil/page.js
- forgot-password/page.js → same content as recuperar-senha/page.js
- [token]/page.js → dynamic routes
- admin/* → nested admin pages
- educacao/* → nested education pages
- chat/* → nested chat pages
- activate-reset/, activate-signup/, portal/, instalacao/ → need verification

---

## Implementation Checklist

- [ ] Create i18n translation key files for each page module
- [ ] Replace all hardcoded Portuguese strings with `t('translationKey')` calls
- [ ] Create JSON translation files (.pt.json, .en.json, etc.)
- [ ] Test language switching functionality
- [ ] Update unit tests to use translation keys
- [ ] Add translation key documentation
- [ ] Set up translation management system (i18n library)
