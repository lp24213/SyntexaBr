"use client";

import React, { useEffect, useRef, useState } from "react";

function useIsMobile() {
  var _a = useState(false), isMobile = _a[0], setIsMobile = _a[1];
  useEffect(function () {
    function check() { setIsMobile(window.innerWidth <= 768); }
    check();
    window.addEventListener("resize", check, { passive: true });
    return function () { window.removeEventListener("resize", check); };
  }, []);
  return isMobile;
}

function useReducedMotion() {
  var _a = useState(false), reduced = _a[0], setReduced = _a[1];
  useEffect(function () {
    var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    var listener = function (e) { setReduced(e.matches); };
    mq.addEventListener("change", listener);
    return function () { mq.removeEventListener("change", listener); };
  }, []);
  return reduced;
}

var CODE_SNIPPETS = [
  "|ψ⟩ = α|0⟩ + β|1⟩",
  "H ⊗ I · |00⟩",
  "QFT(n) → |k⟩",
  "ρ_A = Tr_B(ρ_AB)",
  "⟨ψ|U†HU|ψ⟩",
  "argmax_x P(x|θ)",
  "∇θ L(θ) ← backprop",
  "encode(q) ⇒ logits",
  "measure() → bit",
  "entangle(a, b)",
  "softmax(QKᵀ/√d)V",
  "qiskit.execute(circ)",
  "cuda::launch<MoE>()",
  "tensor.contract(ij,jk)",
  "σ_x σ_y σ_z",
  "E = ⟨H⟩",
];

function lerp(a, b, t) { return a + (b - a) * t; }
function rand(min, max) { return Math.random() * (max - min) + min; }
function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }

