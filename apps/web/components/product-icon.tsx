"use client";
import { useState } from "react";

export type IconReference = { id: string; source: string; status: string; published_asset_url: string | null };
export type IconData = IconReference;
export function ProductIcon({ icon }: { icon?: IconReference; name?: string }) {
  const [failed, setFailed] = useState<string | null>(null);
  const asset = icon?.published_asset_url ?? "";
  const catalogAsset = asset.startsWith("/catalog/assets/") && !asset.includes("..");
  const localAsset = /^\/product-icons\/[a-z0-9-]+\.svg$/.test(asset);
  const localReview = /^http:\/\/(127\.0\.0\.1|localhost):\d+\/product-icons\/[a-z0-9-]+\.svg$/.test(asset);
  const src = catalogAsset ? asset.replace("/catalog/assets/", "/api/catalog-assets/") : localAsset || localReview || /^https:\/\//.test(asset) ? asset : "";
  // Published identity stays visible while its replacement is generating.
  return <span className="productIcon" aria-hidden="true">{src && failed !== src ? <img src={src} alt="" width={44} height={44} onError={() => setFailed(src)} /> : <svg width="44" height="44" viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="15" stroke="currentColor" strokeWidth="2" /><circle cx="24" cy="24" r="10" stroke="currentColor" strokeWidth="2" /></svg>}</span>;
}
export function IconStatus({ icon }: { icon?: IconReference }) {
  if (icon?.status === "GENERATING") return <span className="statusBadge" data-state="info">Ícone em geração</span>;
  if (icon?.status === "FAILED") return <span className="statusBadge" data-state="warning">Ícone pendente · venda disponível</span>;
  return null;
}
