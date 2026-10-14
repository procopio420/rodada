/** Public labels derive only from canonical fulfillment states. */
export function guestItemStatus(state: string): string {
  switch (state) {
    case "NEW": case "ACCEPTED": return "Recebido";
    case "PREPARING": return "Preparando";
    case "READY": case "PICKED_UP": return "Pronto / chegando";
    case "DELIVERED": return "Entregue";
    case "CANCELLED": return "Cancelado";
    default: return "Estado indisponível";
  }
}
