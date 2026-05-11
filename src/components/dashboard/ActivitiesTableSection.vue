<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import {
  clampText,
  formatCurrency,
  formatDate,
  formatNumber,
  initials,
} from '../../utils/dashboardFormatters'
import { statusSequence } from '../../utils/dashboardConstants'
import { getStatusLegendColor, getStatusLegendSoftColor } from '../../utils/dashboardPresentation'
import RefinedDatePicker from './RefinedDatePicker.vue'
import RefinedSelect from './RefinedSelect.vue'

const props = defineProps({
  activities: {
    type: Array,
    required: true,
  },
  activeStatus: {
    type: String,
    default: '',
  },
  activeService: {
    type: String,
    default: '',
  },
  serviceOptions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:activeStatus', 'update:activeService'])

const columnDefinitions = [
  { key: 'index', label: 'N°', initialWidth: 44, minWidth: 44, resizable: false, sortable: false },
  { key: 'axis', label: 'Axe stratégique', initialWidth: 148, minWidth: 124, resizable: true, sortable: true },
  { key: 'project', label: 'Projet', initialWidth: 154, minWidth: 132, resizable: true, sortable: true },
  { key: 'activity', label: 'Activité', initialWidth: 248, minWidth: 198, resizable: true, sortable: true },
  {
    key: 'service',
    label: 'Service / Responsable',
    initialWidth: 188,
    minWidth: 156,
    resizable: true,
    sortable: true,
  },
  { key: 'planning', label: 'Planification', initialWidth: 156, minWidth: 136, resizable: true, sortable: true },
  { key: 'status', label: 'État', initialWidth: 128, minWidth: 112, resizable: true, sortable: true },
  {
    key: 'observation',
    label: 'Observation',
    initialWidth: 220,
    minWidth: 104,
    resizable: true,
    sortable: true,
  },
]

const planningFilterStart = ref('')
const planningFilterEnd = ref('')
const delayFilter = ref('')
const columnWidths = ref(columnDefinitions.map((column) => column.initialWidth))
const activeResizeIndex = ref(null)
const tableWidth = computed(() => columnWidths.value.reduce((sum, width) => sum + width, 0))
const bodyScrollRef = ref(null)
const tableFrameRef = ref(null)
const tableTooltipRef = ref(null)
const activityDetailPopoverRef = ref(null)
const bodyScrollLeft = ref(0)
const bodyScrollbarWidth = ref(0)
const sortKey = ref('planning')
const sortDirection = ref('asc')
const tableTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  eyebrow: '',
  title: '',
  subtitle: '',
})
const activityDetail = ref({
  visible: false,
  x: 0,
  y: 0,
  activity: null,
})

let resizeState = null
let hasInitializedPlanningFilter = false
let tooltipAnchorElement = null
let activityDetailAnchorElement = null

const statusOrder = new Map(statusSequence.map((status, index) => [status, index]))
const availableStatusOptions = computed(() => {
  const extraStatuses = [...new Set(
    props.activities
      .map((activity) => String(activity.status ?? '').trim())
      .filter((status) => status && !statusSequence.includes(status)),
  )].sort((left, right) => left.localeCompare(right, 'fr-FR'))

  return [...statusSequence, ...extraStatuses]
})

const statusFilterOptions = computed(() => [
  { value: '', label: 'Tous les états' },
  ...availableStatusOptions.value.map((status) => ({ value: status, label: status })),
])

const situationFilterOptions = [
  { value: '', label: 'Toutes les activités' },
  { value: 'overdue', label: 'En retard uniquement' },
  { value: 'started', label: 'Démarrages effectifs' },
]

const serviceFilterOptions = computed(() => [
  { value: '', label: 'Tous les services' },
  ...props.serviceOptions.map((service) => ({ value: service, label: service })),
])

const planningDateBounds = computed(() => {
  const dates = props.activities.flatMap((activity) => {
    const plannedStart = normalizedDateValue(activity.plannedStart)
    const plannedEnd = normalizedDateValue(activity.plannedEnd)

    return [plannedStart, plannedEnd].filter(Boolean)
  })

  if (dates.length === 0) {
    return { min: '', max: '' }
  }

  const sortedDates = [...dates].sort()

  return {
    min: sortedDates[0],
    max: sortedDates[sortedDates.length - 1],
  }
})

const normalizedPlanningFilter = computed(() => {
  const start = planningFilterStart.value
  const end = planningFilterEnd.value

  if (start && end && start > end) {
    return { start: end, end: start }
  }

  return { start, end }
})

