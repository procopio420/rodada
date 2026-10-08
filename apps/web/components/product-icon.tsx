export type IconData = { status: string; asset_url: string; style_version: string; product_id?: string };

export function ProductIcon({ name, icon }: { name: string; icon?: IconData }) {
  const published = icon?.asset_url ?? "";
  const localAsset = /^\/product-icons\/[a-z0-9-]+\.svg$/.test(published);
  // HTTP is accepted only by the isolated local review; production assets remain HTTPS.
  const localReview = /^http:\/\/(127\.0\.0\.1|localhost):\d+\/product-icons\/[a-z0-9-]+\.svg$/.test(published);
  return <span className="productIcon" aria-hidden="true">
    {icon?.status === "READY" && (localAsset || localReview || /^https:\/\//.test(published))
      ? <img src={icon.asset_url} width="44" height="44" alt="" loading="lazy" />
      : <span>{name.trim().slice(0, 2).toUpperCase()}</span>}
  </span>;
}
