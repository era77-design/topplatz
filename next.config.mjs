/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.output.globalObject = 'globalThis'
    }
    return config
  },
};
export default nextConfig;
