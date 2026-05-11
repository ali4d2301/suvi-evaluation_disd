<script setup>
import { formatNumber } from '../../utils/dashboardFormatters'
import { getStatusColor } from '../../utils/dashboardPresentation'

const props = defineProps({
  activeStatus: {
    type: String,
    required: true,
  },
  statusOptions: {
    type: Array,
    required: true,
  },
  statusBreakdown: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:activeStatus'])

function selectStatus(label) {
  emit('update:activeStatus', label)
}
</script>

<template>
  <section class="panel panel--hero">
    <div class="panel__header panel__header--portfolio">
      <div class="section-title section-title--portfolio">
        <div class="section-title__copy section-title__copy--portfolio">
          <p class="panel__eyebrow">Suivi des activités</p>
          <h2>Vue de pilotage du portefeuille</h2>
        </div>
      </div>
    </div>

    <div class="status-filters">
      <button
        v-for="option in props.statusOptions"
        :key="option.label"
        type="button"
        class="status-filter"
        :class="{ 'status-filter--active': props.activeStatus === option.label }"
        @click="selectStatus(option.label)"
      >
        <span>{{ option.label }}</span>
        <strong>{{ formatNumber(option.total) }}</strong>
      </button>
    </div>

    <div class="status-meter">
      <span
        v-for="item in props.statusBreakdown"
        :key="item.label"
        class="status-meter__segment"
        :style="{ background: getStatusColor(item.label), flexGrow: item.total }"
      />
    </div>
  </section>
</template>
