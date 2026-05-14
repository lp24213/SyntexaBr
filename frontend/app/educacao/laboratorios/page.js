"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "../../../components/shell";
import { educationCompute, educationCodeSandbox } from "../../../lib/api";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

// ─── Icons ──────────────────────────────────────────────────────────────────

function BackIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M19 12H5M12 5l-7 7 7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}

function PlayIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M5 3l14 9-14 9V3z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }));
}

function ResetIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M1 4v6h6M23 20v-6h-6", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M20.49 9A9 9 0 105.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 115 14.51", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round" }));
}

// ─── Lab definitions ─────────────────────────────────────────────────────────

const LABS = [
  { id: "projetil", label: "Projétil", category: "Física", iconName: "rocket", desc: "Movimento de projétil em 2D com gravidade" },
  { id: "mola", label: "Oscilação Mola", category: "Física", iconName: "orbit", desc: "Sistema massa-mola com amortecimento" },
  { id: "pendulo", label: "Pêndulo Simples", category: "Física", iconName: "wave", desc: "Oscilação de pêndulo com amortecimento e período" },
  { id: "ondas", label: "Ondas & Interferência", category: "Física", iconName: "wave", desc: "Superposição e interferência de ondas em tempo real" },
  { id: "funcao", label: "Plotter de Funções", category: "Matemática", iconName: "chart", desc: "Gráfico interativo de funções matemáticas" },
  { id: "calculo", label: "Motor de Cálculo", category: "Matemática", iconName: "sigma", desc: "Cálculo simbólico passo a passo com SymPy" },
  { id: "estatistica", label: "Estatística", category: "Matemática", iconName: "chart", desc: "Análise estatística de datasets" },
  { id: "quimica", label: "Balanceador Químico", category: "Química", iconName: "flask", desc: "Balanceamento de equações químicas" },
  { id: "circuito", label: "Circuito Elétrico", category: "Engenharia", iconName: "bolt", desc: "Lei de Ohm e divisor de tensão" },
  { id: "codigo", label: "Sandbox de Código", category: "Programação", iconName: "code", desc: "Execute Python com análise automática" },
  { id: "algoritmos", label: "Ordenação Visualizada", category: "Programação", iconName: "grid", desc: "Visualize Bubble, Insertion e Merge Sort em tempo real" },
  { id: "fourier", label: "Série de Fourier", category: "Matemática", iconName: "wave", desc: "Decomposição de funções periódicas em somas de senos" },
];

const CATEGORY_COLORS = {
  "Física": "border-sky-200 hover:border-sky-300 text-[#1a1c1e]",
  "Matemática": "border-violet-200 hover:border-violet-300 text-violet-700",
  "Química": "border-emerald-200 hover:border-emerald-300 text-emerald-700",
  "Engenharia": "border-amber-200 hover:border-amber-300 text-amber-700",
  "Programação": "border-rose-200 hover:border-rose-300 text-rose-700",
};

const CATEGORY_BADGE = {
  "Física": "bg-sky-50 text-[#1a1c1e] border-sky-200",
  "Matemática": "bg-violet-50 text-violet-700 border-violet-200",
  "Química": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Engenharia": "bg-amber-50 text-amber-700 border-amber-200",
  "Programação": "bg-rose-50 text-rose-700 border-rose-200",
};

// ─── Physics: Projectile Simulator ────────────────────────────────────────

function ProjetilLab() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const [v0, setV0] = useState(40);
  const [angle, setAngle] = useState(45);
  const [running, setRunning] = useState(false);
  const [info, setInfo] = useState(null);

  const runSimulation = useCallback(() => {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const g = 9.8;
    const rad = (angle * Math.PI) / 180;
    const vx = v0 * Math.cos(rad);
    const vy = v0 * Math.sin(rad);
    const tFlight = (2 * vy) / g;
    const range = vx * tFlight;
    const maxH = (vy * vy) / (2 * g);
    setInfo({ range: range.toFixed(1), maxH: maxH.toFixed(1), tFlight: tFlight.toFixed(2) });

    const scaleX = (W - 60) / range;
    const scaleY = (H - 60) / (maxH * 1.3);

    let t = 0;
    const dt = 0.016;
    const trail = [];

    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(148,163,184,0.08)";
      ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

      // Ground
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(40, H - 40); ctx.lineTo(W - 10, H - 40); ctx.stroke();

      // Trajectory curve (ghost)
      ctx.strokeStyle = "rgba(148,163,184,0.12)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let ts = 0; ts <= tFlight; ts += 0.05) {
        const px = 40 + vx * ts * scaleX;
        const py = H - 40 - (vy * ts - 0.5 * g * ts * ts) * scaleY;
        ts === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.stroke();

      // Trail
      ctx.strokeStyle = "rgba(56,189,248,0.5)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      trail.forEach(([tx, ty], i) => { i === 0 ? ctx.moveTo(tx, ty) : ctx.lineTo(tx, ty); });
      ctx.stroke();

      // Ball
      const cx = 40 + vx * t * scaleX;
      const cy = H - 40 - (vy * t - 0.5 * g * t * t) * scaleY;
      trail.push([cx, cy]);
      if (trail.length > 200) trail.shift();

      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 8);
      grad.addColorStop(0, "#38bdf8");
      grad.addColorStop(1, "rgba(56,189,248,0.1)");
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(cx, cy, 8, 0, Math.PI * 2); ctx.fill();

      // Vector arrow
      ctx.strokeStyle = "rgba(251,191,36,0.6)";
      ctx.lineWidth = 1.5;
      const vxNow = vx;
      const vyNow = vy - g * t;
      const vMag = Math.sqrt(vxNow ** 2 + vyNow ** 2);
      if (vMag > 0.5) {
        const arrowLen = Math.min(vMag * 0.8, 40);
        const endX = cx + (vxNow / vMag) * arrowLen;
        const endY = cy - (vyNow / vMag) * arrowLen;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(endX, endY); ctx.stroke();
      }

      t += dt;
      if (t <= tFlight) {
        animRef.current = requestAnimationFrame(draw);
      } else {
        setRunning(false);
      }
    }
    setRunning(true);
    draw();
  }, [v0, angle]);

  const reset = () => {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    setRunning(false);
    setInfo(null);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
  };

  useEffect(() => { reset(); return () => { if (animRef.current) cancelAnimationFrame(animRef.current); }; }, []);

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 600, height: 320, className: "w-full rounded-xl border border-zinc-200 bg-[#f1f5f9]" }),
    React.createElement("div", { className: "grid grid-cols-2 gap-4 sm:grid-cols-4" },
      [["Velocidade inicial (m/s)", v0, setV0, 5, 100, 1], ["Ângulo (°)", angle, setAngle, 1, 89, 1]].map(([label, val, setter, min, max, step]) =>
        React.createElement("div", { key: label },
          React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, label, ": ", React.createElement("span", { className: "text-zinc-700" }, val)),
          React.createElement("input", { type: "range", min, max, step, value: val, onChange: e => setter(Number(e.target.value)), className: "w-full accent-sky-500" })
        )
      ),
      info && React.createElement("div", { className: "col-span-2 grid grid-cols-3 gap-2" },
        [["Alcance", info.range + " m"], ["Alt. máx.", info.maxH + " m"], ["Tempo voo", info.tFlight + " s"]].map(([k, v]) =>
          React.createElement("div", { key: k, className: "rounded-xl border border-[rgba(20,24,30,0.06)] bg-[#f8f9fa] p-2 text-center" },
            React.createElement("p", { className: "text-[10px] text-zinc-500" }, k),
            React.createElement("p", { className: "text-sm font-bold text-[#1a1c1e]" }, v)
          )
        )
      )
    ),
    React.createElement("div", { className: "flex gap-2" },
      React.createElement("button", { onClick: runSimulation, disabled: running, className: "inline-flex items-center gap-1.5 rounded-xl bg-[#1a1c1e] border border-sky-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" }, React.createElement(PlayIcon, null), "Lançar"),
      React.createElement("button", { onClick: reset, className: "inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 px-4 py-2 text-sm text-zinc-500 hover:text-zinc-900" }, React.createElement(ResetIcon, null), "Resetar")
    )
  );
}

