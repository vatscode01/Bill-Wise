/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for the multi-stage Docker build (runner stage copies standalone output)
  output: "standalone",
};
export default nextConfig;
