import type { NextConfig } from "next";

// The browser calls /api/... on the frontend's own origin and Next forwards it to FastAPI,
// so the backend needs no CORS setup in development.
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
