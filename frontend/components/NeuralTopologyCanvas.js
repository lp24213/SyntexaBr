"use client";

/**
 * SYNTEXA NEURAL TOPOLOGY CANVAS
 * ================================
 * Fundo cinematográfico procedural para o chat.
 * Otimizado para mobile: menos nodes, sem mouse tracking, intersection observer.
 */

import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

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

const PALETTE = {
  bg: [248, 250, 252],
  node: [148, 163, 184],
  edge: [203, 213, 225],
  particle: [180, 190, 200],
  accent: [148, 163, 184],
};

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

class NeuralNode {
  constructor(w, h) {
    this.x = rand(0, w);
    this.y = rand(0, h);
    this.vx = rand(-0.3, 0.3);
    this.vy = rand(-0.3, 0.3);
    this.radius = rand(1.5, 4);
    this.pulse = rand(0, Math.PI * 2);
    this.pulseSpeed = rand(0.01, 0.04);
    this.connections = [];
  }

  update(w, h, time) {
    this.x += this.vx;
    this.y += this.vy;
    this.pulse += this.pulseSpeed;

    // Bounce
    if (this.x < 0 || this.x > w) this.vx *= -1;
    if (this.y < 0 || this.y > h) this.vy *= -1;
    this.x = Math.max(0, Math.min(w, this.x));
    this.y = Math.max(0, Math.min(h, this.y));
  }
}

class DataParticle {
  constructor(path) {
    this.path = path; // array de {x,y} nodes
    this.progress = 0;
    this.speed = rand(0.003, 0.012);
    this.alpha = rand(0.4, 1);
    this.size = rand(1, 2.5);
    this.dead = false;
  }

  update() {
    this.progress += this.speed;
    if (this.progress >= 1) this.dead = true;
  }

  getPos() {
    const idx = this.progress * (this.path.length - 1);
    const i = Math.floor(idx);
    const t = idx - i;
    const a = this.path[i];
    const b = this.path[Math.min(i + 1, this.path.length - 1)];
    return {
      x: lerp(a.x, b.x, t),
      y: lerp(a.y, b.y, t),
    };
  }
}

