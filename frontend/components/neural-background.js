"use client";

import React, { useRef, useMemo, useEffect, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

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

/**
 * NeuralBackground — visualização procedural de atividade neural
 * Three.js + React Three Fiber
 * Sem neon exagerado, sem partículas infinitas.
 * Visual sofisticado, cinematográfico, limpo.
 */

function NeuralNode({ position, color, intensity = 0.5, reducedMotion = false }) {
  var meshRef = useRef();
  var scale = useMemo(function () {
    return 0.02 + Math.random() * 0.04;
  }, []);

  useFrame(function (state) {
    if (!meshRef.current || reducedMotion) return;
    var t = state.clock.elapsedTime;
    meshRef.current.scale.setScalar(scale * (1 + Math.sin(t * 2 + position[0] * 10) * 0.3));
    meshRef.current.material.opacity = intensity * (0.5 + Math.sin(t * 1.5 + position[1] * 8) * 0.3);
  });

  return React.createElement("mesh", { ref: meshRef, position: position },
    React.createElement("sphereGeometry", { args: [1, 8, 8] }),
    React.createElement("meshBasicMaterial", {
      color: color,
      transparent: true,
      opacity: intensity * 0.35,
      blending: THREE.AdditiveBlending,
    })
  );
}

function NeuralConnections({ nodes, maxDistance = 0.8 }) {
  var linesRef = useRef();
  var count = Math.min(nodes.length, 200);

  var { positions, colors } = useMemo(function () {
    var pos = [];
    var col = [];
    var color1 = new THREE.Color("#5A7A96");
    var color2 = new THREE.Color("#94a3b8");

    for (var i = 0; i < count; i++) {
      for (var j = i + 1; j < count; j++) {
        var dx = nodes[i][0] - nodes[j][0];
        var dy = nodes[i][1] - nodes[j][1];
        var dz = nodes[i][2] - nodes[j][2];
        var dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < maxDistance) {
          var alpha = 1 - dist / maxDistance;
          var c = color1.clone().lerp(color2, alpha * 0.5);
          pos.push(nodes[i][0], nodes[i][1], nodes[i][2]);
          pos.push(nodes[j][0], nodes[j][1], nodes[j][2]);
          col.push(c.r, c.g, c.b, alpha * 0.15);
          col.push(c.r, c.g, c.b, alpha * 0.15);
        }
      }
    }
    return { positions: new Float32Array(pos), colors: new Float32Array(col) };
  }, [nodes, maxDistance, count]);

  if (positions.length === 0) return null;

  return React.createElement("lineSegments", { ref: linesRef },
    React.createElement("bufferGeometry", null,
      React.createElement("bufferAttribute", {
        attach: "attributes-position",
        count: positions.length / 3,
        array: positions,
        itemSize: 3,
      }),
      React.createElement("bufferAttribute", {
        attach: "attributes-color",
        count: colors.length / 4,
        array: colors,
        itemSize: 4,
      })
    ),
    React.createElement("lineBasicMaterial", {
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      opacity: 0.3,
    })
  );
}

function NeuralFlow({ count = 60, reducedMotion = false }) {
  var nodes = useMemo(function () {
    var arr = [];
    for (var i = 0; i < count; i++) {
      arr.push([
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 3,
      ]);
    }
    return arr;
  }, [count]);

  var groupRef = useRef();

  useFrame(function (state) {
    if (!groupRef.current || reducedMotion) return;
    var t = state.clock.elapsedTime * 0.1;
    groupRef.current.rotation.y = t * 0.05;
    groupRef.current.rotation.x = Math.sin(t * 0.02) * 0.1;
  });

  return React.createElement("group", { ref: groupRef },
    nodes.map(function (pos, i) {
      return React.createElement(NeuralNode, {
        key: i,
        position: pos,
        color: i % 3 === 0 ? "#94a3b8" : i % 3 === 1 ? "#cbd5e1" : "#e2e8f0",
        intensity: 0.2 + (i / count) * 0.25,
        reducedMotion: reducedMotion,
      });
    }),
    React.createElement(NeuralConnections, { nodes: nodes, maxDistance: 0.6 })
  );
}

function CameraController({ reducedMotion = false }) {
  var cameraRef = useRef();
  useFrame(function (state) {
    if (!cameraRef.current || reducedMotion) return;
    var t = state.clock.elapsedTime * 0.03;
    cameraRef.current.position.x = Math.sin(t) * 0.5;
    cameraRef.current.position.y = Math.cos(t * 0.7) * 0.3;
    cameraRef.current.lookAt(0, 0, 0);
  });
  return React.createElement("perspectiveCamera", { ref: cameraRef, position: [0, 0, 4], fov: 50 });
}

export default React.memo(function NeuralBackground() {
  var isMobile = useIsMobile();
  var reducedMotion = useReducedMotion();
  var _a = useState(true), visible = _a[0], setVisible = _a[1];
  var containerRef = useRef(null);

  useEffect(function () {
    var el = containerRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        setVisible(entry.isIntersecting);
      });
    }, { threshold: 0 });
    observer.observe(el);
    return function () { observer.disconnect(); };
  }, []);

  var count = isMobile ? 15 : reducedMotion ? 20 : 60;
  var dpr = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 2);

  if (!visible) return null;

  return React.createElement("div", { ref: containerRef, className: "fixed inset-0 z-0 pointer-events-none overflow-hidden" },
    React.createElement(Canvas, {
      camera: { position: [0, 0, 4], fov: 50 },
      gl: { antialias: !isMobile, alpha: true, powerPreference: isMobile ? "low-power" : "high-performance" },
      dpr: dpr,
      style: { background: "transparent", pointerEvents: "none" },
      events: function () { return { enabled: false, priority: 0, compute: function () {} }; },
    },
      React.createElement("ambientLight", { intensity: isMobile ? 0.15 : 0.3 }),
      !isMobile && React.createElement("pointLight", { position: [5, 5, 5], intensity: 0.5 }),
      React.createElement(NeuralFlow, { count: count, reducedMotion: reducedMotion || isMobile }),
      React.createElement(CameraController, { reducedMotion: reducedMotion || isMobile })
    )
  );
});
