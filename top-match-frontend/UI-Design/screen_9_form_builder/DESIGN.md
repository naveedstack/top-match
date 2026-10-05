---
name: Calm Precision Middleware
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#006398'
  on-secondary: '#ffffff'
  secondary-container: '#5bb8fe'
  on-secondary-container: '#00476e'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#00201d'
  on-tertiary-container: '#0c9488'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#cce5ff'
  secondary-fixed-dim: '#93ccff'
  on-secondary-fixed: '#001d31'
  on-secondary-fixed-variant: '#004b73'
  tertiary-fixed: '#89f5e7'
  tertiary-fixed-dim: '#6bd8cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#005049'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.025em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.005em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.025em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  margin: 2rem
  margin-sm: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system establishes a high-trust, low-cognitive-load environment engineered for enterprise HR leaders and high-volume talent recruiters. Because algorithmic screening directly impacts career mobility and compliance, the visual atmosphere intentionally rejects hype-driven AI tropes (glowing gradients, noisy particle nets, skeuomorphic robotics) in favor of calm, clinical precision.

The style unites **Modern Corporate** structure with **Swiss Editorial Minimalism**:
- **Clarity over ornamentation**: Whitespace serves as functional separation; every pixel reinforces operational certainty.
- **Controlled density**: High-throughput tabular overviews contrast gracefully with spacious, legible candidate dossier panels.
- **Defensive clarity**: Subtle 1px structural framing guarantees auditability and clear demarcation of machine outputs versus human evaluation.

## Colors

The palette relies on a cool slate foundation accented with precise oceanic cues to communicate reliability, analytical depth, and ethical rigor.

- **Foundational Canvas**: Backdrops transition from `#F8FAFC` (slate-50 canvas) into `#FFFFFF` (elevated card sheets) framed by crisp `#E2E8F0` borders. High-contrast typography sits predominantly in `#0F172A` (slate-900) and `#334155` (slate-700), yielding robust WCAG AAA compliance.
- **Primary & Interactive Accents**: 
  - Slate Navy (`#0F172A`) commands foundational hierarchy, primary navigation anchors, and definitive user commitments.
  - Sky Blue (`#0284C7` resting, `#0369A1` active) directs focus to high-priority interactive workflows, links, and active filtering criteria.
  - Deep Teal (`#0D9488` resting, `#0F766E` active) highlights algorithmic match thresholds, high-confidence candidates, and positive delta values.
- **Audit-Grade Status System**: Status tokens feature low-saturation pastel backgrounds combined with high-contrast text to prevent cognitive fatigue in dense table views:
  - **Scored / Qualified**: `#ECFDF5` surface, `#059669` text (Emerald).
  - **Processing / Queued**: `#F0F9FF` surface, `#0284C7` text (Sky) or `#FFFBEB` surface, `#D97706` text (Amber).
  - **Received / Idle**: `#F1F5F9` surface, `#475569` text (Slate).
  - **Refused / Archived**: `#F4F4F5` surface, `#71717A` text (Zinc).
  - **Failed / Flagged**: `#FFF1F2` surface, `#E11D48` text (Rose).

## Typography

The type system is powered entirely by Inter with contextual OpenType features (`cv02`, `cv03`, `cv04`, `tnum`). It prioritizes scan speed, high-volume data legibility, and zero visual ambiguity between numerical metrics.

- **Tabular Figures (`tnum`)**: Mandatory across candidate scores, percentage bars, salary ranges, and table pagination.
- **Negative Tracking**: Subtle negative letter spacing applied across all headlines preserves compact visual rhythm at larger scale.
- **Label Calibration**: Sub-12px elements (`label-sm`) require uppercase rendering or semi-bold treatment to remain legible within tight micro-badges and status tags.

## Layout & Spacing

A desktop-first 12-column grid anchors recruiter workstations, reflowing to a focused single-column flow for candidate application portals.

