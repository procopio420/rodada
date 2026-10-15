"use client";

import { useCallback, useEffect, useState } from "react";

import { OperationalHeading } from "@/components/operational-heading";
import { guestApi } from "@/lib/client/guest-api";

type Identity = {
  authenticated: boolean;
  display_name?: string;
  linked_tab_id?: string | null;
  claimable_tabs: { id: string; label: string }[];
};
type ErrorBody = { message?: string };

export function GuestCustomerProfile({
  selector, tabId, locked, onLinked,
}: {
  selector: string;
  tabId: string | null;
  locked: boolean;
  onLinked: () => void;
}) {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!selector) return;
    const response = await guestApi<Identity>("customer/context/", selector);
    if (response.ok) setIdentity(response.body as Identity);
    else if (response.status === 401) setIdentity({ authenticated: false, claimable_tabs: [] });
    else setError((response.body as ErrorBody).message ?? "Não foi possível consultar o perfil.");
  }, [selector]);

  useEffect(() => { void load(); }, [load]);

  async function authenticate() {
    if (busy || locked) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await guestApi<Identity>(`customer/${mode}/`, selector, {
        method: "POST",
        body: JSON.stringify({
          username: username.trim(),
          password,
          ...(mode === "register" ? { display_name: displayName.trim() } : {}),
        }),
      });
      if (!response.ok) {
        setError((response.body as ErrorBody).message ?? "Não foi possível autenticar.");
        return;
      }
      await load();
      setNotice(mode === "register" ? "Perfil criado e associado à sua comanda." : "Perfil autenticado.");
      if (mode === "register") onLinked();
    } finally {
      setPassword("");
      setBusy(false);
    }
  }

  async function claim(targetId: string) {
    if (busy || locked) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await guestApi("customer/claim/", selector, {
        method: "POST", body: JSON.stringify({ target_tab_id: targetId }),
      });
      if (!response.ok) {
        setError((response.body as ErrorBody).message ?? "Não foi possível vincular a comanda.");
        return;
      }
      setNotice("Perfil vinculado a esta comanda.");
      await load();
      onLinked();
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    if (busy || locked) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await guestApi("customer/logout/", selector, { method: "POST", body: "{}" });
      if (!response.ok) {
        setError((response.body as ErrorBody).message ?? "Não foi possível sair do perfil.");
        return;
      }
      setIdentity({ authenticated: false, claimable_tabs: [] });
      setPassword("");
      setNotice("Perfil desconectado. Sua comanda e pedidos permanecem nesta visita.");
    } finally {
      setBusy(false);
    }
  }

  async function rotatePassword() {
    if (busy || locked || !oldPassword || newPassword.length < 12) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await guestApi("customer/password/", selector, {
        method: "POST",
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });
      if (!response.ok) {
        setError((response.body as ErrorBody).message ?? "Não foi possível trocar a senha.");
        return;
      }
      await load();
      setNotice("Senha trocada. Outros acessos ao perfil foram revogados.");
    } finally {
      setOldPassword(""); setNewPassword("");
      setBusy(false);
    }
  }

  return <details className="panel">
    <summary>Meu perfil (opcional)</summary>
    <OperationalHeading as="h2" icon="wallet">Continuar com meu perfil</OperationalHeading>
    <p className="muted">Seu pedido funciona sem cadastro. Perfil exige senha e nunca é autorizado só pelo nome da mesa. CPF não é necessário.</p>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {notice && <p className="notice" role="status">{notice}</p>}
    {identity?.authenticated ? <>
      <p>Perfil: <strong>{identity.display_name}</strong></p>
      {tabId && <button className="buttonSecondary" disabled={busy || locked} onClick={() => void claim(tabId)}>Vincular perfil à minha comanda</button>}
      {!tabId && <>
        <p className="muted">Escolha uma comanda do seu perfil nesta visita. Não basta conhecer o nome de outra pessoa.</p>
        {!identity.claimable_tabs.length && <p className="muted">Nenhuma comanda do perfil nesta mesa. Você ainda pode abrir uma comanda anônima.</p>}
        {identity.claimable_tabs.map(tab => <div className="dataRow" key={tab.id}>
          <span>{tab.label} · {tab.id.slice(0, 8)}</span>
          <button className="buttonSecondary" disabled={busy || locked} onClick={() => void claim(tab.id)}>Assumir comanda</button>
        </div>)}
      </>}
      <details>
        <summary>Trocar senha e encerrar outras sessões</summary>
        <div className="field"><label htmlFor="guest-profile-old-password">Senha atual</label><input id="guest-profile-old-password" type="password" autoComplete="current-password" value={oldPassword} onChange={event => setOldPassword(event.target.value)} /></div>
        <div className="field"><label htmlFor="guest-profile-new-password">Nova senha (mínimo 12 caracteres)</label><input id="guest-profile-new-password" type="password" autoComplete="new-password" minLength={12} maxLength={128} value={newPassword} onChange={event => setNewPassword(event.target.value)} /></div>
        <button className="buttonSecondary" disabled={busy || locked || !oldPassword || newPassword.length < 12} onClick={() => void rotatePassword()}>Trocar senha e revogar acessos anteriores</button>
      </details>
      <button className="buttonQuiet" disabled={busy || locked} onClick={() => void logout()}>Sair do perfil</button>
    </> : <>
      <div className="actions">
        <button type="button" className={mode === "login" ? "buttonPrimary" : "buttonSecondary"} disabled={busy} onClick={() => setMode("login")}>Entrar</button>
        <button type="button" className={mode === "register" ? "buttonPrimary" : "buttonSecondary"} disabled={busy} onClick={() => setMode("register")}>Criar perfil</button>
      </div>
      {mode === "register" && !tabId && <p className="notice" data-state="warning">Abra uma comanda anônima antes de criar seu perfil.</p>}
      {mode === "register" && <div className="field"><label htmlFor="guest-profile-name">Nome para o perfil</label><input id="guest-profile-name" value={displayName} maxLength={120} autoComplete="name" onChange={event=>setDisplayName(event.target.value)} /></div>}
      <div className="field"><label htmlFor="guest-profile-username">Usuário (3 a 64 letras, números, ponto, hífen ou _)</label><input id="guest-profile-username" value={username} minLength={3} maxLength={64} autoCapitalize="none" autoComplete="username" onChange={event=>setUsername(event.target.value)} /></div>
      <div className="field"><label htmlFor="guest-profile-password">Senha {mode === "register" ? "(mínimo 12 caracteres)" : ""}</label><input id="guest-profile-password" type="password" value={password} minLength={mode === "register" ? 12 : 1} maxLength={128} autoComplete={mode === "register" ? "new-password" : "current-password"} onChange={event=>setPassword(event.target.value)} /></div>
      <button className="buttonPrimary" disabled={busy || locked || username.length < 3 || password.length < (mode === "register" ? 12 : 1) || (mode === "register" && (!tabId || !displayName.trim()))} onClick={() => void authenticate()}>{busy ? "Verificando…" : mode === "login" ? "Entrar no perfil" : "Criar perfil opcional"}</button>
      <p className="muted">Perfis antigos cadastrados apenas pelo bar não podem ser assumidos por nome. Consulte a equipe para recuperação assistida.</p>
    </>}
  </details>;
}
