<template>
  <div :class="['shell', { 'shell--collapsed': collapsed, 'shell--drawer-open': drawerOpen }]">
    <!-- Backdrop only matters on mobile, where the sidebar is an overlay drawer -->
    <div v-if="drawerOpen" class="shell__backdrop" @click="drawerOpen = false" />

    <aside id="app-sidebar" class="sidebar">
      <div class="sidebar__brand">
        <slot name="brand" />
      </div>

      <nav class="sidebar__nav" :aria-label="navLabel">
        <div v-for="group in navGroups" :key="group.id" class="sidebar__group">
          <div v-if="group.label" class="sidebar__group-label">{{ group.label }}</div>
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
          :title="collapseLabel"
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
          <button
            type="button"
            class="topbar__icon-btn"
            :aria-label="themeLabel"
            :title="themeLabel"
            @click="toggleTheme"
          >
            <span aria-hidden="true" v-html="theme === 'dark' ? icons.sun : icons.moon" />
          </button>
        </div>
      </header>

      <slot name="toolbar" />

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
    // [{ id, label?, items: [{ to, label, icon, exact? }] }]
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
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  color: var(--sidebar-text-active);
  white-space: nowrap;
}
.shell--collapsed .sidebar__brand { justify-content: center; padding: 0; }
.shell--collapsed .sidebar__brand :deep(.brand-text) { display: none; }
.sidebar__nav { flex: 1; overflow-y: auto; overflow-x: hidden; padding: var(--space-3); }
.sidebar__group + .sidebar__group { margin-top: var(--space-5); }
.sidebar__group-label {
  padding: 0 var(--space-3) var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--sidebar-text);
  opacity: 0.7;
}
/* Collapsed: a short divider keeps the grouping visible without the label text */
.shell--collapsed .sidebar__group-label {
  height: 1px;
  margin: 0 var(--space-3) var(--space-2);
  padding: 0;
  overflow: hidden;
  color: transparent;
  background: var(--sidebar-item-hover);
  opacity: 1;
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
.sidebar__link.is-active .sidebar__icon { color: var(--accent); }
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
  flex-shrink: 0;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease);
}
.sidebar__collapse :deep(svg),
.topbar__menu :deep(svg),
.topbar__icon-btn :deep(svg) { width: 20px; height: 20px; display: block; }
.sidebar__collapse { align-self: flex-end; color: var(--sidebar-text); }
.shell--collapsed .sidebar__collapse { align-self: center; }
.sidebar__collapse:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
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
    /* visibility keeps the closed drawer's links out of the tab order */
    visibility: hidden;
    transition: transform var(--duration) var(--ease), visibility 0s linear var(--duration);
    z-index: var(--z-drawer);
  }
  .shell--drawer-open .sidebar {
    transform: none;
    visibility: visible;
    transition: transform var(--duration) var(--ease);
    box-shadow: var(--shadow-lg);
  }
  .shell--collapsed .sidebar__brand { justify-content: flex-start; padding: 0 var(--space-4); }
  .shell--collapsed .sidebar__brand :deep(.brand-text) { display: flex; }
  .shell--collapsed .sidebar__group-label {
    height: auto;
    margin: 0;
    padding: 0 var(--space-3) var(--space-2);
    color: var(--sidebar-text);
    background: none;
    opacity: 0.7;
  }
  .shell--collapsed .sidebar__label { display: inline; }
  .shell--collapsed .sidebar__link { justify-content: flex-start; padding: 0 var(--space-3); }
  .sidebar__collapse { display: none; }
  .topbar__menu { display: inline-flex; }
  .topbar { padding: 0 var(--space-4); }
  .content { padding: var(--space-4); }
}
</style>
