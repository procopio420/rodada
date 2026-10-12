"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiCall, type StaffSessionView } from "@/lib/client/staff-auth";
export function DeveloperLink() {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    let active = true;
    void Promise.all([fetch("/api/dev/status").then(response => response.json()), apiCall<StaffSessionView>("/api/auth/me")])
      .then(([data, auth]) => { if (active) setEnabled(data.enabled === true && auth.response.ok && (auth.body as StaffSessionView).capabilities.includes("staff.manage")); })
      .catch(() => {});
    return () => { active = false; };
  }, []);
  return enabled ? <Link className="buttonSecondary" href="/dev/staff">Área DEV · administrar equipe</Link> : null;
}
