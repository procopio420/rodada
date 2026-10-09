"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { use, useEffect, useState } from "react";
export default function SharedReceipt({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const [text, setText] = useState(""), [error, setError] = useState("");
  useEffect(() => { void fetch(`/api/receipt/${encodeURIComponent(token)}`, { cache: "no-store" }).then(async response => { if (!response.ok) throw new Error(); const body = await response.json(); setText(body.text); }).catch(() => setError("Este recibo expirou, foi revogado ou não está disponível.")); }, [token]);
  return <main className="appShell"><OperationalHeading as="h1" icon="receipt">Recibo não fiscal</OperationalHeading>{error ? <p role="alert">{error}</p> : text ? <pre className="receiptText">{text}</pre> : <p role="status">Carregando recibo…</p>}</main>;
}
