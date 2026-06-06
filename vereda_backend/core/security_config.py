# 🔒 CORS & Security Configuration
# Migrado de production-node/api/src/index.js para vereda_backend

ALLOWED_ORIGINS = [
    "https://syntexabr.com.br",
    "https://www.syntexabr.com.br",
    "https://app.syntexabr.com.br",
    "https://db2ba8b5.syntexa-frontend.pages.dev",
    "https://610d6e7d.syntexa-frontend.pages.dev",
    "https://bb64fb4c.syntexa-frontend.pages.dev",
    "https://syntexa-gateway.contato-00d.workers.dev",
    "http://localhost:3000",
    "http://localhost:8000",
]

# ✅ WHITELIST de tipos MIME permitidos SOMENTE
ALLOWED_MIME_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/plain",
    "text/csv",
}

ALLOWED_EXTENSIONS = {".webm", ".mp4", ".mp3", ".wav", ".ogg", ".flac", ".pdf", ".docx", ".xlsx", ".txt", ".csv"}

# Max file size: 40MB
MAX_FILE_SIZE = 40 * 1024 * 1024
