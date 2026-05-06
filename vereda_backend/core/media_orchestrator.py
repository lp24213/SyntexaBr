from __future__ import annotations

import re
from dataclasses import dataclass

from vereda_backend.core.config import settings


@dataclass
class ImagePlan:
    prompt: str
    width: int
    height: int
    quality: str
    negative_prompt: str


@dataclass
class VideoPlan:
    prompt: str
    resolution: str
    fps: int
    duration_sec: int
    quality: str
    negative_prompt: str


def _parse_resolution(raw: str, *, fallback_w: int, fallback_h: int) -> tuple[int, int]:
    txt = (raw or "").strip().lower().replace(" ", "")
    m = re.match(r"^(\d{3,5})[x\*](\d{3,5})$", txt)
    if not m:
        return fallback_w, fallback_h
    w = max(512, min(4096, int(m.group(1))))
    h = max(512, min(4096, int(m.group(2))))
    return w, h


def _looks_like_toy_prompt(prompt: str) -> bool:
    p = (prompt or "").lower()
    if not p:
        return True
    toy_hits = [
        "figura geom",
        "shape",
        "triangulo",
        "quadrado",
        "círculo",
        "icone simples",
        "minimalista",
        "clipart",
        "stickman",
    ]
    realism_hits = [
        "fotoreal",
        "realista",
        "cinematic",
        "ultra detail",
        "fotorrealista",
        "documentary",
        "8k",
        "hdr",
    ]
    if any(k in p for k in realism_hits):
        return False
    return any(k in p for k in toy_hits)


def plan_image_request(user_prompt: str) -> ImagePlan:
    w, h = _parse_resolution(
        str(getattr(settings, "media_image_target_resolution", "2048x2048") or "2048x2048"),
        fallback_w=2048,
        fallback_h=2048,
    )
    quality = str(getattr(settings, "media_image_quality", "ultra") or "ultra").strip() or "ultra"
    negative = str(
        getattr(
            settings,
            "media_image_negative_prompt",
            "lowres, blurry, watermark, artifacts, cartoonish, toy-like geometry, flat icon style",
        )
        or ""
    ).strip()
    prompt = (user_prompt or "").strip()
    if bool(getattr(settings, "media_realism_enhance_prompts", True)):
        realism_suffix = (
            "Photorealistic, physically plausible lighting, high dynamic range, crisp textures, "
            "real-world details, professional composition, sharp focus, production quality."
        )
        if _looks_like_toy_prompt(prompt):
            prompt = f"{prompt}. {realism_suffix} Avoid simplistic geometric-only composition."
        else:
            prompt = f"{prompt}. {realism_suffix}"
    return ImagePlan(prompt=prompt, width=w, height=h, quality=quality, negative_prompt=negative)


def plan_video_request(user_prompt: str) -> VideoPlan:
    resolution = str(getattr(settings, "media_video_target_resolution", "1920x1080") or "1920x1080").strip()
    fps = int(getattr(settings, "media_video_target_fps", 30) or 30)
    fps = max(12, min(60, fps))
    duration = int(getattr(settings, "media_video_target_duration_sec", 8) or 8)
    duration = max(2, min(60, duration))
    quality = str(getattr(settings, "media_video_quality", "cinematic") or "cinematic").strip() or "cinematic"
    negative = str(
        getattr(
            settings,
            "media_video_negative_prompt",
            "blurry, jitter, flicker, low-detail, unrealistic anatomy, flat geometric-only scenes",
        )
        or ""
    ).strip()
    prompt = (user_prompt or "").strip()
    if bool(getattr(settings, "media_realism_enhance_prompts", True)):
        prompt = (
            f"{prompt}. Cinematic realism, coherent motion, stable camera, physically plausible scene, "
            "detailed materials, natural lighting, no toy-like abstraction."
        )
    return VideoPlan(
        prompt=prompt,
        resolution=resolution,
        fps=fps,
        duration_sec=duration,
        quality=quality,
        negative_prompt=negative,
    )