export var QuantumCodeStream = React.memo(function QuantumCodeStream() {
  var canvasRef = useRef(null);
  var rafRef = useRef(null);
  var isMobile = useIsMobile();
  var reducedMotion = useReducedMotion();
  var _a = useState(true), visible = _a[0], setVisible = _a[1];
  var containerRef = useRef(null);

  useEffect(function () {
    var el = containerRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { setVisible(entry.isIntersecting); });
    }, { threshold: 0 });
    observer.observe(el);
    return function () { observer.disconnect(); };
  }, []);

  useEffect(function () {
    var canvas = canvasRef.current;
    if (!canvas || !visible) return;
    var ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    var dpr = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 2);
    var W, H;
    var nodes = [];
    var edges = [];
    var particles = [];
    var codeLabels = [];
    var fadeIn = 0;
    var time = 0;

    var NODE_COUNT = isMobile ? 18 : 42;
    var MAX_PARTICLES = isMobile ? 12 : 35;
    var CONNECTION_DIST_RATIO = isMobile ? 0.18 : 0.16;
    var throttleFrames = isMobile ? 3 : 2;

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

    function createTopology() {
      nodes = [];
      edges = [];
      var maxDist = Math.min(W, H) * CONNECTION_DIST_RATIO;
      for (var i = 0; i < NODE_COUNT; i++) {
        nodes.push({
          x: rand(40, W - 40),
          y: rand(40, H - 40),
          vx: rand(-0.15, 0.15),
          vy: rand(-0.15, 0.15),
          radius: rand(1.5, 3.5),
          phase: rand(0, Math.PI * 2),
          pulseSpeed: rand(0.008, 0.025),
          baseAlpha: rand(0.12, 0.28),
        });
      }
      for (var i = 0; i < nodes.length; i++) {
        var conns = 0;
        for (var j = i + 1; j < nodes.length; j++) {
          if (conns >= 3) break;
          var dx = nodes[i].x - nodes[j].x;
          var dy = nodes[i].y - nodes[j].y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < maxDist && Math.random() > 0.35) {
            edges.push({ a: i, b: j, alpha: rand(0.04, 0.1), phase: rand(0, Math.PI * 2) });
            conns++;
          }
        }
      }
    }

    function createCodeLabels() {
      codeLabels = [];
      var count = isMobile ? 5 : 10;
      for (var i = 0; i < count; i++) {
        codeLabels.push({
          text: CODE_SNIPPETS[i % CODE_SNIPPETS.length],
          x: rand(60, W - 100),
          y: rand(40, H - 40),
          targetY: -30,
          speed: rand(0.12, 0.28),
          phase: rand(0, Math.PI * 2),
          baseAlpha: rand(0.12, 0.22),
          typeProgress: rand(0, 1),
          typeSpeed: rand(0.004, 0.01),
          accent: i % 3 === 0,
        });
      }
    }

    function spawnParticle() {
      if (particles.length >= MAX_PARTICLES || edges.length === 0) return;
      var edge = edges[Math.floor(rand(0, edges.length))];
      var a = nodes[edge.a];
      var b = nodes[edge.b];
      var reverse = Math.random() > 0.5;
      particles.push({
        ax: reverse ? b.x : a.x,
        ay: reverse ? b.y : a.y,
        bx: reverse ? a.x : b.x,
        by: reverse ? a.y : b.y,
        progress: 0,
        speed: rand(0.006, 0.018),
        size: rand(1.2, 2.8),
        alpha: rand(0.4, 0.85),
        glow: Math.random() > 0.7,
      });
    }

    var frame = 0;
    function draw() {
      frame++;
      if (frame % throttleFrames !== 0) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }

      time += 0.016;
      ctx.clearRect(0, 0, W, H);

      if (!reducedMotion) {
        fadeIn = Math.min(fadeIn + 0.006, 1);
      } else {
        fadeIn = Math.min(fadeIn + 0.03, 1);
      }

      // Update node positions (subtle drift)
      if (!reducedMotion) {
        for (var i = 0; i < nodes.length; i++) {
          var n = nodes[i];
          n.x += n.vx;
          n.y += n.vy;
          n.phase += n.pulseSpeed;
          if (n.x < 20 || n.x > W - 20) n.vx *= -1;
          if (n.y < 20 || n.y > H - 20) n.vy *= -1;
          n.x = Math.max(20, Math.min(W - 20, n.x));
          n.y = Math.max(20, Math.min(H - 20, n.y));
        }
      }

      // Draw edges
      for (var e = 0; e < edges.length; e++) {
        var edge = edges[e];
        var na = nodes[edge.a];
        var nb = nodes[edge.b];
        if (!reducedMotion) edge.phase += 0.003;
        var edgeAlpha = edge.alpha * (0.6 + 0.4 * Math.sin(edge.phase)) * fadeIn;
        if (edgeAlpha < 0.005) continue;
        ctx.beginPath();
        ctx.moveTo(na.x, na.y);
        ctx.lineTo(nb.x, nb.y);
        ctx.strokeStyle = "rgba(148,163,184," + edgeAlpha.toFixed(3) + ")";
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }

      // Draw nodes with pulse
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        var pulse = 0.6 + 0.4 * Math.sin(n.phase);
        var r = n.radius * pulse;
        var alpha = n.baseAlpha * pulse * fadeIn;
        if (alpha < 0.005) continue;

        // Outer glow on every 5th node
        if (!isMobile && i % 5 === 0) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, r * 3.5, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(99,102,241," + (alpha * 0.08).toFixed(4) + ")";
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = (i % 6 === 0)
          ? "rgba(99,102,241," + (alpha * 0.7).toFixed(3) + ")"
          : "rgba(148,163,184," + alpha.toFixed(3) + ")";
        ctx.fill();
      }

      // Draw & update particles (data flow along edges)
      for (var p = particles.length - 1; p >= 0; p--) {
        var part = particles[p];
        part.progress += part.speed;
        if (part.progress >= 1) {
          particles.splice(p, 1);
          continue;
        }
        var t = easeInOut(part.progress);
        var px = lerp(part.ax, part.bx, t);
        var py = lerp(part.ay, part.by, t);
        var pAlpha = part.alpha * Math.sin(part.progress * Math.PI) * fadeIn;

        if (part.glow && !isMobile) {
          ctx.beginPath();
          ctx.arc(px, py, part.size * 3, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(99,102,241," + (pAlpha * 0.15).toFixed(4) + ")";
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(px, py, part.size, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(99,102,241," + pAlpha.toFixed(3) + ")";
        ctx.fill();
      }

      // Spawn particles periodically
      if (!reducedMotion && Math.random() < (isMobile ? 0.04 : 0.1)) {
        spawnParticle();
      }

      // Quantum code labels — floating upward with typing reveal
      ctx.font = (isMobile ? 9 : 11) + "px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
      for (var li = 0; li < codeLabels.length; li++) {
        var lb = codeLabels[li];
        if (!reducedMotion) {
          lb.y -= lb.speed;
          lb.typeProgress += lb.typeSpeed;
          lb.phase += 0.008;
          if (lb.y < -20) {
            lb.y = H + rand(10, 40);
            lb.x = rand(60, W - 120);
            lb.text = CODE_SNIPPETS[Math.floor(rand(0, CODE_SNIPPETS.length))];
            lb.typeProgress = 0;
            lb.baseAlpha = rand(0.12, 0.22);
            lb.accent = Math.random() > 0.65;
          }
        }

        var la = lb.baseAlpha * fadeIn * (0.7 + 0.3 * Math.sin(lb.phase));
        if (la < 0.01) continue;

        var revealLen = Math.max(1, Math.min(lb.text.length, Math.floor(lb.typeProgress * lb.text.length)));
        var shown = lb.text.slice(0, revealLen);

        ctx.fillStyle = lb.accent
          ? "rgba(99,102,241," + (la * 0.9).toFixed(3) + ")"
          : "rgba(71,85,105," + la.toFixed(3) + ")";
        ctx.fillText(shown, lb.x, lb.y);

        // Blinking cursor while typing
        if (revealLen < lb.text.length && Math.floor(frame / 10) % 2 === 0) {
          var cursorX = lb.x + ctx.measureText(shown).width + 2;
          ctx.fillRect(cursorX, lb.y - (isMobile ? 7 : 9), 1, isMobile ? 8 : 10);
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    }

    resize();
    createTopology();
    createCodeLabels();
    rafRef.current = requestAnimationFrame(draw);

    var onResize = function () { resize(); createTopology(); createCodeLabels(); };
    window.addEventListener("resize", onResize, { passive: true });

    return function () {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", onResize);
    };
  }, [isMobile, reducedMotion, visible]);

  return React.createElement("div", { ref: containerRef, className: "absolute inset-0 w-full h-full pointer-events-none overflow-hidden" },
    visible && React.createElement("canvas", {
      ref: canvasRef,
      className: "absolute inset-0 w-full h-full pointer-events-none",
      style: { display: "block", zIndex: 1, pointerEvents: "none" },
      "aria-hidden": true,
      "data-decorative": "true",
    })
  );
});
