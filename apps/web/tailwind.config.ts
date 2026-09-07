import type { Config } from "tailwindcss";
import medfreePreset from "@medfree/config/tailwind";

export default {
  presets: [medfreePreset],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
    "../../packages/atlas/src/**/*.{ts,tsx}",
  ],
} satisfies Config;
