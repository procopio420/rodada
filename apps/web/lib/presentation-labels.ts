// Presentation only: canonical values remain unchanged in commands and comparisons.
const methods: Record<string, string> = {
  CASH: "Dinheiro", PIX: "Pix", CARD: "Cartão", TAP_TO_PAY: "Tap to Pay",
  EXTERNAL_TERMINAL: "Maquininha externa", CARD_ONLINE: "Cartão online", OTHER: "Outro",
};
const paymentStates: Record<string, string> = {
  CREATED: "Criado", PENDING: "Pendente", PROCESSING: "Processando",
  AUTHORIZED: "Autorizado", CONFIRMATION_PENDING: "Confirmação pendente", EXPIRED: "Expirado",
  CONFIRMED: "Confirmado", FAILED: "Falhou", CANCELLED: "Cancelado",
  PARTIALLY_REFUNDED: "Estornado parcialmente", REFUNDED: "Estornado",
};
const closeStates: Record<string, string> = {
  INCOMPLETE: "Incompleto", READY_FOR_REVIEW: "Pronto para revisão", REVIEWED: "Revisado",
};
const cashStates: Record<string, string> = { OPEN: "Aberto", COUNTING: "Em contagem", CLOSED: "Fechado" };
const reviewStates: Record<string, string> = { NOT_REQUIRED: "Revisão dispensada", PENDING: "Revisão pendente", REVIEWED: "Revisado" };
const proposalStates: Record<string, string> = { PENDING: "Pendente", APPROVED: "Aprovada", REJECTED: "Rejeitada" };
export const paymentMethodLabel = (value: string) => methods[value] ?? "Método não reconhecido";
export const paymentStatusLabel = (value: string) => paymentStates[value] ?? "Estado não reconhecido";
export const closeStatusLabel = (value: string) => closeStates[value] ?? "Estado não reconhecido";
export const cashStatusLabel = (value: string) => cashStates[value] ?? "Estado não reconhecido";
export const cashReviewLabel = (value: string) => reviewStates[value] ?? "Revisão não reconhecida";
export const proposalStatusLabel = (value: string) => proposalStates[value] ?? "Estado não reconhecido";
