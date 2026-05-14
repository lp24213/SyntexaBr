from dataclasses import dataclass


BLOCK_PATTERNS = (
    "ignore previous instructions",
    "disable safety",
    "bypass jailbreak",
)


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
    sanitized_prompt: str


class SecurityGuardrails:
    def inspect_prompt(self, prompt: str) -> GuardrailResult:
        low = prompt.lower()
        for pattern in BLOCK_PATTERNS:
            if pattern in low:
                return GuardrailResult(
                    allowed=False,
                    reason=f"blocked_pattern:{pattern}",
                    sanitized_prompt="",
                )
        sanitized = prompt.replace("\x00", " ").strip()
        return GuardrailResult(allowed=True, reason="ok", sanitized_prompt=sanitized)