- **Desktop (≥ 1280px)**: A 12-column fluid grid, utilizing a fixed 260px collapsible sidebar for global navigation. Max body canvas constraints lock at 1600px to avoid exaggerated tracking on ultra-wide panels. Margins are fixed at `2rem` with `1.5rem` gutters.
- **Tablet (768px - 1279px)**: Columns collapse to 8; navigation tucks into an off-canvas drawer; canvas margins step down to `1.5rem` with `1rem` gutters. Dual-pane inspection views switch to stacked accordion cards.
- **Mobile (< 768px)**: 4-column stack geared toward responsive candidate submittals and quick-status applicant tracking. Margins scale to `1rem` with `1rem` gutters. Tables shift to card lists with sticky contextual action bars.
- **Rhythm**: UI components adhere strictly to a 4px/8px incremental spatial scale. Interior paddings for interactive cells rely on `space-sm` (`0.5rem`) vertically and `space-md` (`1rem`) horizontally.

## Elevation & Depth

Visual hierarchy leverages crisp boundary containment combined with subtle ambient light diffusion, avoiding heavy dropped shadows.

- **Base Layer (Flat Canvas)**: Main view canvas uses `#F8FAFC`. It holds no elevation.
- **Level 1 (Data Cards & Standard Cells)**: Pure `#FFFFFF` fill bounded by a continuous 1px `#E2E8F0` border. Shadow: `0 1px 2px 0 rgba(15, 23, 42, 0.04)`.
- **Level 2 (Hover States & Candidate Inspection Drawers)**: Pure `#FFFFFF` surface with `#CBD5E1` border. Shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.04)`.
- **Level 3 (Modals, Overlays & Popovers)**: Bounded by 1px `#CBD5E1`. Shadow: `0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`. Dimmed backdrops use `rgba(15, 23, 42, 0.4)` with an optical blur of `4px`.

## Shapes

The geometric silhouette reflects understated enterprise efficiency. The system relies on soft, engineered corners (`0.25rem` / 4px base):

- **Micro Controls**: Checkboxes, radio inputs, and tag badges utilize `0.25rem` (4px).
- **Standard Controls**: Buttons, text inputs, dropdown toggles, and notification toasts use `0.375rem` (6px) or `0.5rem` (8px).
- **Containers**: Structural cards, table wrappers, and flyout side-panels specify `0.5rem` (8px), capping at `0.75rem` (12px) for large modals.
- **Pills**: Exclusively reserved for numerical match affinity indicators and dynamic pipeline stage badges.

## Components

### Buttons
- **Primary**: Background `#0F172A`, text `#FFFFFF`, border transparent. Hover state shifts to `#1E293B`. Focus state creates a 2px offset ring in `#0284C7`.
- **Secondary (Action)**: Background `#0284C7`, text `#FFFFFF`. Hover `#0369A1`.
- **Outline / Neutral**: Background `#FFFFFF`, text `#334155`, border 1px `#E2E8F0`. Hover switches background to `#F8FAFC` and border to `#CBD5E1`.
- **Destructive**: Background `#FFFFFF`, text `#E11D48`, border 1px `#FECDD3`. Hover `#FFF1F2`.

### Status Badges & Chips
- Heights are fixed at 22px (`label-sm`) or 26px (`label-md`). 
- Structure comprises a solid circular 6px status dot alongside tabular text inside a tint background (e.g., Emerald `#ECFDF5` background with `#059669` dot and label).

### Data Tables
- Column headers: Height 40px, background `#F8FAFC`, uppercase `label-sm` tracking with subtle text color `#64748B`.
- Row height: Fixed at 52px for comfortable scan density. Alternating hover state: `#F8FAFC`.
- Match confidence cells: Embed mini radial charts or clean text badges accompanied by numerical percentage indicators using monospace/tabular fonts.

### Form Inputs
- Background `#FFFFFF`, border 1px `#CBD5E1`, text `#0F172A`, border-radius `0.375rem`.
- Active focus state: 1px border `#0284C7` with a concurrent outer ring of `0 0 0 3px rgba(2, 132, 199, 0.15)`.
- Error state: 1px border `#E11D48` with a ring of `0 0 0 3px rgba(225, 29, 72, 0.15)`.

### Checkboxes & Radios
- Size: 16px × 16px. Border: 1.5px solid `#CBD5E1`. Checkbox fill triggers `#0F172A` with white iconography.

### Cards & Candidate Panels
- Primary card wrapper utilizes `#FFFFFF` fill with 1px `#E2E8F0` border and `0.5rem` border-radius.
- Inspection drawers slide out from the right edge with a Level 3 elevation, featuring a sticky candidate header, resume preview window, and an AI scoring summary breakdown.