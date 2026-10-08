import Link from "next/link";

const items = [
  ["Agora", "/manage"],
  ["Operação", "/manage#operacao"],
  ["Vendas", "/manage#vendas"],
  ["Gestão", "/manage#gestao"],
  ["Mais", "/manage#mais"],
] as const;

export function ManagementNav() {
  return (
    <nav className="surfaceNav" aria-label="Navegação da Gerência">
      {items.map(([label, href]) => (
        <Link key={label} href={href} className={label === "Agora" ? "surfaceNavActive" : ""}>
          {label}
        </Link>
      ))}
    </nav>
  );
}
