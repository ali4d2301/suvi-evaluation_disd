<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, Teleport, watch } from 'vue'

const weekdayLabels = ['lu', 'ma', 'me', 'je', 've', 'sa', 'di']

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  min: {
    type: String,
    default: '',
  },
  max: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: 'Choisir une date',
  },
})

const emit = defineEmits(['update:modelValue'])

const rootRef = ref(null)
const panelRef = ref(null)
const isOpen = ref(false)
const panelReady = ref(false)
const panelStyle = ref({
  left: '0px',
  top: '0px',
})
const displayedMonth = ref(startOfMonth(parseISODate(props.modelValue) ?? new Date()))

const selectedDate = computed(() => parseISODate(props.modelValue))
const todayIso = formatISODate(new Date())
const monthLabel = computed(() => {
  const formatted = new Intl.DateTimeFormat('fr-FR', {
    month: 'long',
    year: 'numeric',
  }).format(displayedMonth.value)

  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
})

const canGoPreviousMonth = computed(() => {
  if (!props.min) {
    return true
  }

  const previousMonth = addMonths(displayedMonth.value, -1)
  const monthEnd = endOfMonth(previousMonth)

  return formatISODate(monthEnd) >= props.min
})

const canGoNextMonth = computed(() => {
  if (!props.max) {
    return true
  }

  const nextMonth = addMonths(displayedMonth.value, 1)

  return formatISODate(nextMonth) <= props.max
})

const calendarDays = computed(() => {
  const firstVisibleDay = startOfWeek(displayedMonth.value)

  return Array.from({ length: 42 }, (_, index) => {
    const dayDate = addDays(firstVisibleDay, index)
    const iso = formatISODate(dayDate)
    const isCurrentMonth = dayDate.getMonth() === displayedMonth.value.getMonth()

    return {
      iso,
      label: dayDate.getDate(),
      isCurrentMonth,
      isToday: iso === todayIso,
      isSelected: iso === props.modelValue,
      isDisabled: !isSelectableDate(iso, props.min, props.max),
    }
  })
})

watch(
  () => props.modelValue,
  (value) => {
    const parsedValue = parseISODate(value)

    if (parsedValue) {
      displayedMonth.value = startOfMonth(parsedValue)
    }
  },
)

function parseISODate(value) {
  if (!value) {
    return null
  }

  const [year, month, day] = String(value)
    .split('-')
    .map((part) => Number(part))

  if (!year || !month || !day) {
    return null
  }

  return new Date(year, month - 1, day)
}

function formatISODate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

function formatDisplayDate(value) {
  const parsedValue = parseISODate(value)

  if (!parsedValue) {
    return ''
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(parsedValue)
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

function endOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

function addMonths(date, amount) {
  return new Date(date.getFullYear(), date.getMonth() + amount, 1)
}

function addDays(date, amount) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + amount)
}

function startOfWeek(date) {
  const start = startOfMonth(date)
  const offset = (start.getDay() + 6) % 7

  return addDays(start, -offset)
}

function isSelectableDate(iso, min, max) {
  if (min && iso < min) {
    return false
  }

  if (max && iso > max) {
    return false
  }

  return true
}

function updatePlacement() {
  const rootElement = rootRef.value
  const panelElement = panelRef.value

  if (!rootElement || !panelElement || typeof window === 'undefined') {
    return
  }

  const rootRect = rootElement.getBoundingClientRect()
  const panelRect = panelElement.getBoundingClientRect()
  const gap = 8
  const viewportPadding = 16
  const openUp =
    window.innerHeight - rootRect.bottom < panelRect.height + gap + viewportPadding &&
    rootRect.top > window.innerHeight - rootRect.bottom
  const alignEnd =
    window.innerWidth - rootRect.left < panelRect.width + viewportPadding &&
    rootRect.right > window.innerWidth - rootRect.left

  let left = alignEnd ? rootRect.right - panelRect.width : rootRect.left
  let top = openUp ? rootRect.top - panelRect.height - gap : rootRect.bottom + gap

  left = Math.min(
    Math.max(viewportPadding, left),
    Math.max(viewportPadding, window.innerWidth - panelRect.width - viewportPadding),
  )
  top = Math.min(
    Math.max(viewportPadding, top),
    Math.max(viewportPadding, window.innerHeight - panelRect.height - viewportPadding),
  )

  panelStyle.value = {
    left: `${Math.round(left)}px`,
    top: `${Math.round(top)}px`,
  }
  panelReady.value = true
}

function openPanel() {
  if (selectedDate.value) {
    displayedMonth.value = startOfMonth(selectedDate.value)
  }

  isOpen.value = true
  panelReady.value = false

  nextTick(() => {
    updatePlacement()
  })
}

