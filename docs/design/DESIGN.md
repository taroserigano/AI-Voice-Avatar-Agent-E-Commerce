# Serigan Mart design system

This is the guide for anyone restyling a Serigan Mart page. Tokens live in `apps/web/app/globals.css` (Tailwind v4 `@theme`). Primitives live in `apps/web/components/ui/*`, icons in `apps/web/components/icons.tsx`, and the logo in `apps/web/components/logo.tsx`. Copy the class strings below as written.

## 1. Direction and principles

**"Twilight larkspur."** Three colors carry the brand: deep violet-tinted ink, a luminous blue-violet taken from the flower, and one warm marigold accent. Everything else is quiet: near-white canvas, white raised cards, hairline borders, and soft layered shadows. Headings use a characterful grotesk (Bricolage Grotesque) and the UI uses Inter. The aim is premium and calm, and still friendly enough for a mass-market store.

1. **Content first, chrome quiet.** Product art and prices carry the color. UI surfaces stay white or neutral. Use violet for actions and brand moments, not for decoration everywhere.
2. **One primary action per view.** Only one `primary` (glowing violet) button per screen region. Everything else is `secondary`, `outline` or `ghost`.
3. **Generous rhythm.** Leave plenty of whitespace: sections sit 64–96px apart and cards use 20px radii. When unsure, add space rather than lines.
4. **Soft depth, not borders everywhere.** Use a hairline `border-line` plus `shadow-xs` at rest, and lift to `shadow-lg` on hover. Avoid heavy outlines.
5. **Accessible by construction.** Use only the documented contrast pairs. Keep text at `muted` or darker. Make targets ≥44px. Keep visible focus rings. Never let color be the only signal.
6. **Motion is feedback.** Keep it short (150–300ms) and eased with `ease-smooth` / `ease-snappy`. Motion always turns off under reduced motion, which the global rule already handles.

## 2. Color

All values were checked numerically (WCAG 2.x relative luminance). Pairs marked **text** are ≥4.5:1, **large** are ≥3:1 for text ≥24px (or ≥18.66px bold), and **UI** are ≥3:1 for icons, borders and focus rings.

### Semantic tokens (reach for these first)

| Token | Value | Use |
|---|---|---|
| `ink` | neutral-900 `#181823` | Primary text, headings |
| `ink-soft` | neutral-700 `#40414e` | Long-form body copy, secondary headings |
| `muted` | neutral-600 `#595a66` | Secondary text, captions, helper text |
| `subtle` | neutral-500 `#6e6f7b` | Placeholders, meta. **Only on white/canvas**, never on `sunken` |
| `canvas` (= legacy `surface`) | neutral-50 `#f9f9fb` | Page background |
| `raised` | `#ffffff` | Cards, popovers, inputs, header |
| `sunken` | neutral-100 `#f2f3f6` | Wells, image mats, table header/stripes |
| `overlay` | `rgb(13 13 22 / .5)` | Modal/drawer scrim |
| `inverse` | brand-950 `#1b123e` | Dark brand bands (hero, footer) |
| `line` | neutral-200 `#e5e6ec` | Card borders, dividers (decorative) |
| `line-strong` | neutral-300 `#d3d3db` | Hover borders, outline button ring |
| `control` | neutral-400 `#92939e` | Input/checkbox borders (3.05:1 on white). **Never text** |
| `focus` | brand-600 | Focus ring color. The `focus-inverse` utility swaps it to white |
| `star` / `star-empty` | accent-600 / neutral-300 | Rating stars |

### Scales

- **brand** 50–950 (larkspur violet, OKLCH hue ≈ 287): `brand-600 #6740de` is the action color, `brand-700 #5530be` is hover and brand text, and `brand-950` is the inverse surface.
- **accent** 50–900 (marigold): `accent-400 #ffb439` is a surface color for use with ink text. `accent-700` is the accent text color on white.
- **neutral** 50–950: cool, faintly violet greys. This overrides Tailwind's `neutral`. Prefer it over `stone`/`gray`/`slate`.
- **success / warning / danger / info**: 50, 100, 200, 500, 600, 700, 800, 900. Use 50 for backgrounds, 200 for borders, 600 for icons and solid fills, and 700–900 for text.