// ─── Physics: Spring Oscillation ─────────────────────────────────────────

function MolaLab() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const [k, setK] = useState(20);
  const [mass, setMass] = useState(2);
  const [damping, setDamping] = useState(0.3);
  const [running, setRunning] = useState(false);

  const run = useCallback(() => {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const eq = H / 2;
    let x = 100, v = 0, t = 0;
    const history = [];
    setRunning(true);

    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, W, H);

      // Wall
      ctx.fillStyle = "rgba(148,163,184,0.15)";
      ctx.fillRect(0, 0, 20, H);

      // Spring (zigzag)
      const springEnd = W / 2 + x;
      const coils = 10;
      const segLen = (springEnd - 20) / (coils * 2);
      ctx.strokeStyle = "rgba(148,163,184,0.6)";
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(20, eq);
      for (let i = 0; i < coils * 2; i++) {
        const px = 20 + i * segLen;
        const py = eq + (i % 2 === 0 ? -20 : 20);
        ctx.lineTo(px, py);
      }
      ctx.lineTo(springEnd, eq); ctx.stroke();

      // Mass block
      const bx = springEnd, bh = 50;
      const grad = ctx.createLinearGradient(bx, eq - bh / 2, bx + bh, eq + bh / 2);
      grad.addColorStop(0, "rgba(139,92,246,0.9)");
      grad.addColorStop(1, "rgba(79,70,229,0.6)");
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.roundRect(bx, eq - bh / 2, bh, bh, 8); ctx.fill();
      ctx.strokeStyle = "rgba(139,92,246,0.4)";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = "white";
      ctx.font = "11px monospace";
      ctx.textAlign = "center";
      ctx.fillText(`${mass}kg`, bx + bh / 2, eq + 4);

      // Graph
      history.push({ t, x });
      if (history.length > 300) history.shift();
      ctx.strokeStyle = "rgba(139,92,246,0.7)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      history.forEach((pt, i) => {
        const px = W * 0.7 + (i / 300) * W * 0.28;
        const py = eq - pt.x * 1.5;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      });
      ctx.stroke();

      // Equilibrium line
      ctx.strokeStyle = "rgba(148,163,184,0.2)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(W * 0.7, eq); ctx.lineTo(W, eq); ctx.stroke();
      ctx.setLineDash([]);

      // Physics
      const F = -k * x;
      const Fd = -damping * v;
      const a = (F + Fd) / mass;
      v += a * 0.016;
      x += v * 0.016;
      t += 0.016;

      animRef.current = requestAnimationFrame(draw);
    }
    draw();
  }, [k, mass, damping]);

  const stop = () => { if (animRef.current) cancelAnimationFrame(animRef.current); setRunning(false); };

  useEffect(() => { return () => { if (animRef.current) cancelAnimationFrame(animRef.current); }; }, []);

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 600, height: 280, className: "w-full rounded-xl border border-zinc-200 bg-[#f1f5f9]" }),
    React.createElement("div", { className: "grid grid-cols-3 gap-4" },
      [["Constante k (N/m)", k, setK, 5, 100, 5], ["Massa (kg)", mass, setMass, 0.5, 10, 0.5], ["Amortecimento (b)", damping, setDamping, 0, 2, 0.1]].map(([label, val, setter, min, max, step]) =>
        React.createElement("div", { key: label },
          React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, label, ": ", React.createElement("span", { className: "text-[#5a5c5e] font-mono" }, val)),
          React.createElement("input", { type: "range", min, max, step, value: val, onChange: e => setter(Number(e.target.value)), className: "w-full accent-violet-500" })
        )
      )
    ),
    React.createElement("div", { className: "flex gap-2" },
      React.createElement("button", { onClick: running ? stop : run, className: `inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-sm font-medium transition-all ${running ? "bg-red-600/70 border-red-500/40 text-zinc-900" : "bg-[#1a1c1e] border-[rgba(20,24,30,0.1)] text-zinc-900"}` }, running ? "Pausar" : React.createElement(React.Fragment, null, React.createElement(PlayIcon, null), "Iniciar")),
      React.createElement("p", { className: "self-center text-xs text-zinc-500" }, `ω = ${(k / mass) ** 0.5 > 0 ? Math.sqrt(k / mass).toFixed(2) : 0} rad/s`)
    )
  );
}

// ─── Math: Function Plotter ───────────────────────────────────────────────

function FuncaoLab() {
  const canvasRef = useRef(null);
  const [funcStr, setFuncStr] = useState("sin(x)");
  const [xMin, setXMin] = useState(-10);
  const [xMax, setXMax] = useState(10);
  const [error, setError] = useState(null);

  const plot = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    setError(null);

    let f;
    try {
      const safeStr = funcStr
        .replace(/\^/g, "**")
        .replace(/sin/g, "Math.sin").replace(/cos/g, "Math.cos").replace(/tan/g, "Math.tan")
        .replace(/sqrt/g, "Math.sqrt").replace(/abs/g, "Math.abs").replace(/log/g, "Math.log")
        .replace(/exp/g, "Math.exp").replace(/pi/g, "Math.PI").replace(/e(?=[^x])/g, "Math.E");
      f = new Function("x", `"use strict"; return ${safeStr};`);
      f(0);
    } catch (e) { setError("Função inválida: " + e.message); return; }

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#f1f5f9";
    ctx.fillRect(0, 0, W, H);

    const xs = xMin, xe = xMax;
    const samples = 800;
    const ys = [];
    for (let i = 0; i <= samples; i++) {
      const x = xs + (i / samples) * (xe - xs);
      try { const y = f(x); ys.push(isFinite(y) ? y : null); } catch { ys.push(null); }
    }
    const validYs = ys.filter(y => y !== null);
    const yMin = Math.min(...validYs);
    const yMax = Math.max(...validYs);
    const pad = 40;

    const toCanvasX = x => pad + ((x - xs) / (xe - xs)) * (W - 2 * pad);
    const toCanvasY = y => H - pad - ((y - yMin) / (yMax - yMin || 1)) * (H - 2 * pad);

    // Grid + axes
    ctx.strokeStyle = "rgba(148,163,184,0.07)";
    ctx.lineWidth = 1;
    for (let x = xs; x <= xe; x += (xe - xs) / 10) { ctx.beginPath(); ctx.moveTo(toCanvasX(x), pad); ctx.lineTo(toCanvasX(x), H - pad); ctx.stroke(); }
    for (let y = yMin; y <= yMax; y += (yMax - yMin) / 8) { ctx.beginPath(); ctx.moveTo(pad, toCanvasY(y)); ctx.lineTo(W - pad, toCanvasY(y)); ctx.stroke(); }

    // X axis
    if (yMin <= 0 && yMax >= 0) {
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pad, toCanvasY(0)); ctx.lineTo(W - pad, toCanvasY(0)); ctx.stroke();
    }
    // Y axis
    if (xs <= 0 && xe >= 0) {
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.beginPath(); ctx.moveTo(toCanvasX(0), pad); ctx.lineTo(toCanvasX(0), H - pad); ctx.stroke();
    }

    // Function curve
    const grad = ctx.createLinearGradient(0, 0, W, 0);
    grad.addColorStop(0, "#818cf8");
    grad.addColorStop(0.5, "#a78bfa");
    grad.addColorStop(1, "#c084fc");
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.beginPath();
    let penDown = false;
    for (let i = 0; i <= samples; i++) {
      const x = xs + (i / samples) * (xe - xs);
      const y = ys[i];
      if (y === null) { penDown = false; continue; }
      const cx2 = toCanvasX(x);
      const cy2 = toCanvasY(y);
      if (!penDown) { ctx.moveTo(cx2, cy2); penDown = true; } else { ctx.lineTo(cx2, cy2); }
    }
    ctx.stroke();

    // Label
    ctx.fillStyle = "rgba(167,139,250,0.7)";
    ctx.font = "13px monospace";
    ctx.fillText(`f(x) = ${funcStr}`, pad + 6, pad + 18);
  }, [funcStr, xMin, xMax]);

  useEffect(() => { plot(); }, [plot]);

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 600, height: 320, className: "w-full rounded-xl border border-zinc-200 bg-[#f1f5f9]" }),
    React.createElement("div", { className: "flex flex-wrap gap-3" },
      React.createElement("div", { className: "flex-1 min-w-[200px]" },
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "f(x) ="),
        React.createElement("input", { value: funcStr, onChange: e => setFuncStr(e.target.value), onKeyDown: e => e.key === "Enter" && plot(), className: "w-full rounded-xl border border-[rgba(20,24,30,0.1)] bg-white px-3 py-2 text-sm font-mono text-violet-200 focus:outline-none focus:border-violet-400/60", placeholder: "sin(x), x**2, cos(x)*x ..." })
      ),
      React.createElement("div", null,
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "x mín"),
        React.createElement("input", { type: "number", value: xMin, onChange: e => setXMin(Number(e.target.value)), className: "w-20 rounded-xl border border-zinc-200 bg-white px-2 py-2 text-sm text-zinc-900 focus:outline-none" })
      ),
      React.createElement("div", null,
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "x máx"),
        React.createElement("input", { type: "number", value: xMax, onChange: e => setXMax(Number(e.target.value)), className: "w-20 rounded-xl border border-zinc-200 bg-white px-2 py-2 text-sm text-zinc-900 focus:outline-none" })
      ),
      React.createElement("button", { onClick: plot, className: "self-end rounded-xl bg-[#1a1c1e] border border-[rgba(20,24,30,0.1)] px-4 py-2 text-sm font-medium text-zinc-900" }, "Plotar")
    ),
    error && React.createElement("p", { className: "text-xs text-red-400" }, error),
    React.createElement("div", { className: "flex flex-wrap gap-1.5" },
      ["sin(x)", "cos(x)", "x**2", "1/x", "sqrt(abs(x))", "exp(-x**2)", "x*sin(x)"].map(fn =>
        React.createElement("button", { key: fn, onClick: () => setFuncStr(fn), className: "rounded-lg border border-zinc-200 px-2.5 py-1 text-xs font-mono text-zinc-500 hover:text-[#5a5c5e] hover:border-[rgba(20,24,30,0.1)] transition-all" }, fn)
      )
    )
  );
}

