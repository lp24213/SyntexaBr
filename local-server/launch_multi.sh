#!/bin/bash
# Syntexa Sovereign AI — Multi-Environment Launcher (Linux/Mac)

GPU_PORT=8000
CPU1_PORT=8001
CPU2_PORT=8002
CPU3_PORT=8003
MODEL_DIR="./models/syntexa-export/merged"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  Syntexa Sovereign AI — Multi-Launch"
echo "========================================="

# GPU main instance
echo "[GPU-MAIN] Starting on port $GPU_PORT..."
python server.py --port $GPU_PORT --model-dir "$MODEL_DIR" &
GPU_PID=$!

sleep 5

# CPU instance 1 (no GPU)
echo "[CPU-FAST] Starting on port $CPU1_PORT..."
CUDA_VISIBLE_DEVICES="" python server.py --port $CPU1_PORT --model-dir "$MODEL_DIR" &
CPU1_PID=$!

sleep 2

# CPU instance 2
echo "[CPU-MED] Starting on port $CPU2_PORT..."
CUDA_VISIBLE_DEVICES="" python server.py --port $CPU2_PORT --model-dir "$MODEL_DIR" &
CPU2_PID=$!

sleep 2

# CPU instance 3
echo "[CPU-BACKUP] Starting on port $CPU3_PORT..."
CUDA_VISIBLE_DEVICES="" python server.py --port $CPU3_PORT --model-dir "$MODEL_DIR" &
CPU3_PID=$!

echo ""
echo "All instances launched!"
echo ""
echo "Endpoints:"
echo "  GPU Main:   http://localhost:$GPU_PORT"
echo "  CPU Fast:   http://localhost:$CPU1_PORT"
echo "  CPU Med:    http://localhost:$CPU2_PORT"
echo "  CPU Backup: http://localhost:$CPU3_PORT"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Trap Ctrl+C to kill all
trap 'echo ""; echo "Stopping all servers..."; kill $GPU_PID $CPU1_PID $CPU2_PID $CPU3_PID 2>/dev/null; exit 0' INT

wait
