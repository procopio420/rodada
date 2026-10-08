import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";
import { surfaceForHost, surfaceForId } from "@/lib/surfaces";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const surface =
    surfaceForId(requestHeaders.get("x-rodada-surface")) ??
    surfaceForHost(requestHeaders.get("host"));
  return {
    title: surface.title,
    description: surface.description,
    manifest: "/manifest.webmanifest",
    applicationName: surface.title,
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>
        {children}
        <footer className="siteFooter">
          <a href="https://wa.me/5521999353530" target="_blank" rel="noopener noreferrer">
            desenvolvido por Erick Grotz
          </a>
        </footer>
      </body>
    </html>
  );
}
