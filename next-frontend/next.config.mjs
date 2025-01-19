/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  webpack: (config) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      child_process: false,
    };
    config.output.webassemblyModuleFilename = 'static/wasm/[modulehash].wasm'
    config.experiments = { ...config.experiments, asyncWebAssembly: true }
    return config;
  },

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'i.blocketcdn.se',
      },
      {
        protocol: 'https',
        hostname: 'imagedelivery.net',
      },
      {
        protocol: 'https',
        hostname: 'img.kleinanzeigen.de',
      },
      {
        protocol: 'https',
        hostname: 'img.ricardostatic.ch',
      },
      {
        protocol: 'https',
        hostname: 'frankfurt.apollo.olxcdn.com',
      },
      {
        protocol: 'https',
        hostname: 'billeder.dba.dk',
      },
      {
        protocol: 'https',
        hostname: 'img.tori.net',
      },
    ],
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*', // Proxy to Flask API
      },
    ];
  },
};

export default nextConfig;
