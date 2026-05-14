#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — Kubernetes Deploy
# ============================================================
set -euo pipefail

NAMESPACE="${1:-syntexa}"
ENVIRONMENT="${2:-production}"
K8S_DIR="infrastructure/k8s"

echo "============================================================"
echo "  VEREDA / SYNTEXA — KUBERNETES DEPLOY"
echo "  Namespace: $NAMESPACE"
echo "  Environment: $ENVIRONMENT"
echo "============================================================"

# ── VALIDATION ─────────────────────────────────────────────
if ! command -v kubectl &> /dev/null; then
    echo "[ERRO] kubectl não encontrado"
    exit 1
fi

# ── NAMESPACE ──────────────────────────────────────────────
echo "[1/8] Creating namespace..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ── SECRETS ────────────────────────────────────────────────
echo "[2/8] Applying secrets..."
if [ -f "$K8S_DIR/secrets.yaml" ]; then
    kubectl apply -f "$K8S_DIR/secrets.yaml" -n "$NAMESPACE"
else
    echo "[WARN] secrets.yaml não encontrado — crie manualmente"
fi

# ── CONFIGMAP ────────────────────────────────────────────
echo "[3/8] Applying ConfigMap..."
kubectl apply -f "$K8S_DIR/configmap.yaml" -n "$NAMESPACE"

# ── PV/PVC ───────────────────────────────────────────────
echo "[4/8] Applying persistent volumes..."
kubectl apply -f "$K8S_DIR/pv.yaml" -n "$NAMESPACE"

# ── DEPLOYMENTS ──────────────────────────────────────────
echo "[5/8] Applying deployments..."
kubectl apply -f "$K8S_DIR/deployment.yaml" -n "$NAMESPACE"

# ── SERVICES ─────────────────────────────────────────────
echo "[6/8] Applying services..."
kubectl apply -f "$K8S_DIR/service.yaml" -n "$NAMESPACE"

# ── INGRESS ────────────────────────────────────────────────
echo "[7/8] Applying ingress..."
kubectl apply -f "$K8S_DIR/ingress.yaml" -n "$NAMESPACE"

# ── HPA ──────────────────────────────────────────────────
echo "[8/8] Applying HPA..."
kubectl apply -f "$K8S_DIR/hpa.yaml" -n "$NAMESPACE"

# ── MONITORING ─────────────────────────────────────────────
echo "[BONUS] Applying monitoring..."
kubectl apply -f "$K8S_DIR/prometheus-service-monitor.yaml" -n "$NAMESPACE" 2>/dev/null || echo "[WARN] ServiceMonitor requer Prometheus Operator"

# ── WAIT FOR ROLLOUT ─────────────────────────────────────
echo ""
echo "[VEREDA] Waiting for rollout..."
kubectl rollout status deployment/syntexa-backend -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/syntexa-redis -n "$NAMESPACE" --timeout=120s

# ── VALIDATION ─────────────────────────────────────────────
echo ""
echo "[VEREDA] Validating deployment..."
kubectl get pods -n "$NAMESPACE"
kubectl get svc -n "$NAMESPACE"
kubectl get ingress -n "$NAMESPACE"

echo ""
echo "============================================================"
echo "  KUBERNETES DEPLOY COMPLETE"
echo "============================================================"
