from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def load_module(module_name: str, file_path: Path):
    spec = spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module {module_name} from {file_path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    model_registry = load_module("model_registry", root / "llm-core" / "model_registry.py")
    runtime_scheduler = load_module("scheduler", root / "llm-runtime" / "scheduler.py")
    guardrails = load_module("guardrails", root / "llm-security" / "guardrails.py")
    inference_engine = load_module("engine", root / "llm-inference" / "engine.py")
    router_module = load_module("router", root / "llm-router" / "router.py")

    registry = model_registry.ModelRegistry()
    registry.register(
        model_registry.ModelSpec(
            model_id="syntexa-transformer-moe-v0",
            family="hybrid-transformer-moe",
            path="/models/syntexa-transformer-moe-v0",
            quantization="fp16",
            context_window=16384,
        )
    )

    scheduler = runtime_scheduler.RuntimeScheduler()
    security = guardrails.SecurityGuardrails()
    engine = inference_engine.SovereignInferenceEngine(registry, scheduler, security)
    router = router_module.NeuralRouter(root / "llm-router" / "routing.policy.json")
    decision = router.decide()
    print(f"[router] external_fallback={decision.use_external_fallback} reason={decision.reason}")

    response = engine.generate("Explique o núcleo soberano da Syntexa.", complexity_score=0.8)
    print(response)


if __name__ == "__main__":
    main()

