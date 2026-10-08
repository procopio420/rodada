export type IconData = { status: string; asset_url: string; style_version: string; product_id?: string };

export function ProductIcon({ name, icon }: { name: string; icon?: IconData }) {
  return <span className="productIcon" aria-hidden="true">
    {icon?.status === "READY" && /^https:\/\//.test(icon.asset_url)
      ? <img src={icon.asset_url} width="44" height="44" alt="" loading="lazy" />
      : <span>{name.trim().slice(0, 2).toUpperCase()}</span>}
  </span>;
}
