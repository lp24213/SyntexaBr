from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from vereda_backend.core.query_profile import (  # noqa: E402
    analyze_query_profile,
    build_profile_directives,
)


def test_query_profile_detects_extended_domains() -> None:
    p = analyze_query_profile(
        "Quero análise de biologia molecular, física quântica, política internacional e literatura comparada"
    )
    assert "biologia" in p.domains
    assert "fisica" in p.domains
    assert "politica" in p.domains
    assert "literatura" in p.domains


def test_query_profile_engineering_social_defensive_directive() -> None:
    p = analyze_query_profile("Faça plano de prevenção contra phishing e engenharia social")
    txt = build_profile_directives(p).lower()
    assert "engenharia social" in txt
    assert "enfoque defensivo" in txt
