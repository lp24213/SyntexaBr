import base64
import io
import os
import threading
import uuid
from typing import Optional

import torch
from diffusers import AutoPipelineForText2Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Syntexa GPU Image Service", version="1.0.0")

_pipe_lock = threading.Lock()
_pipe: Optional[AutoPipelineForText2Image] = None


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1800)
    negative_prompt: str = Field(
        default=(
            "cartoon, anime, geometric shapes, lowpoly, abstract, illustration, "
            "painting, drawing, logo, watermark, deformed, blurry, low quality"
        ),
        max_length=1000,
    )
    width: int = Field(default=1024, ge=512, le=1536)
    height: int = Field(default=1024, ge=512, le=1536)
    steps: int = Field(default=28, ge=12, le=80)
    guidance_scale: float = Field(default=6.5, ge=1.0, le=20.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2**31 - 1)


def _model_id() -> str:
    return os.getenv("IMAGE_MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0")


def _load_pipe() -> AutoPipelineForText2Image:
    global _pipe
    if _pipe is not None:
        return _pipe
    with _pipe_lock:
        if _pipe is not None:
            return _pipe
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        pipe = AutoPipelineForText2Image.from_pretrained(
            _model_id(),
            torch_dtype=dtype,
            use_safetensors=True,
            variant="fp16" if dtype == torch.float16 else None,
        )
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
        pipe.set_progress_bar_config(disable=True)
        _pipe = pipe
        return _pipe


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "cuda": bool(torch.cuda.is_available()),
        "model_id": _model_id(),
    }


@app.post("/generate")
def generate(req: GenerateRequest) -> dict:
    pipe = _load_pipe()
    gen = None
    if req.seed is not None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        gen = torch.Generator(device=device).manual_seed(req.seed)
    try:
        result = pipe(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            width=req.width,
            height=req.height,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            generator=gen,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"image_generation_failed: {exc}") from exc

    if not result.images:
        raise HTTPException(status_code=500, detail="empty_image_result")

    img = result.images[0]
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    raw = buf.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    return {
        "ok": True,
        "id": f"img-gpu-{uuid.uuid4()}",
        "provider": "syntexa-gpu-diffusers",
        "prompt": req.prompt,
        "mime": "image/png",
        "image_base64": b64,
    }