const filteredActivities = computed(() =>
  props.activities.filter((activity) =>
    matchesPlanningPeriod(
      activity,
      normalizedPlanningFilter.value.start,
      normalizedPlanningFilter.value.end,
    ) &&
    matchesDelayFilter(activity) &&
    matchesSharedFilters(activity),
  ),
)

const sortedActivities = computed(() =>
  [...filteredActivities.value].sort((left, right) => compareActivities(left, right)),
)

const hasSourceActivities = computed(() => props.activities.length > 0)
const hasDisplayedActivities = computed(() => sortedActivities.value.length > 0)
const isPlanningFilterModified = computed(
  () =>
    planningFilterStart.value !== planningDateBounds.value.min ||
    planningFilterEnd.value !== planningDateBounds.value.max,
)
const hasDelayFilter = computed(() => Boolean(delayFilter.value))
const hasSharedFilters = computed(() => Boolean(props.activeStatus || props.activeService))

function pointFocalLabel(activity) {
  return activity.pointFocal ?? activity.point_focal ?? 'Non renseigné'
}

function generalObjectiveLabel(activity) {
  const rawValue = activity.generalObjective ?? activity.objectif_general ?? ''
  const normalizedValue = String(rawValue).trim()

  return normalizedValue || 'Non renseigné'
}

function executionStartValue(activity) {
  return normalizedDateValue(activity.executionStart ?? activity.date_debut_execution)
}

function executionEndValue(activity) {
  return normalizedDateValue(activity.executionEnd ?? activity.date_fin_execution)
}

function observationLabel(activity) {
  const rawValue = activity.observation ?? activity.observations ?? ''
  const normalizedValue = String(rawValue).trim()

  return normalizedValue === 'Non renseigné' ? '' : normalizedValue
}

function hasActivityDetailOpen(activity) {
  return activityDetail.value.visible && activityDetail.value.activity?.id === activity.id
}

function normalizedDateValue(value) {
  return typeof value === 'string' && value ? value.slice(0, 10) : ''
}

