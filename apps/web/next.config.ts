import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: false,
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "minio" },
    ],
  },
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${api}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
