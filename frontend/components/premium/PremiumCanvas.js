"use client";

import React, { useEffect, useRef } from "react";

/**
 * PremiumCanvas — Efeito visual leve com grid animado e glow
 * IMPORTANTE: Canvas MUITO leve, sem impacto em performance/FPS
 * Compatível com Safari/iPhone
 */
export function PremiumCanvas({ variant = "grid", className = "" }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const particlesRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Responsive canvas
    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const width = canvas.width / window.devicePixelRatio;
    const height = canvas.height / window.devicePixelRatio;

    // Grid animado leve
    const drawGrid = (opacity = 0.03) => {
      ctx.strokeStyle = `rgba(5, 150, 105, ${opacity})`;
      ctx.lineWidth = 0.5;
      const gridSize = 60;

      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }

      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
    };

    // Linhas suaves conectadas
    const drawConnections = () => {
      if (particlesRef.current.length === 0) {
        // Inicializar partículas
        particlesRef.current = Array.from({ length: 8 }, () => ({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          radius: Math.random() * 1.5 + 0.5,
        }));
      }

      particlesRef.current.forEach((p, i) => {
        // Mover partículas
        p.x += p.vx;
        p.y += p.vy;

        // Bounce nas bordas
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;
        p.x = Math.max(0, Math.min(width, p.x));
        p.y = Math.max(0, Math.min(height, p.y));

        // Desenhar linhas entre partículas próximas
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const p2 = particlesRef.current[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 200) {
            ctx.strokeStyle = `rgba(5, 150, 105, ${0.15 * (1 - dist / 200)})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });
    };

    // Glow ambiente leve
    const drawGlow = () => {
      const time = Date.now() * 0.0001;
      const glowX = (Math.sin(time) * 0.5 + 0.5) * width;
      const glowY = (Math.cos(time * 0.7) * 0.5 + 0.5) * height;

      const gradient = ctx.createRadialGradient(glowX, glowY, 0, glowX, glowY, 300);
      gradient.addColorStop(0, "rgba(5, 150, 105, 0.08)");
      gradient.addColorStop(1, "rgba(5, 150, 105, 0)");

      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
    };

    const animate = () => {
      ctx.fillStyle = "rgba(255, 255, 255, 0)";
      ctx.clearRect(0, 0, width, height);

      if (variant === "grid") {
        drawGrid(0.02);
      } else if (variant === "connections") {
        drawConnections();
      }

      drawGlow();

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [variant]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 ${className}`}
      style={{
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    />
  );
}
