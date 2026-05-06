from types import SimpleNamespace
from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from vereda_ai.router.prompt_router import RouteCategory

_EXECUTOR_PATH = Path(__file__).resolve().parents[2] / "vereda_ai" / "agents" / "executor.py"
_SPEC = importlib.util.spec_from_file_location("syntexa_executor_module", _EXECUTOR_PATH)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)
Executor = _MOD.Executor


def test_executor_math_programmatic_verification_ok() -> None:
    ex = Executor(llm=None)
    task = SimpleNamespace(id="t1", description="calcule 2+2", metadata={})
    out = ex.execute_task(task)
    assert out["route"] == "math"
    assert out["ok"] is True
    assert out["programmatic_check"]["status"] in {"ok", "skipped"}


def test_executor_math_programmatic_verification_corrects_wrong_result() -> None:
    ex = Executor(llm=None)
    checked = {"ok": True, "final_output": "Resultado: 2+2 = 5."}
    verified = ex._programmatic_post_verify(
        route=RouteCategory.MATH,
        description="calcule 2+2",
        checked=checked,
    )
    assert verified["ok"] is False
    assert "Correcao numerica" in verified["final_output"]


def test_executor_science_crypto_hash_path() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("gere hash sha256 para este texto")
    assert result["tool"] == "science_tool"
    assert "SHA-256" in result["output"]


def test_executor_science_chemistry_concentration() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("calcule a concentracao molar com 2 mol em 0.5 L")
    assert result["tool"] == "science_tool"
    assert "mol/L" in result["output"]
    assert result["raw"]["domain"] == "chemistry"


def test_executor_science_chemistry_concentration_ml_units() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("calcule concentracao molar para 2 mol em 500 mL")
    assert result["tool"] == "science_tool"
    assert "4.00000000 mol/L" in result["output"]
    assert result["domain"] == "chemistry"


def test_executor_science_biology_gc_content() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("analise DNA ACGTACGTGGGGTTTT")
    assert result["tool"] == "science_tool"
    assert "Conteudo GC" in result["output"]
    assert result["raw"]["domain"] == "biology"


def test_executor_task_output_has_domain() -> None:
    ex = Executor(llm=None)
    task = SimpleNamespace(id="t2", description="engenharia viga 2 3 4 5", metadata={})
    out = ex.execute_task(task)
    assert out["tool_used"] == "science_tool"
    assert out["domain"] == "engineering"


def test_executor_physics_kinetic_energy_with_units() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("calcule energia cinetica para 1200 g e 36 km/h")
    assert result["tool"] == "science_tool"
    assert "60.000000 J" in result["output"]
    assert result["domain"] == "physics"


def test_executor_physics_pressure_normalization_mpa() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("normalizar pressao 2 MPa")
    assert result["tool"] == "science_tool"
    assert "2000000.000000 Pa" in result["output"]
    assert result["domain"] == "physics"


def test_executor_output_includes_confidence() -> None:
    ex = Executor(llm=None)
    task = SimpleNamespace(id="t3", description="calcule 3+5", metadata={})
    out = ex.execute_task(task)
    assert isinstance(out.get("confidence"), dict)
    assert out["confidence"]["band"] in {"high", "medium", "low"}
    assert isinstance(out["confidence"].get("factors"), dict)


def test_executor_chemistry_concentration_normalization_mol_l() -> None:
    ex = Executor(llm=None)
    result = ex._run_science("normalizar concentracao 0.2 mol/L")
    assert result["tool"] == "science_tool"
    assert "0.20000000 mol/L" in result["output"]
    assert result["domain"] == "chemistry"


def test_executor_physics_power_and_energy_wh_normalization() -> None:
    ex = Executor(llm=None)
    power = ex._run_science("normalizar potencia 2.5 kW")
    energy = ex._run_science("normalizar energia 3 kWh")
    assert "2500.000000 W" in power["output"]
    assert "10800000.000000 J" in energy["output"]


def test_confidence_auto_adjust_with_failure_history() -> None:
    conf = Executor._confidence_score(
        primary={"ok": True},
        checked={"self_check": {"status": "ok"}},
        verified={"programmatic_check": {"status": "ok"}},
        security={"allowed": True},
        domain="physics",
        tool="science_tool",
        execution_state={
            "domain_failures": {"physics": 3},
            "tool_failures": {"science_tool": 2},
            "confidence_history": [0.9, 0.86, 0.7, 0.62, 0.55, 0.5],
        },
    )
    assert conf["score"] < 0.9
    assert "domain_failure_penalty" in conf["factors"]
    assert "tool_failure_penalty" in conf["factors"]


def test_adapt_chain_promotes_modular_when_science_degrades() -> None:
    chain = Executor._adapt_chain_by_history(
        base_chain=["science_tool", "modular_reasoning"],
        execution_state={
            "tool_failures": {"science_tool": 3},
            "domain_failures": {"physics": 1, "chemistry": 1},
        },
    )
    assert chain[0] == "modular_reasoning"
    assert "science_tool" in chain


def test_emergency_recovery_hard_fallback_when_modular_empty() -> None:
    ex = Executor(llm=None)

    def _fake_run_modular(description: str, context: dict, tool_name: str) -> dict:
        return {"ok": False, "tool": tool_name, "output": ""}

    ex._run_modular = _fake_run_modular  # type: ignore[method-assign]
    recovered = ex._emergency_recovery(
        description="tarefa sem resposta",
        context={},
        primary={"ok": False, "output": ""},
        checked={"ok": False, "final_output": ""},
        verified={"ok": False, "final_output": ""},
    )
    assert recovered["recovered"] is True
    assert recovered["reason"] == "hard_fallback_message"
    assert "Recuperacao automatica acionada" in recovered["final_output"]


def test_adapt_chain_skips_quarantined_tool() -> None:
    chain = Executor._adapt_chain_by_history(
        base_chain=["science_tool", "modular_reasoning"],
        execution_state={
            "now_ts": 1000.0,
            "tool_runtime": {
                "science_tool": {"quarantined_until": 1100.0},
                "modular_reasoning": {"quarantined_until": 0.0},
            },
        },
    )
    assert "science_tool" not in chain
    assert chain[0] == "modular_reasoning"


def test_tool_priority_score_penalizes_failure_and_latency() -> None:
    fast = Executor._tool_priority_score(
        "modular_reasoning",
        {"tool_runtime": {"modular_reasoning": {"calls": 10, "failures": 1, "avg_duration_ms": 400}}},
    )
    slow = Executor._tool_priority_score(
        "science_tool",
        {"tool_runtime": {"science_tool": {"calls": 10, "failures": 5, "avg_duration_ms": 2800}}},
    )
    assert fast < slow