### Verified pairs

| Foreground on background | Ratio | OK for |
|---|---|---|
| ink on white / canvas / sunken | 17.6 / 16.7 / 15.9 | text |
| ink on brand-50 | 16.2 | text |
| ink-soft on white / sunken | 10.1 / 9.1 | text |
| muted on white / canvas / sunken / brand-50 / warning-50 | 6.8 / 6.5 / 6.2 / 6.3 / 6.4 | text |
| subtle on white / canvas | 4.97 / 4.73 | text (**4.48 on sunken: not allowed**) |
| brand-600 on white / canvas / sunken / brand-50 | 6.2 / 5.9 / 5.6 / 5.8 | text (links) |
| brand-700 on white / brand-50 / brand-100 | 8.2 / 7.6 / 6.9 | text |
| brand-800 on brand-50 / brand-100 | 9.7 / 8.9 | text |
| brand-900 on brand-50 / brand-100 | 12.7 / 11.6 | text |
| white on brand-600 / 700 / 800 / 900 / 950 | 6.2 / 8.2 / 10.6 / 13.8 / 17.5 | text |
| brand-100 on brand-800 / brand-900 | 8.9 / 11.6 | text |
| brand-200 on inverse (brand-950) | 12.4 | text |
| brand-300 on inverse | 9.4 | text |
| accent-300 on inverse / accent-400 on brand-900 | 11.4 / 7.8 | text (eyebrows on dark) |
| ink on accent-300 / accent-400 / accent-500 | 11.5 / 9.9 / 8.0 | text |
| accent-700 on white | 5.4 | text |
| accent-800 on accent-50 / accent-100 | 7.5 / 7.0 | text |
| success-700 on white / success-50 | 6.4 / 6.0 | text |
| success-800 / 900 on success-50 | 8.7 / 12.1 | text |
| warning-700 on white | 5.7 | text |
| warning-800 / 900 on warning-50 | 7.8 / 10.8 | text |
| danger-700 on white / danger-50 | 6.9 / 6.3 | text |
| danger-800 / 900 on danger-50 | 8.8 / 11.4 | text |
| white on danger-600 / danger-700 | 5.3 / 6.9 | text |
| info-700 on white; info-800 / 900 on info-50 | 6.7; 8.9 / 11.7 | text |
| white on success-700 | 6.4 | text |
| brand-500 on white | 4.25 | large / UI only |
| control (neutral-400) on white | 3.05 | UI (input borders) |
| accent-600 (star) on white | 3.19 | UI |
| warning-600 on white / warning-50 | 3.5 / 3.25 | UI (icons) |
| success-600 on white / success-50 | 4.4 / 4.1 | UI (icons) |
| danger-600 on danger-50 | 4.9 | UI / text |
| brand-600 focus ring on white / canvas | 6.2 / 5.9 | UI |

**Don'ts:** no neutral-400 or lighter text. No brand-400/300 text on white. No accent-400/500 text on white (use accent-700). No white text on accent. `subtle` is not allowed on `sunken`. Use `focus-inverse` on every dark surface.

## 3. Typography

- `font-sans` is **Inter** (UI and body). `font-display` is **Bricolage Grotesque** (headings, prices in heroes, the logo). Both are self-hosted via `next/font/google` in `app/layout.tsx`.
- `h1`–`h3` default to `font-display` and every heading gets `text-wrap: balance`. Paragraphs get `text-wrap: pretty`.
- Use weights **600 (semibold)** for display headings and 500–600 for UI. Avoid `font-extrabold`/`font-black` on Bricolage because it gets chunky. Use `font-bold` sparingly for prices.
- Tracking is built into the size tokens (−0.01em at xl, down to −0.04em at display), so you rarely need `tracking-*`.