// ─── Math: Compute Engine ────────────────────────────────────────────────

function CalculoLab() {
  const [expr, setExpr] = useState("");
  const [computeType, setComputeType] = useState("auto");
  const [variable, setVariable] = useState("x");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const TYPES = ["auto", "derivada", "integral", "limite", "equacao", "matriz", "estatistica"];

  const compute = async () => {
    if (!expr.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await educationCompute(expr, computeType, variable);
      setResult(r);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const EXAMPLES = [
    ["d/dx sin(x²)", "auto", "x"],
    ["∫ x² dx", "integral", "x"],
    ["x² - 5x + 6 = 0", "equacao", "x"],
    ["lim(1/x) quando x→∞", "limite", "x"],
    ["1 2 3 4 5 6 7 8 9", "estatistica", "x"],
    ["[[1,2],[3,4]]", "matriz", "x"],
  ];

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("div", { className: "flex flex-wrap gap-2" },
      React.createElement("div", { className: "flex-1 min-w-[240px]" },
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "Expressão"),
        React.createElement("input", { value: expr, onChange: e => setExpr(e.target.value), onKeyDown: e => e.key === "Enter" && compute(), className: "w-full rounded-xl border border-[rgba(20,24,30,0.1)] bg-white px-3 py-2 text-sm font-mono text-violet-200 focus:outline-none focus:border-violet-400/60", placeholder: "d/dx sin(x), ∫ x² dx, x²-5x+6=0 ..." })
      ),
      React.createElement("div", null,
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "Tipo"),
        React.createElement("select", { value: computeType, onChange: e => setComputeType(e.target.value), className: "rounded-xl border border-zinc-200 bg-white px-2 py-2 text-sm text-zinc-900 focus:outline-none" },
          TYPES.map(t => React.createElement("option", { key: t, value: t }, t))
        )
      ),
      React.createElement("div", null,
        React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "Variável"),
        React.createElement("input", { value: variable, onChange: e => setVariable(e.target.value), className: "w-16 rounded-xl border border-zinc-200 bg-white px-2 py-2 text-sm font-mono text-zinc-900 focus:outline-none" })
      ),
      React.createElement("button", { onClick: compute, disabled: loading || !expr.trim(), className: "self-end rounded-xl bg-[#1a1c1e] border border-[rgba(20,24,30,0.1)] px-4 py-2 text-sm font-medium text-zinc-900 disabled:opacity-50" }, loading ? "..." : "Calcular")
    ),
    React.createElement("div", { className: "flex flex-wrap gap-1.5" },
      EXAMPLES.map(([e, t, v]) =>
        React.createElement("button", { key: e, onClick: () => { setExpr(e); setComputeType(t); setVariable(v); }, className: "rounded-lg border border-zinc-200 px-2 py-1 text-xs font-mono text-zinc-500 hover:text-[#5a5c5e] hover:border-[rgba(20,24,30,0.1)] transition-all" }, e)
      )
    ),
    error && React.createElement("p", { className: "text-xs text-red-400" }, error),
    result && React.createElement(motion.div, { className: "rounded-2xl border border-[rgba(20,24,30,0.06)] bg-white p-5 space-y-3", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
      result.steps && result.steps.length > 0 && React.createElement("div", null,
        React.createElement("p", { className: "mb-2 text-xs font-medium text-[#5a5c5e] uppercase tracking-wider" }, "Passos"),
        React.createElement("ol", { className: "space-y-1" }, result.steps.map((s, i) => React.createElement("li", { key: i, className: "flex gap-2 text-sm text-zinc-600" },
          React.createElement("span", { className: "text-violet-400/60 font-mono shrink-0" }, i + 1 + "."), s)))
      ),
      result.result && React.createElement("div", { className: "rounded-xl border border-violet-500/20 bg-violet-500/8 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-0.5" }, "Resultado"),
        React.createElement("p", { className: "font-mono text-lg text-violet-200" }, result.result)
      ),
      result.interpretation && React.createElement("p", { className: "text-sm text-zinc-500 italic" }, result.interpretation),
      result.ai_solution && React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-4" },
        React.createElement("p", { className: "mb-2 text-xs text-zinc-500 uppercase tracking-wider" }, "Resolução detalhada"),
        React.createElement("div", { className: "whitespace-pre-wrap text-sm text-zinc-900/75 leading-relaxed" }, result.ai_solution)
      ),
      result.explanation && React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-4" },
        React.createElement("p", { className: "mb-1 text-xs text-zinc-500 uppercase tracking-wider" }, "Explicação pedagógica"),
        React.createElement("p", { className: "text-sm text-zinc-600 leading-relaxed" }, result.explanation)
      )
    )
  );
}

// ─── Chemistry: Equation Balancer ────────────────────────────────────────

function QuimicaLab() {
  const [equation, setEquation] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { educationCompute: compute } = { educationCompute: educationCompute };

  const balance = async () => {
    if (!equation.trim()) return;
    setLoading(true); setResult(null);
    try {
      const r = await educationCompute(equation + " (balancear equação química)", "auto", "x");
      setResult(r);
    } catch (e) { setResult({ ai_solution: "Erro: " + e.message }); }
    finally { setLoading(false); }
  };

  const EXAMPLES = ["H2 + O2 → H2O", "C3H8 + O2 → CO2 + H2O", "Fe + HCl → FeCl2 + H2", "Na + H2O → NaOH + H2"];

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("div", { className: "rounded-2xl border border-emerald-500/15 bg-white p-5" },
      React.createElement("p", { className: "mb-3 text-xs text-zinc-500 uppercase tracking-wider" }, "Balanceador de Equações Químicas"),
      React.createElement("div", { className: "flex gap-2" },
        React.createElement("input", { value: equation, onChange: e => setEquation(e.target.value), onKeyDown: e => e.key === "Enter" && balance(), className: "flex-1 rounded-xl border border-emerald-500/25 bg-zinc-50 px-3 py-2 text-sm font-mono text-emerald-200 focus:outline-none focus:border-emerald-400/50", placeholder: "H2 + O2 → H2O" }),
        React.createElement("button", { onClick: balance, disabled: loading || !equation.trim(), className: "rounded-xl bg-emerald-600/80 border border-emerald-500/40 px-4 py-2 text-sm font-medium text-zinc-900 disabled:opacity-50" }, loading ? "..." : "Balancear")
      ),
      React.createElement("div", { className: "mt-3 flex flex-wrap gap-1.5" },
        EXAMPLES.map(ex => React.createElement("button", { key: ex, onClick: () => setEquation(ex), className: "rounded-lg border border-zinc-200 px-2 py-1 text-xs font-mono text-zinc-500 hover:text-emerald-300 hover:border-emerald-500/30 transition-all" }, ex))
      )
    ),
    result && React.createElement(motion.div, { className: "rounded-2xl border border-emerald-500/10 bg-white p-5", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
      (result.ai_solution || result.explanation || result.interpretation) &&
        React.createElement("div", { className: "whitespace-pre-wrap text-sm text-zinc-900/75 leading-relaxed" },
          result.ai_solution || result.explanation || result.interpretation)
    )
  );
}

