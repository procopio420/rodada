import type { Metadata } from "next";
import { headers } from "next/headers";
import { readVenueContext } from "@/lib/server/venue-context";
import { GuestOrdering } from "@/components/guest-ordering";

export async function generateMetadata(): Promise<Metadata> {
  const context = await readVenueContext(await headers());
  return { title: context ? `Rodada Cliente — ${context.venue.name}` : "Rodada Cliente" };
}

export default async function GuestPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <GuestOrdering qrToken={token} />;
}
