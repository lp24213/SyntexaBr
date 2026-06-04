/**
 * normalizeContent — Converte QUALQUER tipo de payload para string segura
 * Evita [object Object], null, undefined, e outras anomalias
 */

export function normalizeContent(payload) {
  if (payload === null || payload === undefined) {
    return ""
  }

  if (typeof payload === "string") {
    return payload
  }

  if (typeof payload === "number" || typeof payload === "boolean") {
    return String(payload)
  }

  // Se é objeto com propriedade content
  if (typeof payload === "object" && payload.content !== undefined) {
    const c = payload.content
    if (typeof c === "string") return c
    if (typeof c === "number") return String(c)
    if (c === null || c === undefined) return ""
    try {
      return JSON.stringify(c)
    } catch {
      return ""
    }
  }

  // Se é objeto com propriedade message
  if (typeof payload === "object" && payload.message !== undefined) {
    const m = payload.message
    if (typeof m === "string") return m
    if (typeof m === "number") return String(m)
    if (m === null || m === undefined) return ""
    try {
      return JSON.stringify(m)
    } catch {
      return ""
    }
  }

  // Se é objeto com propriedade text
  if (typeof payload === "object" && payload.text !== undefined) {
    const t = payload.text
    if (typeof t === "string") return t
    if (typeof t === "number") return String(t)
    if (t === null || t === undefined) return ""
    try {
      return JSON.stringify(t)
    } catch {
      return ""
    }
  }

  // Último recurso: tentar serializar
  if (typeof payload === "object") {
    try {
      return JSON.stringify(payload, null, 2)
    } catch {
      return ""
    }
  }

  return ""
}

/**
 * Para chunks de stream — versão rápida sem JSON.stringify
 */
export function normalizeStreamChunk(chunk) {
  if (chunk === null || chunk === undefined) {
    return ""
  }

  if (typeof chunk === "string") {
    return chunk
  }

  if (typeof chunk === "number" || typeof chunk === "boolean") {
    return String(chunk)
  }

  if (typeof chunk === "object" && chunk.content) {
    const c = chunk.content
    if (typeof c === "string") return c
    return String(c)
  }

  return ""
}