function normalizeTextValue(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function getTodayDateValue() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000

  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

function isOverdueActivity(activity) {
  const plannedEnd = normalizedDateValue(activity.plannedEnd)

  if (!plannedEnd) {
    return false
  }

  const normalizedStatus = normalizeTextValue(activity.status)
  const isExcludedStatus = ['terminee', 'realisee', 'annulee', 'suspendue'].includes(normalizedStatus)

  if (isExcludedStatus) {
    return false
  }

  return plannedEnd < getTodayDateValue()
}

function hasEffectiveKickoff(activity) {
  const normalizedStatus = normalizeTextValue(activity.status)

  return ['en cours', 'terminee', 'realisee'].includes(normalizedStatus)
}

function matchesDelayFilter(activity) {
  if (!delayFilter.value) {
    return true
  }

  const isOverdue = isOverdueActivity(activity)

  if (delayFilter.value === 'overdue') {
    return isOverdue
  }

  if (delayFilter.value === 'started') {
    return hasEffectiveKickoff(activity)
  }

  return true
}

function matchesSharedFilters(activity) {
  if (props.activeStatus && String(activity.status ?? '') !== props.activeStatus) {
    return false
  }

  if (
    props.activeService &&
    normalizeTextValue(activity.service) !== normalizeTextValue(props.activeService)
  ) {
    return false
  }

  return true
}

function matchesPlanningPeriod(activity, filterStart, filterEnd) {
  if (!filterStart && !filterEnd) {
    return true
  }

  const plannedStart = normalizedDateValue(activity.plannedStart)
  const plannedEnd = normalizedDateValue(activity.plannedEnd)

  if (!plannedStart && !plannedEnd) {
    return false
  }

  const activityStart = plannedStart || plannedEnd
  const activityEnd = plannedEnd || plannedStart

  if (filterStart && activityEnd < filterStart) {
    return false
  }

  if (filterEnd && activityStart > filterEnd) {
    return false
  }

  return true
}

function compareTextValues(leftValue, rightValue, direction = sortDirection.value) {
  const left = normalizeTextValue(leftValue)
  const right = normalizeTextValue(rightValue)

  if (!left && !right) {
    return 0
  }

  if (!left) {
    return 1
  }

  if (!right) {
    return -1
  }

  return direction === 'asc'
    ? left.localeCompare(right, 'fr-FR')
    : right.localeCompare(left, 'fr-FR')
}

function compareDateValues(leftValue, rightValue, direction = sortDirection.value) {
  const left = normalizedDateValue(leftValue)
  const right = normalizedDateValue(rightValue)

  if (!left && !right) {
    return 0
  }

  if (!left) {
    return 1
  }

  if (!right) {
    return -1
  }

  if (left === right) {
    return 0
  }

  if (direction === 'asc') {
    return left < right ? -1 : 1
  }

  return left > right ? -1 : 1
}

function compareRankValues(leftValue, rightValue, direction = sortDirection.value) {
  if (leftValue === rightValue) {
    return 0
  }

  if (direction === 'asc') {
    return leftValue - rightValue
  }

  return rightValue - leftValue
}

function compareActivities(left, right) {
  let comparison = 0

  switch (sortKey.value) {
    case 'axis':
      comparison = compareTextValues(left.axeLabel, right.axeLabel)
      break
    case 'project':
      comparison = compareTextValues(left.project, right.project)
      break
    case 'activity':
      comparison = compareTextValues(left.activity, right.activity)
      break
    case 'service':
      comparison = compareTextValues(left.service, right.service)
      if (comparison === 0) {
        comparison = compareTextValues(pointFocalLabel(left), pointFocalLabel(right))
      }
      break
    case 'status':
      comparison = compareRankValues(
        statusOrder.get(left.status) ?? Number.MAX_SAFE_INTEGER,
        statusOrder.get(right.status) ?? Number.MAX_SAFE_INTEGER,
      )
      break
    case 'observation':
      comparison = compareTextValues(observationLabel(left), observationLabel(right))
      break
    case 'planning':
    default:
      comparison = compareDateValues(
        normalizedDateValue(left.plannedEnd) || normalizedDateValue(left.plannedStart),
        normalizedDateValue(right.plannedEnd) || normalizedDateValue(right.plannedStart),
      )
      if (comparison === 0) {
        comparison = compareDateValues(left.plannedStart, right.plannedStart)
      }
      break
  }

  if (comparison === 0) {
    comparison = Number(left.id ?? 0) - Number(right.id ?? 0)
  }

  return comparison
}

function positionTableTooltip(targetElement) {
  const container = tableFrameRef.value
  const tooltip = tableTooltipRef.value

  if (!container || !tooltip || !targetElement) {
    return
  }

  const containerRect = container.getBoundingClientRect()
  const targetRect = targetElement.getBoundingClientRect()
  const tooltipWidth = tooltip.offsetWidth
  const tooltipHeight = tooltip.offsetHeight
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight
  const edgePadding = 12
  const gap = 10
  const horizontalCenter = targetRect.left - containerRect.left + (targetRect.width - tooltipWidth) / 2
  const verticalCenter = targetRect.top - containerRect.top + (targetRect.height - tooltipHeight) / 2
  const availableSpaces = {
    right: containerRect.right - targetRect.right - edgePadding,
    left: targetRect.left - containerRect.left - edgePadding,
    bottom: containerRect.bottom - targetRect.bottom - edgePadding,
    top: targetRect.top - containerRect.top - edgePadding,
  }

  const placementCandidates = [
    {
      placement: 'right',
      fits: availableSpaces.right >= tooltipWidth + gap,
      score: availableSpaces.right,
      x: targetRect.right - containerRect.left + gap,
      y: verticalCenter,
    },
    {
      placement: 'left',
      fits: availableSpaces.left >= tooltipWidth + gap,
      score: availableSpaces.left,
      x: targetRect.left - containerRect.left - tooltipWidth - gap,
      y: verticalCenter,
    },
    {
      placement: 'bottom',
      fits: availableSpaces.bottom >= tooltipHeight + gap,
      score: availableSpaces.bottom,
      x: horizontalCenter,
      y: targetRect.bottom - containerRect.top + gap,
    },
    {
      placement: 'top',
      fits: availableSpaces.top >= tooltipHeight + gap,
      score: availableSpaces.top,
      x: horizontalCenter,
      y: targetRect.top - containerRect.top - tooltipHeight - gap,
    },
  ]

  placementCandidates.sort((left, right) => {
    if (left.fits !== right.fits) {
      return left.fits ? -1 : 1
    }

    return right.score - left.score
  })

  const bestPlacement = placementCandidates[0]
  let x = bestPlacement.x
  let y = bestPlacement.y

  const maxX = Math.max(edgePadding, containerWidth - tooltipWidth - edgePadding)
  const maxY = Math.max(edgePadding, containerHeight - tooltipHeight - edgePadding)

  tableTooltip.value.x = Math.round(Math.min(Math.max(edgePadding, x), maxX))
  tableTooltip.value.y = Math.round(Math.min(Math.max(edgePadding, y), maxY))
}

function showTableTooltip(event, payload) {
  const targetElement = event?.currentTarget instanceof HTMLElement ? event.currentTarget : null

  if (!payload?.title || !targetElement) {
    return
  }

  tooltipAnchorElement = targetElement

  tableTooltip.value = {
    visible: true,
    x: 0,
    y: 0,
    eyebrow: payload.eyebrow ?? '',
    title: String(payload.title),
    subtitle: payload.subtitle ? String(payload.subtitle) : '',
  }

  nextTick(() => {
    if (!tableTooltip.value.visible || tooltipAnchorElement !== targetElement) {
      return
    }

    positionTableTooltip(targetElement)
  })
}

function hideTableTooltip() {
  tooltipAnchorElement = null
  tableTooltip.value.visible = false
}

function positionActivityDetailPopover(targetElement) {
  const popoverElement = activityDetailPopoverRef.value

  if (!popoverElement || !targetElement || typeof window === 'undefined') {
    return
  }

  const targetRect = targetElement.getBoundingClientRect()
  const popoverRect = popoverElement.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const edgePadding = 16
  const gap = 12
  const horizontalCenter = targetRect.left + (targetRect.width - popoverRect.width) / 2
  const verticalCenter = targetRect.top + (targetRect.height - popoverRect.height) / 2
  const availableSpaces = {
    right: viewportWidth - targetRect.right - edgePadding,
    left: targetRect.left - edgePadding,
    bottom: viewportHeight - targetRect.bottom - edgePadding,
    top: targetRect.top - edgePadding,
  }

  const placementCandidates = [
    {
      fits: availableSpaces.right >= popoverRect.width + gap,
      score: availableSpaces.right,
      x: targetRect.right + gap,
      y: verticalCenter,
    },
    {
      fits: availableSpaces.left >= popoverRect.width + gap,
      score: availableSpaces.left,
      x: targetRect.left - popoverRect.width - gap,
      y: verticalCenter,
    },
    {
      fits: availableSpaces.bottom >= popoverRect.height + gap,
      score: availableSpaces.bottom,
      x: horizontalCenter,
      y: targetRect.bottom + gap,
    },
    {
      fits: availableSpaces.top >= popoverRect.height + gap,
      score: availableSpaces.top,
      x: horizontalCenter,
      y: targetRect.top - popoverRect.height - gap,
    },
  ]

  placementCandidates.sort((left, right) => {
    if (left.fits !== right.fits) {
      return left.fits ? -1 : 1
    }

    return right.score - left.score
  })

  const bestPlacement = placementCandidates[0]
  const maxX = Math.max(edgePadding, viewportWidth - popoverRect.width - edgePadding)
  const maxY = Math.max(edgePadding, viewportHeight - popoverRect.height - edgePadding)

  activityDetail.value.x = Math.round(Math.min(Math.max(edgePadding, bestPlacement.x), maxX))
  activityDetail.value.y = Math.round(Math.min(Math.max(edgePadding, bestPlacement.y), maxY))
}

function openActivityDetail(event, activity) {
  const targetElement = event?.currentTarget instanceof HTMLElement ? event.currentTarget : null

  if (!targetElement) {
    return
  }

  if (hasActivityDetailOpen(activity)) {
    closeActivityDetail()
    return
  }

  hideTableTooltip()
  activityDetailAnchorElement = targetElement
  activityDetail.value = {
    visible: true,
    x: 0,
    y: 0,
    activity,
  }

  nextTick(() => {
    if (!activityDetail.value.visible || activityDetail.value.activity?.id !== activity.id) {
      return
    }

    positionActivityDetailPopover(targetElement)
  })
}

function closeActivityDetail() {
  activityDetailAnchorElement = null
  activityDetail.value = {
    visible: false,
    x: 0,
    y: 0,
    activity: null,
  }
}

function handleDocumentPointerDown(event) {
  const anchorElement = activityDetailAnchorElement
  const popoverElement = activityDetailPopoverRef.value

  if (anchorElement?.contains(event.target) || popoverElement?.contains(event.target)) {
    return
  }

  closeActivityDetail()
}

function isSortableColumn(column) {
  return Boolean(column.sortable)
}

function isActiveSort(columnKey) {
  return sortKey.value === columnKey
}

function toggleSort(columnKey) {
  const column = columnDefinitions.find((item) => item.key === columnKey)

  if (!column || !column.sortable) {
    return
  }

  if (sortKey.value === columnKey) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    return
  }

  sortKey.value = columnKey
  sortDirection.value = 'asc'
}

