<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
  caption: {
    type: String,
    required: true,
  },
  progress: {
    type: Number,
    required: true,
  },
  color: {
    type: String,
    required: true,
  },
  compactValue: {
    type: Boolean,
    default: false,
  },
  neutralChrome: {
    type: Boolean,
    default: false,
  },
})

function hexToRgba(hex, alpha) {
  const normalized = String(hex ?? '').replace('#', '')

  if (normalized.length !== 6) {
    return `rgba(49, 135, 255, ${alpha})`
  }

  const red = Number.parseInt(normalized.slice(0, 2), 16)
  const green = Number.parseInt(normalized.slice(2, 4), 16)
  const blue = Number.parseInt(normalized.slice(4, 6), 16)

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

const cardStyle = computed(() => ({
  '--metric-accent': props.color,
  '--metric-accent-soft': hexToRgba(props.color, 0.18),
  '--metric-accent-fade': hexToRgba(props.color, 0.06),
  '--metric-accent-glow': hexToRgba(props.color, 0.22),
}))
</script>

<template>
  <article
    class="kpi-card"
    :class="{
      'kpi-card--compact-value': props.compactValue,
      'kpi-card--neutral-chrome': props.neutralChrome,
    }"
    :style="cardStyle"
  >
    <div class="kpi-card__chrome" aria-hidden="true" />
    <div class="kpi-card__header">
      <span class="kpi-card__label">{{ props.label }}</span>
    </div>
    <strong class="kpi-card__value">{{ props.value }}</strong>
    <small class="kpi-card__caption">{{ props.caption }}</small>
    <div class="progress-line">
      <span :style="{ width: `${Math.min(props.progress, 100)}%` }" />
    </div>
  </article>
</template>
