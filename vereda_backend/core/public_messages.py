"""Mensagens devolvidas ao cliente (nunca detalhes técnicos, tokens, stack, etc.)."""

# Uso genérico para falhas internas / 5xx / indisponibilidade transitória
MSG_TRY_AGAIN_PT = "Não foi possível concluir agora. Tente novamente em alguns instantes."

# Pedido malformado (substitui exceções de parse JSON no corpo)
MSG_BAD_REQUEST_PT = "Não foi possível processar o pedido. Tente novamente."