// ─── Engineering: Circuit Calculator ─────────────────────────────────────

function CircuitoLab() {
  const canvasRef = useRef(null);
  const [mode, setMode] = useState("serie"); // serie | paralelo | divisor
  const [r1, setR1] = useState(100);
  const [r2, setR2] = useState(220);
  const [v, setV] = useState(12);

  const calc = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#f1f5f9";
    ctx.fillRect(0, 0, W, H);

    let rTotal, i1, i2, iTot, v1, v2;

    if (mode === "serie") {
      rTotal = r1 + r2;
      iTot = v / rTotal;
      v1 = iTot * r1; v2 = iTot * r2;
    } else if (mode === "paralelo") {
      rTotal = (r1 * r2) / (r1 + r2);
      i1 = v / r1; i2 = v / r2; iTot = i1 + i2;
    } else {
      rTotal = r1 + r2;
      iTot = v / rTotal;
      v1 = iTot * r1; v2 = iTot * r2;
    }

    ctx.strokeStyle = "rgba(251,191,36,0.7)";
    ctx.lineWidth = 2.5;

    if (mode === "serie") {
      // Draw series circuit
      const pts = [[60,80],[240,80],[240,200],[60,200],[60,80]];
      ctx.beginPath(); pts.forEach(([x,y], i) => i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y)); ctx.stroke();

      // R1 label
      ctx.fillStyle = "rgba(15,23,42,0.9)";
      ctx.fillRect(90,65,70,30); ctx.strokeStyle = "rgba(251,191,36,0.5)"; ctx.strokeRect(90,65,70,30);
      ctx.fillStyle = "rgba(251,191,36,0.9)"; ctx.font = "11px monospace"; ctx.textAlign = "center";
      ctx.fillText(`R1=${r1}Ω`, 125, 85);

      // R2 label
      ctx.fillStyle = "rgba(15,23,42,0.9)";
      ctx.fillRect(90,185,70,30); ctx.strokeStyle = "rgba(251,191,36,0.5)"; ctx.strokeRect(90,185,70,30);
      ctx.fillStyle = "rgba(251,191,36,0.9)";
      ctx.fillText(`R2=${r2}Ω`, 125, 205);

      // Battery
      ctx.fillStyle = "rgba(56,189,248,0.15)"; ctx.fillRect(30,110,30,60);
      ctx.strokeStyle = "rgba(56,189,248,0.6)"; ctx.strokeRect(30,110,30,60);
      ctx.fillStyle = "rgba(56,189,248,0.9)"; ctx.fillText(`${v}V`, 45, 145);
    } else {
      // Parallel
      ctx.beginPath();
      ctx.moveTo(60,60); ctx.lineTo(250,60);
      ctx.moveTo(60,200); ctx.lineTo(250,200);
      ctx.moveTo(60,60); ctx.lineTo(60,200);
      ctx.moveTo(250,60); ctx.lineTo(250,200);
      ctx.moveTo(130,60); ctx.lineTo(130,200);
      ctx.stroke();

      ctx.fillStyle = "rgba(15,23,42,0.9)"; ctx.fillRect(85,110,50,40); ctx.strokeStyle = "rgba(251,191,36,0.5)"; ctx.strokeRect(85,110,50,40);
      ctx.fillStyle = "rgba(251,191,36,0.9)"; ctx.font = "11px monospace"; ctx.textAlign = "center";
      ctx.fillText(`R1=${r1}Ω`, 110, 135);

      ctx.fillStyle = "rgba(15,23,42,0.9)"; ctx.fillRect(155,110,50,40); ctx.strokeStyle = "rgba(251,191,36,0.5)"; ctx.strokeRect(155,110,50,40);
      ctx.fillStyle = "rgba(251,191,36,0.9)";
      ctx.fillText(`R2=${r2}Ω`, 180, 135);
    }

    // Results panel
    const results = mode === "serie"
      ? [`Rt = ${rTotal.toFixed(1)} Ω`, `I = ${(iTot * 1000).toFixed(2)} mA`, `V₁ = ${v1.toFixed(2)} V`, `V₂ = ${v2.toFixed(2)} V`]
      : [`Rt = ${rTotal.toFixed(1)} Ω`, `It = ${(iTot * 1000).toFixed(2)} mA`, `I₁ = ${(i1 * 1000).toFixed(2)} mA`, `I₂ = ${(i2 * 1000).toFixed(2)} mA`];

    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(148,163,184,0.5)"; ctx.font = "11px monospace";
    ctx.fillText("Resultados:", W - 180, 70);
    results.forEach((r, i) => {
      ctx.fillStyle = "rgba(251,191,36,0.85)"; ctx.font = "bold 12px monospace";
      ctx.fillText(r, W - 180, 90 + i * 20);
    });
  }, [mode, r1, r2, v]);

  useEffect(() => { calc(); }, [calc]);

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 500, height: 260, className: "w-full rounded-xl border border-zinc-200 bg-[#f1f5f9]" }),
    React.createElement("div", { className: "flex gap-2" },
      ["serie", "paralelo"].map(m => React.createElement("button", { key: m, onClick: () => setMode(m), className: `rounded-xl px-3 py-1.5 text-xs font-medium transition-all capitalize ${mode === m ? "bg-amber-600/70 border border-amber-500/40 text-zinc-900" : "border border-zinc-200 text-zinc-500 hover:text-zinc-900"}` }, m === "serie" ? "Série" : "Paralelo"))
    ),
    React.createElement("div", { className: "grid grid-cols-3 gap-4" },
      [["R1 (Ω)", r1, setR1, 10, 1000, 10], ["R2 (Ω)", r2, setR2, 10, 1000, 10], ["Tensão (V)", v, setV, 1, 50, 1]].map(([label, val, setter, min, max, step]) =>
        React.createElement("div", { key: label },
          React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, label, ": ", React.createElement("span", { className: "text-[#5a5c5e] font-mono" }, val)),
          React.createElement("input", { type: "range", min, max, step, value: val, onChange: e => setter(Number(e.target.value)), className: "w-full accent-amber-500" })
        )
      )
    )
  );
}

// ─── Programming: Code Sandbox ────────────────────────────────────────────

