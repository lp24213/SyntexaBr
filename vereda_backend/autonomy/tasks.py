from datetime import datetime


def run_scheduled_jobs() -> dict:
    """
    Gancho para cron/celery/worker no futuro autônomo.
    """
    return {"ok": True, "ran_at": datetime.utcnow().isoformat()}
