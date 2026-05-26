import json
import re
import time
from typing import Any, Dict, Optional

from vereda_ai.ai.llm_engine import LLMEngine
from vereda_ai.core.logging import get_logger
from vereda_ai.science import CryptoEngine, EngineeringEngine, PhysicsEngine, QuantumEngine, SimulationEngine
from vereda_ai.reasoning import ModularReasoningEngine
from vereda_ai.router.prompt_router import PromptRouter, RouteCategory
from vereda_ai.tools.code_tool import CodeTool
from vereda_ai.tools.image_tool import ImageTool
from vereda_ai.tools.math_tool import MathTool


logger = get_logger(__name__)

_BLOCKED_PATTERNS = (
    r"\brm\s+-rf\b",
    r"\bdel\s+/f\b",
    r"\bshutdown\b",
    r"\bformat\s+[a-z]:\b",
    r"\bdrop\s+table\b",
    r"\btruncate\s+table\b",
    r"\bsudo\b",
)

_SENSITIVE_PATTERNS = (
    r"\btransferencia banc",
    r"\bpix\b",
    r"\bpagamento\b",
    r"\bexcluir usuario\b",
    r"\bapagar conta\b",
    r"\bdeploy em producao\b",
    r"\brotate key\b",
    r"\bchave privada\b",
)

_SCIENCE_KEYWORDS = (
    "fisica",
    "física",
    "forca",
    "força",
    "energia cinetica",
    "energia cinética",
    "newton",
    "engenharia",
    "viga",
    "deflexao",
    "deflexão",
    "momento fletor",
    "simulacao",
    "simulação",
    "termica",
    "térmica",
    "fluidos",
    "quantum",
    "quantica",
    "quântica",
    "qubit",
    "bell",
    "crypto",
    "criptografia",
    "rsa",
    "ecc",
    "sha256",
)

_SCIENCE_DOMAIN_KEYWORDS = {
    "physics": ("fisica", "física", "newton", "forca", "força", "energia", "calor", "fluxo", "pressao", "pressão", "potencia", "potência", "watt", "kw", "kwh", "mpa", "kpa", "bar", "atm"),
    "engineering": ("engenharia", "viga", "deflexao", "deflexão", "momento fletor", "estrutura"),
    "quantum": ("quantum", "qubit", "bell", "quantica", "quântica"),
    "crypto": ("crypto", "criptografia", "rsa", "ecc", "sha256", "hash"),
    "chemistry": ("quimica", "química", "mol", "molar", "concentracao", "concentração", "ideal gas", "pv=nrt"),
    "biology": ("biologia", "dna", "rna", "genetica", "genética", "celula", "célula", "doubling time"),
    "simulation": ("simulacao", "simulação", "modelagem", "modelo"),
}

_UNIT_ALIASES = {
    "kg": ("kg",),
    "g": ("g", "grama", "gramas"),
    "mg": ("mg",),
    "m/s": ("m/s", "mps"),
    "km/h": ("km/h", "kmh"),
    "n": ("n", "newton", "newtons"),
    "kn": ("kn",),
    "j": ("j", "joule", "joules"),
    "kj": ("kj",),
    "mj": ("mj",),
    "pa": ("pa",),
    "kpa": ("kpa",),
    "mpa": ("mpa",),
    "bar": ("bar",),
    "atm": ("atm",),
    "l": ("l", "litro", "litros"),
    "ml": ("ml",),
    "m3": ("m3", "m^3"),
    "mol": ("mol",),
    "mmol": ("mmol",),
    "mol/l": ("mol/l", "mol l", "molar", "m"),
    "mmol/l": ("mmol/l", "mmol l"),
    "n*m": ("n*m", "n·m", "nm"),
    "w": ("w", "watt", "watts"),
    "kw": ("kw",),
    "wh": ("wh",),
    "kwh": ("kwh",),
    "k": ("k", "kelvin"),
    "c": ("c", "°c", "celsius"),
}

_UNIT_TO_SI = {
    "kg": 1.0,
    "g": 1e-3,
    "mg": 1e-6,
    "m/s": 1.0,
    "km/h": 1.0 / 3.6,
    "n": 1.0,
    "kn": 1000.0,
    "j": 1.0,
    "kj": 1000.0,
    "mj": 1_000_000.0,
    "pa": 1.0,
    "kpa": 1000.0,
    "mpa": 1_000_000.0,
    "bar": 100000.0,
    "atm": 101325.0,
    "l": 1e-3,
    "ml": 1e-6,
    "m3": 1.0,
    "mol": 1.0,
    "mmol": 1e-3,
    "mol/l": 1000.0,  # mol/L -> mol/m3
    "mmol/l": 1.0,  # mmol/L -> mol/m3
    "n*m": 1.0,
    "w": 1.0,
    "kw": 1000.0,
    "wh": 3600.0,  # Wh -> J
    "kwh": 3_600_000.0,  # kWh -> J
}