function CodigoLab() {
  const [code, setCode] = useState(`# Exemplo: Sequência de Fibonacci
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a + b

fibonacci(10)
`);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("python");

  const run = async () => {
    setLoading(true); setResult(null);
    try {
      const r = await educationCodeSandbox(code, language);
      setResult(r);
    } catch (e) { setResult({ error: e.message }); }
    finally { setLoading(false); }
  };

  const EXAMPLES = {
    python: [
      ["Fibonacci", `def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a, end=" ")\n        a, b = b, a + b\n\nfibonacci(10)`],
      ["Bubble Sort", `def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n\nprint(bubble_sort([64, 34, 25, 12, 22, 11, 90]))`],
      ["NumPy", `import numpy as np\nA = np.array([[1,2],[3,4]])\nprint("Matriz:", A)\nprint("Determinante:", np.linalg.det(A))\nprint("Inversa:", np.linalg.inv(A))`],
    ],
    javascript: [
      ["Array methods", `const nums = [1,2,3,4,5,6,7,8,9,10];\nconst evens = nums.filter(n => n % 2 === 0);\nconst doubled = evens.map(n => n * 2);\nconsole.log(doubled);`],
    ],
  };

  return React.createElement("div", { className: "space-y-3" },
    React.createElement("div", { className: "flex items-center justify-between" },
      React.createElement("div", { className: "flex gap-1.5" },
        ["python", "javascript"].map(lang => React.createElement("button", { key: lang, onClick: () => setLanguage(lang), className: `rounded-xl px-3 py-1 text-xs font-medium transition-all ${language === lang ? "bg-rose-600/70 border border-rose-500/40 text-zinc-900" : "border border-zinc-200 text-zinc-500 hover:text-zinc-900"}` }, lang))
      ),
      React.createElement("div", { className: "flex flex-wrap gap-1.5" },
        (EXAMPLES[language] || []).map(([label]) => React.createElement("button", { key: label, onClick: () => setCode(EXAMPLES[language].find(e => e[0] === label)[1]), className: "rounded-lg border border-zinc-200 px-2 py-1 text-xs text-zinc-500 hover:text-rose-300 hover:border-rose-500/25 transition-all" }, label))
      )
    ),
    React.createElement("textarea", { value: code, onChange: e => setCode(e.target.value), rows: 10, className: "w-full rounded-xl border border-zinc-200 bg-[rgba(8,15,30,0.9)] px-4 py-3 font-mono text-sm text-zinc-800 leading-relaxed focus:outline-none focus:border-rose-500/30 resize-y" }),
    React.createElement("button", { onClick: run, disabled: loading || !code.trim(), className: "inline-flex items-center gap-1.5 rounded-xl bg-rose-600/80 border border-rose-500/40 px-4 py-2 text-sm font-medium text-zinc-900 disabled:opacity-50" },
      loading ? React.createElement(React.Fragment, null, React.createElement("span", { className: "h-3.5 w-3.5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600" }), "Executando...") : React.createElement(React.Fragment, null, React.createElement(PlayIcon, null), "Executar")
    ),
    result && React.createElement(motion.div, { className: "space-y-2", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
      result.stdout && React.createElement("div", { className: "rounded-xl border border-emerald-500/15 bg-zinc-50 p-4" },
        React.createElement("p", { className: "mb-1 text-xs text-[#5a5c5e]/70 uppercase tracking-wider" }, "Saída"),
        React.createElement("pre", { className: "font-mono text-sm text-emerald-300 whitespace-pre-wrap" }, result.stdout)
      ),
      (result.stderr || result.error) && React.createElement("div", { className: "rounded-xl border border-red-500/15 bg-[rgba(30,8,8,0.5)] p-4" },
        React.createElement("p", { className: "mb-1 text-xs text-red-400/70 uppercase tracking-wider" }, "Erro"),
        React.createElement("pre", { className: "font-mono text-sm text-red-300 whitespace-pre-wrap" }, result.stderr || result.error)
      ),
      (result.code_analysis || result.debug_analysis) && React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-[rgba(15,23,42,0.7)] p-4" },
        React.createElement("p", { className: "mb-2 text-xs text-zinc-500 uppercase tracking-wider" }, result.debug_analysis ? "Análise de erro" : "Análise de código"),
        React.createElement("div", { className: "whitespace-pre-wrap text-sm text-zinc-600 leading-relaxed" }, result.code_analysis || result.debug_analysis)
      )
    )
  );
}

// ─── Statistics Lab ───────────────────────────────────────────────────────

function EstatisticaLab() {
  const canvasRef = useRef(null);
  const [data, setData] = useState("12 15 18 22 25 28 30 32 35 18 21 24");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true); setResult(null);
    try {
      const r = await educationCompute(data, "estatistica", "x");
      setResult(r);
      if (r.result && typeof r.result === "object") {
        drawHistogram(data.trim().split(/[\s,]+/).map(Number).filter(n => !isNaN(n)));
      }
    } catch (e) { setResult({ error: e.message }); }
    finally { setLoading(false); }
  };

  const drawHistogram = (nums) => {
    const canvas = canvasRef.current;
    if (!canvas || !nums.length) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#f1f5f9"; ctx.fillRect(0, 0, W, H);

    const mn = Math.min(...nums), mx = Math.max(...nums);
    const bins = 8;
    const binSize = (mx - mn) / bins;
    const counts = new Array(bins).fill(0);
    nums.forEach(n => { const bi = Math.min(Math.floor((n - mn) / binSize), bins - 1); counts[bi]++; });
    const maxCount = Math.max(...counts);

    const pad = 30, barW = (W - 2 * pad) / bins;
    counts.forEach((c, i) => {
      const bh = (c / maxCount) * (H - 2 * pad - 20);
      const bx = pad + i * barW + 2;
      const by = H - pad - bh;
      const grad = ctx.createLinearGradient(bx, by, bx, H - pad);
      grad.addColorStop(0, "rgba(139,92,246,0.9)");
      grad.addColorStop(1, "rgba(79,70,229,0.3)");
      ctx.fillStyle = grad;
      ctx.fillRect(bx, by, barW - 4, bh);
      ctx.fillStyle = "rgba(148,163,184,0.5)";
      ctx.font = "9px monospace"; ctx.textAlign = "center";
      const lb = (mn + i * binSize).toFixed(1);
      ctx.fillText(lb, bx + (barW - 4) / 2, H - pad + 10);
      if (c > 0) { ctx.fillStyle = "rgba(167,139,250,0.8)"; ctx.fillText(c, bx + (barW - 4) / 2, by - 4); }
    });
  };

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("div", null,
      React.createElement("label", { className: "mb-1 block text-xs text-zinc-500" }, "Dados (separados por espaço ou vírgula)"),
      React.createElement("div", { className: "flex gap-2" },
        React.createElement("input", { value: data, onChange: e => setData(e.target.value), className: "flex-1 rounded-xl border border-violet-500/25 bg-white px-3 py-2 text-sm font-mono text-violet-200 focus:outline-none", placeholder: "12 15 18 22 25 ..." }),
        React.createElement("button", { onClick: analyze, disabled: loading, className: "rounded-xl bg-[#1a1c1e] border border-[rgba(20,24,30,0.1)] px-4 py-2 text-sm font-medium text-zinc-900 disabled:opacity-50" }, loading ? "..." : "Analisar")
      )
    ),
    React.createElement("canvas", { ref: canvasRef, width: 500, height: 200, className: "w-full rounded-xl border border-zinc-200 bg-[#f1f5f9]" }),
    result && !result.error && React.createElement(motion.div, { className: "grid grid-cols-2 gap-2 sm:grid-cols-4", initial: { opacity: 0 }, animate: { opacity: 1 } },
      result.steps && result.steps.slice(2).map((s, i) =>
        React.createElement("div", { key: i, className: "rounded-xl border border-[rgba(20,24,30,0.06)] bg-violet-500/5 p-3" },
          React.createElement("p", { className: "font-mono text-sm text-violet-200" }, s)
        )
      )
    )
  );
}

// ─── Lab component map ────────────────────────────────────────────────────

// ─── Physics: Pendulum ───────────────────────────────────────────────────────

