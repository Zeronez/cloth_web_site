import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https: http:",
  "font-src 'self' data:",
  "connect-src 'self' https: http:",
  "media-src 'self' data: blob: https:",
  "frame-src 'self' https:"
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: contentSecurityPolicy
          },
          {
            key: "Referrer-Policy",
            value: "same-origin"
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=2592000; includeSubDomains"
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff"
          },
          {
            key: "X-Frame-Options",
            value: "DENY"
          }
        ]
      }
    ];
  },
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
