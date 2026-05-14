"use client";

import React, { useEffect, useRef } from "react";

var CODE_SNIPPETS = [
  "H(q[0])",
  "CNOT(q[0], q[1])",
  "QuantumScheduler.initialize()",
  "LLMRouter.probabilistic_route()",
  "TensorRuntime.execute()",
  "NeuralInference.begin()",
  "QuantumEntropy.calculate()",
  "PyQPandaCircuit.compile()",
  "CUDA_KERNEL<<<blocks,threads>>>(d_a)",
  "transformer.forward(x, mask)",
  "distributed_inference.all_reduce(grad)",
  "wasm_runtime.instantiate(module)",
  "qubit_map.entangle(q0, q1)",
  "attention_scores = Q @ K.T / sqrt(d_k)",
  " QuantumStatevector.evolve(U)",
  "sovereign_llm.load_weights('/models/7B')",
  "pipeline.orchestrate([encoder, router, decoder])",
  "quantum_noise.apply_decoherence(t=1.2e-3)",
  "cudaMemcpyAsync(d_out, h_out, size, D2H)",
  "neural_memory.compress(token_buffer)",
  "inference_stream.throttle(120tok/s)",
  "probabilistic_graph.sample_posterior(n=4096)",
  "WASM_SIMD.v128_load(ptr)",
  "qft.apply(q_reg, n_qubits=8)",
  "tensor_parallel.shard(layer, n=4)",
  "kv_cache.evict_oldest(stride=512)",
  "quantum_grover.oracle(marked_states)",
  "neural_scheduler.optimize_latency()",
  "cudaStreamSynchronize(stream_id)",
  "llm_runtime.speculative_decode(draft)",
  "distributed_topology.ring_all_gather()",
  "quantum_amplitude.estimate(phi, shots=8192)",
  "embedding_space.project(tokens, dim=4096)",
  "ai_orchestrator.dispatch(agent_pool)",
  "gpu_memory.defrag(heap)",
  "circuit_depth.minimize(gateset='universal')",
  "neural_quantize.int8(weights, scale=0.012)",
  "inference_batch.dynamic_pad(max_len=2048)",
  "qubit_alloc.reserve(n=16, backend='simulator')",
  "neural_router.select_expert(gating_scores)",
  "quantum_phase.estimate_eigenvalue(U, psi)",
  "tensor_contract.indices('ij,jk->ik', A, B)",
  "llm_context_window.shift(stride=512)",
  "distributed_sync.barrier(cluster_id)",
  "quantum_decoherence.model_t1_t2(t1=50us, t2=30us)",
  "neural_attention.sparse_pattern(block_size=64)",
  "cuda_event.record(stream)",
  "sovereign_runtime.isolate_tenant(tenant_id)",
  "quantum_error_correction.stabilize(surface_code)",
  "neural_pipeline.parallel_encode_decode(src, tgt)",
  "inference_cache.warm(prefix_tokens)",
  "quantum_teleport.transfer(q0, entangled_pair)",
];

function useScrollVelocity() {
  var ref = useRef(0);
  var lastY = useRef(0);
  var lastT = useRef(Date.now());

  useEffect(function () {
    function onScroll() {
      var now = Date.now();
      var dt = Math.max(now - lastT.current, 1);
      var dy = window.scrollY - lastY.current;
      var v = Math.abs(dy) / dt;
      ref.current = Math.min(v * 1.2, 5.0);
      lastY.current = window.scrollY;
      lastT.current = now;
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return function () { window.removeEventListener("scroll", onScroll); };
  }, []);

  return ref;
}

export function QuantumCodeStream() {
  var canvasRef = useRef(null);
  var rafRef = useRef(null);
  var velocityRef = useScrollVelocity();

  useEffect(function () {
    var canvas = canvasRef.current;
    if (!canvas) return;
    var ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W, H;
    var COLS = 20;
    var streams = [];
    var fadeIn = 0;

    function resize() {
      var rect = canvas.parentElement.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function createStreams() {
      streams = [];
      var colW = W / COLS;
      for (var c = 0; c < COLS; c++) {
        var count = Math.floor(H / 18) + 10;
        for (var i = 0; i < count; i++) {
          var depth = Math.random();
          streams.push({
            x: c * colW + Math.random() * (colW - 10) + 5,
            y: Math.random() * H - 80,
            speed: 0.5 + Math.random() * 1.0,
            text: CODE_SNIPPETS[Math.floor(Math.random() * CODE_SNIPPETS.length)],
            opacity: 0.15 + Math.random() * 0.25,
            phase: Math.random() * Math.PI * 2,
            fontSize: 15 + Math.floor(Math.random() * 7),
            depth: depth,
            scale: 0.8 + depth * 0.6,
          });
        }
      }
    }

    var frame = 0;
    function draw() {
      frame++;
      if (frame % 2 === 0) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }

      ctx.clearRect(0, 0, W, H);
      fadeIn = Math.min(fadeIn + 0.015, 1);

      var scrollVel = velocityRef.current;
      var speedMult = 1 + scrollVel * 2.0;

      for (var i = 0; i < streams.length; i++) {
        var s = streams[i];
        s.y += s.speed * speedMult;
        s.phase += 0.006;

        if (s.y > H + 60) {
          s.y = -80;
          s.text = CODE_SNIPPETS[Math.floor(Math.random() * CODE_SNIPPETS.length)];
          s.opacity = 0.15 + Math.random() * 0.25;
        }

        var wobble = Math.sin(s.phase) * 16;
        var flicker = 0.5 + Math.sin(s.phase * 3.1) * 0.5;
        var alpha = s.opacity * flicker * fadeIn;
        if (alpha < 0.005) continue;

        var baseColor = 100 + Math.floor(s.depth * 60);
        ctx.fillStyle = "rgba(" + baseColor + "," + (baseColor + 10) + "," + (baseColor + 25) + "," + alpha + ")";
        ctx.font = "600 " + s.fontSize + "px 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace";
        ctx.save();
        ctx.translate(s.x + wobble, s.y);
        ctx.scale(s.scale, s.scale);
        ctx.fillText(s.text, 0, 0);
        ctx.restore();
      }

      rafRef.current = requestAnimationFrame(draw);
    }

    resize();
    createStreams();
    rafRef.current = requestAnimationFrame(draw);

    var onResize = function () { resize(); createStreams(); };
    window.addEventListener("resize", onResize, { passive: true });

    return function () {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return React.createElement("canvas", {
    ref: canvasRef,
    className: "absolute inset-0 w-full h-full pointer-events-none",
    style: { display: "block", zIndex: 1 },
    "aria-hidden": true,
  });
}
