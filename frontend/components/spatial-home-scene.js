"use client";

import React, { useMemo, useRef, useEffect, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";

function useLightScene() {
  const [light, setLight] = useState(false);
  useEffect(function () {
    if (typeof window === "undefined") return;
    var mq = window.matchMedia("(max-width: 768px), (prefers-reduced-motion: reduce)");
    function apply() {
      setLight(Boolean(mq.matches));
    }
    apply();
    mq.addEventListener("change", apply);
    return function () {
      mq.removeEventListener("change", apply);
    };
  }, []);
  return light;
}

function ServerBlade(props) {
  var position = props.position;
  var s = props.s || 1;
  return React.createElement(
    "group",
    { position: position },
    React.createElement(
      "mesh",
      null,
      React.createElement("boxGeometry", { args: [0.36 * s, 1.35 * s, 0.2 * s] }),
      React.createElement("meshPhysicalMaterial", {
        color: "#f2f5f9",
        roughness: 0.5,
        metalness: 0.06,
        clearcoat: 0.18,
      })
    ),
    React.createElement(
      "mesh",
      { position: [0, 0, 0.106 * s] },
      React.createElement("planeGeometry", { args: [0.22 * s, 1.08 * s] }),
      React.createElement("meshBasicMaterial", {
        color: "#cfe0f5",
        transparent: true,
        opacity: 0.42,
      })
    )
  );
}

function DatacenterHall(props) {
  var pointer = props.pointer;
  var lite = props.lite;
  var ref = useRef(null);
  var blades = lite ? [6, 2] : [9, 3];
  var n = blades[0];
  var rows = blades[1];

  var positions = useMemo(function () {
    var list = [];
    for (var r = 0; r < rows; r++) {
      var z = (r - (rows - 1) / 2) * 1.05;
      for (var i = 0; i < n; i++) {
        var x = (i - (n - 1) / 2) * 0.5;
        list.push([x, -0.2, z]);
      }
    }
    return list;
  }, [n, rows]);

  var px = typeof pointer !== "undefined" && pointer !== null ? pointer.x : 0;
  var py = typeof pointer !== "undefined" && pointer !== null ? pointer.y : 0;

  useFrame(function (state) {
    var g = ref.current;
    if (!g) return;
    var t = state.clock.elapsedTime;
    g.rotation.y = t * (lite ? 0.04 : 0.065);
    g.position.x = THREE.MathUtils.lerp(g.position.x, px * (lite ? 0.08 : 0.18), 0.035);
    g.position.y = THREE.MathUtils.lerp(g.position.y, py * (lite ? 0.04 : 0.1), 0.035);
  });

  return React.createElement(
    "group",
    { ref: ref, position: [0, -0.9, -0.2] },
    positions.map(function (pos, idx) {
      return React.createElement(ServerBlade, { key: "b-" + idx, position: pos, s: lite ? 0.82 : 1 });
    }),
    React.createElement(
      "mesh",
      { position: [0, -1.08, -0.2], rotation: [-Math.PI / 2, 0, 0] },
      React.createElement("planeGeometry", { args: [16, 10] }),
      React.createElement("meshPhysicalMaterial", {
        color: "#fbfcfe",
        roughness: 0.85,
        metalness: 0,
        opacity: 0.55,
        transparent: true,
      })
    )
  );
}

function QuantumWires(props) {
  var lite = props.lite;
  var ref = useRef(null);
  var segs = lite ? 5 : 10;
  var lines = useMemo(function () {
    var arr = [];
    for (var i = 0; i < segs; i++) {
      var a = (i / segs) * Math.PI * 2;
      arr.push([
        [Math.cos(a) * 1.05, Math.sin(a * 2) * 0.38, Math.sin(a) * 1.05],
        [Math.cos(a + 0.55) * 2.15, Math.sin(a * 2 + 1) * 0.32, Math.sin(a + 0.55) * 2],
      ]);
    }
    return arr;
  }, [segs]);

  useFrame(function (state) {
    var g = ref.current;
    if (!g) return;
    g.rotation.y = state.clock.elapsedTime * (lite ? 0.06 : 0.1);
    g.rotation.x = Math.sin(state.clock.elapsedTime * 0.15) * 0.06;
  });

  return React.createElement(
    "group",
    { ref: ref },
    lines.map(function (pts, idx) {
      return React.createElement(Line, {
        key: "q-" + idx,
        points: pts,
        color: "#b9cbe3",
        lineWidth: lite ? 1 : 1.8,
        transparent: true,
        opacity: 0.45,
      });
    })
  );
}

function QuantumCoreMesh() {
  var ref = useRef(null);
  useFrame(function (state) {
    var m = ref.current;
    if (!m) return;
    var t = state.clock.elapsedTime;
    m.rotation.y = t * 0.15;
    m.rotation.x = Math.sin(t * 0.35) * 0.08;
    m.scale.setScalar(1 + Math.sin(t * 0.8) * 0.03);
  });
  return React.createElement(
    "mesh",
    { ref: ref },
    React.createElement("octahedronGeometry", { args: [0.48, 0] }),
    React.createElement("meshStandardMaterial", {
      color: "#ffffff",
      emissive: "#e5edf8",
      emissiveIntensity: 0.32,
      roughness: 0.22,
      metalness: 0.25,
    })
  );
}

function Scene(props) {
  var pointer = props.pointer;
  var lite = props.lite;
  return React.createElement(
    React.Fragment,
    null,
    React.createElement("ambientLight", { intensity: lite ? 0.95 : 0.82 }),
    React.createElement("directionalLight", { position: [4, 6, 3], intensity: lite ? 0.75 : 0.95, color: "#ffffff" }),
    React.createElement("directionalLight", { position: [-3, 2, -2], intensity: lite ? 0.25 : 0.38, color: "#eef3fb" }),
    React.createElement(QuantumCoreMesh, null),
    React.createElement(DatacenterHall, { pointer: pointer, lite: lite }),
    React.createElement(QuantumWires, { lite: lite })
  );
}

export function SpatialHomeScene(props) {
  var pointer = props.pointer;
  var lite = useLightScene();
  var dpr = lite ? 1 : 1.25;

  return React.createElement(
    "div",
    {
      className: "pointer-events-none absolute inset-x-0 top-0 z-[5] mx-auto h-[min(52dvh,580px)] w-full max-w-[1380px] [contain:strict]",
      "aria-hidden": true,
    },
    React.createElement(
      Canvas,
      {
        camera: { position: [0, 0.85, 6.4], fov: 40 },
        dpr: dpr,
        gl: {
          antialias: !lite,
          alpha: true,
          powerPreference: "high-performance",
          stencil: false,
        },
        style: { background: "transparent" },
      },
      React.createElement("fog", { attach: "fog", args: ["#fafbfc", 5.8, 12.8] }),
      React.createElement(Scene, { pointer: pointer, lite: lite })
    )
  );
}
