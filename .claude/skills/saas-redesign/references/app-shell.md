# AppShell reference

A ready-to-adapt layout component: sidebar, top bar and content area. It's written with `setup()` + `export default` because that style works in every Vue 3 project. Converting to `<script setup>` is mechanical: drop `export default`/`setup()`/`return`, and declare props with `defineProps`.

Contents:
1. Component code
2. Wiring it into `App.vue`
3. Inline icon set
4. Behavior notes (collapse, drawer, theme)

---

## 1. `src/components/AppShell.vue`

```vue
<template>
  <div :class="['shell', { 'shell--collapsed': collapsed, 'shell--drawer-open': drawerOpen }]">
    <!-- Backdrop only matters on mobile, where the sidebar is an overlay drawer -->
    <div v-if="drawerOpen" class="shell__backdrop" @click="drawerOpen = false" />

    <aside id="app-sidebar" class="sidebar">
      <div class="sidebar__brand">
        <slot name="brand" :collapsed="collapsed" />
      </div>

      <nav class="sidebar__nav" :aria-label="navLabel">
        <div v-for="group in navGroups" :key="group.label || 'default'" class="sidebar__group">
          <div v-if="group.label && !collapsed" class="sidebar__group-label">{{ group.label }}</div>
          <router-link
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="sidebar__link"
            :class="{ 'is-active': isActive(item) }"
            :aria-current="isActive(item) ? 'page' : null"
            :title="collapsed ? item.label : null"
          >
            <span class="sidebar__icon" aria-hidden="true" v-html="item.icon" />
            <span class="sidebar__label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar__footer">
        <slot name="sidebar-footer" :collapsed="collapsed" />
        <button
          type="button"
          class="sidebar__collapse"
          :aria-expanded="!collapsed"
          aria-controls="app-sidebar"
          :aria-label="collapseLabel"
          @click="toggleCollapsed"
        >
          <span aria-hidden="true" v-html="collapsed ? icons.chevronRight : icons.chevronLeft" />
        </button>
      </div>
    </aside>

    <div class="shell__main">
      <header class="topbar">
        <button
          type="button"
          class="topbar__menu"
          :aria-expanded="drawerOpen"
          aria-controls="app-sidebar"
          :aria-label="menuLabel"
          @click="drawerOpen = !drawerOpen"
        >
          <span aria-hidden="true" v-html="icons.menu" />
        </button>
        <div class="topbar__start"><slot name="topbar-start" /></div>
        <div class="topbar__end">
          <slot name="topbar-end" />
          <button type="button" class="topbar__icon-btn" :aria-label="themeLabel" @click="toggleTheme">
            <span aria-hidden="true" v-html="theme === 'dark' ? icons.sun : icons.moon" />
          </button>
        </div>
      </header>

      <main class="content">
        <div class="content__inner">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { icons } from './icons'

// localStorage can throw (private mode, blocked storage), so every access is guarded
const read = (key) => { try { return localStorage.getItem(key) } catch { return null } }
const write = (key, value) => { try { localStorage.setItem(key, value) } catch { /* ignore */ } }

export default {
  name: 'AppShell',
  props: {
    // [{ label?: string, items: [{ to, label, icon, exact? }] }]
    navGroups: { type: Array, required: true },
    navLabel: { type: String, default: 'Main navigation' },
    collapseLabel: { type: String, default: 'Toggle sidebar' },
    menuLabel: { type: String, default: 'Open navigation' },
    themeLabel: { type: String, default: 'Toggle theme' }
  },
  setup() {
    const route = useRoute()
    const collapsed = ref(read('shell-collapsed') === '1')
    const drawerOpen = ref(false)
    const theme = ref(read('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))

    const applyTheme = () => document.documentElement.setAttribute('data-theme', theme.value)

    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value
      write('shell-collapsed', collapsed.value ? '1' : '0')
    }

    const toggleTheme = () => {
      theme.value = theme.value === 'dark' ? 'light' : 'dark'
      write('theme', theme.value)
      applyTheme()
    }

    // Root '/' would match every path with startsWith, so it only matches exactly
    const isActive = (item) =>
      item.exact || item.to === '/' ? route.path === item.to : route.path.startsWith(item.to)

    const onKeydown = (e) => { if (e.key === 'Escape') drawerOpen.value = false }

    // Navigating from the mobile drawer should close it
    watch(() => route.path, () => { drawerOpen.value = false })

    onMounted(() => {
      applyTheme()
      window.addEventListener('keydown', onKeydown)
    })
    onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

    return { collapsed, drawerOpen, theme, icons, isActive, toggleCollapsed, toggleTheme }
  }
}
</script>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns var(--duration) var(--ease);
}
.shell--collapsed { grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr); }

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  z-index: var(--z-sidebar);
  overflow: hidden;
}
.sidebar__brand {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  color: var(--sidebar-text-active);
  white-space: nowrap;
}
.sidebar__nav { flex: 1; overflow-y: auto; padding: var(--space-3); }
.sidebar__group + .sidebar__group { margin-top: var(--space-5); }
.sidebar__group-label {
  padding: 0 var(--space-3) var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--sidebar-text);
  opacity: 0.7;
}
.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 36px;
  padding: 0 var(--space-3);
  margin-bottom: 2px;
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease);
}
.sidebar__link:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
.sidebar__link.is-active { background: var(--sidebar-item-active); color: var(--sidebar-item-active-text); }
.sidebar__icon { display: inline-flex; width: 20px; height: 20px; flex-shrink: 0; }
.sidebar__icon :deep(svg) { width: 20px; height: 20px; }
.shell--collapsed .sidebar__label { display: none; }
.shell--collapsed .sidebar__link { justify-content: center; padding: 0; }

.sidebar__footer {
  border-top: 1px solid var(--sidebar-border);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.sidebar__collapse,
.topbar__menu,
.topbar__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}
.sidebar__collapse { align-self: flex-end; color: var(--sidebar-text); }
.shell--collapsed .sidebar__collapse { align-self: center; }
.sidebar__collapse:hover { background: var(--sidebar-item-hover); }
.topbar__menu:hover,
.topbar__icon-btn:hover { background: var(--surface-sunken); color: var(--text); }

.shell__main { display: flex; flex-direction: column; min-width: 0; }
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-6);
  background: color-mix(in srgb, var(--bg) 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
}
.topbar__menu { display: none; }
.topbar__start { flex: 1; min-width: 0; }
.topbar__end { display: flex; align-items: center; gap: var(--space-2); }

.content { flex: 1; padding: var(--space-6); }
.content__inner { max-width: var(--content-max); margin: 0 auto; }

.shell__backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: var(--z-backdrop);
}

/* Mobile: the sidebar becomes an off-canvas drawer and collapse mode doesn't apply */
@media (max-width: 767px) {
  .shell, .shell--collapsed { grid-template-columns: minmax(0, 1fr); }
  .sidebar {
    position: fixed;
    left: 0;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease);
    z-index: var(--z-drawer);
  }
  .shell--drawer-open .sidebar { transform: none; box-shadow: var(--shadow-lg); }
  .shell--collapsed .sidebar__label { display: inline; }
  .shell--collapsed .sidebar__link { justify-content: flex-start; padding: 0 var(--space-3); }
  .sidebar__collapse { display: none; }
  .topbar__menu { display: inline-flex; }
  .topbar { padding: 0 var(--space-4); }
  .content { padding: var(--space-4); }
}
</style>
```

