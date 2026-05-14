"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";

// ─── Canvas 2D Constellation — ultra leve (~60 partículas) ───────────────────
function QuantumCanvas() {
  var canvasRef = useRef(null);
  var rafRef = useRef(null);

  useEffect(function () {
    var canvas = canvasRef.current;
    if (!canvas) return;
    var ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var width, height;
    var particles = [];
    var PARTICLE_COUNT = 48;
    var CONNECTION_DIST = 110;
    var MOUSE_DIST = 160;
    var mouse = { x: -9999, y: -9999, active: false };

    function resize() {
      var rect = canvas.parentElement.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function createParticles() {
      particles = [];
      for (var i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.25,
          vy: (Math.random() - 0.5) * 0.25,
          r: Math.random() * 1.4 + 0.6,
          opacity: Math.random() * 0.35 + 0.1,
        });
      }
    }

    var frameCount = 0;
    function draw() {
      frameCount++;
      // Skip every 2nd frame on low-end devices for 30fps fallback
      if (frameCount % 2 === 0 && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Update positions
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;
      }

      // Draw connections (only check subset for performance)
      ctx.lineWidth = 0.5;
      for (var a = 0; a < particles.length; a++) {
        var pa = particles[a];
        for (var b = a + 1; b < particles.length; b++) {
          var pb = particles[b];
          var dx = pa.x - pb.x;
          var dy = pa.y - pb.y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DIST) {
            var alpha = (1 - dist / CONNECTION_DIST) * 0.12;
            ctx.strokeStyle = "rgba(140,145,155," + alpha + ")";
            ctx.beginPath();
            ctx.moveTo(pa.x, pa.y);
            ctx.lineTo(pb.x, pb.y);
            ctx.stroke();
          }
        }
        // Mouse interaction
        if (mouse.active) {
          var mdx = pa.x - mouse.x;
          var mdy = pa.y - mouse.y;
          var mdist = Math.sqrt(mdx * mdx + mdy * mdy);
          if (mdist < MOUSE_DIST) {
            var malpha = (1 - mdist / MOUSE_DIST) * 0.15;
            ctx.strokeStyle = "rgba(120,128,140," + malpha + ")";
            ctx.beginPath();
            ctx.moveTo(pa.x, pa.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }

      // Draw particles
      for (var k = 0; k < particles.length; k++) {
        var pk = particles[k];
        ctx.fillStyle = "rgba(160,165,175," + pk.opacity + ")";
        ctx.beginPath();
        ctx.arc(pk.x, pk.y, pk.r, 0, Math.PI * 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    }

    function onMouseMove(e) {
      var rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      mouse.active = true;
    }
    function onMouseLeave() {
      mouse.active = false;
    }

    resize();
    createParticles();
    rafRef.current = requestAnimationFrame(draw);

    window.addEventListener("resize", resize, { passive: true });
    canvas.addEventListener("mousemove", onMouseMove, { passive: true });
    canvas.addEventListener("mouseleave", onMouseLeave, { passive: true });

    return function () {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseleave", onMouseLeave);
    };
  }, []);

  return React.createElement("canvas", {
    ref: canvasRef,
    className: "absolute inset-0 w-full h-full pointer-events-auto",
    style: { display: "block" },
    "aria-hidden": true,
  });
}

// ─── CSS 3D Quantum Rings ──────────────────────────────────────────────────────
function QuantumRings() {
  return React.createElement(
    "div",
    {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
      style: { width: 320, height: 320, perspective: 800 },
      "aria-hidden": true,
    },
    // Inner core glow
    React.createElement("div", {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full",
      style: {
        width: 14,
        height: 14,
        background: "radial-gradient(circle, rgba(200,205,215,0.5) 0%, transparent 70%)",
        boxShadow: "0 0 24px rgba(200,205,215,0.25), 0 0 60px rgba(200,205,215,0.08)",
      },
    }),
    // Ring 1
    React.createElement("div", {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[rgba(180,185,195,0.15)]",
      style: {
        width: 120,
        height: 120,
        animation: "quantum-spin-a 14s linear infinite",
        transformStyle: "preserve-3d",
      },
    }),
    // Ring 2
    React.createElement("div", {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[rgba(160,168,180,0.12)]",
      style: {
        width: 200,
        height: 200,
        animation: "quantum-spin-b 22s linear infinite reverse",
        transformStyle: "preserve-3d",
        transform: "rotateX(60deg) rotateY(20deg)",
      },
    }),
    // Ring 3
    React.createElement("div", {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[rgba(140,150,165,0.08)]",
      style: {
        width: 280,
        height: 280,
        animation: "quantum-spin-c 30s linear infinite",
        transformStyle: "preserve-3d",
        transform: "rotateX(45deg) rotateZ(30deg)",
      },
    })
  );
}

// ─── Staggered text reveal (Igloo-style) ─────────────────────────────────────
function AnimatedTitle({ children, delay = 0 }) {
  var words = String(children).split(" ");
  return React.createElement(
    motion.h1,
    {
      className: "text-[2.4rem] font-semibold leading-[1.08] tracking-tight text-[#1a1c1e] md:text-[3.2rem] md:leading-[1.05] lg:text-[3.8rem]",
      initial: "hidden",
      animate: "visible",
      variants: {
        hidden: {},
        visible: {
          transition: { staggerChildren: 0.04, delayChildren: delay },
        },
      },
    },
    words.map(function (word, i) {
      return React.createElement(
        motion.span,
        {
          key: i,
          className: "inline-block mr-[0.25em]",
          variants: {
            hidden: { opacity: 0, y: 18 },
            visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] } },
          },
        },
        word
      );
    })
  );
}

