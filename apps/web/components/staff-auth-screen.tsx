"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  AccessInvalidationFeed,
  ApiError,
  ReauthReceipt,
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
  return (
    <div className="field">
      <label>{label}</label>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={type}
        autoComplete={autoComplete}
      />
    </div>
  );
}

export function StaffAuthScreen() {
  const [session, setSession] = useState<StaffSessionView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reauthValidUntil, setReauthValidUntil] = useState<string | null>(null);

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
            setReauthValidUntil(null);
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
          setReauthValidUntil(null);
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

  if (!session) {
    return (
      <LoginPanel
        loading={loading}
        error={error}
        onLogin={async (venueSlug, loginIdentifier, pin) => {
          const result = await submitJson<Record<string, unknown>>("/api/auth/login", {
            venue_slug: venueSlug,
            login_identifier: loginIdentifier,
            pin,
          });
          if (result) await loadSession();
        }}
      />
    );
  }

  return (
    <SessionPanel
      session={session}
      loading={loading}
      error={error}
      reauthValidUntil={reauthValidUntil}
      onLock={async () => {
        await submitJson("/api/auth/lock", {});
        setSession(null);
        setReauthValidUntil(null);
      }}
      onLogout={async () => {
        await submitJson("/api/auth/logout", {});
        setSession(null);
        setReauthValidUntil(null);
      }}
      onSwitch={async (loginIdentifier, pin) => {
        const result = await submitJson<Record<string, unknown>>(
          "/api/auth/switch-operator",
          {
            login_identifier: loginIdentifier,
            pin,
          },
        );
        if (result) {
          setReauthValidUntil(null);
          await loadSession();
        }
      }}
      onReauthenticate={async (pin) => {
        const receipt = await submitJson<ReauthReceipt>("/api/auth/reauthenticate", {
          pin,
        });
        if (receipt) setReauthValidUntil(receipt.valid_until);
      }}
    />
  );
}

function LoginPanel({
  loading,
  error,
  onLogin,
}: {
  loading: boolean;
  error: ApiError | null;
  onLogin: (venueSlug: string, loginIdentifier: string, pin: string) => Promise<void>;
}) {
  const [venueSlug, setVenueSlug] = useState("");
  const [loginIdentifier, setLoginIdentifier] = useState("");
  const [pin, setPin] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const currentPin = pin;
    setPin("");
    await onLogin(venueSlug.trim(), loginIdentifier.trim(), currentPin);
  }

  return (
    <main className="appShell">
      <header className="productHeader">
        <div className="eyebrow">RODADA / STAFF</div>
        <h1>Entrar no atendimento</h1>
        <p className="muted">Identifique o operador sem levar credenciais para o browser.</p>
      </header>

      {error ? <ErrorNotice error={error} /> : null}

      <form className="panel" onSubmit={submit}>
        <Field
          label="Estabelecimento"
          value={venueSlug}
          onChange={setVenueSlug}
          autoComplete="organization"
        />
        <Field
          label="Operador"
          value={loginIdentifier}
          onChange={setLoginIdentifier}
          autoComplete="username"
        />
        <Field
          label="PIN"
          value={pin}
          onChange={setPin}
          type="password"
          autoComplete="current-password"
        />
        <button
          className="buttonPrimary"
          type="submit"
          disabled={
            loading ||
            !venueSlug.trim() ||
            !loginIdentifier.trim() ||
            !pin
          }
          style={{ width: "100%" }}
        >
          {loading ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}

function SessionPanel({
  session,
  loading,
  error,
  reauthValidUntil,
  onLock,
  onLogout,
  onSwitch,
  onReauthenticate,
}: {
  session: StaffSessionView;
  loading: boolean;
  error: ApiError | null;
  reauthValidUntil: string | null;
  onLock: () => Promise<void>;
  onLogout: () => Promise<void>;
  onSwitch: (loginIdentifier: string, pin: string) => Promise<void>;
  onReauthenticate: (pin: string) => Promise<void>;
}) {
  const [switchIdentifier, setSwitchIdentifier] = useState("");
  const [switchPin, setSwitchPin] = useState("");
  const [reauthPin, setReauthPin] = useState("");
  const trusted = session.device?.trust_state === "TRUSTED";

  return (
    <main className="appShell">
      <header className="productHeader">
        <div className="eyebrow">RODADA / STAFF</div>
        <h1>{session.venue.name}</h1>
        <p className="muted">Sessão operacional ativa</p>
      </header>

      {error ? <ErrorNotice error={error} /> : null}

      <section className="panel">
        <div className="eyebrow">OPERADOR ATIVO</div>
        <div className="operatorName">{session.staff.display_name}</div>
        <div className="dataRow">
          <span>Função</span>
          <strong>{session.membership.role}</strong>
        </div>
        <div className="dataRow">
          <span>Dispositivo</span>
          <strong>
            <span
              className="statusBadge"
              data-state={trusted ? "success" : "danger"}
            >
              {session.device?.trust_state ?? "SEM DEVICE"}
            </span>
          </strong>
        </div>
        <div className="actions" style={{ marginTop: 16 }}>
          <button
            className="buttonSecondary"
            type="button"
            onClick={() => void onLock()}
            disabled={loading}
          >
            Bloquear
          </button>
          <button
            className="buttonQuiet"
            type="button"
            onClick={() => void onLogout()}
            disabled={loading}
          >
            Sair
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Trocar operador</h2>
        {!trusted ? (
          <div className="notice" data-state="danger">
            Troca rápida só é liberada em terminal confiável.
          </div>
        ) : null}
        <Field
          label="Próximo operador"
          value={switchIdentifier}
          onChange={setSwitchIdentifier}
          autoComplete="off"
        />
        <Field
          label="PIN do próximo operador"
          value={switchPin}
          onChange={setSwitchPin}
          type="password"
          autoComplete="off"
        />
        <button
          className="buttonPrimary"
          type="button"
          disabled={
            loading ||
            !trusted ||
            !switchIdentifier.trim() ||
            !switchPin
          }
          onClick={() => {
            const pin = switchPin;
            setSwitchPin("");
            void onSwitch(switchIdentifier.trim(), pin);
          }}
          style={{ width: "100%" }}
        >
          Trocar operador
        </button>
      </section>

      <section className="panel">
        <h2>Confirmar ação privilegiada</h2>
        <p className="muted">
          Reconfirme sua própria identidade antes de operações sensíveis.
        </p>
        <Field
          label="Seu PIN"
          value={reauthPin}
          onChange={setReauthPin}
          type="password"
          autoComplete="off"
        />
        <button
          className="buttonSecondary"
          type="button"
          disabled={loading || !reauthPin}
          onClick={() => {
            const pin = reauthPin;
            setReauthPin("");
            void onReauthenticate(pin);
          }}
          style={{ width: "100%" }}
        >
          Confirmar identidade
        </button>
        {reauthValidUntil ? (
          <p
            style={{
              color: "var(--color-success)",
              marginTop: 12,
              marginBottom: 0,
            }}
          >
            Identidade confirmada recentemente.
          </p>
        ) : null}
      </section>
    </main>
  );
}

function ErrorNotice({ error }: { error: ApiError }) {
  return (
    <div className="notice" data-state="danger" role="alert">
      <strong>{error.code}</strong>
      <br />
      {error.message}
      {error.retry_after_seconds ? (
        <>
          <br />
          Tente novamente em {error.retry_after_seconds}s.
        </>
      ) : null}
    </div>
  );
}
