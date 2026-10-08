"use client";
import { useState } from "react";

export type IconReference = { id: string; source: string; status: string; published_asset_url: string | null };
export type IconData = IconReference;
export function ProductIcon({ icon }: { icon?: IconReference; name?: string }) {
  const [failed, setFailed] = useState<string | null>(null);
  const asset = icon?.published_asset_url;
  const src = asset?.startsWith("/catalog/assets/") ? asset.replace("/catalog/assets/", "/api/catalog-assets/") : asset;
  return <span className="productIcon" aria-hidden="true">{src && failed !== src ? <img src={src} alt="" width={48} height={48} onError={() => setFailed(src)} /> : <svg viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="15" stroke="currentColor" strokeWidth="2" /><circle cx="24" cy="24" r="10" stroke="currentColor" strokeWidth="2" /></svg>}</span>;
}
export function IconStatus({ icon }: { icon?: IconReference }) {
  if (icon?.status === "GENERATING") return <span className="statusBadge" data-state="info">Ícone em geração</span>;
  if (icon?.status === "FAILED") return <span className="statusBadge" data-state="warning">Ícone pendente · venda disponível</span>;
  return null;
}
