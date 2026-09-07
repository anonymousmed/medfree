/** A renderable part of an Atlas model (typically an exported mesh). */
export interface AtlasPart {
  id: string;
  /** Display name, linked to an anatomical_structure for metadata. */
  name: string;
  /** Human-readable label shown when toggled. */
  label?: string;
  /** Default color for the part (hex). */
  color?: string;
}

export type AtlasViewTool = "rotate" | "zoom" | "isolate" | "hide" | "label";

export interface AtlasViewerProps {
  parts: AtlasPart[];
  activePartId?: string | null;
  onSelectPart?: (id: string) => void;
  /** Progressive loading / fallback for weak devices. */
  fallbackMesh?: boolean;
  /** Optional GLB/glTF model URL. When provided, the viewer loads the real
   *  3D asset and falls back to labelled primitives if it fails to load. */
  modelUrl?: string;
  className?: string;
  height?: number;
}
