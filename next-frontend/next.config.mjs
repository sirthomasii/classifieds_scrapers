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
        hostname: '**.tori.net',
      },
      {
        protocol: 'https',
        hostname: '**.blocket.se',
      },
      {
        protocol: 'https',
        hostname: '**.ebay-kleinanzeigen.de',
      },
      {
        protocol: 'https',
        hostname: '**.gumtree.com',
      },
      {
        protocol: 'https',
        hostname: '**.ricardo.ch',
      },
      {
        protocol: 'https',
        hostname: '**.dba.dk',
      },
      {
        protocol: 'https',
        hostname: '**.olx.ro',
      },
      {
        protocol: 'https',
        hostname: 'images.prismic.io',
      }
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
