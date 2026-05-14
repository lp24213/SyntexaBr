"use client";

import React from "react";
import { motion } from "framer-motion";

const CODE_STREAMS = [
  "fn quantum_route(mesh: &NeuralMesh) -> InferencePath",
  "let entropy = qrand::kyber_seed(4096);",
  "cuda::launch_kernel::<MoEAttention>(grid, block, stream);",
  "qiskit.execute(circuit, backend='statevector_simulator')",
  "tokio::spawn(async move { guardian.scan().await; });",
  "SELECT * FROM memory_vectors ORDER BY embedding <=> $1 LIMIT 8;",
  "autonomous_repair.apply_patch(node_id, signed_bundle)",
  "proof.verify(dilithium_signature, model_manifest_hash)",
];

function Stream(props) {
  const { line, delay } = props;
  return React.createElement(
    motion.div,
    {
      className: "quantum-code-line",
      initial: { opacity: 0, y: 16 },
      animate: { opacity: [0.12, 0.8, 0.12], y: [16, 0, -10] },
      transition: { duration: 9, repeat: Infinity, delay },
    },
    line
  );
}

export function QuantumBackground() {
  return React.createElement(
    "div",
    { className: "quantum-bg", "aria-hidden": true },
    React.createElement("div", { className: "quantum-bg-grid" }),
    React.createElement("div", { className: "quantum-bg-vignette" }),
    React.createElement("div", { className: "quantum-bg-orb quantum-bg-orb-a" }),
    React.createElement("div", { className: "quantum-bg-orb quantum-bg-orb-b" }),
    React.createElement(
      motion.div,
      {
        className: "quantum-core-pulse",
        animate: { scale: [1, 1.08, 1], opacity: [0.32, 0.75, 0.32] },
        transition: { duration: 4.2, repeat: Infinity, ease: "easeInOut" },
      },
      React.createElement("div", { className: "quantum-core-inner" })
    ),
    React.createElement(
      "div",
      { className: "quantum-code-streams" },
      CODE_STREAMS.map(function (line, i) {
        return React.createElement(Stream, { key: line, line: line, delay: i * 0.45 });
      })
    )
  );
}

