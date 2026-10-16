"use client";

import {useCallback,useEffect,useRef,useState} from "react";
import {apiCall,asApiError} from "@/lib/client/staff-auth";
import type {StaffTask} from "@/lib/client/dispatch-target";

type Action="claim"|"complete";
export function AttendanceTaskContext({taskId,staffId,recoveryScope,onBack,onChanged}:{taskId:string;staffId:string;recoveryScope:string;onBack:()=>void;onChanged?:()=>void}) {
  const [task,setTask]=useState<StaffTask|null>(null),[pending,setPending]=useState<Action|null>(null);
  const [fresh,setFresh]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
  const sending=useRef(false),active=useRef(true),currentTask=useRef(taskId),readEpoch=useRef(0);
  const storageKey=`rodada:dispatch-action:${recoveryScope}:${taskId}`;
  const refresh=useCallback(async()=>{
    const epoch=++readEpoch.current;
    const result=await apiCall<StaffTask>(`/api/attendance/dispatch/tasks/${taskId}/`);
    if(!result.response.ok||!result.body||!("id" in result.body)||result.body.id!==taskId)throw new Error(asApiError(result.body).message);
    if(!active.current||currentTask.current!==taskId||epoch!==readEpoch.current)return;
    const canonical=result.body;setTask(canonical);setFresh(true);
    const saved=localStorage.getItem(storageKey);
    if(saved&&(canonical.state==="DONE"||(saved==="claim"&&canonical.claimed_by_id===staffId))){localStorage.removeItem(storageKey);setPending(null);onChanged?.();}
    return canonical;
  },[taskId,storageKey,staffId,onChanged]);
  useEffect(()=>{
    active.current=true;currentTask.current=taskId;setTask(null);setPending(null);setFresh(false);setError("");
    try{const stored=localStorage.getItem(storageKey);if(stored==="claim"||stored==="complete")setPending(stored);}
    catch{setError("Recuperação indisponível. Confira a chamada antes de agir.");return()=>{active.current=false;readEpoch.current++;};}
    const read=()=>{if(sending.current)return;void refresh().catch(failure=>{if(active.current){setFresh(false);setError(failure.message)}});};
    read();const timer=setInterval(read,15000);return()=>{active.current=false;readEpoch.current++;clearInterval(timer)};
  },[storageKey,refresh]);
  async function act(action:Action){
    if(sending.current||!fresh||!task)return;
    sending.current=true;readEpoch.current++;setBusy(true);setError("");
    try{
      // Save before the mutation. Reopening retries this task/action, never a new task.
      localStorage.setItem(storageKey,action);setPending(action);
      const result=await apiCall(`/api/attendance/dispatch/requests/${taskId}/${action}/`,{method:"POST",body:"{}"});
      if(!result.response.ok&&result.response.status<500){localStorage.removeItem(storageKey);setPending(null);setError(asApiError(result.body).message);}
      await refresh();
    }catch{setFresh(false);setError("Resultado não confirmado. Verifique a mesma chamada antes de repetir.");}
    finally{sending.current=false;setBusy(false);}
  }
  const mine=task?.claimed_by_id===staffId,other=!!task?.claimed_by_id&&!mine,done=task?.state==="DONE";
  return <aside className="ux2TaskContext" aria-label="Chamado de origem">
    <strong>{task?.task_type==="BILL_REQUEST"?"Pedido de conta pelo celular":"Pedido de atendimento"}</strong>
    <p>{done?"Chamada concluída no servidor.":other?"Outro operador está responsável.":"Abrir a comanda não conclui o chamado."}</p>
    {error&&<p role="alert">{error}</p>}
    {pending&&<p role="status">Ação sem confirmação preservada nesta chamada.</p>}
    {!fresh&&<button disabled={busy} onClick={()=>void refresh().catch(failure=>setError(failure.message))}>Verificar mesma chamada</button>}
    {fresh&&!done&&!other&&<button disabled={busy} onClick={()=>void act(pending??(mine||task?.task_type==="BILL_REQUEST"?"complete":"claim"))}>{pending?"Verificar mesma ação":mine?"Atendimento resolvido":task?.task_type==="BILL_REQUEST"?"Apenas concluir pedido de conta":"Assumir chamado"}</button>}
    <button disabled={busy} onClick={onBack}>Voltar à fila →</button>
  </aside>;
}