| Role | Recipe |
|---|---|
| Hero display | `font-display text-display font-semibold text-ink` (fluid 40→72px) |
| Page title (h1) | `font-display text-3xl sm:text-4xl font-semibold tracking-tight text-ink` |
| Section title (h2) | `font-display text-2xl sm:text-3xl font-semibold text-ink` (or `<SectionHeading>`) |
| Card/panel title (h3) | `font-display text-lg font-semibold text-ink` |
| Eyebrow | `text-xs font-semibold uppercase tracking-eyebrow text-brand-700` (on dark: `text-accent-300`) |
| Lead paragraph | `text-lg text-muted max-w-2xl` |
| Body | `text-base text-ink-soft leading-relaxed` |
| UI label | `text-sm font-semibold text-ink` |
| Caption / meta | `text-sm text-muted` (or `text-xs text-muted`) |
| Price (card) | `text-lg font-semibold tabular-nums text-ink` |
| Price (PDP) | `font-display text-4xl font-semibold tabular-nums text-ink` |
| Strike price | `text-sm text-muted line-through tabular-nums` |
| Inline link | `font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700` |

## 4. Layout and spacing

- **Container:** `<Container>` or `containerClasses()`, which gives `mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8`. The `narrow` size (max-w-3xl) is for forms, legal and reading. `wide` (90rem) is for full-bleed bands.
- **Vertical rhythm:** page top padding is `pt-6 sm:pt-10`. Sections sit `space-y-16 sm:space-y-24` apart. The gap from heading to content is `mt-6 sm:mt-8`.
- **Grids:** product grid is `grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 lg:gap-x-6`. Department tiles use `grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 sm:gap-4`. Content with a sidebar uses `lg:grid lg:grid-cols-[16rem_1fr] lg:gap-10`.
- **Spacing steps:** stick to 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24 (Tailwind units).

## 5. Radius and elevation

| Radius | px | Use |
|---|---|---|
| `rounded-full` | – | Buttons, pills, badges, search bar, avatars |
| `rounded-lg` | 12 | Inputs, menu items, small tiles |
| `rounded-xl` | 16 | Image mats inside cards, notices, popovers |
| `rounded-2xl` | 20 | Cards, panels |
| `rounded-3xl` | 28 | Hero and feature panels |
| `rounded-4xl` | 36 | Oversized marketing bands |

| Shadow | Use |
|---|---|
| `shadow-xs` | Resting cards, inputs, outline buttons |
| `shadow-sm` | Sticky header after scroll, chips |
| `shadow-md` | Hovered small elements, dropdown triggers |
| `shadow-lg` | Card hover lift, popovers, menus |
| `shadow-xl` / `shadow-2xl` | Modals, drawers, floating assistant panel |
| `shadow-glow` / `shadow-glow-lg` | **Primary CTA only** (and its hover) |
| `inset-shadow-highlight` | Top sheen on filled buttons (composes with `shadow-*`) |
| `inset-shadow-well` | Inputs |

## 6. Motion

- **Easing:** `ease-smooth` for entrances and lifts, `ease-snappy` for hover/press, `ease-spring` for playful bumps (cart count, logo).
- **Durations:** 150ms for color/hover, 200–300ms for lifts and menus, 500ms for page-section entrances. Variables are `--duration-fast|base|slow|slower`.
- **Animations:** `animate-fade-in`, `animate-fade-up` (section/hero entrance), `animate-scale-in` (popovers, dialogs), `animate-slide-down` (menus, `<details>` panels), `animate-pop` (cart badge change) and `animate-shimmer` (skeletons).
- **Stagger:** `animate-fade-up animation-delay-80`, then `-160`, `-240` and so on. Stagger at most the first 8 items.
- **Hover lift:** `transition-[box-shadow,transform] duration-300 ease-smooth hover:-translate-y-0.5 hover:shadow-lg motion-reduce:hover:translate-y-0`.
- The global `prefers-reduced-motion: reduce` rule zeroes animation and transition time and disables smooth scroll. Don't fight it.

