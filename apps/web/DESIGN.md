# Helix — Visual Design Language

> **Source of truth for the Helix web app aesthetic.**
> Helix OS (Next.js shell) consumes this document. The `CreativeDirectorAgent` may also
> select the `minimax-monochrome` design school from `design-systems/schools/` to apply
> the same tokens to brand-internal screens.

Inspired by MiniMax's brand language: a stark monochrome canvas broken by a small number
of vibrant gradient product tiles. Single typeface. Pill-shaped buttons. Two card families
with distinct corner-radius signatures.

---

## 1. Dual Identity

Helix has two visual registers used in deliberate alternation:

1. **Quiet system surface** — white canvas, black ink, hairline borders, 16px corner radii.
   Used for: dashboards, navigation, prose, tables, settings, lists.
2. **Vibrant product surface** — saturated brand-color gradients, 32px corner radii,
   black 80px display type. Used for: hero bands, headline product cards, AI tile matrix,
   marketing-style call-outs inside the app shell.

Never mix the two within a single component. The contrast between them is the design.

---

## 2. Typography

**Family:** DM Sans (primary, variable). Inter as fallback. Single typeface across the
entire system — no secondary display face, no serif.

**Numeric:** `font-variant-numeric: tabular-nums` on metrics, prices, table values.

| Token              | Size  | Line height | Weight | Tracking | Usage                              |
|--------------------|-------|-------------|--------|----------|------------------------------------|
| `display-hero`     | 80px  | 1.10        | 700    | -2px     | Hero band headline                 |
| `display-xl`       | 64px  | 1.10        | 700    | -1.5px   | Section heroes                     |
| `display-lg`       | 48px  | 1.12        | 700    | -1.2px   | Page titles                        |
| `heading-xl`       | 36px  | 1.18        | 700    | -0.6px   | Major section heading              |
| `heading-lg`       | 28px  | 1.22        | 600    | -0.4px   | Subsection heading                 |
| `heading-md`       | 22px  | 1.28        | 600    | -0.2px   | Card title                         |
| `heading-sm`       | 18px  | 1.32        | 600    | 0        | Inline heading                     |
| `body-lg`          | 17px  | 1.55        | 400    | 0        | Long-form prose lead               |
| `body-md`          | 15px  | 1.55        | 400    | 0        | Default body                       |
| `body-sm`          | 13px  | 1.50        | 400    | 0        | Secondary text                     |
| `label`            | 13px  | 1.20        | 500    | 0.2px    | Button text, labels                |
| `eyebrow`          | 12px  | 1.20        | 600    | 1.2px    | Uppercase eyebrows (`text-transform: uppercase`) |
| `micro`            | 12px  | 1.40        | 500    | 0        | Captions, footnotes                |

---

## 3. Color Tokens

### 3.1 Canvas + ink (monochrome)

| Token              | Hex       | Usage                                   |
|--------------------|-----------|-----------------------------------------|
| `canvas`           | `#FFFFFF` | Page background                          |
| `surface`          | `#FAFAFA` | Card on canvas, code blocks, table head |
| `surface-elev`     | `#F4F4F5` | Hover surface, pressed state             |
| `hairline`         | `#E6E6E6` | 1px borders, dividers                    |
| `ink`              | `#0A0A0A` | Primary text, primary button bg          |
| `charcoal`         | `#1F1F1F` | Headings on canvas                       |
| `slate`            | `#3A3A3A` | Body text                                |
| `steel`            | `#6B6B6B` | Secondary text                           |
| `stone`            | `#8E8E8E` | Tertiary text, captions                  |
| `muted`            | `#B4B4B4` | Disabled text                            |

### 3.2 Brand gradients (vibrant product surfaces)

Used **sparingly** — typically 4–6 cards per page maximum. Each gradient is a
two-stop linear gradient at 135°.

| Token              | Stop 1    | Stop 2    | Usage                                   |
|--------------------|-----------|-----------|-----------------------------------------|
| `brand-coral`      | `#FF6A4D` | `#FF3D7F` | Primary product tile, hero CTAs         |
| `brand-magenta`    | `#FF3D7F` | `#A24BFF` | Secondary product tile                  |
| `brand-blue`       | `#4D7BFF` | `#7AB6FF` | Tertiary product tile, info bands       |
| `brand-purple`     | `#7B4DFF` | `#C04DFF` | Workflow / AI tile                      |
| `brand-amber`      | `#FFB347` | `#FF7A4D` | Promo banner                            |

