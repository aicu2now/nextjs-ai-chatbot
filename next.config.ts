import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    ppr: true,
  },
  images: {
    remotePatterns: [
      {
        hostname: 'avatar.vercel.sh',
      },
    ],
  },
  env: {
    MOE_API_URL: process.env.MOE_API_URL,
    MOE_TIMEOUT_MS: process.env.MOE_TIMEOUT_MS,
  },
};

export default nextConfig;
