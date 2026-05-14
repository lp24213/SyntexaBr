"""
VEREDA / SYNTEXA — AI Worker Runtime v3.0 (CPU Bridge)
Stub leve para exposição de API. Substituir por GPU quando provisionado.
"""
import os, time, hashlib, json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="VEREDA AI Worker", version="3.0.0")
START = time.time()

class Msg(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    model: str
    messages: List[Msg]
    stream: bool = False
    max_tokens: Optional[int] = 512

class EmbReq(BaseModel):
    model: str
    input: List[str]

@app.get("/health")
def health():
    return {"status":"ok","service":"vereda-ai-worker","version":"3.0.0","mode":"cpu-bridge","uptime":time.time()-START}

def _chat_response(req: ChatReq):
    return {"id":"chatcmpl-"+hashlib.md5(str(time.time()).encode()).hexdigest()[:12],"object":"chat.completion","created":int(time.time()),"model":req.model,"choices":[{"index":0,"message":{"role":"assistant","content":"[VEREDA AI Worker v3.0] Recebi sua mensagem. GPU cluster em provisionamento — resposta via bridge CPU."},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}}

@app.post("/v1/chat/completions")
def chat(req: ChatReq):
    return _chat_response(req)

@app.post("/public-chat")
def public_chat(req: ChatReq):
    return _chat_response(req)

@app.post("/public-chat/stream")
def public_chat_stream(req: ChatReq):
    def event_generator():
        content = "[VEREDA AI Worker v3.0] Recebi sua mensagem. GPU cluster em provisionamento — resposta via bridge CPU."
        for word in content.split():
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
        yield f"data: {json.dumps({'content': ''})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream; charset=utf-8")

@app.post("/v1/embeddings")
def emb(req: EmbReq):
    return {"object":"list","data":[{"object":"embedding","embedding":[0.1]*384,"index":i} for i,_ in enumerate(req.input)],"model":req.model,"usage":{"prompt_tokens":sum(len(t.split()) for t in req.input),"total_tokens":sum(len(t.split()) for t in req.input)}}

@app.get("/v1/models")
def models():
    return {"object":"list","data":[{"id":"vereda-ai-worker","object":"model","created":int(START),"owned_by":"syntexa"}]}

@app.get("/v1/health/detailed")
def detailed():
    return {"status":"healthy","components":{"vllm":{"status":"not_loaded","reason":"GPU cluster provisioning"},"embeddings":{"status":"cpu_fallback"},"redis":{"status":"connected"}}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT","8000")))