function AnimatedSubtitle({ children, delay = 0 }) {
  return React.createElement(
    motion.p,
    {
      className: "mx-auto mt-5 max-w-2xl text-base leading-relaxed text-[#5a5c5e] md:text-lg",
      initial: { opacity: 0, y: 14 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.55, delay: delay, ease: [0.22, 1, 0.36, 1] },
    },
    children
  );
}

function AnimatedBadge({ children, delay = 0 }) {
  return React.createElement(
    motion.p,
    {
      className: "mb-6 inline-flex rounded-full border border-[rgba(20,24,30,0.08)] bg-white px-4 py-2 text-[11px] font-medium uppercase tracking-[0.2em] text-[#8e9094]",
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.4, delay: delay },
    },
    children
  );
}

function AnimatedButtons({ children, delay = 0 }) {
  return React.createElement(
    motion.div,
    {
      className: "mt-9 flex flex-wrap items-center justify-center gap-3",
      initial: { opacity: 0, y: 12 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.45, delay: delay },
    },
    children
  );
}

// ─── Exported Quantum Hero ───────────────────────────────────────────────────
export function QuantumHero({ locale, t, Link }) {
  return React.createElement(
    "section",
    { id: "nucleo", className: "relative flex min-h-[92dvh] items-center justify-center overflow-hidden" },
    // Ambient background layer
    React.createElement("div", {
      className: "absolute inset-0 z-0",
      style: {
        background: "linear-gradient(180deg, #fafbfc 0%, #f5f6f8 45%, #f0f1f4 100%)",
      },
      "aria-hidden": true,
    }),
    // Subtle radial glow behind rings
    React.createElement("div", {
      className: "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[1] pointer-events-none",
      style: {
        width: 500,
        height: 500,
        background: "radial-gradient(circle, rgba(210,215,225,0.15) 0%, transparent 65%)",
        borderRadius: "50%",
      },
      "aria-hidden": true,
    }),
    // Quantum canvas constellation
    React.createElement("div", { className: "absolute inset-0 z-[2] pointer-events-none" },
      React.createElement(QuantumCanvas, null)
    ),
    // 3D rings
    React.createElement("div", { className: "absolute inset-0 z-[3] pointer-events-none" },
      React.createElement(QuantumRings, null)
    ),
    // Content
    React.createElement(
      "div",
      { className: "relative z-10 max-w-[940px] text-center px-5 pt-24 md:pt-16 pb-16" },
      React.createElement(AnimatedBadge, { delay: 0.1 }, t("homeBadge", locale)),
      React.createElement(AnimatedTitle, { delay: 0.2 }, t("homeTitle", locale)),
      React.createElement(AnimatedSubtitle, { delay: 0.35 }, t("homeSubtitle", locale)),
      React.createElement(AnimatedButtons, { delay: 0.45 },
        React.createElement(Link, {
          href: "/chat",
          className: "rounded-full border border-[#1a1c1e] bg-[#1a1c1e] px-6 py-3 text-sm font-medium text-white shadow-[0_1px_3px_rgba(0,0,0,0.1)] transition-opacity hover:opacity-90",
        }, t("homeCtaPrimary", locale)),
        React.createElement("a", {
          href: "#capabilities",
          className: "rounded-full border border-[rgba(20,24,30,0.1)] bg-white px-6 py-3 text-sm font-medium text-[#1a1c1e] shadow-[0_1px_3px_rgba(0,0,0,0.04)] hover:bg-[#f8f9fa]",
        }, t("homeCtaSecondary", locale))
      )
    )
  );
}
