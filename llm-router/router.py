import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RoutingDecision:
    use_external_fallback: bool
    reason: str


class NeuralRouter:
    def __init__(self, policy_path: Path) -> None:
        self.policy_path = policy_path
        self.policy = json.loads(policy_path.read_text(encoding="utf-8"))

    def decide(self) -> RoutingDecision:
        fallback_enabled = bool(
            self.policy.get("fallback", {}).get("external_provider_enabled", False)
        )
        if fallback_enabled:
            return RoutingDecision(
                use_external_fallback=True,
                reason="fallback_explicitly_enabled_by_policy",
            )
        return RoutingDecision(
            use_external_fallback=False,
            reason="local_first_sovereign_policy",
        )

