"use client";
import { useEffect, useId, useRef, type ReactNode } from "react";
export function ActionDialog({ title, children, locked = false, onClose, closeButtonClassName = "buttonQuiet", returnFocus, open = true, dialogClassName = "" }: { title: string; children: ReactNode; locked?: boolean; onClose: () => void; closeButtonClassName?: string; returnFocus?: HTMLElement | null; open?: boolean; dialogClassName?: string }) {
 const ref = useRef<HTMLDialogElement>(null);
 const titleId = useId();
 useEffect(() => {
  if (!open) return;
  const previous = returnFocus ?? document.activeElement as HTMLElement | null;
  const element = ref.current;
  element?.showModal();
  return () => { element?.close(); requestAnimationFrame(() => previous?.focus()); };
 }, [open, returnFocus]);
 return <dialog ref={ref} className={`removalDialog ${dialogClassName}`} aria-labelledby={titleId} onCancel={event => { event.preventDefault(); if (!locked) onClose(); }}>
  <h2 id={titleId}>{title}</h2>{children}
  <button className={closeButtonClassName} disabled={locked} onClick={onClose}>Voltar</button>
 </dialog>;
}
