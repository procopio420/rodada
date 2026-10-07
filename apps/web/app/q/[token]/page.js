"use client";
import {useEffect, useMemo, useState} from "react";
import {useParams} from "next/navigation";

const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api";
const money=(c=0)=>new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL",maximumFractionDigits:0}).format(c/100);
const state={NEW:"Recebido",ACCEPTED:"Aceito",PREPARING:"Preparando",READY:"Pronto",PICKED_UP:"A caminho",DELIVERED:"Entregue",CANCELLED:"Cancelado"};
async function call(path, options={}){const res=await fetch(`${API}${path}`,{...options,headers:{"Content-Type":"application/json",...options.headers}});const data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||"Não foi possível concluir.");return data}

export default function CustomerQr(){
 const {token}=useParams(); const [entry,setEntry]=useState(null),[session,setSession]=useState(null),[cart,setCart]=useState({}),[error,setError]=useState(""),[busy,setBusy]=useState(false),[name,setName]=useState("");
 const load=async()=>{try{const data=await call(`/public/qr/${token}/`);setEntry(data)}catch(e){setError(e.message)}};
 useEffect(()=>{load()},[token]);
 useEffect(()=>{if(!session?.session_token)return;const id=setInterval(async()=>{try{const result=await call(`/public/sessions/${session.session_token}/`);setSession(current=>({...current,...result}))}catch{}},5000);return()=>clearInterval(id)},[session?.session_token]);
 const products=session?.products||entry?.products||[]; const rows=useMemo(()=>products.filter(p=>cart[p.id]).map(p=>({...p,quantity:cart[p.id]})),[products,cart]);
 const add=id=>setCart(c=>({...c,[id]:(c[id]||0)+1}));
 const start=async tab_token=>{setBusy(true);try{setSession(await call(`/public/qr/${token}/sessions/`,{method:"POST",body:JSON.stringify({guest_name:name,tab_token})}))}catch(e){setError(e.message)}finally{setBusy(false)}};
 const order=async()=>{setBusy(true);try{const result=await call(`/public/sessions/${session.session_token}/orders/`,{method:"POST",body:JSON.stringify({items:rows.map(r=>({product_id:r.id,quantity:r.quantity})),idempotency_key:crypto.randomUUID()})});setSession(s=>({...s,...result}));setCart({})}catch(e){setError(e.message)}finally{setBusy(false)}};
 if(error)return <main className="customer"><h1>Rodada</h1><p className="customer-error">{error}</p></main>;
 if(!entry)return <main className="customer"><p>Carregando mesa…</p></main>;
 if(!session)return <main className="customer"><span className="customer-kicker">{entry.venue}</span><h1>{entry.table.label}</h1><p>{entry.table.zone||"No salão"} · peça pelo celular, sem instalar app.</p><label className="customer-name">Seu nome <small>opcional</small><input value={name} onChange={e=>setName(e.target.value)} placeholder="Como podemos chamar você?"/></label>{entry.tabs.length>0&&<><h2>Entrar numa comanda</h2>{entry.tabs.map(tab=><button className="customer-tab" onClick={()=>start(tab.token)} disabled={busy} key={tab.token}>{tab.label}</button>)}</>}<button className="customer-primary" onClick={()=>start(null)} disabled={busy}>Abrir nova comanda</button></main>;
 const tab=session.tab; const items=tab.orders.flatMap(o=>o.items); return <main className="customer"><header><span className="customer-kicker">{session.table.label}</span><h1>{tab.customer_name||tab.label||"Sua comanda"}</h1><p>Em aberto: <b>{money(tab.exposure_cents)}</b></p></header><section><h2>Cardápio</h2><div className="customer-products">{products.map(p=><button key={p.id} className={!p.available?"unavailable":""} disabled={!p.available||busy} onClick={()=>add(p.id)}><span className="item-icon">{p.icon_key?.slice(0,1)||"•"}</span><b>{p.name}</b><small>{p.available?money(p.current_price_cents):"Indisponível"}</small>{cart[p.id]?<em>{cart[p.id]}</em>:null}</button>)}</div></section>{rows.length>0&&<footer className="customer-cart"><span>{rows.map(r=>`${r.quantity}× ${r.name}`).join(" · ")}</span><button className="customer-primary" onClick={order} disabled={busy}>Pedir {money(rows.reduce((v,r)=>v+r.quantity*r.current_price_cents,0))}</button></footer>}<section className="customer-status"><h2>Acompanhar pedido</h2>{items.length?items.map(i=><p key={i.id}><b>{i.quantity}× {i.product_name}</b><span>{state[i.state]}</span></p>):<p>Ainda não há itens nesta comanda.</p>}</section>{error&&<p className="customer-error">{error}</p>}</main>
}
