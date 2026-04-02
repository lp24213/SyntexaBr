# -*- coding: utf-8 -*-
"""
Controle de acesso e conformidade (código próprio).
- Camada LGPD: checklist e princípios de minimização.
- Auditoria: registro de ações em audit_logs.
- Logs: integração com AuditLog no DB.
"""
from typing import Optional, Any
from sqlalchemy.orm import Session

# Checklist LGPD para uso em fluxos que tratam dados pessoais (código próprio).
LGPD_CHECKLIST = [
    "Finalidade: uso apenas para a finalidade informada.",
    "Minimização: coletar só o necessário.",
    "Transparência: informar o titular sobre o tratamento.",
    "Segurança: medidas técnicas e organizacionais.",
    "Não discriminação: não usar para fins discriminatórios.",
    "Responsabilização: demonstrar conformidade (registros).",
]


def audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Registra evento no audit_logs (controle de acesso e auditoria)."""
    from vereda_backend.db import models
    entry = models.AuditLog(
        action=action,
        user_id=user_id,
        resource=resource,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()


def requires_lgpd_consent(purpose: str) -> str:
    """Retorna texto de lembrete para fluxos que tratam dados pessoais."""
    return (
        f"Tratamento para: {purpose}. "
        "Respeitar LGPD e princípios de minimização; registrar consentimento quando aplicável."
    )


def may_access_personal_data(
    user_id: Optional[int],
    resource_owner_id: Optional[int],
    is_admin: bool = False,
) -> bool:
    """Verificação simples: usuário acessa próprio dado ou é admin."""
    if resource_owner_id is None:
        return True
    if user_id is None:
        return False
    if user_id == resource_owner_id:
        return True
    if is_admin:
        return True
    return False
