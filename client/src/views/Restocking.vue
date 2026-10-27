<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else>
      <div class="card">
        <div class="budget-control">
          <label for="restock-budget" class="budget-label">{{ t('restocking.budgetLabel') }}</label>
          <input
            id="restock-budget"
            v-model.number="budget"
            type="range"
            class="budget-slider"
            min="0"
            :max="sliderMax"
            step="500"
            @input="onBudgetInput"
          />
          <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="confirmation" class="confirmation">
        {{ t('restocking.orderPlaced', { orderNumber: confirmation }) }}
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>

      <div v-if="recommendation">
        <div class="stats-grid">
          <div class="stat-card info">
            <div class="stat-label">{{ t('restocking.budget') }}</div>
            <div class="stat-value">{{ formatCurrency(recommendation.budget, currentCurrency) }}</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-label">{{ t('restocking.recommendedTotal') }}</div>
            <div class="stat-value">{{ formatCurrency(recommendation.total_cost, currentCurrency) }}</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">{{ t('restocking.remaining') }}</div>
            <div class="stat-value">{{ formatCurrency(recommendation.remaining, currentCurrency) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('restocking.items') }}</div>
            <div class="stat-value">{{ items.length }}</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
            <button
              class="place-order-button"
              :disabled="submitting || items.length === 0"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
            </button>
          </div>
          <div v-if="items.length === 0" class="empty-state">{{ t('restocking.noItems') }}</div>
          <div v-else :class="['table-container', { refreshing }]">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.name') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th class="numeric">{{ t('restocking.table.quantity') }}</th>
                  <th class="numeric">{{ t('restocking.table.unitCost') }}</th>
                  <th class="numeric">{{ t('restocking.table.lineTotal') }}</th>
                  <th class="numeric">{{ t('restocking.table.leadTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="item.sku">
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ translateProductName(item.name) }}</td>
                  <td>
                    <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                  </td>
                  <td class="numeric">{{ item.quantity }}</td>
                  <td class="numeric">{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                  <td class="numeric"><strong>{{ formatCurrencyWithDecimals(item.line_total, currentCurrency, 2) }}</strong></td>
                  <td class="numeric">{{ item.lead_time_days }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 500
const DEFAULT_BUDGET = 10000
const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const refreshing = ref(false)
    const submitting = ref(false)
    const error = ref(null)
    const confirmation = ref(null)
    const budget = ref(DEFAULT_BUDGET)
    const recommendation = ref(null)

    const items = computed(() => recommendation.value?.items || [])

    // Round the slider max up to a whole step: a range input snaps to the
    // largest step that fits under max, so an unrounded max would leave the
    // "buy everything" budget unreachable.
    const sliderMax = computed(() => {
      const max = recommendation.value?.max_useful_budget
      if (!max) return DEFAULT_BUDGET
      return Math.ceil(max / BUDGET_STEP) * BUDGET_STEP
    })

    // Slider drags can fire several overlapping requests; only the latest
    // response is applied so a slow earlier one can't overwrite it.
    let latestRequestId = 0

    const loadRecommendations = async () => {
      const requestId = ++latestRequestId
      try {
        refreshing.value = true
        const data = await api.getRestockRecommendations(budget.value)
        if (requestId !== latestRequestId) return
        recommendation.value = data
        error.value = null
      } catch (err) {
        if (requestId !== latestRequestId) return
        error.value = `${t('restocking.loadError')}: ${err.response?.data?.detail || err.message}`
      } finally {
        if (requestId === latestRequestId) {
          refreshing.value = false
          loading.value = false
        }
      }
    }

    // Debounce: wait until the slider has been still for DEBOUNCE_MS before
    // fetching, instead of requesting on every input event during a drag.
    let debounceTimer = null
    const onBudgetInput = () => {
      confirmation.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    }

    const placeOrder = async () => {
      if (submitting.value || items.value.length === 0) return
      try {
        submitting.value = true
        error.value = null
        confirmation.value = null
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: items.value.map(({ sku, quantity }) => ({ sku, quantity }))
        })
        confirmation.value = order.order_number
        await loadRecommendations()
      } catch (err) {
        error.value = `${t('restocking.submitError')}: ${err.response?.data?.detail || err.message}`
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      loading,
      refreshing,
      submitting,
      error,
      confirmation,
      budget,
      recommendation,
      items,
      sliderMax,
      onBudgetInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  accent-color: var(--accent);
  cursor: pointer;
}

.budget-value {
  min-width: 120px;
  text-align: right;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text);
}

.confirmation {
  background: var(--success-soft);
  border: 1px solid color-mix(in srgb, var(--success) 35%, transparent);
  color: var(--success-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.confirmation-link {
  margin-left: 0.5rem;
  color: var(--success-text);
  font-weight: 600;
}

.place-order-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  background: var(--accent);
  color: var(--text-inverse);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.place-order-button:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.place-order-button:disabled {
  background: var(--border-strong);
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.table-container.refreshing {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.numeric {
  text-align: right;
}

/* Phones: label on its own line above the slider and amount */
@media (max-width: 767px) {
  .budget-control {
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-4);
  }

  .budget-label {
    flex-basis: 100%;
    white-space: normal;
  }

  .budget-slider {
    min-width: 0;
  }

  .budget-value {
    min-width: 0;
  }
}
</style>
