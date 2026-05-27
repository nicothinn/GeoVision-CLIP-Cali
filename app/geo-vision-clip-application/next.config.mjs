/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // En producción (build estático), no hacemos rewrites
    // porque FastAPI sirve el frontend y la API desde el mismo dominio
    if (process.env.NODE_ENV === 'production') {
      return [];
    }

    // En desarrollo, redirigimos /api/* al backend FastAPI :8000
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