## 7. Components

### Button: `components/ui/button.tsx`

```tsx
<Button>Add to cart</Button>                                // primary, md (44px)
<Button variant="secondary" size="sm">Apply</Button>        // tonal violet, 36px visible / 44px hit area
<Button variant="outline"><SlidersIcon />Filters</Button>
<Button variant="ghost">Cancel</Button>
<Button variant="danger" loading={pending}>Delete review</Button>
<Button variant="accent">Search</Button>                    // marigold, ink text
<Button variant="inverse">Start shopping</Button>          // on dark surfaces
<Button size="icon" variant="ghost" aria-label="Close"><CloseIcon /></Button>
<ButtonLink href="/cart" size="lg">Go to cart<ArrowRightIcon /></ButtonLink>
<Link className={buttonClasses("outline", "sm")} href="…">Next</Link>
```

- Variants: `primary | secondary | outline | ghost | danger | accent | inverse`. Sizes: `sm | md | lg | icon`.
- `loading` shows a spinner, disables the button and sets `aria-busy`. Keep the text label.
- Icon-only buttons **must** have `aria-label`.

### Field, Input, Select, Textarea: `components/ui/field.tsx`

```tsx
<Field id="title" label="Review title" optional hint="Up to 120 characters." error={errors.title}>
  <Input id="title" name="title" maxLength={120}
    aria-describedby="title-hint title-error" aria-invalid={errors.title ? true : undefined} />
</Field>
<Select id="sort" name="sort">…</Select>
<Textarea id="body" name="body" rows={5} />
```

The class strings `inputClasses`, `selectClasses` and `textareaClasses` are exported for custom controls. Controls are 48px tall. Focus shows a 2px violet edge plus a halo. `aria-invalid="true"` turns the border red, and the error text carries an icon so color isn't the only signal.

### Notice: `components/ui/notice.tsx`

```tsx
<Notice tone="success" title="Added to cart">2 × Trail socks</Notice>
<Notice tone="warning" action={<ButtonLink size="sm" variant="outline" href="/cart">Review</ButtonLink>}>Prices changed.</Notice>
<Notice tone="error">{error}</Notice>          // role="alert"
<Notice tone="info" role="note">Sample reviews are labeled.</Notice>
```

### Stars and RatingBadge: `components/ui/stars.tsx`

```tsx
<Stars rating={product.rating_average} size="lg" showValue />     // PDP summary
<Stars rating={review.rating} size="sm" />                          // each review (sr: "Rated 4.0 out of 5")
<RatingBadge average={p.rating_average} count={p.rating_count} />   // cards: ★ 4.3 (128) / "No reviews yet"
<RatingBadge average={…} count={…} variant="stars" size="md" />    // ★★★★☆ 4.3 (128)
```

These are Server-Component safe (CSS width overlay, no ids). Stars are graphics, so show the number next to them (`showValue` or RatingBadge) wherever the rating matters. Rating-distribution bars use `h-2 rounded-full bg-sunken` with an `bg-star` fill, a visible count, and `aria-hidden` on the bar.

### Badge: `components/ui/badge.tsx`

```tsx
<Badge tone="sale">Sale</Badge>  <Badge tone="success" dot>In stock</Badge>
<Badge tone="danger" dot>Out of stock</Badge>  <Badge tone="brand">New</Badge>
<Badge tone="neutral">Sample review</Badge>  <Badge tone="success"><CheckIcon />Verified purchase</Badge>
```

Tones: `neutral | brand | success | warning | danger | sale | accent`. Sizes: `sm | md`. `badgeClasses()` is exported.

### Card: `components/ui/card.tsx`

