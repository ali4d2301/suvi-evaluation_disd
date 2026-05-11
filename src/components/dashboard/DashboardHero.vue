<script setup>
import { computed } from 'vue'

import { formatNumber } from '../../utils/dashboardFormatters'
import DashboardPeriodFilter from './DashboardPeriodFilter.vue'

const props = defineProps({
  summary: {
    type: Object,
    required: true,
  },
  view: {
    type: String,
    default: 'ACT',
  },
  availableYears: {
    type: Array,
    default: () => [],
  },
  periodSelection: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:periodSelection'])

const isAxisView = computed(() => props.view === 'AXE')
const showPeriodFilter = computed(() => ['ACT', 'AXE'].includes(props.view))
const heroTitle = computed(() => (isAxisView.value ? 'Axes stratégiques' : 'Tableau de bord de suivi'))
const heroSubtitle = computed(() =>
  isAxisView.value ? "Vue d'ensemble du portefeuille par axe" : "Pilotage du plan d'activités",
)

function updatePeriodSelection(nextSelection) {
  emit('update:periodSelection', nextSelection)
}
</script>

<template>
  <div class="hero-anchor">
    <header class="hero">
      <div class="hero__copy">
        <h1>{{ heroTitle }}</h1>
        <p class="hero__subtitle">{{ heroSubtitle }}</p>
        <p v-if="!isAxisView" class="hero__description">
          <span class="hero__description-item">
            {{ formatNumber(props.summary.totalActivities) }} activit&eacute;s suivies sur
            {{ formatNumber(props.summary.coveredProjects) }} projets et
            {{ formatNumber(props.summary.coveredAxes) }} axes strat&eacute;giques
          </span>
          <span v-if="props.summary.overdueActivities > 0" class="hero__description-separator">|</span>
          <span v-if="props.summary.overdueActivities > 0" class="hero__description-item">
            {{ formatNumber(props.summary.overdueActivities) }} activit&eacute;s d&eacute;passent leur horizon
            planifi&eacute;
          </span>
        </p>
      </div>

      <div v-if="showPeriodFilter" class="hero__controls">
        <DashboardPeriodFilter
          :mode="props.view"
          :available-years="props.availableYears"
          :selection="props.periodSelection"
          @update:selection="updatePeriodSelection"
        />
      </div>
    </header>
  </div>
</template>