function sortIndicator(columnKey) {
  if (sortKey.value !== columnKey) {
    return '↕'
  }

  return sortDirection.value === 'asc' ? '↑' : '↓'
}

function stickyHeaderStyle(index) {
  if (index !== 0) {
    return undefined
  }

  return {
    transform: `translateX(${bodyScrollLeft.value}px)`,
  }
}

function updateBodyScrollbarWidth() {
  const element = bodyScrollRef.value

  if (!element) {
    bodyScrollbarWidth.value = 0
    return
  }

  bodyScrollbarWidth.value = Math.max(0, element.offsetWidth - element.clientWidth)
}

function handleBodyScroll(event) {
  bodyScrollLeft.value = event.target.scrollLeft
  updateBodyScrollbarWidth()
  hideTableTooltip()
  closeActivityDetail()
}

function startResize(event, index) {
  if (!columnDefinitions[index]?.resizable) {
    return
  }

  event.preventDefault()

  resizeState = {
    index,
    startX: event.clientX,
    startWidth: columnWidths.value[index],
  }

  activeResizeIndex.value = index
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  window.addEventListener('pointermove', handleResize)
  window.addEventListener('pointerup', stopResize)
  window.addEventListener('pointercancel', stopResize)
}

function handleResize(event) {
  if (!resizeState) {
    return
  }

  const definition = columnDefinitions[resizeState.index]
  const delta = event.clientX - resizeState.startX
  const nextWidth = Math.max(definition.minWidth, resizeState.startWidth + delta)

  columnWidths.value = columnWidths.value.map((width, index) =>
    index === resizeState.index ? nextWidth : width,
  )
}

