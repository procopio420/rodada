"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { tabReference, tableLocationLabel } from "@/lib/client/tab-identity";
import { attendanceCategory, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";
import { AttendanceOrderStatus } from "./attendance-order-status";
import { CustomizationText, money, unitPrice, type OrderingProduct, type Selection } from "./product-customization";
import type { HistoricalOrder } from "./repeat-order";
import "./attendance-ux2-workspace.css";

type Product = OrderingProduct & { active: boolean; availability: string; category?: string };
type Line = { product: Product; quantity: number; selection: Selection };
export type AttendanceSurface = "tab" | "catalog" | "draft" | "bill" | "limit";
export function AttendanceUx2Workspace({ hidden = false, tab, surface, products, lines, total, locked, canSend, fresh, pending, confirming, message, success, bill, credit, contextualTaskNode, catalogState, onCatalogState, onSurface, onBack, onAdd, onCustomize, onReduce, onEdit, onQuantity, onSend, onRepeat, onDiscard }: {
  hidden?: boolean; tab: { id: string; display_label: string; table_label?: string | null; state: string; exposure_cents: number; orders?: HistoricalOrder[] };
  surface: AttendanceSurface; products: Product[]; lines: Line[]; total: number; locked: boolean; canSend: boolean; fresh: boolean;
  pending: boolean; confirming: boolean; message: ReactNode; success: string; bill: ReactNode; credit?: ReactNode; contextualTaskNode?: ReactNode; catalogState?: {query: string; category: string}; onCatalogState?: (state: {query:string;category:string}) => void;
  onSurface: (surface: AttendanceSurface) => void; onBack: () => void;
  onAdd: (product: Product) => void; onCustomize: (product: Product, trigger: HTMLElement) => void; onReduce: (product: Product) => void; onEdit: (index: number) => void;
  onQuantity: (index: number, delta: number) => void; onSend: () => void; onRepeat: () => void; onDiscard: () => void;
}) {
  const [localQuery, setLocalQuery] = useState("");
  const [localCategory, setLocalCategory] = useState("");
  const query = catalogState?.query ?? localQuery, category = catalogState?.category ?? localCategory;
  const setQuery = (value: string) => onCatalogState ? onCatalogState({query:value,category}) : setLocalQuery(value);
  const setCategory = (value: string) => onCatalogState ? onCatalogState({query,category:value}) : setLocalCategory(value);
  const surfaceRef = useRef<HTMLElement>(null);
  useEffect(() => { surfaceRef.current?.querySelector<HTMLHeadingElement>("h1")?.focus(); }, [surface]);
  useEffect(() => { const back = (event: KeyboardEvent) => { if (event.key !== "Escape" || locked || (event.target instanceof Element && event.target.closest("dialog[open]"))) return; event.preventDefault(); if (surface === "tab") onBack(); else onSurface(surface === "draft" ? "catalog" : "tab"); }; window.addEventListener("keydown", back); return () => window.removeEventListener("keydown", back); }, [surface, locked, onBack, onSurface]);
  const count = lines.reduce((sum, line) => sum + line.quantity, 0);
  const closed = ["CLOSED", "CANCELLED"].includes(tab.state);
  const categories = ["", ...new Set(products.filter(product => product.active).map(attendanceCategory))];
  const filtered = products.filter(product => product.active && (category === "" || attendanceCategory(product) === category) && normalizeCatalogSearch(product.name).includes(normalizeCatalogSearch(query)));
  const reference = tabReference(tab);
  const destination = `${tab.display_label || reference} · ${tableLocationLabel(tab.table_label)}`;
  const latest = tab.orders?.at(-1);
  return <section hidden={hidden} ref={surfaceRef} className="ux2Workspace" aria-label="Comanda selecionada">
    <button className="ux2Back" disabled={locked} onClick={() => surface === "tab" ? onBack() : onSurface(surface === "draft" ? "catalog" : "tab")}><span aria-hidden="true">‹</span> Voltar</button>
    {surface === "tab" ? <>
      <div className="ux2Eyebrow">{reference}</div>
      <div className="ux2Context"><div><h1 tabIndex={-1}>{tab.display_label || reference}</h1><p>{tableLocationLabel(tab.table_label)} · {closed ? "Encerrada" : "Comanda aberta"}</p></div><span className="ux2Tag">{closed ? "Encerrada" : "Em consumo"}</span></div>
    </> : <><div className="ux2Eyebrow">{surface === "catalog" ? `Pedido para ${reference}` : surface === "draft" ? "Resumo opcional" : surface === "limit" ? "Conta da casa · perfil da comanda" : `Conta · ${reference}`}</div><h1 tabIndex={-1}>{surface === "catalog" ? "Adicionar itens." : surface === "draft" ? "Resumo do pedido." : surface === "limit" ? "Limite e garantias." : closed ? "Conta encerrada." : "Fechar a conta."}</h1><p className="ux2Lede">{surface === "draft" ? "Conferência opcional: itens e destino antes do envio." : <>{destination}{surface === "catalog" && <span className="ux2FixedDestination"> · Destino fixo</span>}</>}</p></>}
    {success && <p className="ux2Toast" role="status">{success}</p>}
    {message}
    {contextualTaskNode}
    {!fresh && <p className="ux2Notice" role="status">Dados desatualizados. Atualize antes de enviar.</p>}
    {pending && <div className="ux2Unknown" role="status"><strong>Envio sem confirmação</strong><p>A intenção original está preservada. Não envie outro pedido.</p><button className="ux2Button primary" disabled={confirming} onClick={onSend}>Verificar mesmo pedido</button></div>}
    {surface === "tab" && <>
      <div className="ux2ActionCluster"><button className="ux2Button primary" disabled={locked || closed || pending} onClick={() => onSurface("catalog")}>＋ Adicionar itens</button><div className="ux2TwoActions"><button className="ux2Button ghost" disabled={locked || closed || pending || !latest} onClick={onRepeat}>↻ Mais uma rodada</button><button className="ux2Button ghost" disabled={locked} onClick={() => onSurface("bill")}>{closed ? "Ver conta encerrada" : "Conferir / fechar conta"}</button></div></div>
      <AttendanceOrderStatus orders={tab.orders ?? []} fresh={fresh} />
      <div className="ux2BillPeek"><span><label>Saldo em aberto</label><small>Sem incluir rascunhos não enviados</small></span><strong>{money(tab.exposure_cents)}</strong></div>
      {credit}
      {count > 0 && <p className="ux2Notice"><strong>{count} item(ns) não enviados.</strong> Confira ou descarte o rascunho antes de encerrar.</p>}
      {!latest && <><div className="ux2SectionHead"><h2>Último pedido</h2></div><div className="ux2Empty">Nenhum pedido anterior.</div></>}
      <button className="ux2Button ghost block" disabled={locked} onClick={onBack}>Trocar de mesa ou comanda</button>
    </>}
    {surface === "catalog" && <>
      {credit}
      <label className="ux2Search"><span aria-hidden="true">⌕</span><input aria-label="Buscar produto" placeholder="Buscar no cardápio" type="search" value={query} disabled={locked} onChange={event => setQuery(event.target.value)} /></label>
      <div className="ux2Pills" role="group" aria-label="Categorias">{categories.map(value => <button key={value} data-category={value} aria-pressed={value === category} disabled={locked} onClick={() => setCategory(value)}>{value === "" ? "Todos" : value === "Todos" ? "Todos (categoria)" : value}</button>)}</div>
      <div className="ux2SectionHead"><h2>Cardápio</h2><small>{filtered.length} ITENS</small></div>
      {filtered.map(product => { const quantity = lines.filter(line => line.product.id === product.id).reduce((sum, line) => sum + line.quantity, 0); return <div className="ux2CatalogLine" data-product-id={product.id} key={product.id}><div><button className="ux2ProductName" aria-label={`Personalizar ${product.name}`} disabled={locked || !fresh || product.availability !== "AVAILABLE"} onClick={event => onCustomize(product, event.currentTarget)}><strong>{product.name}</strong></button><small>{money(product.price_cents)}{product.availability !== "AVAILABLE" && " · Indisponível"}</small></div><div className="ux2Quantity"><button aria-label={`Remover ${product.name}`} disabled={locked || !quantity} onClick={() => onReduce(product)}>−</button><output aria-label={`Quantidade de ${product.name}`}>{quantity}</output><button aria-label={`Adicionar ${product.name}`} disabled={locked || !fresh || product.availability !== "AVAILABLE" || quantity >= 99} onClick={() => onAdd(product)}>+</button></div></div>; })}
      {!filtered.length && <div className="ux2Empty">Nenhum produto corresponde à pesquisa. Limpe a busca para ver o cardápio inteiro.</div>}
      {count > 0 && <div className="ux2DraftSummary"><span><strong>{count} item(ns) · {money(total)}</strong><small>Destino: {reference}{tab.table_label ? ` · ${tableLocationLabel(tab.table_label)}` : " · Balcão"}</small></span><button className="ux2Button ghost" disabled={locked} onClick={() => onSurface("draft")}>Ver resumo</button></div>}
      <p className="ux2Notice">O pedido é enviado somente ao tocar em <strong>Enviar</strong>. Valores e itens são revalidados pela API.</p>
    </>}
    {surface === "draft" && <>
      <div className="ux2CardNote"><strong>{tab.display_label || reference} · {reference}</strong><p>{tableLocationLabel(tab.table_label)} · Rascunho ainda não enviado</p></div>
      {lines.map((line, index) => <div className="ux2ReviewRow" key={index}><div><strong>{line.quantity}× {line.product.name}</strong><CustomizationText snapshot={{ variant: line.product.variants?.find(value => value.id === line.selection.variant_id), modifiers: line.product.modifier_groups?.flatMap(group => group.options.filter(value => line.selection.modifier_option_ids.includes(value.id)).map(value => ({ ...value, group_name: group.name }))), special_instructions: line.selection.special_instructions }} /><small>{money(unitPrice(line.product, line.selection))} cada</small>{(line.product.variants?.length || line.product.modifier_groups?.length || line.selection.special_instructions || line.selection.modifier_option_ids.length || line.selection.variant_id) ? <button className="ux2Inline" disabled={locked} onClick={() => onEdit(index)}>Editar</button> : null}{(!line.product.active || line.product.availability !== "AVAILABLE") && <p>Indisponível. Retire ou revise o item.</p>}</div><div><span>{money(unitPrice(line.product, line.selection) * line.quantity)}</span><div className="ux2Quantity"><button aria-label={`Reduzir ${line.product.name}`} disabled={locked} onClick={() => onQuantity(index, -1)}>−</button><button aria-label={`Aumentar ${line.product.name}`} disabled={locked || !fresh || line.quantity >= 99 || !line.product.active || line.product.availability !== "AVAILABLE"} onClick={() => onQuantity(index, 1)}>+</button></div></div></div>)}
      {!count && <div className="ux2Empty">O pedido está vazio.</div>}
      <div className="ux2AmountLine"><small>Total do novo pedido</small><strong>{money(total)}</strong></div>{credit}
      {count > 0 && <button className="ux2Button ghost block" disabled={locked || pending || confirming} onClick={onDiscard}>Descartar rascunho</button>}
      <button className="ux2Button ghost block" disabled={locked} onClick={() => onSurface("catalog")}>← Continuar escolhendo itens</button>
    </>}
    {surface === "bill" && bill}
    {surface === "limit" && <>{credit}<div className="ux2SectionHead"><h2>Regra do estabelecimento</h2></div><p className="ux2Notice">Bloquear pedidos (ENFORCE). Somente a Gerência altera a política canônica. Excesso exige recebimento parcial ou aprovação autorizada.</p><div className="ux2SectionHead"><h2>Garantia financeira</h2></div><p className="ux2Notice">Nenhuma garantia verificada foi informada. Limite operacional e aprovação não representam caução, Pix ou cartão confirmado.</p><button className="ux2Button ghost block" disabled={locked} onClick={() => onSurface("bill")}>Conferir conta</button></>}
    {!closed && !pending && (surface === "catalog" || surface === "draft" || (surface === "tab" && count > 0)) && <div className="ux2TaskFoot"><button className="ux2Button primary block" disabled={!canSend || locked} onClick={onSend}>{confirming ? "Confirmando…" : count ? `Enviar ${count} ${count === 1 ? "item" : "itens"} · ${money(total)}` : "Adicione itens para enviar"}</button></div>}
  </section>;
}
