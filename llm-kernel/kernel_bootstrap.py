import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class KernelConfig:
    version: str
    mode: str
    external_fallback_enabled: bool
    modules: List[str]


def load_kernel_config(manifest_path: Path) -> KernelConfig:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    sovereignty = raw.get("sovereignty", {})
    return KernelConfig(
        version=str(raw.get("version", "0.0.0")),
        mode=str(sovereignty.get("mode", "strict_local_first")),
        external_fallback_enabled=bool(sovereignty.get("external_fallback_enabled", False)),
        modules=list(raw.get("modules", [])),
    )


def validate_sovereignty(config: KernelConfig) -> Dict[str, str]:
    checks = {
        "mode": "ok" if config.mode == "strict_local_first" else "invalid",
        "fallback": "ok" if not config.external_fallback_enabled else "warning",
        "module_count": "ok" if len(config.modules) >= 18 else "invalid",
    }
    return checks


if __name__ == "__main__":
    manifest = Path(__file__).with_name("kernel.manifest.json")
    cfg = load_kernel_config(manifest)
    result = validate_sovereignty(cfg)
    print(f"[kernel] version={cfg.version} mode={cfg.mode}")
    print(f"[kernel] checks={result}")
