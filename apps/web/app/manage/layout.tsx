import type { Metadata } from "next";

export const metadata: Metadata = { title: "Rodada Gerência" };

export default function ManagementLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
