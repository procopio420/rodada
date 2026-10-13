import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import "./globals.css";
import { surfaceForHost, surfaceForId } from "@/lib/surfaces";
import { tenantHostname } from "@/lib/tenant-host";
import { readVenueContext } from "@/lib/server/venue-context";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const surface =
    surfaceForId(requestHeaders.get("x-rodada-surface")) ??
    surfaceForHost(requestHeaders.get("host"));
  const context = tenantHostname(requestHeaders.get("host")) ? await readVenueContext(requestHeaders) : null;
  const title = context ? `Rodada — ${context.venue.name}` : surface.title;
  return {
    title,
    description: surface.description,
    manifest: "/manifest.webmanifest",
    applicationName: title,
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const requestHeaders = await headers();
  // Reject unknown or disabled tenant domains for all deep-linked modules.
  if (tenantHostname(requestHeaders.get("host")) && !(await readVenueContext(requestHeaders))) {
    notFound();
  }
  return (
    <html lang="pt-BR">
      <body>
        {children}
      </body>
    </html>
  );
}
