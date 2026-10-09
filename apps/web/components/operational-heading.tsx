import type { HTMLAttributes } from "react";
import { OperationalIcon, type OperationalIconName } from "./operational-icon";

/** Decorative context only: preserve heading semantics, focus and accessible text. */
export function OperationalHeading({ as: Tag = "h2", icon, children, className = "", ...props }: HTMLAttributes<HTMLHeadingElement> & { as?: "h1" | "h2"; icon: OperationalIconName }) {
  return <Tag {...props} className={`operationalHeading ${className}`} data-level={Tag === "h1" ? "1" : "2"}><OperationalIcon name={icon} size={Tag === "h1" ? 24 : 20} /><span className="operationalHeadingText">{children}</span></Tag>;
}
