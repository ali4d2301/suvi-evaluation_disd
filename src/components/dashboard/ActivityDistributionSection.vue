<script setup>
import { computed, ref } from 'vue'

import { clampText, formatNumber, formatPercent } from '../../utils/dashboardFormatters'
import { getStatusLegendColor, getStatusLegendSoftColor } from '../../utils/dashboardPresentation'

const props = defineProps({
  statusBreakdown: {
    type: Array,
    required: true,
  },
  serviceStatusBreakdown: {
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
})

const emit = defineEmits(['update:activeStatus', 'update:activeService'])
const distributionPanelRef = ref(null)
const chartTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  eyebrow: '',
  title: '',
  subtitle: '',
  accent: '#3187ff',
  softAccent: 'rgba(49, 135, 255, 0.14)',
  lines: [],
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

function getChartStatusColor(label) {
  return getStatusLegendColor(label)
}

function getChartStatusSoftColor(label) {
  return getStatusLegendSoftColor(label)
}

function normalizeLabel(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function toRadians(angle) {
  return (angle * Math.PI) / 180
}

function polarPoint(cx, cy, radius, angle) {
  const radians = toRadians(angle)

  return {
    x: cx + radius * Math.cos(radians),
    y: cy + radius * Math.sin(radians),
  }
}

function svgNumber(value) {
  return Number(value).toFixed(2)
}

function describeDonutSlice(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
  const outerStart = polarPoint(cx, cy, outerRadius, startAngle)
  const outerEnd = polarPoint(cx, cy, outerRadius, endAngle)
  const innerEnd = polarPoint(cx, cy, innerRadius, endAngle)
  const innerStart = polarPoint(cx, cy, innerRadius, startAngle)
  const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0

  return [
    `M ${svgNumber(outerStart.x)} ${svgNumber(outerStart.y)}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${svgNumber(outerEnd.x)} ${svgNumber(outerEnd.y)}`,
    `L ${svgNumber(innerEnd.x)} ${svgNumber(innerEnd.y)}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${svgNumber(innerStart.x)} ${svgNumber(innerStart.y)}`,
    'Z',
  ].join(' ')
}

const totalActivities = computed(() =>
  props.statusBreakdown.reduce((sum, item) => sum + Number(item.total ?? 0), 0),
)

const legendStatuses = computed(() =>
  props.statusBreakdown.map((item) => {
    const color = getChartStatusColor(item.label)

    return {
      ...item,
      total: Number(item.total ?? 0),
      percentage: Number(item.percentage ?? 0),
      color,
      softColor: getChartStatusSoftColor(item.label),
      glowColor: hexToRgba(color, 0.22),
    }
  }),
)

const selectedStatus = computed(
  () => legendStatuses.value.find((item) => item.label === props.activeStatus) ?? null,
)

const donutSegments = computed(() => {
  const total = totalActivities.value
  const centerX = 300
  const centerY = 210
  const innerRadius = 104
  const outerRadius = 176
  const gapDegrees = legendStatuses.value.filter((item) => item.total > 0).length > 1 ? 2.8 : 0
  let cursor = -90

  return legendStatuses.value
    .filter((item) => item.total > 0)
    .map((item) => {
      const sweep = total ? (item.total / total) * 360 : 0
      const startAngle = cursor + gapDegrees / 2
      const endAngle = cursor + sweep - gapDegrees / 2
      const midAngle = cursor + sweep / 2
      const lineStart = polarPoint(centerX, centerY, outerRadius + 4, midAngle)
      const lineBend = polarPoint(centerX, centerY, outerRadius + 18, midAngle)
      const direction = Math.cos(toRadians(midAngle)) >= 0 ? 1 : -1
      const connectorLength = direction === 1 ? 36 : 18
      const labelGap = direction === 1 ? 9 : 3
      const lineEndX = lineBend.x + direction * connectorLength
      const lineEndY = lineBend.y
      const labelX = lineEndX + direction * labelGap
      const labelY = lineEndY - 2
      const offsetDistance = props.activeStatus === item.label ? 8 : 0
      const offsetX = Math.cos(toRadians(midAngle)) * offsetDistance
      const offsetY = Math.sin(toRadians(midAngle)) * offsetDistance

      cursor += sweep

      return {
        ...item,
        path: describeDonutSlice(centerX, centerY, innerRadius, outerRadius, startAngle, endAngle),
        connectorPath: [
          `M ${svgNumber(lineStart.x)} ${svgNumber(lineStart.y)}`,
          `L ${svgNumber(lineBend.x)} ${svgNumber(lineBend.y)}`,
          `L ${svgNumber(lineEndX)} ${svgNumber(lineEndY)}`,
        ].join(' '),
        labelX: svgNumber(labelX),
        labelY: svgNumber(labelY),
        labelAnchor: direction === 1 ? 'start' : 'end',
        groupTransform: `translate(${svgNumber(offsetX)} ${svgNumber(offsetY)})`,
      }
    })
})

const filteredServices = computed(() =>
  props.serviceStatusBreakdown
    .map((service) => {
      const statuses = (service.statuses ?? [])
        .map((status) => {
          const total = Number(status.total ?? 0)

          return {
            ...status,
            total: props.activeStatus && status.label !== props.activeStatus ? 0 : total,
          }
        })
        .filter((status) => status.total > 0)

      const total = statuses.reduce((sum, status) => sum + status.total, 0)

      return {
        ...service,
        total,
        statuses,
      }
    })
    .filter((service) => service.total > 0)
    .sort(
      (left, right) =>
        right.total - left.total || String(left.label).localeCompare(String(right.label), 'fr-FR'),
    ),
)

const displayedTotalActivities = computed(
  () => selectedStatus.value?.total ?? totalActivities.value,
)

const displayedServiceCount = computed(() => filteredServices.value.length)

const chartMax = computed(() => {
  const maxValue = Math.max(0, ...filteredServices.value.map((item) => Number(item.total ?? 0)))

  if (maxValue <= 4) {
    return 4
  }

  return Math.ceil(maxValue / 4) * 4
})

const chartTicks = computed(() =>
  Array.from({ length: 5 }, (_, index) => {
    const value = (chartMax.value / 4) * index

    return {
      value,
      position: (index / 4) * 100,
    }
  }),
)

const chartBarsStyle = computed(() => ({
  gridTemplateColumns:
    filteredServices.value.length <= 4
      ? `repeat(${Math.max(filteredServices.value.length, 1)}, minmax(0, 1fr))`
      : `repeat(${Math.max(filteredServices.value.length, 1)}, minmax(102px, 1fr))`,
  minWidth:
    filteredServices.value.length <= 4
      ? '100%'
      : `${Math.max(filteredServices.value.length * 112, 100)}px`,
}))

const sectionMeta = computed(() => {
  if (selectedStatus.value) {
    return `${formatNumber(displayedTotalActivities.value)} activités ${selectedStatus.value.label.toLowerCase()} | ${formatNumber(displayedServiceCount.value)} services`
  }

  return `${formatNumber(displayedTotalActivities.value)} activités | ${formatNumber(displayedServiceCount.value)} services`
})

const donutCenterCaption = computed(() => {
  if (selectedStatus.value) {
    return selectedStatus.value.label
  }

  return 'Activités'
})

const donutCenterDetail = computed(() => {
  if (selectedStatus.value) {
    return `${formatPercent(selectedStatus.value.percentage)} du total`
  }

  return `${formatNumber(displayedServiceCount.value)} services`
})

const donutHint = computed(() => {
  if (selectedStatus.value) {
    return `Filtre actif : ${selectedStatus.value.label}. Cliquez à nouveau sur l'état actif pour réinitialiser.`
  }

  return "Cliquez sur un secteur ou une pastille pour filtrer l'histogramme."
})

const histogramHint = computed(() => {
  if (selectedStatus.value) {
    return `Filtre actif : ${selectedStatus.value.label}. Cliquez à nouveau sur l'état actif pour revenir à la vue globale.`
  }

  return "X : Service responsable | Y : Nbre d'activités par état"
})

function countServicesForStatus(label) {
  const normalizedLabel = normalizeLabel(label)

  return props.serviceStatusBreakdown.filter((service) =>
    (service.statuses ?? []).some(
      (status) =>
        normalizeLabel(status.label) === normalizedLabel && Number(status.total ?? 0) > 0,
    ),
  ).length
}

function resolveTooltipPosition(event, lineCount = 0, hasSubtitle = false) {
  const target = event?.currentTarget ?? event?.target ?? null
  const rect = target?.getBoundingClientRect?.()
  const panelRect = distributionPanelRef.value?.getBoundingClientRect?.() ?? null
  const clientX =
    typeof event?.clientX === 'number' ? event.clientX : (rect?.left ?? 0) + (rect?.width ?? 0) / 2
  const clientY =
    typeof event?.clientY === 'number' ? event.clientY : (rect?.top ?? 0) + (rect?.height ?? 0) / 2
  const availableWidth = panelRect?.width ?? (typeof window !== 'undefined' ? window.innerWidth : 0)
  const availableHeight = panelRect?.height ?? (typeof window !== 'undefined' ? window.innerHeight : 0)
  const tooltipWidth = 270
  const tooltipHeight = 88 + lineCount * 22 + (hasSubtitle ? 18 : 0)
  const cursorGap = 10
  const edgePadding = 10
  let x = panelRect ? clientX - panelRect.left + cursorGap : clientX + cursorGap
  let y = panelRect ? clientY - panelRect.top + cursorGap : clientY + cursorGap

  if (availableWidth && x + tooltipWidth > availableWidth - edgePadding) {
    x = panelRect
      ? clientX - panelRect.left - tooltipWidth - cursorGap
      : clientX - tooltipWidth - cursorGap
  }

  if (availableHeight && y + tooltipHeight > availableHeight - edgePadding) {
    y = panelRect
      ? clientY - panelRect.top - tooltipHeight - cursorGap
      : clientY - tooltipHeight - cursorGap
  }

  if (availableWidth) {
    x = Math.min(x, availableWidth - tooltipWidth - edgePadding)
    x = Math.max(edgePadding, x)
  }

  if (availableHeight) {
    y = Math.min(y, availableHeight - tooltipHeight - edgePadding)
    y = Math.max(edgePadding, y)
  }

  return { x, y }
}

function showChartTooltip(event, payload) {
  const position = resolveTooltipPosition(event, payload.lines?.length ?? 0, Boolean(payload.subtitle))

  chartTooltip.value = {
    visible: true,
    x: position.x,
    y: position.y,
    eyebrow: payload.eyebrow ?? '',
    title: payload.title ?? '',
    subtitle: payload.subtitle ?? '',
    accent: payload.accent ?? '#3187ff',
    softAccent: payload.softAccent ?? 'rgba(49, 135, 255, 0.14)',
    lines: payload.lines ?? [],
  }
}

function hideChartTooltip() {
  chartTooltip.value.visible = false
}

function showDonutTooltip(segment, event) {
  showChartTooltip(event, {
    eyebrow: 'État',
    title: segment.label,
    subtitle: `${formatNumber(segment.total)} activités`,
    accent: segment.color,
    softAccent: segment.softColor,
    lines: [
      { label: 'Part du total', value: formatPercent(segment.percentage) },
      { label: 'Services concernés', value: formatNumber(countServicesForStatus(segment.label)) },
    ],
  })
}

function showServiceTooltip(service, event) {
  const leadingStatus = service.statuses[0]

  showChartTooltip(event, {
    eyebrow: 'Service responsable',
    title: service.label,
    subtitle: `${formatNumber(service.total)} activités`,
    accent: leadingStatus ? getChartStatusColor(leadingStatus.label) : '#3187ff',
    softAccent: leadingStatus ? getChartStatusSoftColor(leadingStatus.label) : 'rgba(49, 135, 255, 0.14)',
    lines: service.statuses.map((status) => ({
      label: status.label,
      value: formatNumber(status.total),
    })),
  })
}

function showServiceStatusTooltip(service, status, event) {
  const share = service.total > 0 ? (Number(status.total ?? 0) / Number(service.total)) * 100 : 0

  showChartTooltip(event, {
    eyebrow: 'Service / état',
    title: status.label,
    subtitle: service.label,
    accent: getChartStatusColor(status.label),
    softAccent: getChartStatusSoftColor(status.label),
    lines: [
      { label: 'Activités', value: formatNumber(status.total) },
      { label: 'Part du service', value: formatPercent(share) },
    ],
  })
}

function selectStatus(label) {
  emit('update:activeStatus', props.activeStatus === label ? '' : label)
}

function selectDonutStatus(label, event) {
  event?.currentTarget?.blur?.()
  selectStatus(label)
}

function selectService(label) {
  emit('update:activeService', props.activeService === label ? '' : label)
}

function isFilterActive(label) {
  return props.activeStatus === label
}

function isFilterDimmed(label) {
  return Boolean(props.activeStatus) && props.activeStatus !== label
}

function isSegmentDimmed(label) {
  return Boolean(props.activeStatus) && props.activeStatus !== label
}

function isSegmentActive(label) {
  return props.activeStatus === label
}

function segmentStyle(status) {
  return {
    height: `${(Number(status.total ?? 0) / chartMax.value) * 100}%`,
    background: getChartStatusColor(status.label),
  }
}

function donutSliceStyle(segment) {
  return {
    fill: segment.color,
    filter: isSegmentActive(segment.label)
      ? `drop-shadow(0 0 18px ${segment.glowColor})`
      : `drop-shadow(0 0 10px ${segment.glowColor})`,
  }
}

</script>

<template>
  <section ref="distributionPanelRef" class="panel panel--distribution">
    <div class="panel__header panel__header--space panel__header--executive distribution-panel__header">
      <div class="distribution-panel__title">
        <h2>Vue par état et service responsable</h2>
      </div>

      <div class="panel__meta">{{ sectionMeta }}</div>
    </div>

    <div class="distribution-grid">
      <article class="distribution-card">
        <div class="distribution-card__header">
          <div>
            <h3>Répartition des états d'exécution</h3>
          </div>
          <span class="distribution-card__meta">{{ formatNumber(displayedTotalActivities) }} activités</span>
        </div>

        <p class="distribution-card__hint">{{ donutHint }}</p>

        <div class="chart-filter__legend">
          <button
            v-for="filter in legendStatuses"
            :key="filter.label"
            type="button"
            class="chart-filter__pill"
            :class="{
              'chart-filter__pill--active': isFilterActive(filter.label),
              'chart-filter__pill--dimmed': isFilterDimmed(filter.label),
            }"
            :style="{
              background: filter.softColor,
              color: filter.color,
            }"
            @click="selectStatus(filter.label)"
          >
            <span class="chart-filter__dot" :style="{ background: filter.color }" />
            <span class="chart-filter__label">{{ filter.label }}</span>
            <span class="chart-filter__value">{{ formatNumber(filter.total) }}</span>
          </button>
        </div>

        <div v-if="totalActivities > 0" class="donut-layout">
          <div class="donut-figure">
            <svg class="donut-chart" viewBox="0 0 600 420" aria-label="Répartition des états">
              <circle class="donut-chart__track" cx="300" cy="210" r="140" />
              <circle class="donut-chart__inner-ring" cx="300" cy="210" r="104" />

              <g
                v-for="segment in donutSegments"
                :key="segment.label"
                class="donut-chart__group"
                :class="{
                  'donut-chart__group--active': isSegmentActive(segment.label),
                  'donut-chart__group--dimmed': isSegmentDimmed(segment.label),
                }"
                :transform="segment.groupTransform"
              >
                <path class="donut-chart__connector" :d="segment.connectorPath" />
                <text
                  class="donut-chart__label"
                  :x="segment.labelX"
                  :y="segment.labelY"
                  :text-anchor="segment.labelAnchor"
                >
                  <tspan class="donut-chart__label-name">{{ segment.label }}</tspan>
                  <tspan class="donut-chart__label-value" :x="segment.labelX" dy="18">
                    {{ formatPercent(segment.percentage) }}
                  </tspan>
                </text>
                <path
                  class="donut-chart__slice"
                  :d="segment.path"
                  :style="donutSliceStyle(segment)"
                  role="button"
                  tabindex="0"
                  :aria-label="`${segment.label}: ${formatNumber(segment.total)}`"
                  @mouseenter="showDonutTooltip(segment, $event)"
                  @mousemove="showDonutTooltip(segment, $event)"
                  @mouseleave="hideChartTooltip"
                  @focus="showDonutTooltip(segment, $event)"
                  @blur="hideChartTooltip"
                  @click="selectDonutStatus(segment.label, $event)"
                  @keydown.enter.prevent="selectStatus(segment.label)"
                  @keydown.space.prevent="selectStatus(segment.label)"
                />
              </g>
            </svg>

            <div class="donut-card__center">
              <strong>{{ formatNumber(displayedTotalActivities) }}</strong>
              <span>{{ donutCenterCaption }}</span>
              <small>{{ donutCenterDetail }}</small>
            </div>
          </div>
        </div>

        <div v-else class="distribution-empty">
          <h3>Aucune activité à répartir</h3>
          <p>Le donut apparaîtra dès qu'au moins une activité sera disponible.</p>
        </div>
      </article>

      <article class="distribution-card">
        <div class="distribution-card__header">
          <div>
            <h3>Répartition par service</h3>
          </div>
          <span class="distribution-card__meta">{{ formatNumber(displayedServiceCount) }} services</span>
        </div>

        <p class="distribution-card__hint">{{ histogramHint }}</p>

        <div class="chart-filter__legend">
          <button
            v-for="filter in legendStatuses"
            :key="`hist-${filter.label}`"
            type="button"
            class="chart-filter__pill"
            :class="{
              'chart-filter__pill--active': isFilterActive(filter.label),
              'chart-filter__pill--dimmed': isFilterDimmed(filter.label),
            }"
            :style="{
              background: filter.softColor,
              color: filter.color,
            }"
            @click="selectStatus(filter.label)"
          >
            <span class="chart-filter__dot" :style="{ background: filter.color }" />
            <span class="chart-filter__label">{{ filter.label }}</span>
            <span class="chart-filter__value">{{ formatNumber(filter.total) }}</span>
          </button>
        </div>

        <div v-if="filteredServices.length" class="stacked-chart">
          <div class="stacked-chart__body">
              <div
                class="stacked-chart__scroller"
                :class="{ 'stacked-chart__scroller--fit': filteredServices.length <= 4 }"
              >
                <div class="stacked-chart__plot">
                <div class="stacked-chart__grid" aria-hidden="true">
                  <span
                    v-for="tick in chartTicks"
                    :key="tick.value"
                    class="stacked-chart__grid-line"
                    :style="{ bottom: `${tick.position}%` }"
                  />
                </div>

                <div class="stacked-chart__bars" :style="chartBarsStyle">
                  <div
                    v-for="service in filteredServices"
                    :key="service.label"
                    class="stacked-chart__group"
                    :class="{ 'stacked-chart__group--active': props.activeService === service.label }"
                    role="button"
                    tabindex="0"
                    :aria-label="`Filtrer le tableau sur le service ${service.label}`"
                    @mouseenter="showServiceTooltip(service, $event)"
                    @mousemove="showServiceTooltip(service, $event)"
                    @mouseleave="hideChartTooltip"
                    @click="selectService(service.label)"
                    @keydown.enter.prevent="selectService(service.label)"
                    @keydown.space.prevent="selectService(service.label)"
                  >
                    <div class="stacked-chart__value">{{ formatNumber(service.total) }}</div>

                    <div class="stacked-chart__column">
                      <div class="stacked-chart__stack">
                        <span
                          v-for="status in service.statuses"
                          :key="status.label"
                          class="stacked-chart__segment"
                          :style="segmentStyle(status)"
                          @mouseenter.stop="showServiceStatusTooltip(service, status, $event)"
                          @mousemove.stop="showServiceStatusTooltip(service, status, $event)"
                        />
                      </div>
                    </div>

                    <div class="stacked-chart__label">
                      {{ clampText(service.label, 36) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="distribution-empty">
          <h3>Aucune activité pour ce filtre</h3>
          <p>Cliquez à nouveau sur l'état actif pour réafficher tous les services.</p>
        </div>
      </article>
    </div>

    <div
      v-if="chartTooltip.visible"
      class="chart-tooltip"
      :style="{
        left: `${chartTooltip.x}px`,
        top: `${chartTooltip.y}px`,
        '--chart-tooltip-accent': chartTooltip.accent,
        '--chart-tooltip-accent-soft': chartTooltip.softAccent,
      }"
    >
      <span v-if="chartTooltip.eyebrow" class="chart-tooltip__eyebrow">{{ chartTooltip.eyebrow }}</span>

      <div class="chart-tooltip__title-row">
        <span class="chart-tooltip__dot" />
        <strong class="chart-tooltip__title">{{ chartTooltip.title }}</strong>
      </div>

      <div v-if="chartTooltip.subtitle" class="chart-tooltip__subtitle">{{ chartTooltip.subtitle }}</div>

      <div v-if="chartTooltip.lines.length" class="chart-tooltip__list">
        <div v-for="line in chartTooltip.lines" :key="`${chartTooltip.title}-${line.label}`" class="chart-tooltip__item">
          <span>{{ line.label }}</span>
          <strong>{{ line.value }}</strong>
        </div>
      </div>
    </div>
  </section>
</template>
