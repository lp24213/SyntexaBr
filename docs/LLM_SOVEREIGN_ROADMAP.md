# SYNTEXABR Neural Core - Sovereign LLM Roadmap

## North Star

Build a sovereign LLM platform where the default inference path is fully owned by SYNTEXABR:

- own tokenizer, embeddings, and inference runtime
- own routing, memory, reasoning, and agent orchestration
- optional external providers only as non-default fallback/benchmark

## Sovereignty Rules

1. External APIs are disabled by default.
2. `primary_provider` must always point to a local/self-hosted runtime.
3. Every response records provenance (`model_id`, `runtime`, `source=local|fallback|benchmark`).
4. Security gates run before and after generation.

## Target Modules

- `llm-core`: model abstractions, contracts, model registry
- `llm-runtime`: execution scheduler and hardware orchestration
- `llm-router`: intent-aware model routing and policy enforcement
- `llm-memory`: semantic/contextual/temporal memory pipelines
- `llm-training`: training, fine-tuning, LoRA/QLoRA toolchain
- `llm-embeddings`: proprietary embedding models and services
- `llm-tokenizer`: tokenizer training/versioning and runtime codecs
- `llm-inference`: low-latency serving APIs and batching engines
- `llm-security`: prompt defense, sandboxing, integrity checks
- `llm-quantum`: quantum-assisted optimization and experiments
- `llm-agents`: autonomous agent framework
- `llm-reasoning`: reasoning engine and planning policies
- `llm-context-engine`: long-context packing and retrieval fusion
- `llm-multimodal`: text/image/audio/video orchestration
- `llm-voice`: STT/TTS pipelines
- `llm-vision`: CV pipelines, OCR and scene understanding
- `llm-autonomous`: self-healing and adaptive operations
- `llm-kernel`: platform kernel and cross-module governance

## Delivery Phases

### Phase 0 - Foundation

- create module skeletons and contracts
- define sovereignty policy and fallback controls
- set model artifact format (`safetensors`) and signature requirements

### Phase 1 - Core Inference

- hybrid Transformer + MoE baseline in PyTorch
- vLLM/ONNX runtime path with TensorRT/CUDA acceleration
- tokenizer v1 + embeddings v1 + local serving endpoint

### Phase 2 - Memory and Reasoning

- persistent memory (Redis + pgvector + Qdrant + FAISS adapters)
- context engine (chunking, ranking, compression, long-context)
- reasoning graph with tool/action planning

### Phase 3 - Multimodal and Agents

- voice (ASR + TTS), vision (OCR + understanding), PDF and video ingestion
- autonomous agents for infra, security, routing and repair
- governed action execution with risk scoring and rollback

### Phase 4 - Quantum Assist

- plug-in quantum optimizers with PyQPanda3/Qiskit/PennyLane
- probabilistic routing experiments and entropy generation
- benchmark quality/cost/latency/energy against classical baselines

## Stack Baseline

- Training/Inference: PyTorch, Triton, CUDA, TensorRT, Flash Attention
- Serving: vLLM, ONNX Runtime, WASM edge runners
- Performance: Rust kernels, Numba, CuPy
- Quantum: PyQPanda3, Qiskit, PennyLane
- Storage/Memory: Redis, FAISS, Qdrant, pgvector
- Artifacts: safetensors + cryptographic signatures

## Non-Goals (for now)

- no blind dependency on closed external APIs
- no production quantum path without reproducible benchmark gains
- no autonomous actions without policy and audit trail
