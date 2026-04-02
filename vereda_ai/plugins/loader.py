# -*- coding: utf-8 -*-
"""Descoberta de agentes e tools nos diretórios. Plugins: adicione arquivos e classes."""
import importlib.util
import os
from pathlib import Path
from typing import Dict, List, Optional, Type

from vereda_ai.agents.base_agent import BaseAgent
from vereda_ai.tools.base_tool import BaseTool


def _load_module_from_file(filepath: Path, package: str):
    spec = importlib.util.spec_from_file_location(package + "." + filepath.stem, filepath)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None


def discover_agents(agents_dir: Optional[str] = None) -> Dict[str, Type[BaseAgent]]:
    """Retorna dict name -> class para cada BaseAgent no diretório."""
    if agents_dir is None:
        agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
    result = {}
    path = Path(agents_dir)
    if not path.exists():
        return result
    for f in path.glob("*.py"):
        if f.name.startswith("_") or f.name == "base_agent.py":
            continue
        mod = _load_module_from_file(f, "vereda_ai.agents")
        if mod:
            for attr in dir(mod):
                cls = getattr(mod, attr)
                if isinstance(cls, type) and issubclass(cls, BaseAgent) and cls is not BaseAgent:
                    result[cls.name] = cls
    return result


def discover_tools(tools_dir: Optional[str] = None) -> Dict[str, Type[BaseTool]]:
    """Retorna dict name -> class para cada BaseTool no diretório."""
    if tools_dir is None:
        tools_dir = os.path.join(os.path.dirname(__file__), "..", "tools")
    result = {}
    path = Path(tools_dir)
    if not path.exists():
        return result
    for f in path.glob("*.py"):
        if f.name.startswith("_") or f.name == "base_tool.py":
            continue
        mod = _load_module_from_file(f, "vereda_ai.tools")
        if mod:
            for attr in dir(mod):
                cls = getattr(mod, attr)
                if isinstance(cls, type) and issubclass(cls, BaseTool) and cls is not BaseTool:
                    result[cls.name] = cls
    return result
