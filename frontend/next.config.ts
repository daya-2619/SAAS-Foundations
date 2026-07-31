import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://web:8000/api/:path*', // Proxy to Django backend
      },
    ];
  },
};

export default nextConfig;
