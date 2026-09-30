"use client";

// Sumi brush stroke that draws itself in once scrolled into view.
// Ported from VG app/components/landing/{Landing,InkReveal}.tsx. CSS: references/ink-and-motion.md.
// No JS or reduced motion: the CSS shows the stroke finished, so nothing is ever missing.
import { useEffect } from "react";

export function Brush({ className = "", d = "M8 24 C80 12 250 30 392 14", tone = "sapphire" }: {
  className?: string;
  d?: string;                                  // one gentle curve across a 400x40 box
  tone?: "sapphire" | "navy" | "rust";
}) {
  return (
    <svg className={`qi-brush ${className}`} data-tone={tone} data-ink="" viewBox="0 0 400 40"
      preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <path d={d} pathLength={1} />
      <path className="qi-brush-dry" d={d} pathLength={1} />
    </svg>
  );
}

/** Mount once per page, inside the .qi root. */
export function InkReveal() {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>(".qi");
    if (!root || !("IntersectionObserver" in window)) return;
    root.dataset.inkLive = "true";
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        (e.target as HTMLElement).dataset.inked = "true";
        io.unobserve(e.target);
      }
    }, { rootMargin: "0px 0px -12% 0px" });
    root.querySelectorAll<HTMLElement>("[data-ink]").forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);
  return null;
}