```tsx
<Card>…</Card>                                  // p-5 sm:p-6, rounded-2xl, border-line, shadow-xs
<Card as="section" padding="lg" aria-labelledby="summary">…</Card>
<Card as="li" padding="none" interactive>…</Card>
```

### Skeleton: `components/ui/skeleton.tsx`

```tsx
<div role="status" aria-live="polite">
  <span className="sr-only">Loading…</span>
  <Skeleton className="h-9 w-64 rounded-full" />
  <SkeletonText lines={3} className="mt-4 max-w-md" />
  <ul className="mt-8 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4">
    {Array.from({ length: 8 }, (_, i) => <li key={i}><ProductCardSkeleton /></li>)}
  </ul>
</div>
```

### SectionHeading: `components/ui/section-heading.tsx`

```tsx
<section aria-labelledby="featured">
  <SectionHeading id="featured" eyebrow="Just in" title="New and in stock"
    description="Fresh picks across every department."
    action={{ href: "/search?sort=newest", label: "See all", srLabel: "new products" }} />
  …
</section>
```

Props: `as` (`h1|h2|h3`, default h2), `size` (`sm|md|lg`).

### Container: `components/ui/container.tsx`

`<Container size="narrow" as="section">…</Container>`, or `containerClasses("default", "py-10")`.

### Icons: `components/icons.tsx`

```tsx
import { CartIcon, SearchIcon, DepartmentIcon } from "@/components/icons";
<SearchIcon />                         // 20px, aria-hidden
<CartIcon className="size-6" />
<StarFilledIcon title="Favorite" />     // labelled image (only when it has no text label)
<DepartmentIcon slug={c.slug} className="size-6 text-brand-700" />
```

Icons are on a 24px grid with 1.75px strokes and `currentColor`. Available icons are: Search, Bag, Cart, User, ChevronRight/Left/Down/Up, ArrowRight/Left, ExternalLink, Menu, Close (X), Check, Plus, Minus, Sliders (Filter), Home, Grid, Sitemap, Map, Star / StarFilled / StarHalf, Heart, Truck, Return, Refresh, ShieldCheck, Sparkles, Package, Gift, Tag, CreditCard, Clock, Mic, Chat, Trash, Pencil, SignOut, Mail, Lock, Eye, EyeOff, Info, AlertTriangle, AlertCircle and CheckCircle. Department glyphs are Headphones, Pot, Shirt, Mountain, Dumbbell, Blocks, Droplet, Notebook, Gift and Basket (the Basket is ready for groceries). Every icon name is suffixed with `Icon`.

### Logo: `components/logo.tsx`

`<Logo />` (ink wordmark, violet tile) or `<Logo inverted />` (on dark). `<LogoMark className="size-10" />` gives the mark alone (decorative).

## 8. Recipes

### Header / nav (white, sticky, glassy)

```tsx
<header className="sticky top-0 z-40 border-b border-line bg-raised/85 backdrop-blur-xl backdrop-saturate-150">
  <div className={containerClasses("default", "flex h-16 items-center gap-4 lg:h-18 lg:gap-8")}>
    <Logo />
    <form role="search" action="/search" className="relative flex-1 max-w-2xl">
      <label htmlFor="site-search" className="sr-only">Search products</label>
      <SearchIcon className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
      <input id="site-search" name="q" type="search" placeholder="Search everything at Serigan Mart"
        className="h-12 w-full rounded-full border border-transparent bg-sunken pl-11 pr-28 text-base text-ink placeholder:text-muted transition focus-visible:border-brand-600 focus-visible:bg-raised focus-visible:outline-transparent focus-visible:ring-4 focus-visible:ring-brand-500/20" />
      <button type="submit" className={buttonClasses("primary", "sm", "absolute right-1.5 top-1/2 -translate-y-1/2")}>Search</button>
    </form>
    {/* account + cart: ghost buttons; cart count = bg-brand-600 text-white text-xs font-semibold rounded-full min-w-5 h-5 px-1.5 */}
  </div>
  <nav aria-label="Departments" className="border-t border-line">
    <ul className={containerClasses("default", "flex gap-1 overflow-x-auto scrollbar-none py-1.5")}>
      <li><Link className="inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded-full px-3.5 text-sm font-medium text-ink-soft transition-colors hover:bg-sunken hover:text-ink aria-[current=page]:bg-brand-50 aria-[current=page]:text-brand-800" href="/c/electronics"><DepartmentIcon slug="electronics" className="size-4" />Electronics</Link></li>
    </ul>
  </nav>
</header>
```


