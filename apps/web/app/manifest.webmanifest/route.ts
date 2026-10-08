import { headers } from "next/headers";
import { surfaceForHost } from "@/lib/surfaces";

export async function GET() {
  const surface = surfaceForHost((await headers()).get("host"));
  return Response.json(
    {
      name: surface.title,
      short_name: surface.shortName,
      description: surface.description,
      start_url: surface.route,
      display: "standalone",
      background_color: "#171512",
      theme_color: "#171512",
      lang: "pt-BR",
    },
    { headers: { "Cache-Control": "private, max-age=0, must-revalidate" } },
  );
}
