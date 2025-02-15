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
    domains: [
      'img.tori.net',
      'i.blocketcdn.se',
      'imagedelivery.net',
      'img.kleinanzeigen.de',
      'img.ricardostatic.ch',
      'frankfurt.apollo.olxcdn.com',
      'billeder.dba.dk'
    ],
    unoptimized: true,
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*', // Proxy to Flask API
      }
    ];
  },
};

export default nextConfig;
