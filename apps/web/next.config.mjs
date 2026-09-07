/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Compile the TS workspace packages directly.
  transpilePackages: ["@medfree/ui", "@medfree/atlas", "@medfree/types", "@medfree/config"],
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.supabase.co" },
      { protocol: "https", hostname: "**" },
    ],
  },
  // Dev/live-preview: proxy /api to the local FastAPI backend. Override the
  // target with the MEDFREE_API_URL env var when running elsewhere.
  async rewrites() {
    const apiTarget = process.env.MEDFREE_API_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${apiTarget}/api/:path*` }];
  },
};

export default nextConfig;