function PenduloLab() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const stateRef = useRef({ angle: Math.PI / 3, omega: 0, t: 0 });
  const [length, setLength] = useState(150);
  const [damping, setDamping] = useState(0.005);
  const [running, setRunning] = useState(false);
  const [period, setPeriod] = useState(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = 70;
    const s = stateRef.current;
    const px = cx + length * Math.sin(s.angle);
    const py = cy + length * Math.cos(s.angle);
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "rgba(10,18,36,0.95)";
    ctx.fillRect(0, 0, W, H);
    // pivot
    ctx.beginPath(); ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#64748b"; ctx.fill();
    // rod
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(px, py);
    ctx.strokeStyle = "#475569"; ctx.lineWidth = 2; ctx.stroke();
    // bob
    ctx.beginPath(); ctx.arc(px, py, 14, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(px - 4, py - 4, 2, px, py, 14);
    grad.addColorStop(0, "#7dd3fc"); grad.addColorStop(1, "#0ea5e9");
    ctx.fillStyle = grad; ctx.fill();
    // info
    ctx.fillStyle = "rgba(255,255,255,0.4)"; ctx.font = "11px monospace";
    ctx.fillText(`θ = ${(s.angle * 180 / Math.PI).toFixed(1)}°`, 10, 20);
    ctx.fillText(`ω = ${s.omega.toFixed(3)} rad/s`, 10, 36);
    ctx.fillText(`t = ${s.t.toFixed(2)} s`, 10, 52);
  }, [length]);

  const step = useCallback(() => {
    const s = stateRef.current;
    const g = 9.81, dt = 0.016;
    const alpha = -(g / (length / 100)) * Math.sin(s.angle) - damping * s.omega;
    s.omega += alpha * dt;
    s.angle += s.omega * dt;
    s.t += dt;
    draw();
    animRef.current = requestAnimationFrame(step);
  }, [length, damping, draw]);

  useEffect(() => {
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [draw]);

  useEffect(() => {
    const T = 2 * Math.PI * Math.sqrt((length / 100) / 9.81);
    setPeriod(T);
  }, [length]);

  const toggle = () => {
    if (running) { cancelAnimationFrame(animRef.current); setRunning(false); }
    else { animRef.current = requestAnimationFrame(step); setRunning(true); }
  };
  const reset = () => {
    cancelAnimationFrame(animRef.current); setRunning(false);
    stateRef.current = { angle: Math.PI / 3, omega: 0, t: 0 }; draw();
  };

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 400, height: 320, className: "w-full rounded-xl border border-zinc-200" }),
    React.createElement("div", { className: "grid gap-4 sm:grid-cols-3" },
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-1.5" }, `Comprimento: ${length} px`),
        React.createElement("input", { type: "range", min: 60, max: 220, value: length, onChange: e => { setLength(+e.target.value); reset(); }, className: "w-full accent-sky-400" })
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-1.5" }, `Amortecimento: ${damping.toFixed(3)}`),
        React.createElement("input", { type: "range", min: 0, max: 0.05, step: 0.001, value: damping, onChange: e => setDamping(+e.target.value), className: "w-full accent-sky-400" })
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-1" }, "Período teórico"),
        React.createElement("p", { className: "text-lg font-bold text-[#5a5c5e]" }, `T = ${period.toFixed(3)} s`),
        React.createElement("p", { className: "text-xs text-zinc-400 mt-0.5" }, "T = 2π √(L/g)")
      )
    ),
    React.createElement("div", { className: "flex gap-3" },
      React.createElement("button", { onClick: toggle, className: `flex-1 rounded-xl border py-2 text-sm font-medium transition-all ${running ? "border-sky-500/30 bg-[#f1f2f4] text-[#5a5c5e]" : "border-zinc-200 bg-zinc-50 text-zinc-900 hover:bg-white"}` }, running ? "Pausar" : "Iniciar"),
      React.createElement("button", { onClick: reset, className: "rounded-xl border border-zinc-200 bg-zinc-100 px-4 py-2 text-sm text-zinc-500 hover:bg-white" }, "Reset")
    )
  );
}

// ─── Physics: Wave Interference ─────────────────────────────────────────────

function OndasLab() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const tRef = useRef(0);
  const [f1, setF1] = useState(1.0);
  const [f2, setF2] = useState(1.3);
  const [a1, setA1] = useState(1.0);
  const [a2, setA2] = useState(0.8);
  const [running, setRunning] = useState(false);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "rgba(10,18,36,0.97)";
    ctx.fillRect(0, 0, W, H);

    const N = W;
    const mid1 = H * 0.22, mid2 = H * 0.5, mid3 = H * 0.78;
    const scaleY = H * 0.1;
    const t = tRef.current;

    const draw_wave = (midY, color, fn) => {
      ctx.beginPath();
      for (let x = 0; x < N; x++) {
        const xRad = (x / N) * 2 * Math.PI * 3;
        const y = midY - fn(xRad, t) * scaleY;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = color; ctx.lineWidth = 1.8; ctx.stroke();
    };

    // labels
    ctx.fillStyle = "rgba(255,255,255,0.25)"; ctx.font = "10px monospace";
    ctx.fillText(`Onda 1 — f=${f1.toFixed(1)} Hz, A=${a1.toFixed(1)}`, 8, mid1 - scaleY - 6);
    ctx.fillText(`Onda 2 — f=${f2.toFixed(1)} Hz, A=${a2.toFixed(1)}`, 8, mid2 - scaleY - 6);
    ctx.fillText("Superposição", 8, mid3 - scaleY - 6);

    draw_wave(mid1, "#38bdf8", (x, t) => a1 * Math.sin(x * f1 - t * f1 * 2));
    draw_wave(mid2, "#a78bfa", (x, t) => a2 * Math.sin(x * f2 - t * f2 * 2));
    draw_wave(mid3, "#4ade80", (x, t) =>
      a1 * Math.sin(x * f1 - t * f1 * 2) + a2 * Math.sin(x * f2 - t * f2 * 2)
    );

    // zero lines
    [mid1, mid2, mid3].forEach(m => {
      ctx.beginPath(); ctx.moveTo(0, m); ctx.lineTo(W, m);
      ctx.strokeStyle = "rgba(255,255,255,0.06)"; ctx.lineWidth = 1; ctx.stroke();
    });
  }, [f1, f2, a1, a2]);

  const animate = useCallback(() => {
    tRef.current += 0.04;
    draw();
    animRef.current = requestAnimationFrame(animate);
  }, [draw]);

  useEffect(() => { draw(); return () => cancelAnimationFrame(animRef.current); }, [draw]);

  const toggle = () => {
    if (running) { cancelAnimationFrame(animRef.current); setRunning(false); }
    else { animRef.current = requestAnimationFrame(animate); setRunning(true); }
  };

  const isBeat = Math.abs(f1 - f2) < 0.3;

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 600, height: 280, className: "w-full rounded-xl border border-zinc-200" }),
    isBeat && React.createElement("div", { className: "rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-[#5a5c5e]" },
      "Batimento detectado: as frequências são próximas — observe a modulação de amplitude na superposição."
    ),
    React.createElement("div", { className: "grid grid-cols-2 gap-3 sm:grid-cols-4" },
      [
        { label: `f₁ = ${f1.toFixed(1)} Hz`, val: f1, set: setF1, min: 0.2, max: 3, step: 0.1, color: "accent-sky-400" },
        { label: `A₁ = ${a1.toFixed(1)}`, val: a1, set: setA1, min: 0.1, max: 2, step: 0.1, color: "accent-sky-400" },
        { label: `f₂ = ${f2.toFixed(1)} Hz`, val: f2, set: setF2, min: 0.2, max: 3, step: 0.1, color: "accent-violet-400" },
        { label: `A₂ = ${a2.toFixed(1)}`, val: a2, set: setA2, min: 0.1, max: 2, step: 0.1, color: "accent-violet-400" },
      ].map(ctrl =>
        React.createElement("div", { key: ctrl.label, className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
          React.createElement("p", { className: "text-xs text-zinc-500 mb-1.5" }, ctrl.label),
          React.createElement("input", { type: "range", min: ctrl.min, max: ctrl.max, step: ctrl.step, value: ctrl.val, onChange: e => ctrl.set(+e.target.value), className: `w-full ${ctrl.color}` })
        )
      )
    ),
    React.createElement("button", { onClick: toggle, className: `w-full rounded-xl border py-2 text-sm font-medium transition-all ${running ? "border-green-500/30 bg-green-500/10 text-green-300" : "border-zinc-200 bg-zinc-50 text-zinc-900 hover:bg-white"}` }, running ? "Pausar animação" : "Animar ondas")
  );
}

// ─── CS: Sorting Algorithm Visualizer ────────────────────────────────────────

/** Valores determinísticos (SSR = cliente). Math.random() no 1.º render quebra hidratação (#418). */
function makeSortLabInitialArray() {
  var a = [];
  for (var i = 0; i < 30; i++) {
    a.push(5 + ((i * 7919 + 13) % 95));
  }
  return a;
}

