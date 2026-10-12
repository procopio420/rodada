"use client";
import { useEffect, useId, useRef, type ReactNode } from "react";
export function ActionDialog({ title, children, locked = false, onClose }: { title: string; children: ReactNode; locked?: boolean; onClose: () => void }) {
 const ref = useRef<HTMLDialogElement>(null);
 const titleId = useId();
 useEffect(() => {
  const previous = document.activeElement as HTMLElement | null;
  const element = ref.current;
  element?.showModal();
  return () => { element?.close(); requestAnimationFrame(() => previous?.focus()); };
 }, []);
 return <dialog ref={ref} className="removalDialog" aria-labelledby={titleId} onCancel={event => { event.preventDefault(); if (!locked) onClose(); }}>
  <h2 id={titleId}>{title}</h2>{children}
  <button className="buttonQuiet" disabled={locked} onClick={onClose}>Voltar</button>
 </dialog>;
}
