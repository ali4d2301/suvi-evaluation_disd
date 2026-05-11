<script setup>
import MetricCard from './MetricCard.vue'

const props = defineProps({
  cards: {
    type: Array,
    required: true,
  },
})
</script>

<template>
  <section class="panel panel--executive">
    <div class="panel__header panel__header--executive">
      <h2>Vue exécutive</h2>
    </div>

    <div class="kpi-grid">
      <MetricCard v-for="card in props.cards" :key="card.label" v-bind="card" />
    </div>
  </section>
</template>