function closePanel() {
  isOpen.value = false
  panelReady.value = false
}

function togglePanel() {
  if (isOpen.value) {
    closePanel()
    return
  }

  openPanel()
}

function selectDate(iso) {
  if (!isSelectableDate(iso, props.min, props.max)) {
    return
  }

  emit('update:modelValue', iso)
  closePanel()
}

function clearDate() {
  emit('update:modelValue', '')
  closePanel()
}

function selectToday() {
  if (!isSelectableDate(todayIso, props.min, props.max)) {
    return
  }

  emit('update:modelValue', todayIso)
  closePanel()
}

function goToPreviousMonth() {
  if (!canGoPreviousMonth.value) {
    return
  }

  displayedMonth.value = addMonths(displayedMonth.value, -1)
  nextTick(() => {
    updatePlacement()
  })
}

function goToNextMonth() {
  if (!canGoNextMonth.value) {
    return
  }

  displayedMonth.value = addMonths(displayedMonth.value, 1)
  nextTick(() => {
    updatePlacement()
  })
}

function handleTriggerKeydown(event) {
  if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openPanel()
  }

  if (event.key === 'Escape') {
    closePanel()
  }
}

function handleDocumentPointerDown(event) {
  const rootElement = rootRef.value
  const panelElement = panelRef.value

  if (rootElement?.contains(event.target) || panelElement?.contains(event.target)) {
    return
  }

  closePanel()
}

function handleWindowChange() {
  if (!isOpen.value) {
    return
  }

  nextTick(() => {
    updatePlacement()
  })
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  window.addEventListener('resize', handleWindowChange)
  window.addEventListener('scroll', handleWindowChange, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  window.removeEventListener('resize', handleWindowChange)
  window.removeEventListener('scroll', handleWindowChange, true)
})
</script>

<template>
  <div ref="rootRef" class="refined-date-picker">
    <button
      type="button"
      class="refined-date-picker__trigger"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click="togglePanel"
      @keydown="handleTriggerKeydown"
    >
      <span
        class="refined-date-picker__value"
        :class="{ 'refined-date-picker__value--placeholder': !props.modelValue }"
      >
        {{ formatDisplayDate(props.modelValue) || props.placeholder }}
      </span>
      <span class="refined-date-picker__icon" aria-hidden="true">
        <span />
      </span>
    </button>

    <Teleport to="body">
      <transition name="refined-date-fade">
        <div
          v-if="isOpen"
          ref="panelRef"
          class="refined-date-picker__panel"
          :style="[panelStyle, { visibility: panelReady ? 'visible' : 'hidden' }]"
        >
          <div class="refined-date-picker__header">
            <button
              type="button"
              class="refined-date-picker__nav"
              :disabled="!canGoPreviousMonth"
              @click="goToPreviousMonth"
            >
              <span aria-hidden="true">&lsaquo;</span>
            </button>
            <strong>{{ monthLabel }}</strong>
            <button
              type="button"
              class="refined-date-picker__nav"
              :disabled="!canGoNextMonth"
              @click="goToNextMonth"
            >
              <span aria-hidden="true">&rsaquo;</span>
            </button>
          </div>

          <div class="refined-date-picker__weekdays">
            <span v-for="weekday in weekdayLabels" :key="weekday">{{ weekday }}</span>
          </div>

          <div class="refined-date-picker__grid">
            <button
              v-for="day in calendarDays"
              :key="day.iso"
              type="button"
              class="refined-date-picker__day"
              :class="{
                'refined-date-picker__day--outside': !day.isCurrentMonth,
                'refined-date-picker__day--today': day.isToday,
                'refined-date-picker__day--selected': day.isSelected,
              }"
              :disabled="day.isDisabled"
              @click="selectDate(day.iso)"
            >
              {{ day.label }}
            </button>
          </div>

          <div class="refined-date-picker__footer">
            <button
              type="button"
              class="refined-date-picker__action"
              :disabled="!props.modelValue"
              @click="clearDate"
            >
              Effacer
            </button>
            <button
              type="button"
              class="refined-date-picker__action"
              :disabled="!isSelectableDate(todayIso, props.min, props.max)"
              @click="selectToday"
            >
              Aujourd'hui
            </button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.refined-date-picker {
  position: relative;
  width: 100%;
  min-width: 0;
}

