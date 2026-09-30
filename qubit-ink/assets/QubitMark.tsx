// Qubit Studio marks: two 2x2 woodblock grids. Q = three cut blocks plus a rising
// quarter-sun (bottom-right); S = arcs on the outer top-left and bottom-right corners (drawn TR/BL, rotated 90).
const Q_BLOCKS = "M4 5 L29 4 L29.5 29 L3.5 29.5Z M35 4.5 L60 5 L59.5 29.5 L34.5 29Z M4.5 35 L29 34.5 L28.5 60 L4 59.5Z";
const Q_SUN = "M35 60 L35 35 A25 25 0 0 1 60 60Z";
const S_BLOCKS = "M4 5 L29 4 L29.5 29 L3.5 29.5Z M35 35 L59.5 34.5 L60 59.5 L34.5 60Z";
const S_ARCS = "M35 29.5 L35 4.5 A25 25 0 0 1 60 29.5Z M29 35 L29 60 A25 25 0 0 1 4 35Z";

type MarkProps = { letter?: "q" | "s"; size?: number; reversed?: boolean };

export default function QubitMark({ letter = "q", size = 30, reversed = false }: MarkProps) {
  const block = reversed ? "#f6f8fb" : "var(--navy, #132a45)";
  const accent =
    letter === "q"
      ? reversed ? "#E07A4E" : "var(--rust, #B0552E)"
      : reversed ? "#7FB3DA" : "var(--sapphire, #306FA8)";
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <g transform={letter === "s" ? "rotate(90 32 32)" : undefined}>
        <path d={letter === "q" ? Q_BLOCKS : S_BLOCKS} fill={block} />
        <path d={letter === "q" ? Q_SUN : S_ARCS} fill={accent} />
      </g>
    </svg>
  );
}

// Full lockup (QS + "Qubit Studio") or short (QS marks only).
export function QubitLockup({ size = 30, short = false, reversed = false }: { size?: number; short?: boolean; reversed?: boolean }) {
  return (
    <>
      <span style={{ display: "inline-flex", gap: Math.round(size * 0.14) }}>
        <QubitMark letter="q" size={size} reversed={reversed} />
        <QubitMark letter="s" size={size} reversed={reversed} />
      </span>
      {!short && <span>Qubit Studio</span>}
    </>
  );
}
