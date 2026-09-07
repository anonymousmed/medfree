"use client";

import { Component, Suspense, useMemo, useState, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html, ContactShadows, Environment, useGLTF } from "@react-three/drei";
import type { AtlasPart, AtlasViewerProps, AtlasViewTool } from "./types";

/** Catches errors thrown while loading a GLB/glTF model and triggers fallback. */
class ModelErrorBoundary extends Component<
  { onError: () => void; children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch() {
    this.props.onError();
  }
  render() {
    return this.state.hasError ? null : this.props.children;
  }
}

/**
 * AtlasViewer — interactive 3D anatomy canvas (hybrid).
 *
 * Two rendering modes (progressive/adaptive, "hybrid" per the roadmap decision):
 *  1. **Real model** — when `modelUrl` is provided, loads a GLB/glTF asset via
 *     drei's `useGLTF`, with automatic fallback to primitives on load failure.
 *  2. **Primitives** — otherwise renders labelled structural primitives so the
 *     full interaction model (rotate/pan/zoom, isolate/hide/show, labels,
 *     select/highlight) is exercised before real assets are wired in.
 *
 * This keeps a consistent API for offline dev, low-end devices (fallback), and
 * the eventual BodyParts3D / NIH asset pipeline.
 */
export function AtlasViewer({
  parts,
  activePartId = null,
  onSelectPart,
  fallbackMesh = true,
  modelUrl,
  className,
  height = 560,
}: AtlasViewerProps) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [showLabels, setShowLabels] = useState(true);
  const [modelFailed, setModelFailed] = useState(false);

  const useReal = Boolean(modelUrl) && !modelFailed;

  const layout = useMemo(() => {
    const n = Math.max(parts.length, 1);
    return parts.map((p, i) => {
      const theta = (i / n) * Math.PI * 2;
      const radius = 1.1 + (i % 3) * 0.35;
      return {
        ...p,
        position: [Math.cos(theta) * radius, ((i % 4) - 1.5) * 0.7, Math.sin(theta) * radius] as [
          number,
          number,
          number,
        ],
      };
    });
  }, [parts]);

  return (
    <div className={className ?? ""} style={{ position: "relative", height }}>
      <Canvas camera={{ position: [4, 3, 5], fov: 45 }} shadows>
        <Suspense fallback={null}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 6, 5]} intensity={1.1} castShadow />
          <Environment preset="city" />
          {useReal && modelUrl && (
            <ModelErrorBoundary onError={() => setModelFailed(true)}>
              <RealModel url={modelUrl} />
            </ModelErrorBoundary>
          )}
          {(!useReal || modelFailed) &&
            layout
              .filter((p) => !hidden.has(p.id))
              .map((p) => {
                const selected = p.id === activePartId;
                return (
                  <Part
                    key={p.id}
                    part={p}
                    selected={selected}
                    showLabel={showLabels}
                    onSelect={() => onSelectPart?.(p.id)}
                  />
                );
              })}
          <ContactShadows position={[0, -2.4, 0]} opacity={0.4} scale={8} blur={2} />
        </Suspense>
        <OrbitControls enableDamping enablePan enableZoom enableRotate />
      </Canvas>

      <div className="absolute inset-x-0 bottom-3 flex justify-center gap-2">
        {(["label", "isolate"] as AtlasViewTool[]).map((tool) =>
          tool === "label" ? (
            <ControlPill key={tool} active={showLabels} onClick={() => setShowLabels((s) => !s)}>
              Labels
            </ControlPill>
          ) : (
            <ControlPill key={tool} active={hidden.size === 0} onClick={() => setHidden(new Set())}>
              Show all
            </ControlPill>
          )
        )}
      </div>

      {parts.length === 0 && !useReal && (
        <div className="absolute inset-0 grid place-items-center text-sm text-ink-3">
          No structures loaded for this region yet.
        </div>
      )}
    </div>
  );
}

function RealModel({ url }: { url: string }) {
  const gltf = useGLTF(url);
  return <primitive object={gltf.scene} scale={0.8} />;
}

function Part({
  part,
  selected,
  showLabel,
  onSelect,
}: {
  part: AtlasPart & { position: [number, number, number] };
  selected: boolean;
  showLabel: boolean;
  onSelect: () => void;
}) {
  return (
    <group position={part.position}>
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
        castShadow
        receiveShadow
      >
        <sphereGeometry args={[0.34, 40, 40]} />
        <meshStandardMaterial
          color={selected ? "#22d3ee" : part.color ?? "#4f7aa8"}
          emissive={selected ? "#22d3ee" : "#000000"}
          emissiveIntensity={selected ? 0.6 : 0}
          metalness={0.15}
          roughness={0.6}
        />
      </mesh>
      {showLabel && (
        <Html center distanceFactor={9} style={{ pointerEvents: "none" }}>
          <span className="whitespace-nowrap rounded bg-black/70 px-1.5 py-0.5 text-xs text-white">
            {part.label ?? part.name}
          </span>
        </Html>
      )}
    </group>
  );
}

function ControlPill({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium shadow transition ${
        active ? "bg-accent text-white" : "bg-surface-2 text-ink-2 hover:bg-surface-3"
      }`}
    >
      {children}
    </button>
  );
}
