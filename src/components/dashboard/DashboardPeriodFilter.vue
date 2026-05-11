<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  mode: {
    type: String,
    required: true,
  },
  availableYears: {
    type: Array,
    default: () => [],
  },
  selection: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:selection'])

const filterRef = ref(null)
const isOpen = ref(false)
const quarterOptions = [1, 2, 3, 4]

const normalizedYears = computed(() =>
  [...new Set(props.availableYears.map((year) => String(year ?? '').trim()).filter(Boolean))].sort(
    (left, right) => Number(left) - Number(right),
  ),
)

const actSelection = computed(() => ({
  year: String(props.selection?.year ?? '').trim(),
  quarterStart: Math.max(1, Math.min(4, Number(props.selection?.quarterStart ?? 1))),
  quarterEnd: Math.max(1, Math.min(4, Number(props.selection?.quarterEnd ?? 4))),
}))

const axisSelection = computed(() => ({
  startYear: String(props.selection?.startYear ?? '').trim(),
  endYear: String(props.selection?.endYear ?? '').trim(),
}))

const triggerLabel = computed(() => {
  if (props.mode === 'AXE') {
    const startYear = axisSelection.value.startYear
    const endYear = axisSelection.value.endYear

    if (!startYear && !endYear) {
      return 'Toutes les ann\u00e9es'
    }

    if ((startYear || endYear) === (endYear || startYear)) {
      return `Ann\u00e9e ${startYear || endYear}`
    }

    return `${startYear || endYear} - ${endYear || startYear}`
  }

  const { year, quarterStart, quarterEnd } = actSelection.value

  if (!year) {
    const latestYear = normalizedYears.value.at(-1)
    return latestYear ? `T1 \u00e0 T4 ${latestYear}` : 'P\u00e9riode'
  }

  if (quarterStart === quarterEnd) {
    return `T${quarterStart} ${year}`
  }

  return `T${quarterStart} \u00e0 T${quarterEnd} ${year}`
})

function updateSelection(nextSelection) {
  emit('update:selection', nextSelection)
}

function selectActYear(year) {
  updateSelection({
    year: String(year),
    quarterStart: 1,
    quarterEnd: 4,
  })
}

function selectActQuarterStart(quarter) {
  const nextStart = Number(quarter)
  const nextEnd = actSelection.value.quarterEnd < nextStart ? nextStart : actSelection.value.quarterEnd

  updateSelection({
    year: actSelection.value.year,
    quarterStart: nextStart,
    quarterEnd: nextEnd,
  })
}

function selectActQuarterEnd(quarter) {
  const nextEnd = Number(quarter)
  const nextStart = actSelection.value.quarterStart > nextEnd ? nextEnd : actSelection.value.quarterStart

  updateSelection({
    year: actSelection.value.year,
    quarterStart: nextStart,
    quarterEnd: nextEnd,
  })
}

function selectAxisStartYear(year) {
  const nextStart = String(year)
  const currentEnd = axisSelection.value.endYear || nextStart
  const nextEnd = Number(currentEnd) < Number(nextStart) ? nextStart : currentEnd

  updateSelection({
    startYear: nextStart,
    endYear: nextEnd,
  })
}

function selectAxisEndYear(year) {
  const nextEnd = String(year)
  const currentStart = axisSelection.value.startYear || nextEnd
  const nextStart = Number(currentStart) > Number(nextEnd) ? nextEnd : currentStart

  updateSelection({
    startYear: nextStart,
    endYear: nextEnd,
  })
}

function isAxisYearInRange(year) {
  const startYear = Number(axisSelection.value.startYear || axisSelection.value.endYear)
  const endYear = Number(axisSelection.value.endYear || axisSelection.value.startYear)
  const numericYear = Number(year)

  if (!startYear || !endYear || !numericYear) {
    return false
  }

  return numericYear >= Math.min(startYear, endYear) && numericYear <= Math.max(startYear, endYear)
}

