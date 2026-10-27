---
name: saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a collapsible vertical sidebar on the left in place of a top nav bar, a design-token system (color, spacing, radius, shadow, type), a consistent page-header pattern, polished cards and tables, and light/dark mode. Use this skill whenever the user wants to modernize, restyle, re-skin, or "make professional" a Vue app; move navigation from the top to the side; add a sidebar or app shell; unify spacing or colors; add dark mode; or make the app look like Linear, Stripe, Vercel or another SaaS dashboard, even if they don't say "redesign" or "SaaS".
---

# SaaS redesign for Vue 3 apps

This skill turns an existing Vue 3 app into a SaaS-style interface: a collapsible left sidebar replaces the top navigation, a token-driven design system sets color, spacing and type, every page shares one header pattern, and the whole app supports light and dark themes.

It is a **visual and structural** redesign. The app must keep working exactly as before: same routes, same data loading, same component logic, same i18n keys and same events. Users judge a redesign by what broke, so treat behavior preservation as the first requirement and polish as the second.

## Workflow

Work through these phases in order. Phases 1 and 2 are read-only. Don't edit files until the inventory in phase 2 exists.

### 1. Discover the app

Find out how this particular app is built before changing anything. Every Vue app puts these things somewhere different.

- **Project rules:** read every `CLAUDE.md`, `AGENTS.md` and contributing guide. They may require a specific subagent for `.vue` edits, forbid new dependencies, or set design rules (for example "no emojis in UI"). Their rules override this skill's.
- **Stack:** read `package.json` for the Vue version, router, UI or component library (Vuetify, PrimeVue, Element Plus, Naive UI, Tailwind) and icon library, and check whether it uses TypeScript.
- **Component style:** check whether components use `<script setup>`, `setup()` with `export default`, or the Options API. Match the existing style in everything you write.
- **App shell:** find the root component, usually `App.vue`, and the element that holds `<router-view>`. Find where the nav is rendered and how its links are built: hardcoded `router-link`s, a loop over routes, or a config array.
- **Global styles:** find where they live, whether that's an unscoped `<style>` in `App.vue`, `src/style.css` or `src/assets/main.css`, and which shared class names the views rely on (`.card`, `.page-header`, `.stats-grid`, and so on).
- **Header widgets:** list everything else in the top bar, such as language switchers, profile menus, search, global filter bars and notification bells. Each one needs a new home.
- **i18n:** if the app uses vue-i18n or a custom `t()`, every new label needs keys in every locale file.

### 2. Write an inventory and plan

Write a short plan in your reply (not a file) covering:
- the nav items, with their routes and labels in the current order
- where each header widget will go (see "Where things go")
- the files you'll create and the files you'll change
- the hardcoded colors you found, from a quick count with grep: `grep -rhoE '#[0-9a-fA-F]{3,8}\b' src | sort | uniq -c | sort -rn | head -30`

If the app uses a component library with its own theming system (Vuetify, PrimeVue and the like), plan to set that library's theme variables from the tokens rather than fighting its CSS. Mention this in the plan.

### 3. Add design tokens

Copy `references/tokens.css` into the app's global styles. It can be a new file such as `src/styles/tokens.css` imported once in `main.js`/`main.ts`, or a block at the top of the existing global style. It defines:

- neutral surface, text and border colors for light and dark
- one accent color, plus success, warning, danger and info
- a 4px-based spacing scale (`--space-1` through `--space-12`)
- radius, shadow, font-size and z-index scales
- the sidebar widths (`--sidebar-width`, `--sidebar-width-collapsed`)

Set `--accent` to the app's existing brand color if it has one, so the redesign still feels like the same product. Keep the token names as they are, since the rest of this skill and the shell component refer to them.

### 4. Build the app shell

Read `references/app-shell.md` and adapt its `AppShell` component to the app's component style. It provides:

