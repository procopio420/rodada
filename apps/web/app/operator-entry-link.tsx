"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { OperationalIcon } from "@/components/operational-icon";
import { apiCall, type StaffSessionView } from "@/lib/client/staff-auth";
import styles from "./home.module.css";

/** Only an authenticated server session can determine the operator shown here. */
export function OperatorEntryLink() {
  const [operator, setOperator] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    void apiCall<StaffSessionView>("/api/auth/me").then(({ response, body }) => {
      if (active && response.ok && body) setOperator((body as StaffSessionView).staff.display_name);
    }).catch(() => {});
    return () => { active = false; };
  }, []);

  return (
    <Link href="/staff" className={styles.operator} aria-label={operator ? "Conta de " + operator : "Entrar no Rodada"}>
      <OperationalIcon name="people" size={20} />
      <span className={styles.operatorShort} aria-hidden="true">{operator ? operator.split(" ")[0] : "Entrar"}</span>
      <span className={styles.operatorLong} aria-hidden="true">{operator ?? "Entrar"}</span>
    </Link>
  );
}