function AlgoritmosLab() {
  const [array, setArray] = useState(makeSortLabInitialArray);
  const [algo, setAlgo] = useState("bubble");
  const [running, setRunning] = useState(false);
  const [highlights, setHighlights] = useState([]);
  const [sorted, setSorted] = useState([]);
  const [speed, setSpeed] = useState(60);
  const runRef = useRef(false);

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  const newArray = () => {
    if (runRef.current) return;
    setArray(Array.from({ length: 30 }, () => Math.floor(Math.random() * 95) + 5));
    setHighlights([]); setSorted([]);
  };

  const bubbleSort = async (arr) => {
    const a = [...arr];
    const n = a.length;
    const done = new Set();
    for (let i = 0; i < n - 1; i++) {
      for (let j = 0; j < n - i - 1; j++) {
        if (!runRef.current) return;
        setHighlights([j, j + 1]);
        if (a[j] > a[j + 1]) { [a[j], a[j + 1]] = [a[j + 1], a[j]]; setArray([...a]); }
        await sleep(speed);
      }
      done.add(n - 1 - i); setSorted([...done]);
    }
    done.add(0); setSorted([...done]);
  };

  const insertionSort = async (arr) => {
    const a = [...arr];
    const done = new Set();
    for (let i = 1; i < a.length; i++) {
      if (!runRef.current) return;
      let j = i;
      while (j > 0 && a[j - 1] > a[j]) {
        setHighlights([j - 1, j]);
        [a[j - 1], a[j]] = [a[j], a[j - 1]];
        setArray([...a]);
        j--;
        await sleep(speed);
        if (!runRef.current) return;
      }
      done.add(i); setSorted([...done]);
    }
    setSorted(Array.from({ length: a.length }, (_, i) => i));
  };

  const mergeSort = async (arr) => {
    const a = [...arr];
    const merge = async (l, m, r) => {
      const left = a.slice(l, m + 1), right = a.slice(m + 1, r + 1);
      let i = 0, j = 0, k = l;
      while (i < left.length && j < right.length) {
        if (!runRef.current) return;
        setHighlights([k]);
        if (left[i] <= right[j]) { a[k++] = left[i++]; }
        else { a[k++] = right[j++]; }
        setArray([...a]);
        await sleep(speed);
      }
      while (i < left.length) { a[k++] = left[i++]; setArray([...a]); await sleep(speed / 2); }
      while (j < right.length) { a[k++] = right[j++]; setArray([...a]); await sleep(speed / 2); }
    };
    const sort = async (l, r) => {
      if (l >= r || !runRef.current) return;
      const m = Math.floor((l + r) / 2);
      await sort(l, m); await sort(m + 1, r); await merge(l, m, r);
    };
    await sort(0, a.length - 1);
    setSorted(Array.from({ length: a.length }, (_, i) => i));
  };

  const run = async () => {
    if (running) { runRef.current = false; setRunning(false); return; }
    runRef.current = true; setRunning(true); setSorted([]); setHighlights([]);
    const fns = { bubble: bubbleSort, insertion: insertionSort, merge: mergeSort };
    await fns[algo](array);
    runRef.current = false; setRunning(false); setHighlights([]);
  };

  const maxVal = Math.max(...array);
  const barW = 100 / array.length;

  return React.createElement("div", { className: "space-y-4" },
    // Bar chart
    React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-100 p-3 h-40 flex items-end gap-px" },
      array.map((v, i) => {
        const isHighlight = highlights.includes(i);
        const isSorted = sorted.includes(i);
        return React.createElement("div", {
          key: i,
          style: { height: `${(v / maxVal) * 100}%`, width: `${barW}%` },
          className: `rounded-t transition-all ${isSorted ? "bg-emerald-400" : isHighlight ? "bg-amber-400" : "bg-sky-500/70"}`,
        });
      })
    ),
    // Controls
    React.createElement("div", { className: "grid gap-3 sm:grid-cols-3" },
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-2" }, "Algoritmo"),
        React.createElement("div", { className: "flex gap-1.5 flex-wrap" },
          [["bubble", "Bubble"], ["insertion", "Insertion"], ["merge", "Merge"]].map(([id, label]) =>
            React.createElement("button", {
              key: id, onClick: () => { if (!running) setAlgo(id); },
              className: `rounded-lg border px-2.5 py-1 text-xs transition-colors ${algo === id ? "border-rose-500/30 bg-rose-500/10 text-rose-300" : "border-zinc-200 text-zinc-500 hover:text-zinc-600"}`,
            }, label)
          )
        )
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-1.5" }, `Velocidade: ${speed}ms`),
        React.createElement("input", { type: "range", min: 5, max: 200, value: speed, onChange: e => setSpeed(+e.target.value), className: "w-full accent-rose-400" })
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3 flex flex-col justify-between" },
        React.createElement("p", { className: "text-xs text-zinc-400" }, "Complexidade"),
        React.createElement("p", { className: "text-xs text-zinc-500 font-mono" },
          algo === "bubble" ? "O(n²) pior caso" : algo === "insertion" ? "O(n²) pior, O(n) melhor" : "O(n log n) garantido"
        )
      )
    ),
    React.createElement("div", { className: "flex gap-3" },
      React.createElement("button", { onClick: run, className: `flex-1 rounded-xl border py-2 text-sm font-medium transition-all ${running ? "border-amber-500/30 bg-amber-500/10 text-[#5a5c5e]" : "border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20"}` }, running ? "Parar" : "Ordenar"),
      React.createElement("button", { onClick: newArray, disabled: running, className: "rounded-xl border border-zinc-200 bg-zinc-100 px-4 py-2 text-sm text-zinc-500 hover:bg-white disabled:opacity-30" }, "Novo array")
    )
  );
}

// ─── Math: Fourier Series ────────────────────────────────────────────────────