function stopResize() {
  resizeState = null
  activeResizeIndex.value = null
  document.body.style.cursor = ''
  document.body.style.userSelect = ''

  window.removeEventListener('pointermove', handleResize)
  window.removeEventListener('pointerup', stopResize)
  window.removeEventListener('pointercancel', stopResize)
}

function handleWindowResize() {
  updateBodyScrollbarWidth()

  if (tableTooltip.value.visible && tooltipAnchorElement) {
    nextTick(() => {
      positionTableTooltip(tooltipAnchorElement)
    })
  }

  if (activityDetail.value.visible && activityDetailAnchorElement) {
    nextTick(() => {
      positionActivityDetailPopover(activityDetailAnchorElement)
    })
  }
}

function applyDefaultPlanningFilter(bounds = planningDateBounds.value) {
  planningFilterStart.value = bounds.min
  planningFilterEnd.value = bounds.max
}

function resetPlanningFilter() {
  applyDefaultPlanningFilter()
}

function updateActiveStatus(value) {
  emit('update:activeStatus', value)
}

function updateActiveService(value) {
  emit('update:activeService', value)
}

function resetAllFilters() {
  resetPlanningFilter()
  delayFilter.value = ''
  updateActiveStatus('')
  updateActiveService('')
}

onMounted(() => {
  nextTick(() => {
    updateBodyScrollbarWidth()
  })

  document.addEventListener('pointerdown', handleDocumentPointerDown)
  window.addEventListener('resize', handleWindowResize)
  window.addEventListener('scroll', handleWindowResize, true)
})

onBeforeUnmount(() => {
  stopResize()
  hideTableTooltip()
  closeActivityDetail()
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  window.removeEventListener('resize', handleWindowResize)
  window.removeEventListener('scroll', handleWindowResize, true)
})

watch(
  [() => sortedActivities.value.length, tableWidth],
  () => {
    nextTick(() => {
      updateBodyScrollbarWidth()

      if (activityDetail.value.visible && activityDetailAnchorElement) {
        positionActivityDetailPopover(activityDetailAnchorElement)
      }
    })
  },
  { immediate: true },
)

watch(
  () => sortedActivities.value.some((activity) => activity.id === activityDetail.value.activity?.id),
  (isVisible) => {
    if (activityDetail.value.visible && !isVisible) {
      closeActivityDetail()
    }
  },
)

watch(
  planningDateBounds,
  (bounds, previousBounds) => {
    const shouldApplyDefaults =
      !hasInitializedPlanningFilter ||
      (!planningFilterStart.value && !planningFilterEnd.value) ||
      (planningFilterStart.value === (previousBounds?.min ?? '') &&
        planningFilterEnd.value === (previousBounds?.max ?? ''))

    if (shouldApplyDefaults) {
      applyDefaultPlanningFilter(bounds)
    }

    hasInitializedPlanningFilter = true
  },
  { immediate: true },
)

