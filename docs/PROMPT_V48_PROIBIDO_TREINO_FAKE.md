# PROMPT V48 — PROIBIDO TREINAR EM PROMPTS DE TESTE

(PROIBIDO LOOP INFINITO DE VALIDAÇÃO)

A SYNTEXA NÃO PODE:

* treinar usando prompts de teste
* treinar usando "Qual o valor de PI?"
* repetir exemplos mínimos infinitamente
* entrar em loop de sanity check
* usar datasets minúsculos
* usar corpus vazio
* overfit em exemplos únicos

━━━━━━━━━━━━━━━━━━━
PROBLEMA ATUAL
━━━━━━━━━━━━━━━━━━━

O SISTEMA ESTÁ:

* preso há horas
* repetindo prompts simples
* aparentemente focado apenas em "PI"
* sem progresso real

ISSO INDICA:

* validation loop
* dataset quebrado
* dataloader inválido
* corpus vazio
* benchmark infinito
* fine-tuning incorreto
* overfit em micro dataset

━━━━━━━━━━━━━━━━━━━
AÇÃO OBRIGATÓRIA
━━━━━━━━━━━━━━━━━━━

PARAR IMEDIATAMENTE:

* loops de validação
* prompts hardcoded
* sanity checks infinitos
* treino em exemplos mínimos

━━━━━━━━━━━━━━━━━━━
DATASET AUDIT OBRIGATÓRIA
━━━━━━━━━━━━━━━━━━━

MOSTRAR:

* quantidade real de documentos
* quantidade real de tokens
* tamanho do corpus
* idiomas detectados
* fontes do dataset
* deduplicação
* distribuição estatística
* train/validation split
* top samples carregados

━━━━━━━━━━━━━━━━━━━
VERIFICAÇÃO DO DATALOADER
━━━━━━━━━━━━━━━━━━━

VALIDAR:

* dataloader carregando corpus real
* batches variando
* samples únicos
* sequência tokenizada corretamente
* context windows válidas

MOSTRAR:

* batch samples reais
* token counts reais
* sequência real do treino

━━━━━━━━━━━━━━━━━━━
PROIBIDO TREINAMENTO FAKE
━━━━━━━━━━━━━━━━━━━

NÃO:

* treinar em prompts únicos
* repetir exemplos
* usar placeholders
* usar corpus artificial minúsculo

━━━━━━━━━━━━━━━━━━━
FOUNDATION MODEL REAL
━━━━━━━━━━━━━━━━━━━

O TREINO PRECISA USAR:

* Common Crawl
* Wikipedia
* livros
* código
* português
* inglês
* multilíngue
* documentos
* datasets curados
* datasets próprios

━━━━━━━━━━━━━━━━━━━
LOGS OBRIGATÓRIOS
━━━━━━━━━━━━━━━━━━━

GERAR:

* dataset.log
* dataloader.log
* tokenizer.log
* training.log
* validation.log

━━━━━━━━━━━━━━━━━━━
MOSTRAR PROGRESSO REAL
━━━━━━━━━━━━━━━━━━━

EXIBIR:

* tokens processados
* samples processados
* throughput
* loss real
* learning rate
* GPU usage
* VRAM usage
* ETA realista

━━━━━━━━━━━━━━━━━━━
PROIBIDO LOOP INFINITO
━━━━━━━━━━━━━━━━━━━

SE O SISTEMA REPETIR:
"Qual o valor de PI?"

MAIS DE UMA VEZ:
ASSUMIR LOOP QUEBRADO.

━━━━━━━━━━━━━━━━━━━
OBJETIVO FINAL
━━━━━━━━━━━━━━━━━━━

TREINAR:
UMA FOUNDATION MODEL REAL.

NÃO:
um benchmark infinito de matemática básica.

FIM DO PROMPT.