class Executor:
    """
    Executor orientado a ferramentas reais + auto-verificacao por etapa.
    """

    def __init__(
        self,
        llm: Optional[LLMEngine] = None,
        modular_engine: Optional[ModularReasoningEngine] = None,
    ) -> None:
        self.llm = llm
        self.router = PromptRouter()
        self.math_tool = MathTool()
        self.code_tool = CodeTool()
        self.image_tool = ImageTool()
        self.physics_engine = PhysicsEngine()
        self.engineering_engine = EngineeringEngine()
        self.simulation_engine = SimulationEngine()
        self.quantum_engine = QuantumEngine()
        self.crypto_engine = CryptoEngine()
        self.modular_engine = modular_engine or ModularReasoningEngine(llm=llm)

    def execute_task(self, task: Any) -> Any:
        description = (getattr(task, "description", "") or "").strip()
        if not description:
            return {"ok": False, "error": "Tarefa sem descricao.", "task_id": getattr(task, "id", None)}

        context: Dict[str, Any] = dict(getattr(task, "metadata", {}) or {})
        context["task_description_hint"] = description
        route = self.router.route(description)
        logger.info("Executando tarefa %s na rota %s", getattr(task, "id", "n/a"), route.value)

        security = self._guardrail_check(description, context)
        if not security.get("allowed", False):
            return {
                "ok": False,
                "task_id": getattr(task, "id", None),
                "task": description,
                "route": route.value,
                "tool_used": "guardrail",
                "primary_output": "",
                "self_check": {"status": "skipped", "reason": "blocked_by_guardrail"},
                "final_output": security.get("message", "Etapa bloqueada por seguranca."),
                "security": security,
            }

        primary = self._execute_chain(route=route, description=description, context=context)
        checked = self._self_check_and_fix(route=route, description=description, primary=primary, context=context)
        verified = self._programmatic_post_verify(route=route, description=description, checked=checked)
        recovered = self._emergency_recovery(description=description, context=context, primary=primary, checked=checked, verified=verified)
        final_output = recovered.get("final_output", verified.get("final_output", checked.get("final_output", primary.get("output", ""))))
        final_ok = bool(verified.get("ok", checked.get("ok", False)) or recovered.get("recovered", False))

        return {
            "ok": final_ok,
            "task_id": getattr(task, "id", None),
            "task": description,
            "route": route.value,
            "tool_used": primary.get("tool"),
            "tool_chain": primary.get("chain", []),
            "attempts": primary.get("attempts", []),
            "domain": primary.get("domain"),
            "primary_output": primary.get("output"),
            "self_check": checked.get("self_check"),
            "programmatic_check": verified.get("programmatic_check"),
            "final_output": final_output,
            "degraded_mode": bool(recovered.get("recovered", False)),
            "recovery": recovered,
            "confidence": self._confidence_score(
                primary=primary,
                checked=checked,
                verified=verified,
                security=security,
                domain=str(primary.get("domain") or "unknown"),
                tool=str(primary.get("tool") or "unknown"),
                execution_state=context.get("execution_state") if isinstance(context.get("execution_state"), dict) else {},
            ),
            "security": security,
        }

    def _execute_chain(
        self,
        route: RouteCategory,
        description: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        chain: list[str] = self._tool_chain_for_route(route, context)
        attempts: list[Dict[str, Any]] = []
        for tool_name in chain:
            started = time.perf_counter()
            if tool_name == "math_tool":
                result = self._run_math(description)
            elif tool_name == "code_tool":
                result = self._run_code(description, context)
            elif tool_name == "image_tool":
                result = self._run_vision(description, context)
            elif tool_name == "science_tool":
                result = self._run_science(description)
            else:
                result = self._run_modular(description, context, tool_name=tool_name)
            duration_ms = int((time.perf_counter() - started) * 1000)
            result["chain"] = chain
            result["duration_ms"] = duration_ms
            attempts.append(
                {
                    "tool": tool_name,
                    "ok": bool(result.get("ok", False)),
                    "duration_ms": duration_ms,
                    "output_preview": str(result.get("output", ""))[:220],
                }
            )
            if result.get("ok"):
                result["attempts"] = attempts
                return result
        # nenhuma etapa ok: retorna ultima tentativa
        fallback = attempts[-1] if attempts else {}
        return {
            "ok": False,
            "tool": str(fallback.get("tool", "none")),
            "chain": chain,
            "output": "Nenhuma ferramenta conseguiu concluir a etapa.",
            "attempts": attempts,
        }

    def _tool_chain_for_route(self, route: RouteCategory, context: Dict[str, Any]) -> list[str]:
        execution_state = context.get("execution_state") if isinstance(context.get("execution_state"), dict) else {}
        base_chain: list[str]
        if route == RouteCategory.MATH:
            base_chain = ["math_tool", "science_tool", "modular_reasoning"]
        elif route == RouteCategory.CODE:
            base_chain = ["code_tool", "modular_reasoning"]
        elif route == RouteCategory.VISION:
            base_chain = ["image_tool", "modular_reasoning"]
        elif self._is_science_task(context.get("task_description_hint") or ""):
            base_chain = ["science_tool", "modular_reasoning"]
        elif self._is_science_task(str(execution_state.get("last_output", ""))):
            base_chain = ["science_tool", "modular_reasoning"]
        elif route == RouteCategory.KNOWLEDGE:
            base_chain = ["science_tool", "modular_reasoning", "modular_reasoning_retry"]
        elif route == RouteCategory.CRYPTO:
            base_chain = ["modular_reasoning", "modular_reasoning_retry"]
        elif route == RouteCategory.WEB:
            base_chain = ["modular_reasoning", "modular_reasoning_retry"]
        elif context.get("previous_outputs"):
            base_chain = ["modular_reasoning_retry", "modular_reasoning"]
        else:
            base_chain = ["modular_reasoning"]
        return self._adapt_chain_by_history(base_chain=base_chain, execution_state=execution_state)

    @staticmethod
    def _adapt_chain_by_history(base_chain: list[str], execution_state: Dict[str, Any]) -> list[str]:
        domain_failures = execution_state.get("domain_failures") if isinstance(execution_state, dict) else {}
        tool_failures = execution_state.get("tool_failures") if isinstance(execution_state, dict) else {}
        tool_runtime = execution_state.get("tool_runtime") if isinstance(execution_state, dict) else {}
        now_ts = float(execution_state.get("now_ts", time.time())) if isinstance(execution_state, dict) else time.time()
        chain = list(base_chain)
        # Se science falhou muito no fluxo, prioriza reasoning para não travar a cadeia.
        science_failures = int((tool_failures or {}).get("science_tool", 0) or 0) if isinstance(tool_failures, dict) else 0
        broad_domain_failures = 0
        if isinstance(domain_failures, dict):
            broad_domain_failures = sum(int(v or 0) for v in domain_failures.values())
        if science_failures >= 2 and "science_tool" in chain and "modular_reasoning" in chain:
            chain = [t for t in chain if t != "modular_reasoning"]
            chain.insert(0, "modular_reasoning")
        if broad_domain_failures >= 3 and "modular_reasoning_retry" not in chain:
            chain.append("modular_reasoning_retry")
        # Quarentena temporaria de ferramentas instaveis.
        filtered: list[str] = []
        for item in chain:
            stats = (tool_runtime or {}).get(item, {}) if isinstance(tool_runtime, dict) else {}
            quarantined_until = float((stats or {}).get("quarantined_until", 0.0) or 0.0) if isinstance(stats, dict) else 0.0
            if quarantined_until > now_ts:
                continue
            filtered.append(item)
        if filtered:
            chain = filtered
        # Roteamento dinamico por SLO (falha + latencia).
        chain = sorted(
            chain,
            key=lambda item: Executor._tool_priority_score(item, execution_state),
        )
        dedup: list[str] = []
        seen: set[str] = set()
        for item in chain:
            if item in seen:
                continue
            dedup.append(item)
            seen.add(item)
        return dedup

    @staticmethod
    def _tool_priority_score(tool: str, execution_state: Dict[str, Any]) -> float:
        tool_runtime = execution_state.get("tool_runtime") if isinstance(execution_state, dict) else {}
        stats = (tool_runtime or {}).get(tool, {}) if isinstance(tool_runtime, dict) else {}
        if not isinstance(stats, dict):
            return 0.5
        calls = max(1, int(stats.get("calls", 0) or 0))
        failures = int(stats.get("failures", 0) or 0)
        avg_duration_ms = float(stats.get("avg_duration_ms", 0.0) or 0.0)
        failure_rate = failures / calls
        latency_norm = min(1.0, avg_duration_ms / 4000.0)
        return (failure_rate * 0.7) + (latency_norm * 0.3)

    def _guardrail_check(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = (description or "").strip()
        lowered = text.lower()
        for pat in _BLOCKED_PATTERNS:
            if re.search(pat, lowered, flags=re.IGNORECASE):
                return {
                    "allowed": False,
                    "level": "high",
                    "reason": "destructive_pattern",
                    "pattern": pat,
                    "message": "Etapa bloqueada por seguranca operacional (comando destrutivo detectado).",
                }
        if not bool(context.get("is_admin", False)) and len(text) > 6000:
            return {
                "allowed": False,
                "level": "medium",
                "reason": "step_too_large_for_non_admin",
                "message": "Etapa grande demais para perfil atual; reduza escopo da instrucao.",
            }
        sensitive_match = None
        for pat in _SENSITIVE_PATTERNS:
            if re.search(pat, lowered, flags=re.IGNORECASE):
                sensitive_match = pat
                break
        if sensitive_match:
            approved = bool(context.get("allow_sensitive_actions", False))
            if not approved:
                return {
                    "allowed": False,
                    "level": "high",
                    "reason": "pending_sensitive_approval",
                    "pattern": sensitive_match,
                    "message": (
                        "Etapa sensivel detectada e bloqueada ate aprovacao explicita "
                        "(allow_sensitive_actions=true)."
                    ),
                }
            return {
                "allowed": True,
                "level": "high",
                "reason": "approved_sensitive_action",
                "pattern": sensitive_match,
            }
        return {"allowed": True, "level": "none"}

    def _run_math(self, description: str) -> Dict[str, Any]:
        if not self.math_tool.available():
            return self._run_modular(description, {}, tool_name="modular_reasoning")
        expression = self._extract_math_expression(description)
        result = self.math_tool.run(expression=expression)
        if result.get("ok"):
            output = "Resultado: %s = %s." % (result.get("expression"), result.get("result"))
            return {"ok": True, "tool": "math_tool", "output": output, "raw": result}
        fallback = self._run_modular(description, {}, tool_name="modular_reasoning")
        fallback["raw"] = {"math_error": result.get("error")}
        return fallback

    def _run_code(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        snippet = self._extract_python_snippet(description) or (context.get("code") or "").strip()
        if snippet:
            result = self.code_tool.run(code=snippet, timeout_seconds=8)
            if result.get("ok"):
                stdout = result.get("stdout") or "(sem saida)"
                return {
                    "ok": True,
                    "tool": "code_tool",
                    "output": "Snippet executado com sucesso. Saida:\n%s" % stdout,
                    "raw": result,
                }
            return {
                "ok": False,
                "tool": "code_tool",
                "output": "Falha ao executar snippet: %s" % (result.get("error") or result.get("stderr") or "erro desconhecido"),
                "raw": result,
            }
        return self._run_modular(description, context, tool_name="modular_reasoning")

    def _run_science(self, description: str) -> Dict[str, Any]:
        text = (description or "").strip().lower()
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", description)]
        domain = self._detect_science_domain(description)
        try:
            if domain == "physics" and ("newton" in text or "forca" in text or "força" in text):
                mass_kg = self._extract_si_quantity(text, ("kg", "g", "mg"), default=(nums[0] if len(nums) >= 1 else None))
                accel = self._extract_acceleration_ms2(text, default=(nums[1] if len(nums) >= 2 else None))
                if mass_kg is not None and accel is not None:
                    force = self.physics_engine.newton_second_law(mass_kg, accel)
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "F = m*a => %.6f N (m=%.6f kg, a=%.6f m/s²)." % (force, mass_kg, accel),
                        "raw": {"domain": "physics", "formula": "F=m*a", "result": force},
                        "domain": "physics",
                    }
            if domain == "physics" and ("energia" in text and ("cinetica" in text or "cinética" in text)):
                mass_kg = self._extract_si_quantity(text, ("kg", "g", "mg"), default=(nums[0] if len(nums) >= 1 else None))
                speed_ms = self._extract_si_quantity(text, ("m/s", "km/h"), default=(nums[1] if len(nums) >= 2 else None))
                if mass_kg is not None and speed_ms is not None:
                    ke = self.physics_engine.kinetic_energy(mass_kg, speed_ms)
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Ec = 0.5*m*v^2 => %.6f J (m=%.6f kg, v=%.6f m/s)." % (ke, mass_kg, speed_ms),
                        "raw": {"domain": "physics", "formula": "Ec=0.5*m*v^2", "result": ke},
                        "domain": "physics",
                    }
            if domain == "physics" and ("pressao" in text or "pressão" in text or "pa" in text or "bar" in text or "atm" in text):
                pressure_pa = self._extract_si_quantity(text, ("pa", "kpa", "mpa", "bar", "atm"))
                if pressure_pa is not None:
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Pressao normalizada: %.6f Pa." % pressure_pa,
                        "raw": {"domain": "physics", "formula": "pressure_unit_normalization", "result": pressure_pa},
                        "domain": "physics",
                    }
            if domain == "physics" and ("energia" in text or "j" in text or "joule" in text):
                energy_j = self._extract_si_quantity(text, ("j", "kj", "mj"))
                if energy_j is not None:
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Energia normalizada: %.6f J." % energy_j,
                        "raw": {"domain": "physics", "formula": "energy_unit_normalization", "result": energy_j},
                        "domain": "physics",
                    }
            if domain == "physics" and ("potencia" in text or "potência" in text or "watt" in text or " kw" in text):
                power_w = self._extract_si_quantity(text, ("w", "kw"))
                if power_w is not None:
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Potencia normalizada: %.6f W." % power_w,
                        "raw": {"domain": "physics", "formula": "power_unit_normalization", "result": power_w},
                        "domain": "physics",
                    }
            if domain == "physics" and ("kwh" in text or "wh" in text):
                energy_j = self._extract_si_quantity(text, ("kwh", "wh"))
                if energy_j is not None:
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Energia normalizada (de Wh): %.6f J." % energy_j,
                        "raw": {"domain": "physics", "formula": "energy_wh_to_joule", "result": energy_j},
                        "domain": "physics",
                    }
            if domain == "physics" and ("torque" in text or "n*m" in text or "n·m" in text or " nm" in text):
                torque_nm = self._extract_si_quantity(text, ("n*m",))
                if torque_nm is not None:
                    return {
                        "ok": True,
                        "tool": "science_tool",
                        "output": "Torque normalizado: %.6f N*m." % torque_nm,
                        "raw": {"domain": "physics", "formula": "torque_unit_normalization", "result": torque_nm},
                        "domain": "physics",
                    }
            if domain == "engineering" and "viga" in text and len(nums) >= 4:
                beam = self.engineering_engine.cantilever_beam_point_load(
                    length=nums[0],
                    load=nums[1],
                    e_modulus=nums[2],
                    inertia=nums[3],
                )
                return {
                    "ok": True,
                    "tool": "science_tool",
                    "output": (
                        "Viga em balanco: Mmax=%.6f, deflexao_max=%.12f "
                        "(L=%.6f, P=%.6f, E=%.6f, I=%.6f)."
                    )
                    % (beam.max_moment, beam.max_deflection, nums[0], nums[1], nums[2], nums[3]),
                    "raw": {
                        "domain": "engineering",
                        "max_moment": beam.max_moment,
                        "max_deflection": beam.max_deflection,
                    },
                    "domain": "engineering",
                }
            if domain == "quantum":
                shots = int(nums[0]) if nums else 1024
                shots = max(64, min(8192, shots))
                if self.quantum_engine.available:
                    bell = self.quantum_engine.bell_state(shots=shots)
                    return {
                        "ok": bool(bell),
                        "tool": "science_tool",
                        "output": "Simulacao quantica (Bell, shots=%s): %s" % (shots, bell),
                        "raw": {"domain": "quantum", "shots": shots, "counts": bell},
                        "domain": "quantum",
                    }
                return {
                    "ok": False,
                    "tool": "science_tool",
                    "output": "QuantumEngine indisponivel (instale qiskit/qiskit-aer).",
                    "raw": {"domain": "quantum", "available": False},
                    "domain": "quantum",
                }
            if domain == "crypto" and ("sha256" in text or "hash" in text):
                msg = description.encode("utf-8")
                digest = self.crypto_engine.sha256(msg)
                return {
                    "ok": True,
                    "tool": "science_tool",
                    "output": "SHA-256 calculado: %s" % digest,
                    "raw": {"domain": "crypto", "sha256": digest},
                    "domain": "crypto",
                }
            if domain == "crypto" and "rsa" in text and "key" in text:
                keys = self.crypto_engine.rsa_keypair(bits=2048)
                if not keys:
                    return {
                        "ok": False,
                        "tool": "science_tool",
                        "output": "CryptoEngine sem backend completo para gerar chave RSA.",
                        "raw": {"domain": "crypto", "has_cryptography": self.crypto_engine.has_cryptography},
                        "domain": "crypto",
                    }
                pub, _priv = keys
                return {
                    "ok": True,
                    "tool": "science_tool",
                    "output": "Par de chaves RSA gerado com sucesso (public key disponível).",
                    "raw": {"domain": "crypto", "public_key_prefix": pub[:120]},
                    "domain": "crypto",
                }
            if domain == "chemistry":
                chem = self._run_chemistry(description, nums)
                if chem.get("ok"):
                    return chem
            if domain == "biology":
                bio = self._run_biology(description, nums)
                if bio.get("ok"):
                    return bio
            if domain == "simulation":
                sim = self.simulation_engine.run({"description": description})
                return {
                    "ok": bool(sim.get("ok", False)),
                    "tool": "science_tool",
                    "output": "SimulationEngine: %s" % sim,
                    "raw": sim,
                    "domain": "simulation",
                }
        except Exception as exc:
            return {"ok": False, "tool": "science_tool", "output": "Falha em science_tool: %s" % exc}
        return {
            "ok": False,
            "tool": "science_tool",
            "output": "Sem parametros suficientes para calculo cientifico.",
            "raw": {"domain": domain},
            "domain": domain,
        }

    def _run_chemistry(self, description: str, nums: list[float]) -> Dict[str, Any]:
        text = (description or "").lower()
        n_mol = self._extract_si_quantity(text, ("mol", "mmol"), default=(nums[0] if len(nums) >= 1 else None))
        vol_l = self._extract_volume_liters(text, default=(nums[1] if len(nums) >= 2 else None))
        conc_mol_m3 = self._extract_si_quantity(text, ("mol/l", "mmol/l"))
        if ("concentr" in text or "molar" in text) and conc_mol_m3 is not None:
            conc_mol_l = conc_mol_m3 / 1000.0
            return {
                "ok": True,
                "tool": "science_tool",
                "output": "Concentracao normalizada: %.8f mol/L." % conc_mol_l,
                "raw": {"domain": "chemistry", "formula": "concentration_unit_normalization", "result": conc_mol_l},
                "domain": "chemistry",
            }
        # Concentração molar: C = n / V
        if ("concentr" in text or "molar" in text) and n_mol is not None and vol_l is not None and vol_l != 0:
            c = n_mol / vol_l
            return {
                "ok": True,
                "tool": "science_tool",
                "output": "Concentracao molar C=n/V => %.8f mol/L (n=%.6f mol, V=%.6f L)." % (c, n_mol, vol_l),
                "raw": {"domain": "chemistry", "formula": "C=n/V", "result": c},
                "domain": "chemistry",
            }
        # Gás ideal: P = nRT/V (usa SI simplificado)
        temp_k = self._extract_temperature_kelvin(text, default=(nums[1] if len(nums) >= 2 else None))
        volume_m3 = self._extract_volume_m3(text, default=(nums[2] if len(nums) >= 3 else None))
        if ("ideal gas" in text or "pv=nrt" in text or "gas ideal" in text) and n_mol is not None and temp_k is not None and volume_m3 is not None and volume_m3 != 0:
            pressure = n_mol * 8.314462618 * temp_k / volume_m3
            return {
                "ok": True,
                "tool": "science_tool",
                "output": "Gas ideal: P=nRT/V => %.8f Pa (n=%.6f, T=%.6fK, V=%.6fm^3)." % (
                    pressure,
                    n_mol,
                    temp_k,
                    volume_m3,
                ),
                "raw": {"domain": "chemistry", "formula": "P=nRT/V", "result": pressure},
                "domain": "chemistry",
            }
        return {"ok": False, "tool": "science_tool", "output": "Parametros insuficientes para química."}

    def _run_biology(self, description: str, nums: list[float]) -> Dict[str, Any]:
        text = (description or "").lower()
        # Crescimento exponencial por tempo de duplicação: N = N0 * 2^(t/g)
        if ("duplic" in text or "doubling" in text or "crescimento" in text) and len(nums) >= 3 and nums[2] != 0:
            n0, t_total, g = nums[0], nums[1], nums[2]
            n_final = n0 * (2 ** (t_total / g))
            return {
                "ok": True,
                "tool": "science_tool",
                "output": "Crescimento celular: N=N0*2^(t/g) => %.8f (N0=%.6f, t=%.6f, g=%.6f)." % (
                    n_final,
                    n0,
                    t_total,
                    g,
                ),
                "raw": {"domain": "biology", "formula": "N=N0*2^(t/g)", "result": n_final},
                "domain": "biology",
            }
        # Conteúdo GC em sequência de DNA no texto
        dna_match = re.search(r"\b[ACGT]{10,}\b", description.upper())
        if dna_match:
            seq = dna_match.group(0)
            gc = sum(1 for ch in seq if ch in {"G", "C"})
            gc_pct = (gc / len(seq)) * 100.0
            return {
                "ok": True,
                "tool": "science_tool",
                "output": "Conteudo GC = %.4f%% (GC=%s, len=%s)." % (gc_pct, gc, len(seq)),
                "raw": {"domain": "biology", "formula": "GC%", "result": gc_pct},
                "domain": "biology",
            }
        return {"ok": False, "tool": "science_tool", "output": "Parametros insuficientes para biologia."}

    def _run_vision(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        image_data = context.get("image_data")
        image_path = context.get("image_path")
        if (image_data or image_path) and self.image_tool.available():
            result = self.image_tool.run(image_data=image_data, path=image_path)
            if result.get("ok"):
                return {
                    "ok": True,
                    "tool": "image_tool",
                    "output": "Analise de imagem concluida: %s" % result,
                    "raw": result,
                }
            return {
                "ok": False,
                "tool": "image_tool",
                "output": "Falha na analise de imagem: %s" % result.get("error", "erro desconhecido"),
                "raw": result,
            }
        return self._run_modular(description, context, tool_name="modular_reasoning")

    def _run_modular(self, description: str, context: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        try:
            max_tokens = self._max_tokens_for_context(context)
            output = self.modular_engine.process(
                prompt=description,
                user_id=str(context.get("user_id", "agent-system")),
                history=self._build_history_with_state(context),
                knowledge_snippets=context.get("knowledge_snippets") or [],
                memory_snippets=context.get("memory_snippets") or [],
                image_data=context.get("image_data"),
                image_path=context.get("image_path"),
            )
            if self.llm and isinstance(output, str) and len(output) > max_tokens * 6:
                output = output[: max_tokens * 6].rstrip() + "\n[resposta truncada pelo orçamento de etapa]"
            return {"ok": True, "tool": tool_name, "output": output}
        except Exception as exc:
            logger.exception("Falha no ModularReasoningEngine: %s", exc)
            return {"ok": False, "tool": tool_name, "output": "Erro de execucao: %s" % exc}

    def _emergency_recovery(
        self,
        description: str,
        context: Dict[str, Any],
        primary: Dict[str, Any],
        checked: Dict[str, Any],
        verified: Dict[str, Any],
    ) -> Dict[str, Any]:
        final_output = str(verified.get("final_output", checked.get("final_output", primary.get("output", ""))) or "").strip()
        already_ok = bool(verified.get("ok", checked.get("ok", False)))
        if already_ok and final_output:
            return {"recovered": False, "final_output": final_output, "reason": "not_needed"}
        repair_prompt = (
            "Recupere esta etapa com resposta util, objetiva e segura.\n"
            "Tarefa original: %s\n"
            "Saida primaria: %s\n"
            "Saida verificada: %s\n"
            "Forneca resposta final robusta e, se houver incerteza, traga premissas e proximo passo."
        ) % (
            description,
            str(primary.get("output", ""))[:1200],
            str(final_output)[:1200],
        )
        retry = self._run_modular(repair_prompt, context, tool_name="modular_reasoning_recovery")
        recovered_output = str(retry.get("output", "") or "").strip()
        if recovered_output:
            return {
                "recovered": True,
                "reason": "modular_recovery",
                "tool": "modular_reasoning_recovery",
                "final_output": recovered_output,
                "was_ok_before_recovery": already_ok,
            }
        hard_fallback = (
            "Recuperacao automatica acionada: nao foi possivel concluir com alta confianca nesta etapa, "
            "mas o sistema manteve continuidade. Reenvie com mais contexto objetivo para elevar precisao."
        )
        return {
            "recovered": True,
            "reason": "hard_fallback_message",
            "tool": "deterministic_fallback",
            "final_output": hard_fallback,
            "was_ok_before_recovery": already_ok,
        }

    def _self_check_and_fix(
        self,
        route: RouteCategory,
        description: str,
        primary: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        base_output = str(primary.get("output", "")).strip()
        if not self.llm:
            return {
                "ok": bool(primary.get("ok", False)),
                "self_check": {"status": "skipped", "reason": "llm_not_configured"},
                "final_output": base_output,
            }
        if not base_output:
            return {
                "ok": False,
                "self_check": {"status": "failed", "issues": ["saida_vazia"]},
                "final_output": "Etapa sem resposta util.",
            }

        review = self.llm.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Voce valida respostas de um executor de IA composto. "
                        "Retorne SOMENTE JSON com chaves: "
                        "status (ok|needs_fix), issues (lista), fixed_output (string)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Rota: %s\nTarefa: %s\nSaida inicial:\n%s\n\n"
                        "Se estiver incorreta, incompleta ou insegura, corrija no fixed_output."
                    )
                    % (route.value, description, base_output),
                },
            ]
            ,
            max_tokens=self._self_check_max_tokens(context),
        )
        parsed = self._parse_self_check(review)
        if parsed.get("status") == "ok":
            return {"ok": True, "self_check": parsed, "final_output": base_output}

        fixed_output = (parsed.get("fixed_output") or "").strip()
        if fixed_output:
            return {"ok": True, "self_check": parsed, "final_output": fixed_output}

        # Sem correcao direta: tenta reprocessar no engine modular como fallback.
        retry_prompt = (
            "Revise e corrija esta etapa de forma completa e objetiva.\n"
            "Tarefa original: %s\nSaida anterior: %s"
        ) % (description, base_output)
        retry = self._run_modular(retry_prompt, context, tool_name="modular_reasoning_retry")
        final_output = str(retry.get("output", "")).strip() or base_output
        return {
            "ok": bool(retry.get("ok", False)),
            "self_check": parsed,
            "final_output": final_output,
        }

    def _programmatic_post_verify(
        self,
        route: RouteCategory,
        description: str,
        checked: Dict[str, Any],
    ) -> Dict[str, Any]:
        final_output = str(checked.get("final_output", "")).strip()
        if route != RouteCategory.MATH:
            return {"ok": checked.get("ok", False), "final_output": final_output, "programmatic_check": {"status": "skipped"}}
        expr = self._extract_math_expression(description)
        expected = self.math_tool.run(expression=expr) if expr else {"ok": False}
        if not expected.get("ok"):
            return {
                "ok": checked.get("ok", False),
                "final_output": final_output,
                "programmatic_check": {"status": "skipped", "reason": "expression_not_evaluable"},
            }
        found = re.search(r"=\s*(-?\d+(?:\.\d+)?)", final_output)
        if not found:
            return {
                "ok": False,
                "final_output": "Verificacao numerica falhou: resposta sem resultado parseavel. " + final_output,
                "programmatic_check": {"status": "failed", "reason": "missing_numeric_result"},
            }
        got = float(found.group(1))
        exp = float(expected.get("result"))
        ok = abs(got - exp) <= max(1e-6, abs(exp) * 1e-6)
        return {
            "ok": bool(ok),
            "final_output": final_output if ok else ("Correcao numerica: %s = %s." % (expected.get("expression"), exp)),
            "programmatic_check": {
                "status": "ok" if ok else "failed",
                "expected": exp,
                "got": got,
                "expression": expected.get("expression"),
            },
        }

    @staticmethod
    def _max_tokens_for_context(context: Dict[str, Any]) -> int:
        raw = int(context.get("max_tokens", 0) or 0)
        if bool(context.get("is_admin", False)):
            cap = 32768
            return max(2048, min(cap, raw or 16384))
        plan = str(context.get("subscription_plan", "free") or "free").strip().lower()
        cap_by_plan = {
            "master": 8192,
            "gov": 8192,
            "government": 8192,
            "medium": 6144,
            "basic": 4096,
            "free": 3072,
            "anon": 2048,
        }
        cap = cap_by_plan.get(plan, 4096)
        return max(512, min(cap, raw or cap))

    @staticmethod
    def _self_check_max_tokens(context: Dict[str, Any]) -> int:
        base = Executor._max_tokens_for_context(context)
        return max(256, min(2048 if not context.get("is_admin") else 4096, base // 2))

    @staticmethod
    def _build_history_with_state(context: Dict[str, Any]) -> list[dict[str, Any]]:
        history = list(context.get("history") or [])
        state = context.get("execution_state") or {}
        facts = list(state.get("facts", []))
        if facts:
            history.append(
                {
                    "role": "system",
                    "content": "Contexto de etapas anteriores:\n- " + "\n- ".join(facts[-5:]),
                }
            )
        last_output = str(state.get("last_output", "") or "").strip()
        if last_output:
            history.append(
                {
                    "role": "system",
                    "content": "Ultimo resultado da cadeia:\n%s" % last_output[:1200],
                }
            )
        return history

    @staticmethod
    def _extract_math_expression(description: str) -> str:
        text = (description or "").strip()
        lowered = text.lower()
        for prefix in ("calcule", "calcular", "quanto e", "quanto e?", "resolva", "equacao"):
            if lowered.startswith(prefix):
                return text[len(prefix):].strip().rstrip("?.,;")
        return text.rstrip("?.,;")

    @staticmethod
    def _extract_python_snippet(description: str) -> str:
        match = re.search(r"```python\s*(.*?)```", description, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _is_science_task(text: str) -> bool:
        lowered = (text or "").lower()
        return any(k in lowered for k in _SCIENCE_KEYWORDS)

    @staticmethod
    def _detect_science_domain(text: str) -> str:
        lowered = (text or "").lower()
        for domain, kws in _SCIENCE_DOMAIN_KEYWORDS.items():
            if any(k in lowered for k in kws):
                return domain
        return "simulation"

    @staticmethod
    def _extract_value_with_unit(text: str, units: tuple[str, ...], default: Optional[float] = None) -> Optional[float]:
        for unit in units:
            m = re.search(r"(-?\d+(?:\.\d+)?)\s*%s\b" % re.escape(unit), text, flags=re.IGNORECASE)
            if m:
                return float(m.group(1))
        return default

    @staticmethod
    def _extract_volume_liters(text: str, default: Optional[float] = None) -> Optional[float]:
        m3 = Executor._extract_si_quantity(text, ("m3",))
        if m3 is not None:
            return m3 * 1000.0
        raw = Executor._extract_raw_unit_value(text, ("l", "ml"))
        if raw is not None:
            value, unit = raw
            if unit == "ml":
                return value / 1000.0
            return value
        return default

    @staticmethod
    def _extract_volume_m3(text: str, default: Optional[float] = None) -> Optional[float]:
        m_m3 = Executor._extract_si_quantity(text, ("m3",))
        if m_m3 is not None:
            return m_m3
        liters = Executor._extract_volume_liters(text)
        if liters is not None:
            return liters / 1000.0
        return default

    @staticmethod
    def _extract_temperature_kelvin(text: str, default: Optional[float] = None) -> Optional[float]:
        raw = Executor._extract_raw_unit_value(text, ("k", "c"))
        if raw is not None:
            value, unit = raw
            if unit == "c":
                return value + 273.15
            return value
        return default

    @staticmethod
    def _extract_acceleration_ms2(text: str, default: Optional[float] = None) -> Optional[float]:
        m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*(?:m/s2|m/s\^2|m/s²)", text, flags=re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
        return default

    @staticmethod
    def _extract_raw_unit_value(text: str, units: tuple[str, ...]) -> Optional[tuple[float, str]]:
        normalized = (text or "").lower()
        for canonical in units:
            aliases = _UNIT_ALIASES.get(canonical, (canonical,))
            for alias in aliases:
                pattern = r"(-?\d+(?:[.,]\d+)?)\s*%s\b" % re.escape(alias)
                m = re.search(pattern, normalized, flags=re.IGNORECASE)
                if m:
                    return float(m.group(1).replace(",", ".")), canonical
        return None

    @staticmethod
    def _extract_si_quantity(text: str, units: tuple[str, ...], default: Optional[float] = None) -> Optional[float]:
        raw = Executor._extract_raw_unit_value(text, units)
        if raw is None:
            return default
        value, canonical = raw
        factor = _UNIT_TO_SI.get(canonical)
        if factor is None:
            return default
        return value * factor

    @staticmethod
    def _confidence_score(
        primary: Dict[str, Any],
        checked: Dict[str, Any],
        verified: Dict[str, Any],
        security: Dict[str, Any],
        domain: str,
        tool: str,
        execution_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        score = 0.35
        factors: Dict[str, float] = {"base": 0.35}
        if bool(primary.get("ok", False)):
            score += 0.25
            factors["primary_ok"] = 0.25
        self_check = checked.get("self_check") if isinstance(checked, dict) else {}
        status = str((self_check or {}).get("status") or "")
        if status == "ok":
            score += 0.2
            factors["self_check_ok"] = 0.2
        elif status == "needs_fix":
            score -= 0.1
            factors["self_check_penalty"] = -0.1
        prog = verified.get("programmatic_check") if isinstance(verified, dict) else {}
        pstatus = str((prog or {}).get("status") or "")
        if pstatus == "ok":
            score += 0.2
            factors["programmatic_ok"] = 0.2
        elif pstatus == "failed":
            score -= 0.25
            factors["programmatic_penalty"] = -0.25
        if not bool(security.get("allowed", True)):
            score = min(score, 0.15)
            factors["security_cap"] = -0.2
        domain_boost = {
            "math": 0.05 if pstatus == "ok" else 0.0,
            "physics": 0.03 if pstatus in {"ok", "skipped"} else 0.0,
            "chemistry": 0.03 if status == "ok" else 0.0,
            "engineering": 0.02 if status == "ok" else 0.0,
            "crypto": 0.02 if status == "ok" else 0.0,
        }.get(domain, 0.0)
        score += domain_boost
        if domain_boost:
            factors["domain_bonus"] = domain_boost
        # Autoajuste por historico da propria cadeia (falhas e tendencia de confianca)
        domain_failures = execution_state.get("domain_failures") if isinstance(execution_state, dict) else {}
        tool_failures = execution_state.get("tool_failures") if isinstance(execution_state, dict) else {}
        domain_fail_count = int((domain_failures or {}).get(domain, 0) or 0) if isinstance(domain_failures, dict) else 0
        tool_fail_count = int((tool_failures or {}).get(tool, 0) or 0) if isinstance(tool_failures, dict) else 0
        domain_penalty = min(0.18, domain_fail_count * 0.03)
        tool_penalty = min(0.12, tool_fail_count * 0.02)
        if domain_penalty > 0:
            score -= domain_penalty
            factors["domain_failure_penalty"] = -domain_penalty
        if tool_penalty > 0:
            score -= tool_penalty
            factors["tool_failure_penalty"] = -tool_penalty
        confidence_history = execution_state.get("confidence_history") if isinstance(execution_state, dict) else None
        if isinstance(confidence_history, list) and len(confidence_history) >= 4:
            hist = [float(v) for v in confidence_history[-8:] if isinstance(v, (int, float))]
            if len(hist) >= 4:
                mid = len(hist) // 2
                first = sum(hist[:mid]) / max(1, mid)
                second = sum(hist[mid:]) / max(1, len(hist) - mid)
                drift = second - first
                if drift < -0.08:
                    score -= 0.06
                    factors["negative_confidence_drift"] = -0.06
                elif drift > 0.08:
                    score += 0.03
                    factors["positive_confidence_drift"] = 0.03
        score = max(0.0, min(0.99, score))
        band = "high" if score >= 0.8 else ("medium" if score >= 0.55 else "low")
        return {
            "score": round(score, 4),
            "band": band,
            "domain": domain,
            "tool": tool,
            "domain_score": round(score, 4),
            "factors": factors,
        }

    @staticmethod
    def _parse_self_check(content: str) -> Dict[str, Any]:
        raw = (content or "").strip()
        if not raw:
            return {"status": "needs_fix", "issues": ["empty_self_check"], "fixed_output": ""}
        # Tenta parse direto; se falhar, extrai primeiro bloco JSON.
        for candidate in (raw, Executor._extract_json_object(raw)):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
                status = data.get("status", "needs_fix")
                issues = data.get("issues", [])
                fixed_output = data.get("fixed_output", "")
                if status not in {"ok", "needs_fix"}:
                    status = "needs_fix"
                if not isinstance(issues, list):
                    issues = [str(issues)]
                return {"status": status, "issues": issues, "fixed_output": str(fixed_output or "")}
            except Exception:
                continue
        return {"status": "needs_fix", "issues": ["invalid_self_check_format"], "fixed_output": ""}

    @staticmethod
    def _extract_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        return ""

