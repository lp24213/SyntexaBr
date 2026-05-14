"use client";

import React, { useRef, useEffect } from "react";

/**
 * InfrastructureVisualization — SVG-based computational ecosystem
 * GPU-safe, cinematic, represents distributed neural infrastructure
 */
export function InfrastructureVisual() {
  const svgRef = useRef(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    // Animate nodes with CSS only — no JS animation loop
    const nodes = svg.querySelectorAll(".infra-node");
    nodes.forEach((node, i) => {
      (node as SVGCircleElement).style.animationDelay = `${i * 0.15}s`;
    });
  }, []);

  return (
    <div className="relative w-full h-full min-h-[500px] flex items-center justify-center overflow-hidden">
      {/* Volumetric glow behind */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(ellipse 50% 50% at 50% 50%, rgba(99,102,241,0.15), transparent 70%)",
        }}
      />

      <svg
        ref={svgRef}
        viewBox="0 0 800 600"
        className="relative z-10 w-full h-full max-w-[900px]"
        style={{ filter: "drop-shadow(0 0 20px rgba(99,102,241,0.1))" }}
      >
        {/* Connection lines */}
        <g stroke="rgba(99,102,241,0.15)" strokeWidth="1" fill="none">
          <line x1="400" y1="100" x2="200" y2="250" />
          <line x1="400" y1="100" x2="600" y2="250" />
          <line x1="400" y1="100" x2="400" y2="450" />
          <line x1="200" y1="250" x2="300" y2="400" />
          <line x1="200" y1="250" x2="150" y2="450" />
          <line x1="600" y1="250" x2="500" y2="400" />
          <line x1="600" y1="250" x2="650" y2="450" />
          <line x1="400" y1="450" x2="300" y2="400" />
          <line x1="400" y1="450" x2="500" y2="400" />
          <line x1="300" y1="400" x2="150" y2="450" />
          <line x1="500" y1="400" x2="650" y2="450" />
        </g>

        {/* Data flow lines (animated) */}
        <g stroke="rgba(99,102,241,0.3)" strokeWidth="1.5" fill="none" strokeDasharray="8 8">
          <line x1="400" y1="100" x2="200" y2="250">
            <animate attributeName="stroke-dashoffset" from="200" to="0" dur="3s" repeatCount="indefinite" />
          </line>
          <line x1="400" y1="100" x2="600" y2="250">
            <animate attributeName="stroke-dashoffset" from="200" to="0" dur="2.5s" repeatCount="indefinite" />
          </line>
          <line x1="200" y1="250" x2="300" y2="400">
            <animate attributeName="stroke-dashoffset" from="200" to="0" dur="2s" repeatCount="indefinite" />
          </line>
          <line x1="600" y1="250" x2="500" y2="400">
            <animate attributeName="stroke-dashoffset" from="200" to="0" dur="2.2s" repeatCount="indefinite" />
          </line>
        </g>

        {/* Central Core */}
        <g>
          <circle cx="400" cy="100" r="28" fill="rgba(99,102,241,0.1)" stroke="rgba(99,102,241,0.4)" strokeWidth="1.5" />
          <circle cx="400" cy="100" r="18" fill="rgba(99,102,241,0.2)" stroke="rgba(99,102,241,0.5)" strokeWidth="1">
            <animate attributeName="r" values="18;22;18" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.8;0.4;0.8" dur="3s" repeatCount="indefinite" />
          </circle>
          <text x="400" y="104" textAnchor="middle" fill="#e8e8ec" fontSize="10" fontWeight="500">CORE</text>
        </g>

        {/* Layer Nodes */}
        {[
          { cx: 200, cy: 250, label: "GPU-0" },
          { cx: 600, cy: 250, label: "GPU-1" },
          { cx: 400, cy: 450, label: "MEM" },
          { cx: 300, cy: 400, label: "RAG" },
          { cx: 500, cy: 400, label: "TTS" },
          { cx: 150, cy: 450, label: "STT" },
          { cx: 650, cy: 450, label: "DOC" },
        ].map((node, i) => (
          <g key={i}>
            <circle
              cx={node.cx}
              cy={node.cy}
              r="20"
              fill="rgba(255,255,255,0.02)"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="1"
              className="infra-node"
              style={{ animation: `node-pulse 3s ease-in-out ${i * 0.15}s infinite` }}
            />
            <circle cx={node.cx} cy={node.cy} r="6" fill="rgba(99,102,241,0.6)">
              <animate attributeName="opacity" values="0.5;1;0.5" dur={`${2 + i * 0.3}s`} repeatCount="indefinite" />
            </circle>
            <text
              x={node.cx}
              y={node.cy + 4}
              textAnchor="middle"
              fill="#9a9aa0"
              fontSize="7"
              fontFamily="monospace"
              letterSpacing="0.1em"
            >
              {node.label}
            </text>
          </g>
        ))}

        {/* Orbiting particles */}
        {[0, 1, 2, 3].map((i) => (
          <circle key={`p-${i}`} r="2" fill="rgba(99,102,241,0.4)">
            <animateMotion
              dur={`${8 + i * 2}s`}
              repeatCount="indefinite"
              path={`M ${400 + Math.cos((i * Math.PI) / 2) * 80} ${100 + Math.sin((i * Math.PI) / 2) * 80} 
                     Q ${400 + Math.cos(((i + 1) * Math.PI) / 2) * 120} ${100 + Math.sin(((i + 1) * Math.PI) / 2) * 60}
                     ${400 + Math.cos(((i + 1) * Math.PI) / 2) * 80} ${100 + Math.sin(((i + 1) * Math.PI) / 2) * 80}`}
            />
          </circle>
        ))}
      </svg>

      {/* Ambient overlay */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0a0a0b] to-transparent" />
    </div>
  );
}
