"use client";
import { use } from "react";
import { ExceptionalContext } from "@/components/exceptional-context";
export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ExceptionalContext id={id} kind="item" />;
}