function FourierLab() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const tRef = useRef(0);
  const [terms, setTerms] = useState(5);
  const [wave, setWave] = useState("square"); // square | sawtooth | triangle
  const [running, setRunning] = useState(false);

  const getCoeff = (wave, n) => {
    if (n % 2 === 0) return 0;
    if (wave === "square") return 4 / (Math.PI * n);
    if (wave === "sawtooth") return (n % 2 === 0 ? 1 : -1) * 2 / (Math.PI * n);
    if (wave === "triangle") return (n % 2 === 0 ? 0 : (8 / (Math.PI * Math.PI * n * n)) * (n % 4 === 1 ? 1 : -1));
    return 0;
  };

  const computeApprox = (x, terms, wave) => {
    let sum = 0;
    for (let n = 1; n <= terms * 2; n += 2) {
      sum += getCoeff(wave, n) * Math.sin(n * x);
    }
    return sum;
  };

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "rgba(10,18,36,0.97)";
    ctx.fillRect(0, 0, W, H);

    const mid = H / 2;
    const scaleY = H * 0.35;
    const t = tRef.current;

    // Draw target wave
    ctx.beginPath();
    for (let px = 0; px < W; px++) {
      const x = (px / W) * 4 * Math.PI + t;
      let y;
      if (wave === "square") y = x % (2 * Math.PI) < Math.PI ? 1 : -1;
      else if (wave === "sawtooth") y = 2 * ((x / (2 * Math.PI)) % 1) - 1;
      else y = 2 * Math.abs(2 * ((x / (2 * Math.PI)) % 1) - 1) - 1;
      const cy = mid - y * scaleY;
      px === 0 ? ctx.moveTo(px, cy) : ctx.lineTo(px, cy);
    }
    ctx.strokeStyle = "rgba(255,255,255,0.12)"; ctx.lineWidth = 2; ctx.stroke();

    // Draw each harmonic
    for (let k = 1; k <= terms; k++) {
      const n = 2 * k - 1;
      const coeff = getCoeff(wave, n);
      ctx.beginPath();
      for (let px = 0; px < W; px++) {
        const x = (px / W) * 4 * Math.PI + t;
        const y = coeff * Math.sin(n * x);
        const cy = mid - y * scaleY;
        px === 0 ? ctx.moveTo(px, cy) : ctx.lineTo(px, cy);
      }
      const hue = (k / terms) * 260 + 180;
      ctx.strokeStyle = `hsla(${hue},80%,65%,0.5)`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw approximation
    ctx.beginPath();
    for (let px = 0; px < W; px++) {
      const x = (px / W) * 4 * Math.PI + t;
      const y = computeApprox(x, terms, wave);
      const cy = mid - y * scaleY;
      px === 0 ? ctx.moveTo(px, cy) : ctx.lineTo(px, cy);
    }
    ctx.strokeStyle = "#34d399"; ctx.lineWidth = 2.5; ctx.stroke();

    // Zero line
    ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(W, mid);
    ctx.strokeStyle = "rgba(255,255,255,0.08)"; ctx.lineWidth = 1; ctx.stroke();

    // Labels
    ctx.fillStyle = "rgba(255,255,255,0.3)"; ctx.font = "10px monospace";
    ctx.fillText(`Série de Fourier · ${terms} harmônico${terms > 1 ? "s" : ""}`, 8, 16);
    ctx.fillStyle = "#34d399"; ctx.fillText("— aproximação", W - 100, 16);
    ctx.fillStyle = "rgba(255,255,255,0.15)"; ctx.fillText("— função alvo", W - 100, 30);
  }, [terms, wave]);

  const animate = useCallback(() => {
    tRef.current += 0.025;
    draw();
    animRef.current = requestAnimationFrame(animate);
  }, [draw]);

  useEffect(() => { draw(); return () => cancelAnimationFrame(animRef.current); }, [draw]);

  const toggle = () => {
    if (running) { cancelAnimationFrame(animRef.current); setRunning(false); }
    else { animRef.current = requestAnimationFrame(animate); setRunning(true); }
  };

  const waveNames = { square: "Quadrada", sawtooth: "Dente-de-serra", triangle: "Triangular" };

  return React.createElement("div", { className: "space-y-4" },
    React.createElement("canvas", { ref: canvasRef, width: 600, height: 260, className: "w-full rounded-xl border border-zinc-200" }),
    React.createElement("div", { className: "grid gap-3 sm:grid-cols-3" },
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-2" }, "Tipo de onda"),
        React.createElement("div", { className: "flex gap-1.5" },
          Object.entries(waveNames).map(([id, label]) =>
            React.createElement("button", {
              key: id, onClick: () => { setWave(id); cancelAnimationFrame(animRef.current); setRunning(false); },
              className: `rounded-lg border px-2.5 py-1 text-xs transition-colors ${wave === id ? "border-[rgba(20,24,30,0.1)] bg-violet-500/15 text-[#5a5c5e]" : "border-zinc-200 text-zinc-500 hover:text-zinc-600"}`,
            }, label)
          )
        )
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3" },
        React.createElement("p", { className: "text-xs text-zinc-500 mb-1.5" }, `Harmônicos: ${terms} (n = 1, 3, … ${2 * terms - 1})`),
        React.createElement("input", { type: "range", min: 1, max: 20, value: terms, onChange: e => setTerms(+e.target.value), className: "w-full accent-violet-400" })
      ),
      React.createElement("div", { className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3 space-y-1" },
        React.createElement("p", { className: "text-xs text-zinc-400" }, "Fórmula"),
        React.createElement("p", { className: "font-mono text-xs text-violet-200" },
          wave === "square" ? "f(x) = Σ (4/nπ) sin(nx)" : wave === "sawtooth" ? "f(x) = Σ (2/nπ)(-1)ⁿ sin(nx)" : "f(x) = Σ (8/n²π²) sin(nx)"
        ),
        React.createElement("p", { className: "text-[10px] text-zinc-400" }, "n ímpar")
      )
    ),
    React.createElement("button", { onClick: toggle, className: `w-full rounded-xl border py-2 text-sm font-medium transition-all ${running ? "border-[rgba(20,24,30,0.1)] bg-violet-500/10 text-[#5a5c5e]" : "border-zinc-200 bg-zinc-50 text-zinc-900 hover:bg-white"}` }, running ? "Pausar animação" : "Animar onda")
  );
}

const LAB_COMPONENTS = {
  projetil: ProjetilLab,
  mola: MolaLab,
  pendulo: PenduloLab,
  ondas: OndasLab,
  funcao: FuncaoLab,
  calculo: CalculoLab,
  quimica: QuimicaLab,
  circuito: CircuitoLab,
  codigo: CodigoLab,
  estatistica: EstatisticaLab,
  algoritmos: AlgoritmosLab,
  fourier: FourierLab,
};

// ─── Main Page ────────────────────────────────────────────────────────────

export default function LaboratoriosPage() {
  const [activeLab, setActiveLab] = useState(null);
  const [filter, setFilter] = useState("Todos");

  const categories = ["Todos", ...Array.from(new Set(LABS.map(l => l.category)))];
  const filtered = filter === "Todos" ? LABS : LABS.filter(l => l.category === filter);

  if (activeLab) {
    const lab = LABS.find(l => l.id === activeLab);
    const LabComp = LAB_COMPONENTS[activeLab];
    const borderColor = CATEGORY_COLORS[lab?.category] || "border-zinc-200";

    return React.createElement(AppShell, null,
      React.createElement("div", { className: "py-6 space-y-5" },
        React.createElement("div", { className: "flex items-center justify-between flex-wrap gap-3" },
          React.createElement("div", { className: "flex items-center gap-3" },
            React.createElement("button", { onClick: () => setActiveLab(null), className: "inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-500 hover:text-zinc-900" }, React.createElement(BackIcon, null), "Laboratórios"),
            lab && React.createElement(FuturisticIcon, { name: lab.iconName, className: "h-7 w-7 text-[#1a1c1e]/85" }),
            React.createElement("span", { className: "font-semibold text-zinc-900" }, lab?.label),
            React.createElement("span", { className: `rounded-full border px-2.5 py-0.5 text-xs ${CATEGORY_BADGE[lab?.category] || ""}` }, lab?.category)
          )
        ),
        React.createElement("div", { className: `rounded-2xl border bg-white p-6 ${borderColor.split(" ")[0]}` },
          React.createElement(LabComp, null)
        )
      )
    );
  }

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "py-8 space-y-8" },
      React.createElement("div", { className: "text-center" },
        React.createElement("button", { onClick: () => window.location.href = "/educacao", className: "inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700 mb-6" }, React.createElement(BackIcon, null), "Educação & Pesquisa"),
        React.createElement("div", { className: "mb-3 inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs text-zinc-500" },
          React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" }),
          "Laboratórios Científicos Interativos"
        ),
        React.createElement("h1", { className: "text-3xl font-bold text-zinc-900 sm:text-4xl" }, "Laboratórios"),
        React.createElement("p", { className: "mt-2 text-sm text-zinc-500" }, "Simulações interativas, motor de cálculo simbólico e sandbox de código")
      ),
      React.createElement("div", { className: "flex flex-wrap gap-2 justify-center" },
        categories.map(cat => React.createElement("button", { key: cat, onClick: () => setFilter(cat), className: `rounded-xl px-3.5 py-1.5 text-sm transition-all ${filter === cat ? "bg-zinc-100 text-zinc-900 border border-zinc-200" : "border border-zinc-200 text-zinc-500 hover:text-zinc-900 hover:border-zinc-200"}` }, cat))
      ),
      React.createElement("div", { className: "grid gap-4 sm:grid-cols-2 lg:grid-cols-4" },
        filtered.map((lab, idx) => {
          const colorClass = CATEGORY_COLORS[lab.category] || "border-zinc-200 hover:border-zinc-300 text-zinc-500";
          return React.createElement("button", {
            key: lab.id,
            onClick: () => setActiveLab(lab.id),
            className: `group flex flex-col items-start gap-3 rounded-2xl border bg-white p-5 text-left transition-all ${colorClass.split(" ").slice(0, 2).join(" ")}`,
          },
            React.createElement("div", { className: "flex w-full items-start justify-between" },
              React.createElement(FuturisticIcon, { name: lab.iconName, className: "h-8 w-8 text-[#1a1c1e]/85" }),
              React.createElement("span", { className: `rounded-full border px-2 py-0.5 text-[10px] ${CATEGORY_BADGE[lab.category] || ""}` }, lab.category)
            ),
            React.createElement("div", null,
              React.createElement("p", { className: `font-semibold text-zinc-900 group-hover:${colorClass.split(" ")[2] || "text-zinc-900"} transition-colors` }, lab.label),
              React.createElement("p", { className: "mt-0.5 text-xs text-zinc-500 leading-relaxed" }, lab.desc)
            )
          );
        })
      )
    )
  );
}
