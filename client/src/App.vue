<template>
  <AppShell
    :nav-groups="navGroups"
    :nav-label="t('nav.main')"
    :collapse-label="t('nav.collapseSidebar')"
    :menu-label="t('nav.openNavigation')"
    :theme-label="t('nav.toggleTheme')"
  >
    <template #brand>
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">{{ t('nav.companyName').charAt(0) }}</span>
        <span class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </span>
      </div>
    </template>
    <template #topbar-end>
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
    </template>
    <template #toolbar>
      <FilterBar />
    </template>
    <router-view />
  </AppShell>

  <!-- Modals stay outside the shell so its grid and overflow never clip them -->
  <ProfileDetailsModal
    :is-open="showProfileDetails"
    @close="showProfileDetails = false"
  />

  <TasksModal
    :is-open="showTasks"
    :tasks="tasks"
    @close="showTasks = false"
    @add-task="addTask"
    @delete-task="deleteTask"
    @toggle-task="toggleTask"
  />
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppShell from './components/AppShell.vue'
import { icons } from './components/icons'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppShell
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Computed so labels follow locale changes
    const navGroups = computed(() => [
      { id: 'main', items: [{ to: '/', label: t('nav.overview'), icon: icons.home }] },
      {
        id: 'operations',
        label: t('nav.groupOperations'),
        items: [
          { to: '/inventory', label: t('nav.inventory'), icon: icons.box },
          { to: '/orders', label: t('nav.orders'), icon: icons.clipboard },
          { to: '/demand', label: t('nav.demandForecast'), icon: icons.trending },
          { to: '/restocking', label: t('nav.restocking'), icon: icons.cart }
        ]
      },
      {
        id: 'analytics',
        label: t('nav.groupAnalytics'),
        items: [
          { to: '/spending', label: t('nav.finance'), icon: icons.wallet },
          { to: '/reports', label: t('nav.reports'), icon: icons.chart }
        ]
      }
    ])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navGroups,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* Shared classes used across views. Colors, spacing and type come from styles/tokens.css. */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  -moz-osx-font-smoothing: grayscale;
}

button,
input,
select,
textarea {
  font-family: inherit;
}

/* Brand block rendered in the sidebar's brand slot */
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.brand-mark {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: var(--text-inverse);
  font-weight: 700;
  font-size: var(--text-sm);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.brand-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--sidebar-text-active);
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--sidebar-text);
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Page header: title with an optional one-line description beneath it */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
  color: var(--text);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  min-width: 0;
  transition: border-color var(--duration) var(--ease), box-shadow var(--duration) var(--ease);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.15;
  color: var(--text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  overflow-wrap: break-word;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

.stat-card.info .stat-value {
  color: var(--info);
}

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
  min-width: 0;
}

.card-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.card-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}

/* Only the table scrolls sideways on narrow screens, never the page */
.table-container {
  overflow-x: auto;
  max-width: 100%;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

thead {
  background: var(--surface-hover);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  height: 40px;
  font-weight: 500;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

td {
  padding: var(--space-3);
  height: 44px;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color var(--duration) var(--ease);
}

tbody tr:hover {
  background: var(--surface-hover);
}

.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.5;
  text-transform: capitalize;
  white-space: nowrap;
}

.badge.success,
.badge.increasing {
  background: var(--success-soft);
  color: var(--success-text);
}

.badge.warning,
.badge.medium {
  background: var(--warning-soft);
  color: var(--warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.badge.info,
.badge.stable,
.badge.low {
  background: var(--info-soft);
  color: var(--info-text);
}

/* Loading and error states render as a centered, muted panel where the data would be */
.loading {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--text-muted);
  font-size: var(--text-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.error {
  background: var(--danger-soft);
  border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent);
  color: var(--danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
  text-align: center;
}
</style>
