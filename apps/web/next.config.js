/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Serve the static prototype at a clean URL (no .html).
      { source: "/prototype", destination: "/prototype.html" },
    ];
  },
};

module.exports = nextConfig;