export default function NeuralTopologyCanvas({ className = "" }) {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });
  const animRef = useRef(null);
  const isMobile = useIsMobile();
  const reducedMotion = useReducedMotion();
  const _a = useState(true), visible = _a[0], setVisible = _a[1];
  const containerRef = useRef(null);

  useEffect(function () {
    var el = containerRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { setVisible(entry.isIntersecting); });
    }, { threshold: 0 });
    observer.observe(el);
    return function () { observer.disconnect(); };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !visible) return;
    const ctx = canvas.getContext("2d");
    let dpr = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 2);

    let width, height;
    const nodes = [];
    const particles = [];
    const MAX_NODES = isMobile ? 16 : 48;
    const CONNECTION_DIST = isMobile ? 120 : 180;
    const MAX_CONNECTIONS = isMobile ? 2 : 3;
    const frameSkip = isMobile ? 2 : 1;

    function resize() {
      const rect = canvas.parentElement.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Rebalanceia nodes
      while (nodes.length < MAX_NODES) {
        nodes.push(new NeuralNode(width, height));
      }
      while (nodes.length > MAX_NODES) {
        nodes.pop();
      }
    }

    function buildConnections() {
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.connections = [];
        const candidates = [];
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          const other = nodes[j];
          const dx = n.x - other.x;
          const dy = n.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DIST) {
            candidates.push({ idx: j, dist });
          }
        }
        candidates.sort((a, b) => a.dist - b.dist);
        n.connections = candidates.slice(0, MAX_CONNECTIONS).map((c) => c.idx);
      }
    }

    function spawnParticle() {
      if (particles.length > (isMobile ? 10 : 30)) return;
      // Escolhe um node aleatório e segue suas conexões
      const startIdx = Math.floor(rand(0, nodes.length));
      const path = [nodes[startIdx]];
      let current = startIdx;
      const visited = new Set([current]);
      for (let step = 0; step < 5; step++) {
        const n = nodes[current];
        const opts = n.connections.filter((c) => !visited.has(c));
        if (opts.length === 0) break;
        const next = opts[Math.floor(rand(0, opts.length))];
        path.push(nodes[next]);
        visited.add(next);
        current = next;
      }
      if (path.length >= 2) {
        particles.push(new DataParticle(path));
      }
    }

    var frameCount = 0;
    function draw() {
      frameCount++;
      if (frameCount % frameSkip !== 0) {
        animRef.current = requestAnimationFrame(draw);
        return;
      }

      // Background com gradiente sutil
      const grad = ctx.createLinearGradient(0, 0, width, height);
      grad.addColorStop(0, `rgb(${PALETTE.bg[0]}, ${PALETTE.bg[1]}, ${PALETTE.bg[2]})`);
      grad.addColorStop(1, `rgb(${PALETTE.bg[0] + 4}, ${PALETTE.bg[1] + 6}, ${PALETTE.bg[2] + 10})`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      const time = Date.now() * 0.001;

      // Mouse parallax influence (desabilitado em mobile)
      let mx = 0, my = 0;
      if (!isMobile && mouseRef.current.active) {
        mx = (mouseRef.current.x - width * 0.5) * 0.02;
        my = (mouseRef.current.y - height * 0.5) * 0.02;
      }

      // Edges
      ctx.lineWidth = 0.6;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        for (const j of n.connections) {
          if (j <= i) continue; // evita duplicar
          const other = nodes[j];
          const dx = n.x - other.x;
          const dy = n.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const alpha = Math.max(0, 1 - dist / CONNECTION_DIST) * 0.25;
          ctx.strokeStyle = `rgba(${PALETTE.edge[0]}, ${PALETTE.edge[1]}, ${PALETTE.edge[2]}, ${alpha})`;
          ctx.beginPath();
          ctx.moveTo(n.x + mx * (i % 3), n.y + my * (i % 3));
          ctx.lineTo(other.x + mx * (j % 3), other.y + my * (j % 3));
          ctx.stroke();
        }
      }

      // Particles (data flow)
      for (let p = particles.length - 1; p >= 0; p--) {
        const part = particles[p];
        part.update();
        if (part.dead) {
          particles.splice(p, 1);
          continue;
        }
        const pos = part.getPos();
        ctx.fillStyle = `rgba(${PALETTE.particle[0]}, ${PALETTE.particle[1]}, ${PALETTE.particle[2]}, ${part.alpha})`;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, part.size, 0, Math.PI * 2);
        ctx.fill();
      }

      // Nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.update(width, height, time);
        const pulse = Math.sin(n.pulse) * 0.5 + 0.5;
        const r = n.radius + pulse * 1.5;
        const alpha = 0.4 + pulse * 0.4;

        ctx.fillStyle = `rgba(${PALETTE.node[0]}, ${PALETTE.node[1]}, ${PALETTE.node[2]}, ${alpha})`;
        ctx.beginPath();
        ctx.arc(n.x + mx * (i % 3), n.y + my * (i % 3), r, 0, Math.PI * 2);
        ctx.fill();

        // Glow sutil nos nodes principais (removido em mobile)
        if (!isMobile && i % 7 === 0) {
          ctx.fillStyle = `rgba(${PALETTE.accent[0]}, ${PALETTE.accent[1]}, ${PALETTE.accent[2]}, ${alpha * 0.15})`;
          ctx.beginPath();
          ctx.arc(n.x + mx * (i % 3), n.y + my * (i % 3), r * 4, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Spawn new particles
      if (!reducedMotion && Math.random() < (isMobile ? 0.03 : 0.08)) spawnParticle();

      animRef.current = requestAnimationFrame(draw);
    }

    resize();
    buildConnections();
    animRef.current = requestAnimationFrame(draw);

    const onResize = () => { resize(); buildConnections(); };
    window.addEventListener("resize", onResize);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", onResize);
    };
  }, [isMobile, reducedMotion, visible]);

  return (
    <motion.div
      ref={containerRef}
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      style={{ zIndex: 0 }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.2, ease: "easeOut" }}
    >
      <canvas
        ref={canvasRef}
        data-decorative="true"
        className="pointer-events-none"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />
      {/* Overlay gradiente para legibilidade do conteúdo */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(248,250,252,0.3) 0%, rgba(248,250,252,0) 40%, rgba(248,250,252,0) 60%, rgba(248,250,252,0.3) 100%)",
          zIndex: 1,
          pointerEvents: "none",
        }}
      />
    </motion.div>
  );
}
