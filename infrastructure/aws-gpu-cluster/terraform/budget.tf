# ============================================================
# SYNTEXA AWS BUDGET — Alerta de orçamento $100
# ============================================================

resource "aws_budgets_budget" "syntexa_monthly" {
  name              = "syntexa-monthly-budget"
  budget_type       = "COST"
  limit_amount      = var.budget_limit_usd
  limit_unit        = "USD"
  time_period_start = "2026-05-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["admin@syntexa.dev"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["admin@syntexa.dev"]
  }
}
