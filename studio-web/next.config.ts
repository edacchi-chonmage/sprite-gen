import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/media/:path*",
        destination: "http://100.103.94.8:4323/media/:path*",
      },
    ];
  },
};

export default nextConfig;
