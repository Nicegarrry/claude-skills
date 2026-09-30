# Brand marks

Two 64×64 woodblock grids, each made of 2×2 cut blocks. The block edges are deliberately a hair off square (hand-cut), so never redraw them as perfect squares.

| Mark | Blocks (navy `#132a45`) | Accent |
|---|---|---|
| **Q** | TL, TR, BL | rust quarter-sun rising in the BR cell: `M35 60 L35 35 A25 25 0 0 1 60 60Z` |
| **S** | TL, BR (drawn TR/BL, then rotated 90°) | two sapphire quarter-arcs in the other corners |

- **Lockup:** Q + S side by side with a gap of `round(size × 0.14)`, followed by "Qubit Studio" in Mincho 500. Nav size is 30px marks with 34px text. Footer size is 24px.
- **Short form:** QS marks only, used for favicons, the docked seal and the "Made by" line (16px).
- **VG** wears the Q alone with "VG" in Mincho. It is the same family, so there is no separate VG logo.
- **Reversed** (on navy): blocks `#f6f8fb`, Q sun `#e07a4e`, S arcs `#7fb3da`.
- **Minimum size:** 16px. Keep clear space of at least 0.5× the mark size.
- **Files:** `assets/brand/qubit-mark.svg` (Q), `qubit-mark-s.svg`, `qubit-studio-qs.svg` (pair), `qubit-mark-reversed.svg`, and the React component `assets/QubitMark.tsx` (`QubitMark`, `QubitLockup`).
- **Don't:** recolour the sun sapphire, add outlines, round the blocks, put the mark in a circle, or set the name in the body sans.
