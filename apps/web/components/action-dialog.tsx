"use client";
import { useEffect, useId, useRef, type ReactNode } from "react";
export function ActionDialog({ title, children, locked = false, onClose, closeButtonClassName = "buttonQuiet", returnFocus, open = true, dialogClassName = "", dismissOnBackdrop = false }: { title: string; children: ReactNode; locked?: boolean; onClose: () => void; closeButtonClassName?: string; returnFocus?: HTMLElement | null; open?: boolean; dialogClassName?: string; dismissOnBackdrop?: boolean }) {
 const ref = useRef<HTMLDialogElement>(null);
 const titleId = useId();
 const backdropPress = useRef(false);
 const isOutside = (element: HTMLDialogElement, x: number, y: number) => {
  const bounds = element.getBoundingClientRect();
  return x < bounds.left || x > bounds.right || y < bounds.top || y > bounds.bottom;
 };
 useEffect(() => {
  if (!open) return;
  const previous = returnFocus ?? document.activeElement as HTMLElement | null;
  const element = ref.current;
  element?.showModal();
  return () => { element?.close(); requestAnimationFrame(() => previous?.focus()); };
 }, [open, returnFocus]);
 return <dialog ref={ref} className={`removalDialog ${dialogClassName}`} aria-labelledby={titleId} onPointerDown={event => { backdropPress.current = event.target === event.currentTarget && isOutside(event.currentTarget, event.clientX, event.clientY); }} onClick={event => { const outside = backdropPress.current && event.target === event.currentTarget && isOutside(event.currentTarget, event.clientX, event.clientY); backdropPress.current = false; if (dismissOnBackdrop && !locked && outside) onClose(); }} onCancel={event => { event.preventDefault(); event.stopPropagation(); if (!locked) onClose(); }}>
  <h2 id={titleId}>{title}</h2>{children}
  <button className={closeButtonClassName} disabled={locked} onClick={onClose}>Voltar</button>
 </dialog>;
}
