"use client";

import { OperationalHeading } from "@/components/operational-heading";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { printState } from "@/components/receipt-printing";
export default function PrintedDocument({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [document, setDocument] = useState<{ state: string; output: { html: string; text: string } } | null>(null), [error, setError] = useState("");
  useEffect(() => { void apiCall<{ state: string; output: { html: string; text: string } }>(`/api/pos/printing/jobs/${id}/`).then(result => { if (result.response.ok) setDocument(result.body as typeof document); else setError(asApiError(result.body).message); }).catch(() => setError("Documento indisponível.")); }, [id]);
  return <main className="appShell"><OperationalHeading as="h1" icon="receipt">Documento não fiscal</OperationalHeading><Link className="backLink" href="/manage/printing">Impressoras e trabalhos</Link>{error && <p role="alert">{error}</p>}{document && <><p>{printState[document.state]}</p><iframe className="receiptPreview" title="Documento histórico não fiscal" sandbox="allow-same-origin" srcDoc={document.output.html.replace(/<button[^>]*>.*?<\/button>/, "")} /><a className="backLink" download={`rodada-${id}.txt`} href={`data:text/plain;charset=utf-8,${encodeURIComponent(document.output.text)}`}>Baixar texto</a></>}</main>;
}
