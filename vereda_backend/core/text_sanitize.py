def _bad_score(text: str) -> int:
    t = text or ""
    bad = sum(t.count(x) for x in ("Ã", "Â", "â", "�", "Ð", "þ"))
    weird = sum(1 for ch in t if ord(ch) < 9 or (13 < ord(ch) < 32))
    return bad * 4 + weird


def _latin1_to_utf8(raw: str) -> str:
    """Só aplica correção mojibake típica (UTF-8 lido como Latin-1). Se já há chars > U+00FF, não toca."""
    if not raw:
        return raw
    if any(ord(ch) > 255 for ch in raw):
        return raw
    try:
        return raw.encode("latin1").decode("utf-8")
    except UnicodeDecodeError:
        return raw


def _strip_iso_control_except_newlines(text: str) -> str:
    out: list[str] = []
    for ch in text or "":
        o = ord(ch)
        if ch in "\n\t\r" or o >= 32 or o in (0x85, 0xA0):
            out.append(ch)
    return "".join(out)


def sanitize_for_stream(raw: str) -> str:
    """
    Sanitização segura durante streaming: não aplica heurísticas Latin-1→UTF-8
    (evita cortar emoji/símbolos enquanto o buffer cresce).
    """
    return _normalize_common_pt(_strip_iso_control_except_newlines(str(raw or "")))


def fix_text_encoding(raw: str) -> str:
    from vereda_backend.core.text_polish import polish_portuguese_light

    text = str(raw or "")
    if not text:
        return text
    candidates = [
        text,
        _latin1_to_utf8(text),
        _latin1_to_utf8(_latin1_to_utf8(text)),
    ]
    best = text
    best_score = _bad_score(text)
    for c in candidates:
        score = _bad_score(c)
        if score < best_score:
            best = c
            best_score = score
    out = _normalize_common_pt(_strip_iso_control_except_newlines(best))
    return polish_portuguese_light(out)


def _normalize_common_pt(text: str) -> str:
    out = text or ""
    replacements = {
        "N�o": "Não",
        "n�o": "não",
        "h�": "há",
        "H�": "Há",
        "gal�xia": "galáxia",
        "L�ctea": "Láctea",
        "n�mero": "número",
        "bilh�es": "bilhões",
        "milh�es": "milhões",
        "poss�vel": "possível",
    }
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out
