"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./staff-auth-screen.module.css";

import { FormEvent, ReactNode, useCallback, useEffect, useId, useState } from "react";
import {
  AccessInvalidationFeed,
  ApiError,
  StaffSessionView,
  apiCall,
  asApiError,
} from "@/lib/client/staff-auth";

function Field({
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  autoComplete?: string;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={type}
        inputMode={type === "password" ? "numeric" : undefined}
        autoComplete={autoComplete}
      />
    </div>
  );
}

type VenueLookup = { mode: "loading" | "compatibility" | "unavailable" } | { mode: "establishment"; venue: { slug: string; name: string } };

export function StaffAuthScreen({ renderSession }: { renderSession?: (session: StaffSessionView, logout: () => Promise<void>) => ReactNode } = {}) {
  const router = useRouter();
  const [venueLookup, setVenueLookup] = useState<VenueLookup>({ mode: "loading" });
  useEffect(() => {
    let active = true;
    void fetch("/api/venue/context", { cache: "no-store" })
      .then(async response => response.ok ? await response.json() : null)
      .then(payload => { if (active) setVenueLookup(payload?.mode === "establishment" && payload.venue?.slug && payload.venue?.name ? payload : payload?.mode === "compatibility" ? { mode: "compatibility" } : { mode: "unavailable" }); })
      .catch(() => { if (active) setVenueLookup({ mode: "unavailable" }); });
    return () => { active = false; };
  }, []);
  const [session, setSession] = useState<StaffSessionView | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionChecked, setSessionChecked] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const loadSession = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiCall<StaffSessionView>("/api/auth/me");
      if (result.response.ok && result.body) {
        setSession(result.body as StaffSessionView);
        return;
      }

      if (result.response.status === 401 || result.response.status === 403) {
        setSession(null);
        return;
      }

      setError(asApiError(result.body));
    } catch {
      setError({
        code: "NETWORK_ERROR",
        message: "Não foi possível falar com o Rodada.",
      });
    } finally {
      setLoading(false);
      setSessionChecked(true);
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const sessionId = session?.session.id ?? null;

  useEffect(() => {
    if (!sessionId) return;

    let cancelled = false;
    let cursor = 0;

    async function pollInvalidations() {
      try {
        const result = await apiCall<AccessInvalidationFeed>(
          "/api/auth/invalidation-events?after=" + cursor,
        );
        if (cancelled) return;

        if (result.response.ok && result.body) {
          const feed = result.body as AccessInvalidationFeed;
          cursor = feed.cursor;

          if (feed.results.length > 0) {
            await loadSession();
          }
          return;
        }

        const apiError = asApiError(result.body);
        if (
          apiError.code === "SESSION_REVOKED" ||
          apiError.code === "SESSION_SUPERSEDED" ||
          apiError.code === "SESSION_EXPIRED" ||
          apiError.code === "MEMBERSHIP_REVOKED" ||
          apiError.code === "MEMBERSHIP_SUSPENDED" ||
          apiError.code === "DEVICE_REVOKED" ||
          apiError.code === "STAFF_INACTIVE"
        ) {
          setSession(null);
          setError(apiError);
        }
      } catch {
        // Realtime invalidation is advisory. Normal API auth remains authoritative.
      }
    }

    void pollInvalidations();
    const timer = window.setInterval(() => {
      void pollInvalidations();
    }, 15_000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [sessionId, loadSession]);

  async function submitJson<T>(
    path: string,
    payload: Record<string, string>,
  ): Promise<T | null> {
    setLoading(true);
    setError(null);

    try {
      const result = await apiCall<T>(path, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (!result.response.ok) {
        const apiError = asApiError(result.body);
        setError(apiError);

        if (
          apiError.code === "SESSION_REVOKED" ||
          apiError.code === "SESSION_SUPERSEDED" ||
          apiError.code === "SESSION_EXPIRED" ||
          apiError.code === "MEMBERSHIP_REVOKED" ||
          apiError.code === "MEMBERSHIP_SUSPENDED" ||
          apiError.code === "DEVICE_REVOKED" ||
          apiError.code === "STAFF_INACTIVE"
        ) {
          setSession(null);
        }
        return null;
      }

      return result.body as T | null;
    } catch {
      setError({
        code: "NETWORK_ERROR",
        message: "Não foi possível falar com o Rodada.",
      });
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function endCurrentSession(path: "/api/auth/lock" | "/api/auth/logout") {
    setLoading(true);
    setError(null);
    try {
      // The API intentionally responds 204 without JSON on successful lock/logout.
      const result = await apiCall(path, { method: "POST", body: "{}" });
      if (result.response.ok) setSession(null);
      else setError(asApiError(result.body));
    } catch {
      setError({ code: "NETWORK_ERROR", message: "Não foi possível encerrar a sessão. Confira a conexão." });
    } finally {
      setLoading(false);
    }
  }

  if (!session && !sessionChecked) {
    return <main className={styles.shell}><p className={styles.loading} role="status">Carregando acesso…</p></main>;
  }

  if (!session) {
    return (
      <LoginPanel
        venueLookup={venueLookup}
        loading={loading}
        error={error}
        onLogin={async (venueSlug, loginIdentifier, pin) => {
          const result = await submitJson<Record<string, unknown>>("/api/auth/login", {
            venue_slug: venueSlug,
            login_identifier: loginIdentifier,
            pin,
          });
          if (result) {
            await loadSession();
            // The tenant landing page is the operational entry, not /staff.
            if (!renderSession && venueLookup.mode === "establishment") router.replace("/");
          }
        }}
      />
    );
  }

  if (renderSession) return <>{error && <div className="appShell"><ErrorNotice error={error} /></div>}{renderSession(session, async () => {
    try {
      const result = await apiCall("/api/auth/logout", { method: "POST", body: "{}" });
      if (result.response.ok) { setSession(null); }
      else setError(asApiError(result.body));
    } catch { setError({ code: "NETWORK_ERROR", message: "Não foi possível sair. Verifique a conexão." }); }
  })}</>;

  return (
    <SessionPanel
      session={session}
      destination={venueLookup.mode === "establishment" ? "/" : "/attendance"}
      loading={loading}
      error={error}
      onLock={() => endCurrentSession("/api/auth/lock")}
      onLogout={() => endCurrentSession("/api/auth/logout")}
      onSwitch={async (loginIdentifier, pin) => {
        const result = await submitJson<Record<string, unknown>>(
          "/api/auth/switch-operator",
          {
            login_identifier: loginIdentifier,
            pin,
          },
        );
        if (result) {
          await loadSession();
        }
      }}
    />
  );
}


const roleLabels: Record<string, string> = {
  STAFF: "Equipe",
  CASHIER: "Caixa",
  MANAGER: "Gerente",
  OWNER: "Responsável",
};

function StaffHeader({ venue, description }: { venue: string; description: string }) {
  return (
    <header className={styles.header}>
      <Image src="/brand/wordmark.svg" alt="Rodada" width={144} height={36} priority className={styles.logo} />
      <div className={styles.venue}>{venue}</div>
      <p className={styles.description}>{description}</p>
    </header>
  );
}

function LoginPanel({
  loading,
  error,
  onLogin,
  venueLookup,
}: {
  venueLookup: VenueLookup;
  loading: boolean;
  error: ApiError | null;
  onLogin: (venueSlug: string, loginIdentifier: string, pin: string) => Promise<void>;
}) {
  const [venueSlug, setVenueSlug] = useState("");
  const [loginIdentifier, setLoginIdentifier] = useState("");
  const [pin, setPin] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (venueLookup.mode === "loading" || venueLookup.mode === "unavailable") return;
    const currentPin = pin;
    setPin("");
    await onLogin(
      venueLookup.mode === "establishment" ? venueLookup.venue.slug : venueSlug.trim(),
      loginIdentifier.trim(),
      currentPin,
    );
  }

  const canSubmit =
    venueLookup.mode !== "loading" &&
    venueLookup.mode !== "unavailable" &&
    (venueLookup.mode !== "compatibility" || !!venueSlug.trim()) &&
    !!loginIdentifier.trim() && !!pin && !loading;

  return (
    <main className={styles.shell}>
      <StaffHeader
        venue={venueLookup.mode === "establishment" ? venueLookup.venue.name : "Entrar no Rodada"}
        description="Entre com seu operador para começar."
      />
      <section className={styles.card} aria-labelledby="staff-login-title">
        <h1 id="staff-login-title" className={styles.title}>Quem vai trabalhar?</h1>
        <p className={styles.support}>Seu usuário e PIN, só isso.</p>
        {error && <ErrorNotice error={error} />}
        {venueLookup.mode === "unavailable" && (
          <p className={styles.warning} role="alert">Não foi possível identificar este bar. Atualize a página e tente novamente.</p>
        )}
        <form onSubmit={submit} className={styles.form}>
          {venueLookup.mode === "compatibility" && (
            <Field label="Estabelecimento" value={venueSlug} onChange={setVenueSlug} autoComplete="organization" />
          )}
          <Field label="Operador" value={loginIdentifier} onChange={setLoginIdentifier} autoComplete="username" />
          <Field label="PIN" value={pin} onChange={setPin} type="password" autoComplete="current-password" />
          <button className={styles.primary} type="submit" disabled={!canSubmit}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}

function SessionPanel({
  session,
  destination,
  loading,
  error,
  onLock,
  onLogout,
  onSwitch,
}: {
  session: StaffSessionView;
  destination: string;
  loading: boolean;
  error: ApiError | null;
  onLock: () => Promise<void>;
  onLogout: () => Promise<void>;
  onSwitch: (loginIdentifier: string, pin: string) => Promise<void>;
}) {
  const [switchOpen, setSwitchOpen] = useState(false);
  const [switchIdentifier, setSwitchIdentifier] = useState("");
  const [switchPin, setSwitchPin] = useState("");
  const trusted = session.device?.trust_state === "TRUSTED";

  async function submitSwitch(event: FormEvent) {
    event.preventDefault();
    if (!trusted || !switchIdentifier.trim() || !switchPin || loading) return;
    const currentPin = switchPin;
    setSwitchPin("");
    await onSwitch(switchIdentifier.trim(), currentPin);
    setSwitchOpen(false);
  }

  return (
    <main className={styles.shell}>
      <StaffHeader venue={session.venue.name} description="Acesso da equipe" />
      <section className={styles.card} aria-labelledby="staff-account-title">
        {error && <ErrorNotice error={error} />}
        <div className={styles.online}><span className={styles.dot} aria-hidden="true" /> Você está conectado</div>
        <h1 id="staff-account-title" className={styles.name}>{session.staff.display_name}</h1>
        <p className={styles.role}>{roleLabels[session.membership.role] ?? "Equipe"}</p>
        <Link href={destination} className={styles.primary}>Continuar trabalhando <span aria-hidden="true">→</span></Link>
        <button
          type="button"
          className={styles.secondary}
          disabled={loading}
          aria-expanded={trusted ? switchOpen : undefined}
          onClick={() => trusted ? setSwitchOpen(current => !current) : void onLogout()}
        >
          Trocar de pessoa
        </button>
        {!trusted && (
          <p className={styles.hint}>Para outra pessoa entrar neste celular, encerramos primeiro a sessão atual.</p>
        )}
        {trusted && switchOpen && (
          <form className={styles.switchForm} onSubmit={submitSwitch}>
            <h2 className={styles.subheading}>Próxima pessoa</h2>
            <Field label="Operador" value={switchIdentifier} onChange={setSwitchIdentifier} autoComplete="off" />
            <Field label="PIN" value={switchPin} onChange={setSwitchPin} type="password" autoComplete="off" />
            <button className={styles.primary} type="submit" disabled={loading || !switchIdentifier.trim() || !switchPin}>
              Confirmar troca
            </button>
          </form>
        )}
        <details className={styles.options}>
          <summary>Opções de segurança</summary>
          <div className={styles.optionButtons}>
            <button type="button" onClick={() => void onLock()} disabled={loading}>Bloquear acesso</button>
            <button type="button" onClick={() => void onLogout()} disabled={loading}>Sair desta conta</button>
          </div>
        </details>
      </section>
    </main>
  );
}

function ErrorNotice({ error }: { error: ApiError }) {
  return (
    <div className={styles.error} role="alert">
      {error.message}
      {error.retry_after_seconds ? " Tente novamente em " + error.retry_after_seconds + " segundos." : null}
    </div>
  );
}
