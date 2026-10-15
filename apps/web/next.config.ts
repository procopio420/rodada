import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // Resolve tenant Host before Next can issue a trailing-slash308.
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
