import type { ButtonHTMLAttributes, HTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "quiet";

type ActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    "w-full border-0 bg-ink px-3 py-3 text-left text-white hover:bg-[#29372f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange",
  secondary:
    "border border-ink bg-transparent px-4 py-3 text-ink hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange",
  quiet:
    "border-0 border-b border-ink bg-transparent px-0 py-0.5 text-left font-mono text-[11px] text-ink hover:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange",
};

export function ActionButton({
  className = "",
  variant = "primary",
  ...props
}: ActionButtonProps) {
  return (
    <button
      className={`inline-flex cursor-pointer items-center justify-between gap-3 ${buttonVariants[variant]} ${className}`}
      {...props}
    />
  );
}

export function Panel({
  className = "",
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={`border border-line bg-white/60 p-5 ${className}`}
      {...props}
    />
  );
}

export function SectionLabel({
  className = "",
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={`font-mono text-[10px] font-medium text-muted ${className}`}
      {...props}
    />
  );
}