### Product card

```tsx
<li className="group relative">
  <Link href={`/products/${p.id}`} className="flex h-full flex-col rounded-2xl p-2 -m-2 transition-colors hover:bg-raised hover:shadow-lg">
    <div className="relative overflow-hidden rounded-xl bg-sunken">
      <img src={p.image_path} alt="" width={640} height={640}
        className="aspect-square w-full object-cover transition-transform duration-500 ease-smooth group-hover:scale-[1.04] motion-reduce:group-hover:scale-100" />
      {!p.in_stock ? <Badge tone="neutral" className="absolute left-3 top-3">Out of stock</Badge> : null}
    </div>
    <div className="flex flex-1 flex-col gap-1 px-1.5 pb-2 pt-3">
      <p className="text-xs font-medium uppercase tracking-eyebrow text-muted">{p.brand}</p>
      <h3 className="line-clamp-2 font-sans text-[0.9375rem] font-medium leading-snug text-ink group-hover:text-brand-700">{p.title}</h3>
      <RatingBadge average={p.rating_average} count={p.rating_count} className="mt-0.5" />
      <p className="mt-auto pt-2 text-lg font-semibold tabular-nums text-ink">{price}</p>
    </div>
  </Link>
</li>
```

Stock status must remain as text (a badge or `text-success-700`/`text-danger-700` with a dot), not color alone.

### Hero (dark mesh)

```tsx
<section className="relative isolate overflow-hidden rounded-3xl bg-mesh-dark px-6 py-14 text-white focus-inverse sm:px-12 sm:py-20">
  <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Welcome back, Alice</p>
  <h1 className="mt-4 max-w-3xl font-display text-display font-semibold text-white animate-fade-up">Everyday essentials, beautifully easy.</h1>
  <p className="mt-5 max-w-xl text-lg text-brand-200 animate-fade-up animation-delay-80">…</p>
  <div className="mt-8 flex flex-wrap gap-3 animate-fade-up animation-delay-160">
    <ButtonLink href="/search" variant="inverse" size="lg">Start shopping</ButtonLink>
    <ButtonLink href="/orders" variant="ghost" size="lg" className="text-white hover:bg-white/10">Your orders</ButtonLink>
  </div>
</section>
```

For a light alternative, use `bg-mesh-light text-ink` with an eyebrow in `text-brand-700` and body in `text-muted`.

### Department tiles

```tsx
<Link href={`/c/${c.slug}`} className="group flex min-h-28 flex-col justify-between gap-4 rounded-2xl border border-line bg-raised p-4 shadow-xs transition-[box-shadow,transform,border-color] duration-300 ease-smooth hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-lg">
  <span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-700 transition-colors group-hover:bg-brand-600 group-hover:text-white"><DepartmentIcon slug={c.slug} className="size-6" /></span>
  <span className="font-semibold text-ink">{c.name}</span>
</Link>
```

### Footer (inverse)