.refined-date-picker__trigger {
  width: 100%;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.62rem 0.74rem;
  border: 1px solid rgba(173, 188, 206, 0.96);
  border-radius: 12px;
  background: rgba(255, 255, 255, 1);
  color: #17314c;
  font: inherit;
  text-align: left;
  box-shadow:
    inset 0 1px 1px rgba(234, 239, 244, 0.88),
    0 1px 2px rgba(23, 49, 76, 0.04);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.refined-date-picker__trigger:hover {
  border-color: rgba(121, 140, 164, 0.72);
  background: rgba(251, 253, 255, 1);
}

.refined-date-picker__trigger:focus-visible {
  outline: none;
  border-color: rgba(73, 95, 123, 0.86);
  box-shadow:
    0 0 0 3px rgba(74, 96, 124, 0.14),
    inset 0 1px 1px rgba(234, 239, 244, 0.88);
}

.refined-date-picker__value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.refined-date-picker__value--placeholder {
  color: #5e7590;
}

.refined-date-picker__icon {
  position: relative;
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border: 1.6px solid rgba(78, 99, 124, 0.96);
  border-radius: 6px;
}

.refined-date-picker__icon::before,
.refined-date-picker__icon::after,
.refined-date-picker__icon span::before,
.refined-date-picker__icon span::after {
  content: '';
  position: absolute;
}

.refined-date-picker__icon::before {
  top: 3px;
  left: 3px;
  right: 3px;
  height: 1.6px;
  background: rgba(78, 99, 124, 0.96);
}

.refined-date-picker__icon::after {
  top: -2px;
  left: 4px;
  width: 2px;
  height: 5px;
  border-radius: 999px;
  background: rgba(78, 99, 124, 0.96);
}

.refined-date-picker__icon span::before {
  top: -2px;
  right: 4px;
  width: 2px;
  height: 5px;
  border-radius: 999px;
  background: rgba(78, 99, 124, 0.96);
}

.refined-date-picker__icon span::after {
  inset: 6px 4px 4px;
  border-radius: 3px;
  background: rgba(226, 233, 241, 0.95);
}

.refined-date-picker__panel {
  position: fixed;
  z-index: 120;
  width: min(304px, calc(100vw - 2rem));
  padding: 0.9rem;
  border: 1px solid rgba(185, 199, 216, 0.98);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.995);
  box-shadow:
    0 20px 46px rgba(15, 35, 60, 0.14),
    0 4px 12px rgba(15, 35, 60, 0.06);
  backdrop-filter: blur(12px);
}

.refined-date-picker__header {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 36px;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.refined-date-picker__header strong {
  color: #17314c;
  font-size: 0.98rem;
  text-align: center;
}

.refined-date-picker__nav {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(188, 201, 217, 0.98);
  border-radius: 10px;
  background: rgba(255, 255, 255, 1);
  color: #5b738f;
  font: inherit;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease;
}

.refined-date-picker__nav:hover:not(:disabled),
.refined-date-picker__nav:focus-visible:not(:disabled) {
  outline: none;
  border-color: rgba(121, 140, 164, 0.72);
  background: rgba(243, 247, 251, 0.98);
  color: #17314c;
}

.refined-date-picker__nav:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.refined-date-picker__weekdays,
.refined-date-picker__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.refined-date-picker__weekdays {
  margin-bottom: 0.35rem;
}

.refined-date-picker__weekdays span {
  padding: 0.45rem 0;
  color: #5f7791;
  font-size: 0.78rem;
  font-weight: 700;
  text-align: center;
  text-transform: lowercase;
}

.refined-date-picker__day {
  height: 38px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #17314c;
  font: inherit;
  cursor: pointer;
  transition: background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.refined-date-picker__day:hover:not(:disabled),
.refined-date-picker__day:focus-visible:not(:disabled) {
  outline: none;
  background: rgba(237, 242, 247, 0.96);
}

.refined-date-picker__day--outside {
  color: #7f93ab;
}

.refined-date-picker__day--today:not(.refined-date-picker__day--selected) {
  box-shadow: inset 0 0 0 1px rgba(128, 146, 169, 0.9);
}

.refined-date-picker__day--selected {
  background: #17314c;
  color: #ffffff;
}

.refined-date-picker__day:disabled {
  color: rgba(134, 149, 168, 0.82);
  cursor: not-allowed;
}

.refined-date-picker__footer {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  margin-top: 0.8rem;
  padding-top: 0.82rem;
  border-top: 1px solid rgba(214, 223, 233, 0.96);
}

.refined-date-picker__action {
  padding: 0;
  border: none;
  background: transparent;
  color: #5f7690;
  font: inherit;
  cursor: pointer;
  transition: color 0.16s ease;
}

.refined-date-picker__action:hover:not(:disabled),
.refined-date-picker__action:focus-visible:not(:disabled) {
  outline: none;
  color: #17314c;
}

.refined-date-picker__action:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.refined-date-fade-enter-active,
.refined-date-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.refined-date-fade-enter-from,
.refined-date-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