- a sticky full-height sidebar with the logo, grouped nav items with icons, and a footer slot
- a collapse toggle that switches to icon-only mode, saved in `localStorage` (wrapped in `try/catch`)
- an off-canvas drawer below 768px, with a backdrop, closing on Escape and on route change
- a slim top bar in the content area with a menu button on mobile, a slot for header widgets, and a theme toggle
- accessibility: a `<nav aria-label>`, `aria-current="page"` on the active link, `aria-expanded` on toggles, and visible focus rings

Then change the root component so it renders `<AppShell>` around `<router-view>`, and remove the old top nav markup and its CSS. Build the nav items from the inventory in phase 2. Keep the existing `router-link` targets and `t()` label keys, and keep the existing order unless grouping clearly helps (for example "Operations" and "Finance").

**Icons:** if the app already has an icon library, use it. Otherwise use the small inline-SVG icon set in `references/app-shell.md`. Don't add an icon dependency without asking, since many projects pin their dependencies on purpose.

### 5. Apply the page-header pattern

Every routed view should open the same way: a title, an optional one-line description, and an optional actions area on the right. Global filters go in a toolbar row beneath it.

- If the views already share a `.page-header` class, restyle that class with tokens rather than rewriting every view. This is less risky and gives the same result.
- If each view builds its own header, add a small `PageHeader` component with `title`, `description` and an `actions` slot, and use it in each view. Don't change anything else in the view.

### 6. Restyle shared components with tokens

Restyle in this order, because each step fixes the most pixels for the least risk:

1. **Global classes** that every view uses: cards, stat or KPI cards, tables, badges, buttons, form inputs, modals, loading and error states. Rewrite them with tokens.
2. **Scoped styles** in views and components: replace hardcoded hex colors, pixel paddings and shadows with the matching tokens. Change values only. Don't restructure selectors or markup unless something is visibly broken.
3. **Charts:** set SVG `fill` and `stroke` from CSS variables (or `currentColor`) so charts follow the theme. If a chart library takes colors in JavaScript, read them with `getComputedStyle(document.documentElement).getPropertyValue('--accent')` and recompute them when the theme changes.

4. **Phone width:** a sidebar drawer alone doesn't make an app work on phones. Page content that was laid out for desktop still pushes the page wider than the screen, so the user can scroll sideways. Look for these causes in every view and fix each one:
   - `minmax(<N>px, 1fr)` in `auto-fit` grids, where N is wider than about 300px. Use `minmax(min(<N>px, 100%), 1fr)` so a column can shrink below N on a narrow screen.
   - fixed-column grids (`repeat(2, 1fr)`, `1fr 1fr`, `2fr 1fr`): add a `@media (max-width: 767px)` rule that changes them to one column.
   - fixed `width`/`min-width` of 200px or more on inputs, chart boxes and panels: use `width: 100%` with a `max-width`, or reset the width under the mobile breakpoint.
   - tables: wrap each one in an element with `overflow-x: auto`, so only the table scrolls and the page stays put. Fixed column widths are fine inside that wrapper.
   - SVG charts with a fixed `width` attribute: give them a `viewBox` and `width: 100%; height: auto`.
   - `white-space: nowrap` on long labels outside tables: allow wrapping, or add `text-overflow: ellipsis` with `overflow: hidden` and `min-width: 0`.
   - flex and grid children that hold wide content need `min-width: 0`, or they won't shrink below that content's width.

The style targets are in "Visual standards" below.

### 7. Dark mode

The tokens file already defines a dark palette under `:root[data-theme="dark"]` and under `prefers-color-scheme: dark` when no theme has been chosen. The shell's theme toggle sets `data-theme` on `<html>` and saves the choice. Check that:

- no hardcoded `white`, `#fff` or light hex value remains on a surface. These are the usual cause of white boxes in dark mode, so grep for them.
- status badges stay readable, using the `*-soft` background with the matching foreground.
- chart gridlines and axis text use `--border` and `--text-muted`.

### 8. Verify

The redesign isn't done until you've seen it render. In order:

