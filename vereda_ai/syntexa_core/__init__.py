"""Núcleo proprietário Syntexa (Fase 2): Foundation Model Soberana."""

from vereda_ai.syntexa_core.hybrid_engine import generate_reply, native_embed
from vereda_ai.syntexa_core.model_registry import get_registry

# Foundation Model exports
from vereda_ai.syntexa_core.foundation_model import (
    SyntexaFoundationModel,
    SyntexaFoundationConfig,
)
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer
from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig
from vereda_ai.syntexa_core.foundation_runtime import (
    SyntexaFoundationRuntime,
    get_foundation_runtime,
    foundation_generate,
    foundation_generate_stream,
    is_foundation_available,
)
from vereda_ai.syntexa_core.sovereign_guard import (
    SovereignGuard,
    SovereignGuardViolation,
    guard_runtime,
    quick_check,
)
from vereda_ai.syntexa_core.admin_control import (
    authenticate_admin,
    logout_admin,
    is_admin_active,
    is_root_override,
    can_bypass_guard,
    set_dev_mode,
    set_production_mode,
    set_maintenance_mode,
    enable_root_override,
    disable_root_override,
    get_runtime_state,
    require_admin,
    root_override,
    production_guard,
    dev_or_admin,
    AdminSession,
)

__all__ = [
    "generate_reply",
    "native_embed",
    "get_registry",
    # Foundation Model
    "SyntexaFoundationModel",
    "SyntexaFoundationConfig",
    "SyntexaFoundationTokenizer",
    "SyntexaInferenceEngine",
    "SyntexaFoundationTrainer",
    "TrainingConfig",
    "SyntexaFoundationRuntime",
    "get_foundation_runtime",
    "foundation_generate",
    "foundation_generate_stream",
    "is_foundation_available",
    # Governança
    "SovereignGuard",
    "SovereignGuardViolation",
    "guard_runtime",
    "quick_check",
    # Admin Root Control
    "authenticate_admin",
    "logout_admin",
    "is_admin_active",
    "is_root_override",
    "can_bypass_guard",
    "set_dev_mode",
    "set_production_mode",
    "set_maintenance_mode",
    "enable_root_override",
    "disable_root_override",
    "get_runtime_state",
    "require_admin",
    "root_override",
    "production_guard",
    "dev_or_admin",
    "AdminSession",
]
