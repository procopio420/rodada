import type { Metadata } from "next";
import { GuestOrdering } from "@/components/guest-ordering";

export const metadata: Metadata = { title: "Rodada Cliente" };

export default async function GuestPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <GuestOrdering qrToken={token} />;
}