watch(planningFilterStart, (nextStart) => {
  if (planningFilterEnd.value && nextStart && nextStart > planningFilterEnd.value) {
    planningFilterEnd.value = nextStart
  }
})

watch(planningFilterEnd, (nextEnd) => {
  if (planningFilterStart.value && nextEnd && nextEnd < planningFilterStart.value) {
    planningFilterEnd.value = planningFilterStart.value
  }
})

watch(
  () => props.activities,
  (activities) => {
    if (!import.meta.env.DEV || activities.length === 0) {
      return
    }

    const hasExpectedDetailFields = activities.every(
      (activity) =>
        (Object.prototype.hasOwnProperty.call(activity, 'pointFocal') ||
          Object.prototype.hasOwnProperty.call(activity, 'point_focal')) &&
        (Object.prototype.hasOwnProperty.call(activity, 'generalObjective') ||
          Object.prototype.hasOwnProperty.call(activity, 'objectif_general')) &&
        (Object.prototype.hasOwnProperty.call(activity, 'executionStart') ||
          Object.prototype.hasOwnProperty.call(activity, 'date_debut_execution')) &&
        (Object.prototype.hasOwnProperty.call(activity, 'executionEnd') ||
          Object.prototype.hasOwnProperty.call(activity, 'date_fin_execution')),
    )

    if (hasExpectedDetailFields) {
      sessionStorage.removeItem('dashboard-activity-detail-refresh')
      return
    }

    if (sessionStorage.getItem('dashboard-activity-detail-refresh') === 'done') {
      return
    }

    sessionStorage.setItem('dashboard-activity-detail-refresh', 'done')
    window.location.reload()
  },
  { immediate: true },
)
</script>