Text on brand gradient surfaces is always `ink` (`#0A0A0A`), not white — this is the
MiniMax signature inversion.

### 3.3 Semantic

| Token              | Hex       | Usage                                   |
|--------------------|-----------|-----------------------------------------|
| `success-bg`       | `#E8F5EE` | Success badge background                 |
| `success-text`     | `#0F7B3A` | Success badge text                       |
| `warning-bg`       | `#FFF6E0` | Warning background                       |
| `warning-text`     | `#7A4E00` | Warning text                             |
| `error-bg`         | `#FBE7E7` | Error background                         |
| `error-text`       | `#9B1C1C` | Error text                               |
| `info-bg`          | `#E8EEFF` | Info background                          |
| `info-text`        | `#1F3A99` | Info text                                |

---

## 4. Spacing Scale

4px-based, named tokens (used in Tailwind config + CSS variables).

| Token      | Value  | Token      | Value   |
|------------|--------|------------|---------|
| `xxs`      | 4px    | `xl`       | 32px    |
| `xs`       | 8px    | `2xl`      | 48px    |
| `sm`       | 12px   | `3xl`      | 64px    |
| `md`       | 16px   | `hero`     | 96px    |
| `lg`       | 24px   |            |         |

---

## 5. Border-Radius Scale

| Token      | Value   | Usage                                   |
|------------|---------|-----------------------------------------|
| `xs`       | 4px     | Badge, code chip                         |
| `sm`       | 8px     | Input, segmented tab                     |
| `md`       | 12px    | Inline tile, small card                  |
| `lg`       | 16px    | **Quiet card family** (default)          |
| `xl`       | 20px    | Larger quiet card                        |
| `2xl`      | 24px    | Modal, sheet                             |
| `3xl`      | 28px    | Promo banner                             |
| `hero`     | 32px    | **Vibrant product card family**, hero band |
| `full`     | 9999px  | Pill button, avatar, search pill         |

The 16/32 split is the visual signature. A page reading should be able to identify
quiet vs vibrant surfaces by corner radius alone.

---

## 6. Elevation

Five tiers — used sparingly. Most surfaces are flat with hairline borders only.

| Token          | Shadow                                                   |
|----------------|----------------------------------------------------------|
| `flat`         | none (1px `hairline` border only)                        |
| `subtle`       | `0 1px 2px rgba(10,10,10,0.04)`                          |
| `raised`       | `0 4px 12px rgba(10,10,10,0.06)`                         |
| `floating`     | `0 12px 32px rgba(10,10,10,0.10)`                        |
| `modal`        | `0 24px 64px rgba(10,10,10,0.18)`                        |

---

## 7. Layout

- **Max content width:** 1280px.
- **Page gutters:** 32px (desktop), 24px (tablet), 16px (mobile).
- **Vertical rhythm:** sections separated by `hero` (96px) on marketing pages,
  `2xl` (48px) on app pages.
- **Docs page:** 3-column — left sidebar 240px / prose 720px max / right TOC 200px.
- **App page:** left sidebar 256px / fluid content / optional right rail 320px.

---

## 8. Components

### 8.1 Buttons

All buttons are `rounded-full` (pill). Height 40px default, 32px small, 48px large.

