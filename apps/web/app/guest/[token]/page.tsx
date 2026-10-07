import { GuestOrdering } from "@/components/guest-ordering";

export default async function GuestPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <GuestOrdering qrToken={token} />;
}