function closeOnPointerDown(event) {
  if (!filterRef.value?.contains(event.target)) {
    isOpen.value = false
  }
}

function closeOnEscape(event) {
  if (event.key === 'Escape') {
    isOpen.value = false
  }
}

watch(isOpen, (open) => {
  if (open) {
    document.addEventListener('pointerdown', closeOnPointerDown)
    document.addEventListener('keydown', closeOnEscape)
    return
  }

  document.removeEventListener('pointerdown', closeOnPointerDown)
  document.removeEventListener('keydown', closeOnEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', closeOnPointerDown)
  document.removeEventListener('keydown', closeOnEscape)
})
</script>

<template>
  <div ref="filterRef" class="hero-period-filter">
    <button
      type="button"
      class="hero-period-chip"
      :class="{ 'is-open': isOpen }"
      :aria-expanded="isOpen"
      aria-haspopup="dialog"
      @click="isOpen = !isOpen"
    >
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <rect x="3.5" y="4" width="13" height="12" rx="2.2" />
        <path d="M6.5 2.8v3.1M13.5 2.8v3.1M3.5 7.2h13" />
      </svg>
      <span class="hero-period-chip__copy">
        <small>P&eacute;riode</small>
        <strong>{{ triggerLabel }}</strong>
      </span>
      <svg class="hero-period-chip__chevron" viewBox="0 0 20 20" aria-hidden="true">
        <path d="m6 8 4 4 4-4" />
      </svg>
    </button>

    <div v-if="isOpen" class="hero-period-popover" role="dialog" aria-label="Choisir une p&eacute;riode">
      <template v-if="props.mode === 'ACT'">
        <div class="hero-period-picker">
          <span class="hero-period-picker__label">Ann&eacute;e</span>
          <div class="hero-period-picker__years">
            <button
              v-for="year in normalizedYears"
              :key="`act-year-${year}`"
              type="button"
              class="hero-period-picker__year"
              :class="{ 'is-selected': actSelection.year === year }"
              @click="selectActYear(year)"
            >
              {{ year }}
            </button>
          </div>
        </div>

        <div v-if="actSelection.year" class="hero-period-picker">
          <span class="hero-period-picker__label">Du trimestre</span>
          <div class="hero-period-picker__months">
            <button
              v-for="quarter in quarterOptions"
              :key="`act-quarter-start-${quarter}`"
              type="button"
              class="hero-period-picker__month"
              :class="{ 'is-selected': actSelection.quarterStart === quarter }"
              @click="selectActQuarterStart(quarter)"
            >
              T{{ quarter }}
            </button>
          </div>
        </div>

        <div v-if="actSelection.year" class="hero-period-picker">
          <span class="hero-period-picker__label">Au trimestre</span>
          <div class="hero-period-picker__months">
            <button
              v-for="quarter in quarterOptions"
              :key="`act-quarter-end-${quarter}`"
              type="button"
              class="hero-period-picker__month"
              :class="{ 'is-selected': actSelection.quarterEnd === quarter }"
              @click="selectActQuarterEnd(quarter)"
            >
              T{{ quarter }}
            </button>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="hero-period-picker">
          <span class="hero-period-picker__label">De</span>
          <div class="hero-period-picker__years">
            <button
              v-for="year in normalizedYears"
              :key="`axis-year-start-${year}`"
              type="button"
              class="hero-period-picker__year"
              :class="{ 'is-selected': axisSelection.startYear === year }"
              @click="selectAxisStartYear(year)"
            >
              {{ year }}
            </button>
          </div>
        </div>

        <div class="hero-period-picker">
          <span class="hero-period-picker__label">&Agrave;</span>
          <div class="hero-period-picker__years">
            <button
              v-for="year in normalizedYears"
              :key="`axis-year-end-${year}`"
              type="button"
              class="hero-period-picker__year"
              :class="{
                'is-selected': axisSelection.endYear === year,
                'is-in-range': isAxisYearInRange(year),
              }"
              @click="selectAxisEndYear(year)"
            >
              {{ year }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