<template>
  <section class="panel panel--table">
    <div class="panel__header panel__header--space">
      <div>
        <p class="panel__eyebrow">Feuille de route détaillée</p>
        <h2>Liste des activités</h2>
      </div>

      <div class="panel__meta">
        <span>{{ formatNumber(sortedActivities.length) }} activité(s) affichée(s)</span>
      </div>
    </div>

    <div v-if="hasSourceActivities" class="planning-filter-bar">
      <div class="planning-filter-intro">
        <strong>Période planifiée</strong>
      </div>

      <label class="planning-filter-field">
        <span>Du</span>
        <RefinedDatePicker
          v-model="planningFilterStart"
          :min="planningDateBounds.min || undefined"
          :max="planningFilterEnd || planningDateBounds.max || undefined"
          placeholder="Choisir une date"
        />
      </label>

      <label class="planning-filter-field">
        <span>Au</span>
        <RefinedDatePicker
          v-model="planningFilterEnd"
          :min="planningFilterStart || planningDateBounds.min || undefined"
          :max="planningDateBounds.max || undefined"
          placeholder="Choisir une date"
        />
      </label>

      <label class="planning-filter-field">
        <span>État</span>
        <RefinedSelect
          :model-value="props.activeStatus"
          :options="statusFilterOptions"
          placeholder="Tous les états"
          @update:model-value="updateActiveStatus"
        />
      </label>

      <label class="planning-filter-field">
        <span>Situation</span>
        <RefinedSelect
          v-model="delayFilter"
          :options="situationFilterOptions"
          placeholder="Toutes les activités"
        />
      </label>

      <label class="planning-filter-field">
        <span>Service responsable</span>
        <RefinedSelect
          :model-value="props.activeService"
          :options="serviceFilterOptions"
          placeholder="Tous les services"
          @update:model-value="updateActiveService"
        />
      </label>

      <button
        v-if="isPlanningFilterModified || hasDelayFilter || hasSharedFilters"
        type="button"
        class="planning-filter-reset"
        @click="resetAllFilters"
      >
        Réinitialiser
      </button>
    </div>

    <div v-if="hasDisplayedActivities" ref="tableFrameRef" class="table-frame">
      <div class="table-header-wrap" :style="{ paddingRight: `${bodyScrollbarWidth}px` }">
        <div
          class="table-header-inner"
          :style="{
            width: `${tableWidth}px`,
            transform: `translateX(-${bodyScrollLeft}px)`,
          }"
        >
          <table class="activities-table activities-table--header">
            <colgroup>
              <col
                v-for="(column, index) in columnDefinitions"
                :key="column.key"
                :style="{ width: `${columnWidths[index]}px` }"
              />
            </colgroup>

            <thead>
              <tr>
                <th
                  v-for="(column, index) in columnDefinitions"
                  :key="column.key"
                  :class="{ 'table-cell--sticky': index === 0 }"
                  :style="stickyHeaderStyle(index)"
                >
                  <div
                    class="table-head"
                    :class="{ 'table-head--sortable': isSortableColumn(column) }"
                  >
                    <button
                      v-if="isSortableColumn(column)"
                      type="button"
                      class="table-sort-button"
                      :class="{ 'table-sort-button--active': isActiveSort(column.key) }"
                      @click="toggleSort(column.key)"
                    >
                      <span>{{ column.label }}</span>
                      <span
                        class="table-sort-indicator"
                        :class="{ 'table-sort-indicator--active': isActiveSort(column.key) }"
                      >
                        {{ sortIndicator(column.key) }}
                      </span>
                    </button>

                    <span v-else>{{ column.label }}</span>
                  </div>

                  <button
                    v-if="column.resizable"
                    type="button"
                    class="table-resizer"
                    :class="{ 'table-resizer--active': activeResizeIndex === index }"
                    :aria-label="`Redimensionner la colonne ${column.label}`"
                    @pointerdown="startResize($event, index)"
                  />
                </th>
              </tr>
            </thead>
          </table>
        </div>
      </div>

      <div ref="bodyScrollRef" class="table-body-wrap" @scroll="handleBodyScroll">
        <table class="activities-table" :style="{ width: `${tableWidth}px` }">
          <colgroup>
            <col
              v-for="(column, index) in columnDefinitions"
              :key="column.key"
              :style="{ width: `${columnWidths[index]}px` }"
            />
          </colgroup>

          <tbody>
            <tr
              v-for="(activity, index) in sortedActivities"
              :key="activity.id"
              class="table-row--interactive"
              :class="{ 'table-row--active': hasActivityDetailOpen(activity) }"
              @click="openActivityDetail($event, activity)"
            >
              <td class="table-cell--sticky">{{ index + 1 }}</td>
              <td>
                <div
                  class="table-tooltip-target"
                  @mouseenter="showTableTooltip($event, { eyebrow: 'Axe stratégique', title: activity.axeLabel })"
                  @mouseleave="hideTableTooltip"
                >
                  <div class="table-text table-text--strong table-text--axis">
                    {{ clampText(activity.axeLabel, 72) }}
                  </div>
                </div>
              </td>
              <td>
                <div
                  class="table-tooltip-target"
                  @mouseenter="showTableTooltip($event, { eyebrow: 'Projet', title: activity.project })"
                  @mouseleave="hideTableTooltip"
                >
                  <div class="table-text table-text--project">
                    {{ clampText(activity.project, 70) }}
                  </div>
                </div>
              </td>
              <td>
                <div
                  class="table-tooltip-target"
                  @mouseenter="showTableTooltip($event, { eyebrow: 'Activité', title: activity.activity })"
                  @mouseleave="hideTableTooltip"
                >
                  <div class="table-text table-text--activity">
                    {{ clampText(activity.activity, 150) }}
                  </div>
                </div>
              </td>
              <td>
                <div
                  class="service-pill table-tooltip-target"
                  @mouseenter="
                    showTableTooltip($event, {
                      eyebrow: 'Service / Responsable',
                      title: activity.service,
                      subtitle: `Point focal : ${pointFocalLabel(activity)}`,
                    })
                  "
                  @mouseleave="hideTableTooltip"
                >
                  <span class="service-pill__avatar">{{ initials(activity.service) }}</span>
                  <div class="service-pill__content">
                    <strong>{{ activity.service }}</strong>
                    <div class="service-pill__secondary">
                      {{ pointFocalLabel(activity) }}
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <div class="planning-lines">
                  <div class="planning-line">
                    <span class="planning-line__label">Du</span>
                    <span class="planning-line__value">{{ formatDate(activity.plannedStart) }}</span>
                  </div>
                  <div class="planning-line">
                    <span class="planning-line__label">Au</span>
                    <span class="planning-line__value">{{ formatDate(activity.plannedEnd) }}</span>
                  </div>
                </div>
                <small class="table-subtext">{{ formatCurrency(activity.plannedBudget) }} prévus</small>
              </td>
              <td class="status-cell">
                <span
                  class="status-badge"
                  :style="{
                    background: getStatusLegendSoftColor(activity.status),
                    color: getStatusLegendColor(activity.status),
                    '--status-badge-accent': getStatusLegendColor(activity.status),
                  }"
                >
                  <span class="status-badge__dot" />
                  <span class="status-badge__label">{{ activity.status }}</span>
                </span>
              </td>
              <td class="observation-cell">
                <div
                  v-if="observationLabel(activity)"
                  class="table-text table-text--observation table-tooltip-target"
                  @mouseenter="showTableTooltip($event, { eyebrow: 'Observation', title: observationLabel(activity) })"
                  @mouseleave="hideTableTooltip"
                >
                  {{ clampText(observationLabel(activity), 160) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        v-if="tableTooltip.visible"
        ref="tableTooltipRef"
        class="table-tooltip-floating"
        :style="{
          left: `${tableTooltip.x}px`,
          top: `${tableTooltip.y}px`,
        }"
      >
        <span v-if="tableTooltip.eyebrow" class="table-tooltip-floating__eyebrow">
          {{ tableTooltip.eyebrow }}
        </span>
        <strong class="table-tooltip-floating__title">{{ tableTooltip.title }}</strong>
        <div v-if="tableTooltip.subtitle" class="table-tooltip-floating__subtitle">
          {{ tableTooltip.subtitle }}
        </div>
      </div>
    </div>

    <div v-else class="empty-table">
      <h3>{{ hasSourceActivities ? 'Aucune activité sur cette période' : 'Aucune activité disponible' }}</h3>
      <p>
        {{
          hasSourceActivities
            ? 'Ajuste la période planifiée ou réinitialise le filtre pour revoir la liste complète.'
            : "Les activités apparaîtront ici dès qu'elles seront renseignées."
        }}
      </p>
    </div>

    <Teleport to="body">
      <transition name="activity-detail-fade">
        <div
          v-if="activityDetail.visible && activityDetail.activity"
          ref="activityDetailPopoverRef"
          class="activity-detail-popover"
          :style="{
            left: `${activityDetail.x}px`,
            top: `${activityDetail.y}px`,
          }"
        >
          <div class="activity-detail-popover__header">
            <div class="activity-detail-popover__title-block">
              <span class="activity-detail-popover__eyebrow">Activité</span>
              <strong class="activity-detail-popover__title">
                {{ activityDetail.activity.activity }}
              </strong>
            </div>

            <button
              type="button"
              class="activity-detail-popover__close"
              @click="closeActivityDetail"
            >
              Fermer
            </button>
          </div>

          <div class="activity-detail-popover__grid">
            <div class="activity-detail-popover__item activity-detail-popover__item--wide">
              <span class="activity-detail-popover__label">Objectif général</span>
              <strong class="activity-detail-popover__value activity-detail-popover__value--multiline">
                {{ generalObjectiveLabel(activityDetail.activity) }}
              </strong>
            </div>

            <div class="activity-detail-popover__item">
              <span class="activity-detail-popover__label">Point focal</span>
              <strong class="activity-detail-popover__value">
                {{ pointFocalLabel(activityDetail.activity) }}
              </strong>
            </div>

            <div class="activity-detail-popover__item">
              <span class="activity-detail-popover__label">État</span>
              <span
                class="status-badge status-badge--detail"
                :style="{
                  background: getStatusLegendSoftColor(activityDetail.activity.status),
                  color: getStatusLegendColor(activityDetail.activity.status),
                  '--status-badge-accent': getStatusLegendColor(activityDetail.activity.status),
                }"
              >
                <span class="status-badge__dot" />
                <span class="status-badge__label">{{ activityDetail.activity.status }}</span>
              </span>
            </div>

            <div
              v-if="executionStartValue(activityDetail.activity)"
              class="activity-detail-popover__item"
            >
              <span class="activity-detail-popover__label">Début d'exécution</span>
              <strong class="activity-detail-popover__value">
                {{ formatDate(executionStartValue(activityDetail.activity)) }}
              </strong>
            </div>

            <div
              v-if="executionEndValue(activityDetail.activity)"
              class="activity-detail-popover__item"
            >
              <span class="activity-detail-popover__label">Fin d'exécution</span>
              <strong class="activity-detail-popover__value">
                {{ formatDate(executionEndValue(activityDetail.activity)) }}
              </strong>
            </div>

            <div class="activity-detail-popover__item">
              <span class="activity-detail-popover__label">Montant dépensé</span>
              <strong class="activity-detail-popover__value">
                {{ formatCurrency(activityDetail.activity.spentBudget) }}
              </strong>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </section>
</template>