| Variant            | Background          | Text     | Border                  |
|--------------------|---------------------|----------|-------------------------|
| `primary`          | `ink` (#0A0A0A)     | `canvas` | none                    |
| `secondary`        | `canvas`            | `ink`    | 1px `ink`               |
| `tertiary`         | `surface`           | `ink`    | none                    |
| `link`             | transparent         | `ink`    | none (underline on hover) |
| `icon-circular`    | `surface`           | `ink`    | none — `rounded-full`, 40×40 |

Hover: 4% darken on bg. Active: 8% darken. Disabled: `muted` text, `surface` bg.

### 8.2 Cards

**Vibrant family (`rounded-[32px]`):**
- `product-card-coral` — gradient `brand-coral`, `ink` text, `display-lg` headline
- `product-card-magenta` — gradient `brand-magenta`
- `product-card-blue` — gradient `brand-blue`
- `product-card-purple` — gradient `brand-purple`
- `product-card-photo` — full-bleed photo, gradient overlay, `ink` text on white plate

**Quiet family (`rounded-[16px]`):**
- `card-base` — `canvas` bg, 1px `hairline`, padding `lg`
- `card-feature` — `surface` bg, 1px `hairline`, padding `xl`
- `card-recommendation` — `canvas` bg, hairline, hover lifts to `subtle`

### 8.3 Inputs

- `text-input` — 40px tall, `rounded-[8px]`, 1px `hairline`, `body-md`, padding `sm md`.
  Focus: 2px `ink` ring, hairline becomes `ink`.
- `search-pill` — 44px tall, `rounded-full`, `surface` bg, leading search icon, `body-md`.

### 8.4 Tabs

- `segmented-tab` — 32px tall, `rounded-[8px]`, `surface` track, `canvas` active pill,
  `subtle` elevation on active.
- `pill-tab` — `rounded-full`, `surface` inactive, `ink` active.

### 8.5 Badges

- `badge-success`, `badge-new`, `badge-beta`, `badge-code` — `rounded-[4px]`, 11px
  uppercase `eyebrow`, padding `2px 8px`.

### 8.6 Promo / banner

- `promo-cta-card` — `rounded-[28px]`, brand gradient bg, 64px headline,
  `primary` button anchored bottom-right.
- `promo-banner` — full-width, `brand-amber` gradient, 24px headline, single CTA.

### 8.7 Navigation

- `top-nav` — 64px tall, `canvas` bg, 1px bottom `hairline`. Logo left, primary nav
  center (pill-tab), actions right (icon-circular + primary button).
- `sidebar-nav-item` — 36px tall, `rounded-[10px]`, padding `xs sm`, icon + label,
  active state: `surface-elev` bg + `ink` text.
- `doc-toc-item` — left 2px `hairline` rail, active item: 2px `ink` rail + `ink` text.

### 8.8 Tables

- `data-table` — `surface` header row, hairline rules between rows only (no vertical),
  `body-sm` cells, hover row `surface` bg.

### 8.9 Hero band

- `hero-band-marketing` — `canvas` bg, max-width 1280, `display-hero` headline,
  `body-lg` subhead, primary + secondary button row, 96px top/bottom padding.

### 8.10 Product matrix

- `product-matrix-grid` — 12-col grid, mixes `product-card-*` (vibrant) with `card-feature`
  (quiet). Ratio target: 1 vibrant per 2–3 quiet.
- `ai-product-matrix` — 4 tiles in a row: coral / magenta / blue / purple — used once
  per landing page as the signature visual.

### 8.11 Prose

- `docs-prose-block` — max-width 720, `body-md`, headings auto-link, code blocks
  `surface` bg + `rounded-[8px]`, inline `code` with `rounded-[4px]` + `surface`.

### 8.12 Comparison + stats

- `models-comparison-table` — sticky leading column, brand-gradient header cells
  for highlighted columns.
- `testimonial-stat-row` — 3-up or 4-up `display-xl` numbers on `canvas`,
  `eyebrow` label beneath.

### 8.13 Footer

- `footer-region` — `canvas` bg, 1px top `hairline`, 4-col link grid, brand mark
  + tagline left, copyright row at bottom.
- `footer-link` — `body-sm`, `slate` color, hover `ink`.

---

## 9. Responsive Breakpoints

| Token     | Min width | Notes                                  |
|-----------|-----------|----------------------------------------|
| `mobile`  | 0         | Single column, 16px gutters            |
| `sm`      | 480px     | Larger phones                          |
| `md`      | 768px     | Tablet — 2-col product grid            |
| `lg`      | 1024px    | Desktop — full sidebar appears         |
| `xl`      | 1280px    | Max content width reached              |

Touch targets minimum 44×44 on mobile. Hero typography scales: 80 → 56 → 40 across
xl → md → mobile.

---

## 10. Motion

Framer Motion. Use sparingly — primarily for page transitions and reveal of newly
generated assets.

- Page transition: 200ms fade + 4px y-translate.
- Card hover: 150ms shadow + 2px y-translate.
- Asset arrival (workflow stream): 320ms fade + 8px y-translate + scale 0.98 → 1.
- Easing: `cubic-bezier(0.2, 0.8, 0.2, 1)` (standard) for entries, `ease-out` for exits.

---

## 11. Do / Don't

**Do:**
- Use DM Sans everywhere. One face.
- Pill buttons (`rounded-full`) for every primary action.
- Reserve gradient cards for product/AI features and hero moments.
- Lead with black text on vibrant backgrounds (not white).
- Hairline borders by default; shadows only on hover or modals.

**Don't:**
- Mix corner radii within the same surface group.
- Use brand gradients for chrome, buttons, or backgrounds — only for content cards.
- Introduce a second typeface.
- Add color to the chrome (sidebar, top nav, tables) — they remain monochrome.
- Use shadows as decoration on flat cards.