1. Run a production build (`npm run build` or `npx vite build`) and fix every error and warning you introduced. Delete the build output afterwards if it wasn't there before.
2. With the dev server running, open every route in a browser (use Playwright if it's available) and check:
   - the page renders and the console shows no new errors
   - the active nav item is highlighted
   - there is no horizontal scroll at 1440px or 375px width. Measure it rather than judging from a screenshot: at 375px, `document.documentElement.scrollWidth - document.documentElement.clientWidth` must be 0 on every route. When it isn't, find the elements responsible with:
     ```js
     [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1).map(e => e.tagName + '.' + [...e.classList].join('.')).slice(0, 15)
     ```
     Fix the outermost element in that list, using the causes in phase 6, step 4. Repeat until every route measures 0.
3. Take screenshots of at least two key routes in four states: expanded, collapsed, mobile with the drawer open, and dark mode. Look at them before reporting. A screenshot you didn't look at isn't verification.
4. Exercise one real interaction per page that has one (open a modal, change a filter, submit a form) to confirm behavior survived.
5. Report what changed, the screenshots' locations, and anything you deliberately left alone.

## Where things go

| Old location | New location |
|---|---|
| Logo or app name in the top bar | Top of the sidebar. Collapsed mode shows only a monogram or the logo mark. |
| Nav links | The sidebar, as icon plus label, grouped if there are more than about 7 |
| Profile or user menu | The sidebar footer (avatar, name, menu), or the right of the top bar if the sidebar footer already has settings |
| Language or locale switcher | The top bar, on the right |
| Global search | The top bar, on the left or center |
| Global filter bar | A toolbar row under each page's header. If filters apply to all pages and the app renders them once, render them once below the top bar, inside the content area |
| Theme toggle (new) | The top bar, on the right |

## Visual standards

These are what makes the result look polished. Each one exists for a reason, so apply them with judgment rather than mechanically.

- **Spacing:** use only scale values. Use `--space-6` (24px) between page sections and `--space-5` (20px) for card padding. Use one gap value per grid. Mixed spacing is the most visible sign of an unpolished UI.
- **Content width:** constrain page content to about 1440px and center it. Very long table rows and wide charts are hard to read.
- **Type:** page title 24–28px semibold; card title 15–16px semibold; body 14px; table headers 12px medium in `--text-muted`. Use tabular figures (`font-variant-numeric: tabular-nums`) for numbers in tables and KPIs so columns line up.
- **Cards:** use a `--surface` background, a 1px `--border` and `--radius-lg`. Shadows should be subtle (`--shadow-sm`), or none if borders already separate things. Avoid heavy shadows combined with borders.
- **Tables:** use a sticky header where tables scroll, `--border-subtle` row dividers, a `--surface-hover` hover state, numeric columns aligned right, and generous row height (around 44px).
- **Color:** keep the accent for primary actions, the active nav item and focus. Status colors carry meaning, so don't use them for decoration.
- **Motion:** 150–200ms ease on hover and focus, and on the sidebar width transition. Respect `prefers-reduced-motion`.
- **Empty, loading and error states:** each one gets a centered, muted message in the card where the data would be, never a bare line of text at the top of the page.

## Guardrails

- **Preserve behavior.** Don't touch `<script>` logic, API calls, props, emits, router paths or store code, except to wire in the shell. If a view needs a script change to fit the new layout, keep it minimal and mention it in the report.
- **Keep class names working.** When you restyle a shared class, keep its name, because other views use it. Add new classes rather than renaming old ones.
- **No new runtime dependencies** without asking first. Everything in this skill works with plain CSS and inline SVG.
- **Locales:** every new user-facing string, such as "Collapse sidebar" or "Toggle theme", needs a key in every locale file. Don't hardcode English when the app is localized.
- **Work in reviewable steps.** Tokens, then shell, then page headers, then component restyle. Each step should build on its own, so a problem can be traced to one step.

## Reference files

- `references/tokens.css`: the full token sheet with light and dark palettes. Read it in phase 3.
- `references/app-shell.md`: the `AppShell` component (written with `setup()`, with notes on converting it to `<script setup>`), an inline icon set, wiring into `App.vue`, and notes on the mobile drawer and theme. Read it in phase 4.
