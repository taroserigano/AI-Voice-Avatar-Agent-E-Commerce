import type { NextConfig } from "next";

const COMMERCE_API_URL = process.env.COMMERCE_API_URL ?? "http://127.0.0.1:8000";
const ASSISTANT_API_URL = process.env.ASSISTANT_API_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  transpilePackages: ["@ai-commerce/contracts"],
  // The browser talks to the commerce API through this same origin, so the session cookie
  // is first-party and never exposed to scripts (HttpOnly).
  async rewrites() {
    return [
      // Steph and Xana (services/assistant). Listed first: rewrites match in order.
      { source: "/api/assistant/:path*", destination: `${ASSISTANT_API_URL}/v1/assistant/:path*` },
      { source: "/api/:path*", destination: `${COMMERCE_API_URL}/:path*` },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
