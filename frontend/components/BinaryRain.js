"use client";

import React, { useEffect, useRef } from "react";

export default function BinaryRain(props) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let width = 0;
    let height = 0;
    let columns = [];

    const CHARS = ["0", "1"];

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      if (width < 2 || height < 2) return;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const fontSize = Math.max(11, Math.floor(width / 72));
      ctx.font = `${fontSize}px monospace`;
      const colCount = Math.ceil(width / (fontSize * 0.6));
      columns = new Array(colCount).fill(0).map(() => ({ y: Math.random() * -height, speed: 0.6 + Math.random() * 1.6, size: fontSize }));
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = "source-over";
      for (let i = 0; i < columns.length; i++) {
        const col = columns[i];
        const x = i * (col.size * 0.6);
        for (let j = 0; j < 8; j++) {
          const ch = CHARS[Math.floor(Math.random() * CHARS.length)];
          const y = col.y + j * col.size;
          ctx.fillStyle = j === 0 ? "rgba(51,65,85,0.75)" : "rgba(100,116,139,0.62)";
          ctx.fillText(ch, x, y);
        }
        col.y += col.speed * (col.size / 12) * 4;
        if (col.y > height + 100) col.y = Math.random() * -200;
      }
      rafRef.current = requestAnimationFrame(draw);
    }

    resize();
    var ro = null;
    if (typeof ResizeObserver !== "undefined" && canvas.parentElement) {
      ro = new ResizeObserver(function () {
        resize();
      });
      ro.observe(canvas.parentElement);
    }
    window.addEventListener("resize", resize);
    rafRef.current = requestAnimationFrame(draw);

    return () => {
      if (ro) ro.disconnect();
      window.removeEventListener("resize", resize);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    React.createElement("div", { className: "binary-canvas binary-rain", style: { position: "absolute", inset: 0, zIndex: 1, pointerEvents: "none" } },
      React.createElement("canvas", { ref: canvasRef, style: { width: "100%", height: "100%", display: "block", opacity: 1, mixBlendMode: "normal" } })
    )
  );
}
