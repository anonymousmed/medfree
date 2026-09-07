import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

/* ---------------------------------------------------------------------------
 * cn — tiny classnames joiner (no dependency).
 * ------------------------------------------------------------------------- */
export function cn(...args: (string | false | null | undefined)[]) {
  return args.filter(Boolean).join(" ");
}

const variants: Record<Variant, string> = {
  primary: "bg-accent text-white hover:brightness-110",
  secondary: "bg-surface-2 text-ink-1 hover:bg-surface-3",
  ghost: "bg-transparent text-ink-2 hover:bg-surface-2",
  danger: "bg-danger text-white hover:brightness-110",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export function Button({ variant = "primary", size = "md", className, ...rest }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        "disabled:opacity-50 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...rest}
    />
  );
}

/* --------------------------------------------------------------------------- */

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ className, children, ...rest }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl2 border border-surface-2 bg-surface-1 p-5 shadow-sm",
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function Badge({
  children,
  color = "accent",
  className,
}: {
  children: ReactNode;
  color?: "accent" | "success" | "warning" | "danger" | "neutral";
  className?: string;
}) {
  const colors = {
    accent: "bg-accent-soft text-accent",
    success: "bg-success/15 text-success",
    warning: "bg-warning/15 text-warning",
    danger: "bg-danger/15 text-danger",
    neutral: "bg-surface-2 text-ink-2",
  };
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", colors[color], className)}>
      {children}
    </span>
  );
}

/* --------------------------------------------------------------------------- */

export function ProgressBar({
  value,
  className,
  label,
}: {
  value: number;
  className?: string;
  label?: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between text-xs text-ink-3 mb-1">
        {label && <span>{label}</span>}
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
        <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  action,
  className,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-end justify-between gap-4", className)}>
      <div>
        {eyebrow && <p className="text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</p>}
        <h2 className="text-xl font-semibold text-ink-1 md:text-2xl">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-ink-3">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
