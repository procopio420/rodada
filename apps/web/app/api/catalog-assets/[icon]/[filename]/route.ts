import { NextRequest } from "next/server";
export async function GET(_request: NextRequest, context: { params: Promise<{ icon: string; filename: string }> }) {
  const { icon, filename } = await context.params;
  if (!/^[a-f0-9-]{36}$/.test(icon) || !/^[a-f0-9-]{36}\.png$/.test(filename)) return new Response(null, { status: 404 });
  try {
    const base = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    const upstream = await fetch(`${base}/catalog/assets/${icon}/${filename}/`, { cache: "no-store" });
    if (!upstream.ok) return new Response(null, { status: upstream.status });
    return new Response(upstream.body, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff" } });
  } catch { return new Response(null, { status: 503 }); }
}
