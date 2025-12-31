import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy API calls to Flask backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5000/api/:path*',
      },
      {
        source: '/new_patient',
        destination: 'http://127.0.0.1:5000/new_patient',
      },
      {
        source: '/update_patient/:path*',
        destination: 'http://127.0.0.1:5000/update_patient/:path*',
      },
      {
        source: '/process_consultation/:path*',
        destination: 'http://127.0.0.1:5000/process_consultation/:path*',
      },
      {
        source: '/save_prescription/:path*',
        destination: 'http://127.0.0.1:5000/save_prescription/:path*',
      },
      {
        source: '/search_medicine',
        destination: 'http://127.0.0.1:5000/search_medicine',
      },
      {
        source: '/add_medicine',
        destination: 'http://127.0.0.1:5000/add_medicine',
      },
      {
        source: '/update_medicine/:path*',
        destination: 'http://127.0.0.1:5000/update_medicine/:path*',
      },
      {
        source: '/delete_medicine/:path*',
        destination: 'http://127.0.0.1:5000/delete_medicine/:path*',
      },
    ];
  },
};

export default nextConfig;