```tsx
<footer className="mt-24 bg-inverse text-brand-200 focus-inverse">
  <div className={containerClasses("default", "grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4")}>
    <div><Logo inverted /><p className="mt-4 max-w-xs text-sm text-brand-300">Everyday essentials, easy returns.</p></div>
    <nav aria-label="Legal"><h2 className="font-sans text-sm font-semibold text-white">Legal</h2>
      <ul className="mt-4 space-y-1 text-sm"><li><Link className="inline-flex min-h-11 items-center hover:text-white underline-offset-4 hover:underline" href="/privacy">Privacy</Link></li></ul></nav>
  </div>
  <div className="border-t border-white/10"><p className={containerClasses("default", "py-6 text-xs text-brand-300")}>© Serigan Mart (demo store)</p></div>
</footer>
```

### Empty state

```tsx
<div className="flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center">
  <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md"><BagIcon className="size-8" /></span>
  <h2 className="mt-6 font-display text-2xl font-semibold text-ink">Your cart is empty</h2>
  <p className="mt-2 max-w-sm text-muted">Find something you love. We'll keep it here for you.</p>
  <ButtonLink href="/" className="mt-6">Start shopping</ButtonLink>
</div>
```

### Form page

Put the form in `<Container size="narrow">` or `max-w-md`, inside `<Card padding="lg">`. Stack fields with `space-y-5`. Put the submit button full-width at the end: `<Button type="submit" size="lg" className="w-full" loading={pending}>`. Form-level errors go in `<Notice tone="error">` above the fields.

### Data table (orders)

```tsx
<div className="overflow-x-auto rounded-2xl border border-line bg-raised shadow-xs">
  <table className="w-full text-left text-sm">
    <caption className="sr-only">Your orders</caption>
    <thead className="bg-sunken text-xs font-semibold uppercase tracking-eyebrow text-muted">
      <tr><th scope="col" className="px-5 py-3">Order</th>…<th scope="col" className="px-5 py-3 text-right">Total</th></tr>
    </thead>
    <tbody className="divide-y divide-line">
      <tr className="transition-colors hover:bg-neutral-50"><td className="px-5 py-4 font-medium text-ink">#1042</td>…<td className="px-5 py-4 text-right tabular-nums">$84.00</td></tr>
    </tbody>
  </table>
</div>
```

On phones, render the rows as stacked cards (`sm:hidden` list + `hidden sm:block` table) when there are more than 4 columns.

### Review item

```tsx
<article className="border-b border-line py-6">
  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
    <Stars rating={r.rating} size="sm" />
    {r.title ? <h3 className="font-sans text-base font-semibold text-ink">{r.title}</h3> : null}
  </div>
  <p className="mt-1 text-sm text-muted">{r.author_name} · <time dateTime={r.created_at}>{date}</time></p>
  <div className="mt-2 flex flex-wrap gap-2">{r.verified_purchase ? <Badge tone="success"><CheckIcon />Verified purchase</Badge> : null}{r.is_sample ? <Badge>Sample review</Badge> : null}</div>
  {r.body ? <p className="mt-3 text-ink-soft leading-relaxed">{r.body}</p> : null}
</article>
```

### Sandbox banner

`<p className="bg-neutral-900 px-4 py-2 text-center text-xs text-neutral-300"><strong className="font-semibold text-white">Sandbox store</strong> · …</p>` (neutral-300 on neutral-900 ≈ 11:1), or keep the warning tones `bg-warning-50 text-warning-900`.

## 9. Utilities added in globals.css

`focus-inverse` (white focus ring on dark areas), `scrollbar-none` (horizontal rails), `animation-delay-<ms>`, `bg-shimmer`, `bg-mesh-dark` and `bg-mesh-light`. Merging is handled by `lib/cn.ts`, which knows the custom tokens (`text-display`, `shadow-glow`, `ease-*`, `animate-*`), so `cn()` resolves conflicts correctly.

## 10. Dark theme (future)

This release ships no dark theme. Components use semantic tokens (`ink`, `muted`, `canvas`, `raised`, `sunken`, `line`, `focus`) that are defined with `var()` on top of the scales. A future dark theme can therefore redefine only that semantic layer under `[data-theme="dark"]`, and it must re-verify every pair in §2.
