export function GET() {
  return Response.json({ id: "/attendance", name: "Rodada Atendimento", short_name: "Atendimento",
    description: "Comandas, pedidos, entregas e mesas · sem pagamentos", start_url: "/attendance",
    scope: "/attendance", display: "standalone", background_color: "#120F0C", theme_color: "#120F0C", lang: "pt-BR" });
}