## 2. Wiring into `App.vue`

```vue
<template>
  <AppShell :nav-groups="navGroups" :nav-label="t('nav.main')">
    <template #brand="{ collapsed }">
      <strong v-if="!collapsed">{{ t('nav.companyName') }}</strong>
      <strong v-else>{{ t('nav.companyName').charAt(0) }}</strong>
    </template>
    <template #topbar-end>
      <LanguageSwitcher />
      <ProfileMenu />
    </template>
    <FilterBar />
    <router-view />
  </AppShell>
</template>
```

Build `navGroups` as a `computed` so labels react to locale changes:

```js
const navGroups = computed(() => [
  { items: [{ to: '/', label: t('nav.overview'), icon: icons.home, exact: true }] },
  { label: t('nav.groupOperations'), items: [
    { to: '/inventory', label: t('nav.inventory'), icon: icons.box },
    { to: '/orders', label: t('nav.orders'), icon: icons.clipboard }
  ] }
])
```

Keep modals, toasts and other globally mounted components outside `<AppShell>` (as siblings in a root fragment) so they aren't clipped by the shell's grid or overflow.

## 3. `src/components/icons.js`

Stroke icons on a 24×24 grid using `currentColor`, so they follow the link color in both themes. Add more in the same style (1.75 stroke, round caps) if a nav item needs one.

```js
const svg = (d) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`

export const icons = {
  home: svg('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>'),
  box: svg('<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>'),
  clipboard: svg('<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M9 12h6M9 16h4"/>'),
  truck: svg('<path d="M3 6h11v10H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>'),
  chart: svg('<path d="M4 20V4"/><path d="M4 20h16"/><path d="M8 16v-5M12 16V8M16 16v-3"/>'),
  trending: svg('<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>'),
  wallet: svg('<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18"/><circle cx="16" cy="15" r="1"/>'),
  cart: svg('<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2l2.5 11h11L21 8H7"/>'),
  file: svg('<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4"/><path d="M9 13h6M9 17h6"/>'),
  settings: svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
  users: svg('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14a6 6 0 0 1 3.5 6"/>'),
  menu: svg('<path d="M4 6h16M4 12h16M4 18h16"/>'),
  chevronLeft: svg('<path d="m15 18-6-6 6-6"/>'),
  chevronRight: svg('<path d="m9 18 6-6-6-6"/>'),
  sun: svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  moon: svg('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>')
}
```

`v-html` is safe here because the icon strings are static constants defined in the codebase. Never pass user or API data through it.

## 4. Behavior notes

- **Collapse** applies only at 768px and wider. On mobile the same sidebar slides in as a drawer, with labels always shown.
- **Drawer** closes on backdrop click, on Escape and on route change. If the app has its own focus-trap utility, use it on the drawer. Otherwise, closing on Escape and on backdrop click is enough for a nav drawer.
- **Theme** sets `data-theme` on `<html>` at mount. To avoid a flash of the wrong theme on load, also add this one-liner to `index.html` before the app script:
  ```html
  <script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>
  ```
- **Sticky elements inside views** (sticky table headers, sticky filter rows) should use `top: var(--topbar-height)` so they stick below the top bar instead of under it.
- **Modals** that used a hardcoded `z-index` should use `var(--z-modal)` so they stack above the drawer.
