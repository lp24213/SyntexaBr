# -*- coding: utf-8 -*-
from typing import Any, Dict
from vereda_ai.agents.base_agent import BaseAgent
from vereda_ai.tools.image_tool import ImageTool

class VisionAgent(BaseAgent):
    name = "vision"
    def __init__(self, llm=None):
        self.tool = ImageTool()
        self.llm = llm
    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip()
        image_data = context.get("image_data")
        image_path = context.get("image_path")
        if (image_data or image_path) and self.tool.available():
            out = self.tool.run(image_data=image_data, path=image_path)
            if out.get("ok"):
                info = "Imagem: %sx%s, formato %s, RGB medio %s" % (out.get("width"), out.get("height"), out.get("format"), out.get("mean_rgb"))
                if self.llm:
                    return self.llm.chat([{"role": "system", "content": "Descreva imagens por metadados."}, {"role": "user", "content": info + ". Pergunta: " + prompt}])
                return info
        if self.llm:
            return self.llm.chat([{"role": "system", "content": "Assistente de visao."}, {"role": "user", "content": prompt}])
        return "Envie uma imagem para analise."
