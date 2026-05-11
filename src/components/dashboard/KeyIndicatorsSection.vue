<script setup>
import { computed, ref, watch } from 'vue'

import DashboardStateCard from './DashboardStateCard.vue'
import { formatNumber, formatPercent } from '../../utils/dashboardFormatters'
import {
  formatIndicatorMetricValue,
  formatIndicatorTarget,
  periodicityMeta,
} from '../../utils/keyIndicatorsPresentation'

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const BREAKDOWN_META = {
  attained: {
    label: 'Atteints (>= 100%)',
    shortLabel: 'Atteints',
    rangeLabel: '(>= 100%)',
    color: '#35a853',
    colorEnd: '#58bf6f',
    soft: 'rgba(53, 168, 83, 0.16)',
  },
  on_track: {
    label: 'En bonne voie (80% - 99%)',
    shortLabel: 'En bonne voie',
    rangeLabel: '(80% - 99%)',
    color: '#98c74e',
    colorEnd: '#b1d86b',
    soft: 'rgba(152, 199, 78, 0.16)',
  },
  watch: {
    label: 'A surveiller (50% - 79%)',
    shortLabel: 'A surveiller',
    rangeLabel: '(50% - 79%)',
    color: '#f79a1f',
    colorEnd: '#ffb24c',
    soft: 'rgba(247, 154, 31, 0.16)',
  },
  alert: {
    label: 'En alerte (< 50%)',
    shortLabel: 'En alerte',
    rangeLabel: '(< 50%)',
    color: '#ea4335',
    colorEnd: '#f56a5f',
    soft: 'rgba(234, 67, 53, 0.16)',
  },
  no_target: {
    label: 'Sans cible',
    shortLabel: 'Sans cible',
    rangeLabel: '',
    color: '#8093aa',
    colorEnd: '#a3b2c3',
    soft: 'rgba(128, 147, 170, 0.16)',
  },
}

const AXIS_ACCENTS = ['#2f7be8', '#68b454', '#f79a1f', '#8f65f6', '#35b1c3', '#256ec9', '#e2619d', '#3aa374']

const emptyData = {
  summary: {
    totalIndicators: 0,
    activeAxes: 0,
    registeredAxes: 0,
    targetedAxes: 0,
    targetedIndicators: 0,
    onTargetIndicators: 0,
    belowTargetIndicators: 0,
    noTargetIndicators: 0,
    comparableIndicators: 0,
    upwardIndicators: 0,
    downwardIndicators: 0,
    stableIndicators: 0,
    initialIndicators: 0,
    positiveAxes: 0,
    negativeAxes: 0,
    balancedAxes: 0,
    latestValidPeriod: null,
    latestValidPeriodLabel: null,
    bestAxis: null,
    weakestAxis: null,
  },
  axisPerformance: [],
  indicators: [],
  signals: [],
  attainmentBreakdown: [],
  noTargetIndicators: 0,
  attainmentTimeline: [],
}

const sourceData = computed(() => props.data ?? emptyData)
const summary = computed(() => sourceData.value.summary ?? emptyData.summary)
const axisPerformance = computed(() => sourceData.value.axisPerformance ?? [])
const indicators = computed(() => sourceData.value.indicators ?? [])
const rawBreakdown = computed(() => sourceData.value.attainmentBreakdown ?? [])
const noTargetIndicators = computed(() => Number(sourceData.value.noTargetIndicators ?? 0))
const attainmentTimeline = computed(() => sourceData.value.attainmentTimeline ?? [])
const hasIndicators = computed(() => Number(summary.value.totalIndicators ?? 0) > 0)
const selectedAxisCode = ref('')
const selectedBreakdownKey = ref('')
const hoveredBreakdownKey = ref(null)
const activeBreakdownKey = computed(() => hoveredBreakdownKey.value ?? selectedBreakdownKey.value)
const openHeaderActionMenu = ref(null)
const analysisPeriodMode = ref('latest')
const selectedYear = ref('')
const selectedMonth = ref('')
const openIndicatorFilter = ref(null)
const selectedIndicatorCode = ref('')
const openSummaryControl = ref(null)
const summaryRangeByIndicator = ref({})
const summaryMethodByIndicator = ref({})
const indicatorFilterMenuPlacement = ref({
  axis: {
    direction: 'down',
    maxHeight: 292,
  },
  status: {
    direction: 'down',
    maxHeight: 292,
  },
})
const donutTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
})
const trendTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  label: '',
  value: '',
})
const indicatorHistoryTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  label: '',
  value: '',
  meta: '',
})
const indicatorColumnWidth = ref(null)
let indicatorColumnResize = null
const DONUT_STAGE_WIDTH = 560
const DONUT_STAGE_HEIGHT = 360
const DONUT_CENTER_X = 280
const DONUT_CENTER_Y = 182
const DONUT_OUTER_RADIUS = 124
const DONUT_INNER_RADIUS = 78
const FILTER_MENU_MAX_HEIGHT = 292
const FILTER_MENU_MIN_HEIGHT = 148
const FILTER_MENU_ROW_HEIGHT = 44
const FILTER_MENU_VERTICAL_MARGIN = 12
const INDICATOR_HISTORY_CHART_WIDTH = 520
const INDICATOR_HISTORY_CHART_HEIGHT = 226
const MONTH_OPTIONS = [
  { value: 1, label: 'Janvier', shortLabel: 'Janv.' },
  { value: 2, label: 'Février', shortLabel: 'Févr.' },
  { value: 3, label: 'Mars', shortLabel: 'Mars' },
  { value: 4, label: 'Avril', shortLabel: 'Avr.' },
  { value: 5, label: 'Mai', shortLabel: 'Mai' },
  { value: 6, label: 'Juin', shortLabel: 'Juin' },
  { value: 7, label: 'Juillet', shortLabel: 'Juil.' },
  { value: 8, label: 'Août', shortLabel: 'Août' },
  { value: 9, label: 'Septembre', shortLabel: 'Sept.' },
  { value: 10, label: 'Octobre', shortLabel: 'Oct.' },
  { value: 11, label: 'Novembre', shortLabel: 'Nov.' },
  { value: 12, label: 'Décembre', shortLabel: 'Déc.' },
]

const DONUT_LABEL_LAYOUT = {
  attained: {
    labelX: 420,
    labelY: 100,
    anchor: 'start',
    anchorAngle: 56,
    bendX: 394,
    bendY: 96,
    endX: 412,
    endY: 96,
  },
  on_track: {
    labelX: 402,
    labelY: 276,
    anchor: 'start',
    anchorAngle: 148,
    bendX: 360,
    bendY: 306,
    endX: 394,
    endY: 288,
  },
  watch: {
    labelX: 138,
    labelY: 282,
    anchor: 'end',
    anchorAngle: 202,
    bendX: 208,
    bendY: 304,
    endX: 146,
    endY: 292,
  },
  alert: {
    labelX: 158,
    labelY: 84,
    anchor: 'end',
    anchorAngle: 308,
    bendX: 170,
    bendY: 104,
    endX: 166,
    endY: 94,
  },
}

function axisOrderValue(code) {
  const match = String(code ?? '').match(/(\d+)$/)
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER
}

function extractYear() {
  const candidate = `${summary.value.latestValidPeriodLabel ?? ''} ${summary.value.latestValidPeriod ?? ''}`
  const match = candidate.match(/\b(20\d{2})\b/)

  if (match) {
    return match[1]
  }

  return String(new Date().getUTCFullYear())
}

function extractYearFromText(value) {
  const match = String(value ?? '').match(/\b(20\d{2})\b/)

  return match?.[1] ?? ''
}

function parsePeriodParts(value) {
  const match = String(value ?? '').match(/^(\d{4})-(\d{2})-(\d{2})/)

  if (!match) {
    return null
  }

  return {
    year: Number(match[1]),
    month: Number(match[2]),
    day: Number(match[3]),
    order: Number(match[1]) * 100 + Number(match[2]),
  }
}

function monthLabel(month, variant = 'shortLabel') {
  return MONTH_OPTIONS.find((item) => item.value === Number(month))?.[variant] ?? String(month)
}

function normalizePeriodicityName(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function targetMonthForPeriodicity(periodicity, month) {
  const normalized = normalizePeriodicityName(periodicity)
  const numericMonth = Number(month)

  if (normalized.includes('trimestrielle')) {
    return Math.ceil(numericMonth / 3) * 3
  }

  if (normalized.includes('semestrielle')) {
    return numericMonth <= 6 ? 6 : 12
  }

  if (normalized.includes('annuelle')) {
    return 12
  }

  return numericMonth
}

function buildPeriodLabel(periodicity, year, month) {
  const normalized = normalizePeriodicityName(periodicity)
  const numericMonth = Number(month)

  if (normalized.includes('trimestrielle')) {
    return `T${Math.ceil(numericMonth / 3)} ${year}`
  }

  if (normalized.includes('semestrielle')) {
    return `S${numericMonth <= 6 ? 1 : 2} ${year}`
  }

  if (normalized.includes('annuelle')) {
    return String(year)
  }

  return `${monthLabel(numericMonth)} ${year}`
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, Number(value) || 0))
}

function average(values) {
  if (!values.length) {
    return null
  }

  const total = values.reduce((sum, value) => sum + Number(value || 0), 0)
  return Math.round((total / values.length) * 10) / 10
}

function formatRate(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }

  return formatPercent(value)
}

function compactRangeLabel(value) {
  return String(value ?? '')
    .replace(/\s+/g, '')
    .replace('>=', '>= ')
}

function statusKeyFromRate(value) {
  if (value === null || value === undefined) {
    return 'no_target'
  }

  if (value >= 100) {
    return 'attained'
  }

  if (value >= 80) {
    return 'on_track'
  }

  if (value >= 50) {
    return 'watch'
  }

  return 'alert'
}

function statusMetaFromRate(value) {
  const key = statusKeyFromRate(value)

  return {
    key,
    ...BREAKDOWN_META[key],
  }
}

function summaryCardStyle(card) {
  return {
    '--summary-accent': card.color,
    '--summary-accent-soft': card.soft,
    '--summary-accent-end': card.colorEnd,
  }
}

function progressFillStyle(value, tone) {
  return {
    width: `${clampPercent(value)}%`,
    background: `linear-gradient(90deg, ${tone.color}, ${tone.colorEnd})`,
  }
}

function rateGaugeStyle(value, tone) {
  const arcLength = 100
  const safeValue = clampPercent(value)

  return {
    '--rate-gauge-dash': `${(safeValue / 100) * arcLength} ${arcLength}`,
    '--rate-gauge-color': tone.color,
    '--rate-gauge-color-end': tone.colorEnd,
  }
}

function indicatorPeriodicity(indicator) {
  return periodicityMeta[indicator?.periodicity] ?? periodicityMeta.Mensuelle
}

const availableYearOptions = computed(() => {
  const years = new Set([extractYear()])

  indicators.value.forEach((indicator) => {
    const latestYear = extractYearFromText(`${indicator.latestPeriodLabel ?? ''} ${indicator.latestPeriod ?? ''}`)

    if (latestYear) {
      years.add(latestYear)
    }

    ;(indicator.history ?? []).forEach((entry) => {
      const historyYear = extractYearFromText(`${entry.periodLabel ?? ''} ${entry.period ?? ''}`)

      if (historyYear) {
        years.add(historyYear)
      }
    })
  })

  return [...years]
    .filter(Boolean)
    .sort((left, right) => Number(right) - Number(left))
    .map((year) => ({
      value: year,
      label: `Année ${year}`,
    }))
})

function defaultMonthForYear(year) {
  const targetYear = Number(year || extractYear())
  const months = []

  indicators.value.forEach((indicator) => {
    ;(indicator.history ?? []).forEach((entry) => {
      const period = parsePeriodParts(entry.period)

      if (period?.year === targetYear && entry.value !== null && entry.value !== undefined) {
        months.push(period.month)
      }
    })
  })

  if (months.length) {
    return String(Math.max(...months))
  }

  const latestPeriod = parsePeriodParts(summary.value.latestValidPeriod)

  if (latestPeriod?.year === targetYear) {
    return String(latestPeriod.month)
  }

  return '12'
}

const analysisYear = computed(() => selectedYear.value || extractYear())
const analysisMonth = computed(() => selectedMonth.value || defaultMonthForYear(analysisYear.value))
const displayYear = computed(() => analysisYear.value)
const selectedMonthLabel = computed(() => monthLabel(analysisMonth.value, 'label'))
const analysisPeriodLabel = computed(() =>
  analysisPeriodMode.value === 'latest'
    ? 'Dernière période disponible'
    : `${selectedMonthLabel.value} ${analysisYear.value}`,
)

function comparePeriodEntries(left, right) {
  return (parsePeriodParts(left?.period)?.order ?? 0) - (parsePeriodParts(right?.period)?.order ?? 0)
}

function attainmentRateForValue(value, targetValue) {
  if (value === null || value === undefined || [null, undefined, 0].includes(targetValue)) {
    return null
  }

  return Math.round(Math.min((Number(value) / Number(targetValue)) * 100, 100) * 10) / 10
}

function hasOwnValue(source, key) {
  return Object.prototype.hasOwnProperty.call(source ?? {}, key)
}

function targetValueForYear(indicator, year) {
  const yearTargets = indicator?.yearTargets ?? []
  const target = yearTargets.find((item) => Number(item.year) === Number(year))

  if (target && hasOwnValue(target, 'targetValue')) {
    return target.targetValue ?? null
  }

  if (yearTargets.length) {
    return null
  }

  return indicator?.targetValue ?? null
}

function targetGapForValue(value, targetValue) {
  if (value === null || value === undefined || targetValue === null || targetValue === undefined) {
    return null
  }

  return Math.round((Number(value) - Number(targetValue)) * 10000) / 10000
}

function targetGapRatioForValue(value, targetValue) {
  if (value === null || value === undefined || [null, undefined, 0].includes(targetValue)) {
    return null
  }

  return Math.round(((Number(value) - Number(targetValue)) / Math.abs(Number(targetValue))) * 1000) / 10
}

function selectedEntryForIndicator(indicator, year, month) {
  const targetMonth = targetMonthForPeriodicity(indicator.periodicity, month)
  const targetOrder = Number(year) * 100 + targetMonth
  const history = [...(indicator.history ?? [])]
    .filter((entry) => entry.value !== null && entry.value !== undefined)
    .sort(comparePeriodEntries)
  const selectedEntry = history.find((entry) => parsePeriodParts(entry.period)?.order === targetOrder) ?? null
  const previousEntry = history
    .filter((entry) => (parsePeriodParts(entry.period)?.order ?? 0) < targetOrder)
    .at(-1) ?? null

  return {
    selectedEntry,
    previousEntry,
    targetMonth,
    targetOrder,
  }
}

function buildAnalysisIndicator(indicator) {
  if (analysisPeriodMode.value === 'latest') {
    return indicator
  }

  const year = Number(analysisYear.value)
  const month = Number(analysisMonth.value)
  const { selectedEntry, previousEntry, targetMonth, targetOrder } = selectedEntryForIndicator(indicator, year, month)
  const latestValue = selectedEntry?.value ?? null
  const previousValue = previousEntry?.value ?? null
  const targetValue = selectedEntry && hasOwnValue(selectedEntry, 'targetValue')
    ? selectedEntry.targetValue
    : targetValueForYear(indicator, year)
  const attainmentRate = selectedEntry && hasOwnValue(selectedEntry, 'attainmentRate')
    ? selectedEntry.attainmentRate
    : attainmentRateForValue(latestValue, targetValue)
  const targetGap = selectedEntry && hasOwnValue(selectedEntry, 'targetGap')
    ? selectedEntry.targetGap
    : targetGapForValue(latestValue, targetValue)
  const targetGapRatio = selectedEntry && hasOwnValue(selectedEntry, 'targetGapRatio')
    ? selectedEntry.targetGapRatio
    : targetGapRatioForValue(latestValue, targetValue)
  const filteredHistory = (indicator.history ?? [])
    .filter((entry) => {
      const period = parsePeriodParts(entry.period)
      return period && period.order <= targetOrder
    })
  const delta = latestValue !== null && previousValue !== null
    ? Number(latestValue) - Number(previousValue)
    : null
  const deltaRatio = delta !== null && ![null, undefined, 0].includes(previousValue)
    ? Math.round((delta / Math.abs(Number(previousValue))) * 1000) / 10
    : null

  return {
    ...indicator,
    latestPeriod: selectedEntry?.period ?? `${year}-${String(targetMonth).padStart(2, '0')}-01`,
    latestPeriodLabel: selectedEntry?.periodLabel ?? buildPeriodLabel(indicator.periodicity, year, targetMonth),
    latestValue,
    previousPeriod: previousEntry?.period ?? null,
    previousPeriodLabel: previousEntry?.periodLabel ?? null,
    previousValue,
    delta: delta !== null ? Math.round(delta * 10000) / 10000 : null,
    deltaRatio,
    targetStatus: attainmentRate === null ? 'no_target' : attainmentRate >= 100 ? 'on_target' : 'below_target',
    targetGap,
    targetGapRatio,
    attainmentRate,
    history: filteredHistory,
    analysisTargetPeriodLabel: buildPeriodLabel(indicator.periodicity, year, targetMonth),
  }
}

const analysisIndicators = computed(() =>
  indicators.value.map((indicator) => buildAnalysisIndicator(indicator)),
)

const targetedIndicators = computed(() =>
  analysisIndicators.value.filter((indicator) => indicator.attainmentRate !== null && indicator.attainmentRate !== undefined),
)

const globalAverageAttainment = computed(() =>
  average(targetedIndicators.value.map((indicator) => Number(indicator.attainmentRate))),
)

const targetableIndicators = computed(() =>
  analysisIndicators.value.filter((indicator) => indicator.targetValue !== null && indicator.targetValue !== undefined),
)

const analysisSummary = computed(() => {
  const targetable = targetableIndicators.value
  const rated = targetedIndicators.value

  return {
    totalIndicators: analysisIndicators.value.length,
    targetedIndicators: targetable.length,
    activeAxes: new Set(analysisIndicators.value.map((indicator) => String(indicator.axisCode ?? ''))).size,
    onTargetIndicators: rated.filter((indicator) => indicator.attainmentRate >= 100).length,
    alertIndicators: rated.filter((indicator) => indicator.attainmentRate < 50).length,
  }
})

const breakdown = computed(() => {
  const totals = {
    attained: 0,
    on_track: 0,
    watch: 0,
    alert: 0,
  }

  targetedIndicators.value.forEach((indicator) => {
    const key = statusKeyFromRate(indicator.attainmentRate)

    if (Object.hasOwn(totals, key)) {
      totals[key] += 1
    }
  })

  const denominator = Math.max(analysisSummary.value.targetedIndicators, 1)

  return ['attained', 'on_track', 'watch', 'alert'].map((key) => ({
    ...BREAKDOWN_META[key],
    key,
    total: totals[key],
    percentage: Math.round((totals[key] / denominator) * 1000) / 10,
  }))
})

const targetedBreakdownTotal = computed(() =>
  analysisSummary.value.targetedIndicators,
)

const ratedBreakdownTotal = computed(() =>
  breakdown.value.reduce((total, item) => total + Number(item.total ?? 0), 0),
)

const alertCount = computed(() => breakdown.value.find((item) => item.key === 'alert')?.total ?? 0)

const displayedAttainmentTimeline = computed(() => {
  if (analysisPeriodMode.value === 'latest') {
    return attainmentTimeline.value
  }

  const cutoffOrder = Number(analysisYear.value) * 100 + Number(analysisMonth.value)

  return attainmentTimeline.value.filter((item) => {
    const period = parsePeriodParts(item.period)
    return period && period.order <= cutoffOrder
  })
})

function polarPoint(centerX, centerY, radius, angle) {
  const radians = ((angle - 90) * Math.PI) / 180

  return {
    x: centerX + Math.cos(radians) * radius,
    y: centerY + Math.sin(radians) * radius,
  }
}

function describeDonutSegmentPath(centerX, centerY, outerRadius, innerRadius, startAngle, endAngle) {
  const outerStart = polarPoint(centerX, centerY, outerRadius, startAngle)
  const outerEnd = polarPoint(centerX, centerY, outerRadius, endAngle)
  const innerEnd = polarPoint(centerX, centerY, innerRadius, endAngle)
  const innerStart = polarPoint(centerX, centerY, innerRadius, startAngle)
  const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0

  return [
    `M ${outerStart.x.toFixed(2)} ${outerStart.y.toFixed(2)}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerEnd.x.toFixed(2)} ${outerEnd.y.toFixed(2)}`,
    `L ${innerEnd.x.toFixed(2)} ${innerEnd.y.toFixed(2)}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerStart.x.toFixed(2)} ${innerStart.y.toFixed(2)}`,
    'Z',
  ].join(' ')
}

const donutSegments = computed(() => {
  const total = ratedBreakdownTotal.value

  if (!total) {
    return []
  }

  let cursorAngle = 2

  return breakdown.value
    .filter((item) => Number(item.total ?? 0) > 0)
    .map((item, index, items) => {
      const share = Number(item.total ?? 0) / total
      const spanAngle = share * 360
      const gapAngle = items.length > 1 ? 3.5 : 0
      const visibleAngle = Math.max(spanAngle - gapAngle, 1)
      const startAngle = cursorAngle + gapAngle / 2
      const endAngle = startAngle + visibleAngle
      const midAngle = startAngle + visibleAngle / 2
      const path = describeDonutSegmentPath(
        DONUT_CENTER_X,
        DONUT_CENTER_Y,
        DONUT_OUTER_RADIUS,
        DONUT_INNER_RADIUS,
        startAngle,
        endAngle,
      )
      const layout = DONUT_LABEL_LAYOUT[item.key] ?? {
        labelX: DONUT_CENTER_X + 30,
        labelY: DONUT_CENTER_Y,
        anchor: Math.cos((midAngle * Math.PI) / 180) >= 0 ? 'start' : 'end',
      }
      const connectorAngle = layout.anchorAngle ?? midAngle
      const outerAnchor = polarPoint(DONUT_CENTER_X, DONUT_CENTER_Y, DONUT_OUTER_RADIUS + 8, connectorAngle)
      const bendX = layout.bendX ?? outerAnchor.x
      const bendY = layout.bendY ?? outerAnchor.y
      const endX = layout.endX ?? (layout.anchor === 'start' ? layout.labelX - 10 : layout.labelX + 10)
      const endY = layout.endY ?? layout.labelY - 8

      cursorAngle += spanAngle

      return {
        ...item,
        share,
        criterionLabel: compactRangeLabel(item.rangeLabel),
        startAngle,
        endAngle,
        midAngle,
        path,
        opacity:
          activeBreakdownKey.value && activeBreakdownKey.value !== item.key
            ? selectedBreakdownKey.value
              ? 0.34
              : 0.62
            : 1,
        connectorPath: `M ${outerAnchor.x.toFixed(2)} ${outerAnchor.y.toFixed(2)} L ${bendX.toFixed(2)} ${bendY.toFixed(2)} L ${endX.toFixed(2)} ${endY.toFixed(2)}`,
        labelX: layout.labelX,
        labelY: layout.labelY,
        labelAnchor: layout.anchor,
      }
    })
})

const activeBreakdown = computed(() =>
  donutSegments.value.find((item) => item.key === activeBreakdownKey.value) ?? null,
)

const donutCenterStyle = computed(() => ({
  left: `${((DONUT_CENTER_X - DONUT_INNER_RADIUS) / DONUT_STAGE_WIDTH) * 100}%`,
  top: `${((DONUT_CENTER_Y - DONUT_INNER_RADIUS) / DONUT_STAGE_HEIGHT) * 100}%`,
  width: `${((DONUT_INNER_RADIUS * 2) / DONUT_STAGE_WIDTH) * 100}%`,
  height: `${((DONUT_INNER_RADIUS * 2) / DONUT_STAGE_HEIGHT) * 100}%`,
}))

function donutTooltipStyle(item) {
  return {
    '--donut-tooltip-accent': item.color,
    '--donut-tooltip-soft': item.soft,
  }
}

function activateBreakdown(key) {
  hoveredBreakdownKey.value = key
}

function positionDonutTooltip(event) {
  const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : DONUT_STAGE_WIDTH
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : DONUT_STAGE_HEIGHT

  donutTooltip.value = {
    visible: true,
    x: Math.min(event.clientX + 14, viewportWidth - 96),
    y: Math.min(event.clientY + 14, viewportHeight - 54),
  }
}

function showDonutTooltip(key, event) {
  activateBreakdown(key)
  positionDonutTooltip(event)
}

function moveDonutTooltip(event) {
  if (donutTooltip.value.visible) {
    positionDonutTooltip(event)
  }
}

function clearBreakdown(key) {
  if (!key || hoveredBreakdownKey.value === key) {
    hoveredBreakdownKey.value = null
  }
}

function hideDonutTooltip(key) {
  clearBreakdown(key)
  donutTooltip.value.visible = false
}

function toggleBreakdown(key) {
  selectedBreakdownKey.value = selectedBreakdownKey.value === key ? '' : key
  hoveredBreakdownKey.value = key
}

function positionTrendTooltip(point, event) {
  const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 620
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 282

  trendTooltip.value = {
    visible: true,
    x: Math.min(event.clientX + 12, viewportWidth - 130),
    y: Math.min(event.clientY + 12, viewportHeight - 72),
    label: point.label,
    value: point.valueLabel,
  }
}

function showTrendTooltip(point, event) {
  positionTrendTooltip(point, event)
}

function moveTrendTooltip(point, event) {
  if (trendTooltip.value.visible) {
    positionTrendTooltip(point, event)
  }
}

function hideTrendTooltip() {
  trendTooltip.value.visible = false
}

function positionIndicatorHistoryTooltip(point, event) {
  const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 520
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 226

  indicatorHistoryTooltip.value = {
    visible: true,
    x: Math.min(event.clientX + 12, viewportWidth - 150),
    y: Math.min(event.clientY + 12, viewportHeight - 72),
    label: point.label,
    value: point.valueLabel,
    meta: point.tooltipMeta ?? '',
  }
}

function nearestIndicatorHistoryPoint(chart, event) {
  const target = event.currentTarget

  if (!chart?.points?.length || !target?.getBoundingClientRect) {
    return null
  }

  const rect = target.getBoundingClientRect()
  const chartX = ((event.clientX - rect.left) / Math.max(rect.width, 1)) * chart.width

  return chart.points.reduce((closest, point) => {
    const currentDistance = Math.abs(point.x - chartX)
    const closestDistance = Math.abs(closest.x - chartX)

    return currentDistance < closestDistance ? point : closest
  }, chart.points[0])
}

function showIndicatorHistoryCanvasTooltip(chart, event) {
  const point = nearestIndicatorHistoryPoint(chart, event)

  if (point) {
    positionIndicatorHistoryTooltip(point, event)
  }
}

function moveIndicatorHistoryCanvasTooltip(chart, event) {
  const point = nearestIndicatorHistoryPoint(chart, event)

  if (point) {
    positionIndicatorHistoryTooltip(point, event)
  }
}

function showIndicatorHistoryTooltip(point, event) {
  positionIndicatorHistoryTooltip(point, event)
}

function moveIndicatorHistoryTooltip(point, event) {
  if (indicatorHistoryTooltip.value.visible) {
    positionIndicatorHistoryTooltip(point, event)
  }
}

function hideIndicatorHistoryTooltip() {
  indicatorHistoryTooltip.value.visible = false
}

const axisRateMap = computed(() => {
  const grouped = new Map()

  targetedIndicators.value.forEach((indicator) => {
    const axisCode = String(indicator.axisCode ?? '')
    if (!grouped.has(axisCode)) {
      grouped.set(axisCode, [])
    }

    grouped.get(axisCode).push(Number(indicator.attainmentRate))
  })

  return grouped
})

const axisRows = computed(() =>
  [...axisPerformance.value]
    .sort(
      (left, right) =>
        axisOrderValue(left.code) - axisOrderValue(right.code) ||
        String(left.label).localeCompare(String(right.label), 'fr-FR'),
    )
    .map((axis, index) => {
      const rates = axisRateMap.value.get(String(axis.code)) ?? []
      const averageRate = average(rates)

      return {
        ...axis,
        order: index + 1,
        averageRate,
        status: statusMetaFromRate(averageRate),
        accent: AXIS_ACCENTS[index % AXIS_ACCENTS.length],
      }
    }),
)

const axisAccentMap = computed(() => {
  const map = new Map()

  axisRows.value.forEach((axis) => {
    map.set(String(axis.code), axis.accent)
  })

  return map
})

const axisLabelMap = computed(() => {
  const map = new Map()

  axisRows.value.forEach((axis) => {
    map.set(String(axis.code), axis.label)
  })

  return map
})

const hasActiveIndicatorFilters = computed(() =>
  Boolean(selectedAxisCode.value || selectedBreakdownKey.value),
)

const axisFilterOptions = computed(() => [
  { value: '', label: 'Tous les axes' },
  ...axisRows.value.map((axis) => ({
    value: String(axis.code),
    label: axis.label,
    accent: axis.accent,
  })),
])

const statusFilterOptions = computed(() => [
  { value: '', label: 'Tous les statuts' },
  ...breakdown.value.map((status) => ({
    value: status.key,
    label: `${status.shortLabel} ${status.rangeLabel}`.trim(),
    accent: status.color,
  })),
])

const selectedAxisFilterLabel = computed(() =>
  axisFilterOptions.value.find((option) => option.value === selectedAxisCode.value)?.label ?? 'Tous les axes',
)

const selectedStatusFilterLabel = computed(() =>
  statusFilterOptions.value.find((option) => option.value === selectedBreakdownKey.value)?.label ?? 'Tous les statuts',
)

const filteredIndicators = computed(() =>
  analysisIndicators.value.filter((indicator) => {
    const matchesAxis = selectedAxisCode.value
      ? String(indicator.axisCode ?? '') === selectedAxisCode.value
      : true
    const matchesBreakdown = selectedBreakdownKey.value
      ? statusKeyFromRate(indicator.attainmentRate) === selectedBreakdownKey.value
      : true

    return matchesAxis && matchesBreakdown
  }),
)

function toggleAxisFilter(code) {
  const nextCode = String(code ?? '')

  selectedAxisCode.value = selectedAxisCode.value === nextCode ? '' : nextCode
}

function resetAxisFilter() {
  selectedAxisCode.value = ''
}

function resetBreakdownFilter() {
  selectedBreakdownKey.value = ''
  hoveredBreakdownKey.value = null
  donutTooltip.value.visible = false
}

function toggleHeaderActionMenu(menu) {
  openHeaderActionMenu.value = openHeaderActionMenu.value === menu ? null : menu
}

function closeHeaderActionMenu(event) {
  if (!event?.currentTarget?.contains(event.relatedTarget)) {
    openHeaderActionMenu.value = null
  }
}

function selectHeaderYear(year) {
  selectedYear.value = String(year ?? '') || extractYear()
  selectedMonth.value = defaultMonthForYear(selectedYear.value)
  analysisPeriodMode.value = 'month'
}

function selectLatestAnalysisPeriod() {
  analysisPeriodMode.value = 'latest'
  openHeaderActionMenu.value = null
}

function selectHeaderMonth(month) {
  selectedMonth.value = String(month)
  analysisPeriodMode.value = 'month'
  openHeaderActionMenu.value = null
}

function updateIndicatorFilterMenuPlacement(menu, trigger) {
  const shell = trigger?.closest?.('.indicator-filter-control__shell')

  if (!shell || typeof window === 'undefined') {
    return
  }

  const rect = shell.getBoundingClientRect()
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0
  const optionCount = menu === 'axis' ? axisFilterOptions.value.length : statusFilterOptions.value.length
  const naturalHeight = Math.min(
    FILTER_MENU_MAX_HEIGHT,
    optionCount * FILTER_MENU_ROW_HEIGHT + FILTER_MENU_VERTICAL_MARGIN,
  )
  const spaceBelow = Math.max(viewportHeight - rect.bottom - FILTER_MENU_VERTICAL_MARGIN, 0)
  const spaceAbove = Math.max(rect.top - FILTER_MENU_VERTICAL_MARGIN, 0)
  const direction = spaceBelow >= naturalHeight || spaceBelow >= spaceAbove ? 'down' : 'up'
  const availableSpace = direction === 'down' ? spaceBelow : spaceAbove

  indicatorFilterMenuPlacement.value = {
    ...indicatorFilterMenuPlacement.value,
    [menu]: {
      direction,
      maxHeight: Math.max(FILTER_MENU_MIN_HEIGHT, Math.min(naturalHeight, availableSpace)),
    },
  }
}

function toggleIndicatorFilterMenu(menu, event) {
  updateIndicatorFilterMenuPlacement(menu, event?.currentTarget)
  openIndicatorFilter.value = openIndicatorFilter.value === menu ? null : menu
}

function closeIndicatorFilterMenu(event) {
  if (!event?.currentTarget?.contains(event.relatedTarget)) {
    openIndicatorFilter.value = null
  }
}

function selectAxisFilter(value) {
  selectedAxisCode.value = value
  openIndicatorFilter.value = null
}

function selectBreakdownFilter(value) {
  selectedBreakdownKey.value = value
  if (!value) {
    hoveredBreakdownKey.value = null
    donutTooltip.value.visible = false
  }
  openIndicatorFilter.value = null
}

function csvCell(value) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`
}

function downloadTextFile(filename, content, mimeType) {
  if (typeof document === 'undefined') {
    return
  }

  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function exportFilteredIndicatorsCsv() {
  const headers = ['Code', 'Indicateur', 'Axe', 'Période', 'Valeur', 'Cible', "Taux d'atteinte", 'Statut']
  const rows = previewIndicators.value.map((indicator) => [
    indicator.code,
    indicator.label,
    indicator.axisLabel,
    indicator.latestPeriodLabel ?? '',
    formatIndicatorMetricValue(indicator.latestValue, indicator.valueFormat),
    formatIndicatorTarget(indicator),
    formatRate(indicator.attainmentRate),
    indicator.status.shortLabel,
  ])
  const content = [
    headers.map(csvCell).join(';'),
    ...rows.map((row) => row.map(csvCell).join(';')),
  ].join('\n')

  downloadTextFile(`indicateurs-${displayYear.value}.csv`, `\ufeff${content}`, 'text/csv;charset=utf-8')
  openHeaderActionMenu.value = null
}

function exportFilteredIndicatorsJson() {
  const payload = {
    year: displayYear.value,
    filters: {
      axis: selectedAxisFilterLabel.value,
      status: selectedStatusFilterLabel.value,
    },
    indicators: previewIndicators.value,
  }

  downloadTextFile(
    `indicateurs-${displayYear.value}.json`,
    JSON.stringify(payload, null, 2),
    'application/json;charset=utf-8',
  )
  openHeaderActionMenu.value = null
}

function printKeyIndicators() {
  openHeaderActionMenu.value = null

  const previousTitle = document.title
  document.title = `Indicateurs de performance - ${analysisPeriodLabel.value}`

  window.requestAnimationFrame(() => {
    window.print()
    window.setTimeout(() => {
      document.title = previousTitle
    }, 500)
  })
}

const metricCards = computed(() => [
  {
    key: 'axes',
    label: 'Axes strategiques',
    value: formatNumber(analysisSummary.value.activeAxes ?? 0),
    detail: 'axes suivis',
    icon: 'axes',
    color: '#2f7be8',
    colorEnd: '#5b9af2',
    soft: 'rgba(47, 123, 232, 0.16)',
  },
  {
    key: 'indicators',
    label: 'Indicateurs',
    value: formatNumber(analysisSummary.value.totalIndicators ?? 0),
    detail: 'indicateurs suivis',
    icon: 'bars',
    color: '#8a63f7',
    colorEnd: '#aa8bff',
    soft: 'rgba(138, 99, 247, 0.16)',
  },
  {
    key: 'global-rate',
    label: 'Taux global d’atteinte',
    value: formatRate(globalAverageAttainment.value),
    detail: 'atteinte moyenne',
    icon: 'target',
    color: '#28a464',
    colorEnd: '#5ac786',
    soft: 'rgba(40, 164, 100, 0.16)',
  },
  {
    key: 'on-target',
    label: 'Indicateurs à la cible',
    value: formatNumber(analysisSummary.value.onTargetIndicators ?? 0),
    detail: `sur ${formatNumber(analysisSummary.value.targetedIndicators ?? 0)}`,
    icon: 'check',
    color: '#2ea35e',
    colorEnd: '#60c280',
    soft: 'rgba(46, 163, 94, 0.16)',
  },
  {
    key: 'alert',
    label: 'Indicateurs en alerte',
    value: formatNumber(alertCount.value),
    detail: `sur ${formatNumber(analysisSummary.value.targetedIndicators ?? 0)}`,
    icon: 'warning',
    color: '#e24b43',
    colorEnd: '#f47b72',
    soft: 'rgba(226, 75, 67, 0.16)',
  },
])

const trendChart = computed(() => {
  const series = displayedAttainmentTimeline.value.map((item) => ({
    label: String(item.periodLabel ?? ''),
    value: Number(item.averageRate ?? 0),
  }))

  const width = 620
  const height = 282
  const paddingLeft = 44
  const paddingRight = 18
  const paddingTop = 18
  const paddingBottom = 76
  const chartHeight = height - paddingTop - paddingBottom
  const chartWidth = width - paddingLeft - paddingRight

  if (!series.length) {
    return {
      width,
      height,
      baseline: height - paddingBottom,
      gridStart: paddingLeft,
      gridEnd: width - paddingRight,
      points: [],
      polyline: '',
      areaPath: '',
      ticks: [100, 75, 50, 25, 0].map((tick, index) => ({
        value: tick,
        y: paddingTop + (chartHeight / 4) * index,
      })),
    }
  }

  const maxValue = Math.max(100, ...series.map((item) => item.value))
  const roundedMax = Math.ceil(maxValue / 25) * 25

  const points = series.map((item, index) => {
    const x = paddingLeft + (index / Math.max(series.length - 1, 1)) * chartWidth
    const y = paddingTop + (1 - item.value / roundedMax) * chartHeight

    return {
      ...item,
      x,
      y,
      valueLabel: formatPercent(item.value),
    }
  })

  const polyline = points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')
  const areaPath = points.length
    ? `M ${points[0].x.toFixed(2)} ${(height - paddingBottom).toFixed(2)} L ${points
        .map((point) => `${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
        .join(' L ')} L ${points.at(-1).x.toFixed(2)} ${(height - paddingBottom).toFixed(2)} Z`
    : ''

  const ticks = Array.from({ length: 5 }, (_, index) => {
    const value = roundedMax - (roundedMax / 4) * index
    const y = paddingTop + (chartHeight / 4) * index

    return {
      value: Math.round(value),
      y,
    }
  })

  return {
    width,
    height,
    baseline: height - paddingBottom,
    gridStart: paddingLeft,
    gridEnd: width - paddingRight,
    points,
    polyline,
    areaPath,
    ticks,
  }
})

const previewIndicators = computed(() =>
  filteredIndicators.value.map((indicator) => ({
    ...indicator,
    status: statusMetaFromRate(indicator.attainmentRate),
    accent: axisAccentMap.value.get(String(indicator.axisCode ?? '')) ?? AXIS_ACCENTS[0],
    axisLabel: axisLabelMap.value.get(String(indicator.axisCode ?? '')) ?? 'Axe non défini',
  })),
)

const selectedIndicator = computed(() =>
  previewIndicators.value.find((indicator) => indicator.code === selectedIndicatorCode.value) ?? null,
)

function normalizeMetricChartValue(value, valueFormat) {
  if (value === null || value === undefined) {
    return null
  }

  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return null
  }

  if (valueFormat === 'percent' && Math.abs(numericValue) <= 1.2) {
    return numericValue * 100
  }

  return numericValue
}

function isMonthlyPeriodicity(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .includes('mensuelle')
}

function historyWindowSize(periodicity) {
  const normalized = normalizePeriodicityName(periodicity)

  if (normalized.includes('trimestrielle')) {
    return 8
  }

  if (normalized.includes('semestrielle')) {
    return 4
  }

  if (normalized.includes('annuelle')) {
    return 2
  }

  return 13
}

function buildIndicatorHistoryChart(indicator) {
  const width = INDICATOR_HISTORY_CHART_WIDTH
  const height = INDICATOR_HISTORY_CHART_HEIGHT
  const paddingLeft = 68
  const paddingRight = 54
  const paddingTop = 24
  const paddingBottom = 58
  const chartWidth = width - paddingLeft - paddingRight
  const chartHeight = height - paddingTop - paddingBottom
  const baseline = height - paddingBottom
  const labelY = baseline + 20
  const mode = isMonthlyPeriodicity(indicator?.periodicity) ? 'line' : 'history'
  const windowSize = historyWindowSize(indicator?.periodicity)
  const history = (indicator?.history ?? [])
    .filter((entry) => entry?.value !== null && entry?.value !== undefined)
    .slice(-windowSize)
    .map((entry) => ({
      period: entry.period,
      label: String(entry.periodLabel ?? entry.period ?? ''),
      rawValue: entry.value,
      value: normalizeMetricChartValue(entry.value, indicator.valueFormat),
      valueLabel: formatIndicatorMetricValue(entry.value, indicator.valueFormat),
      targetRawValue: entry.targetValue,
      targetValue: normalizeMetricChartValue(entry.targetValue, indicator.valueFormat),
      targetLabel: entry.targetValue === null || entry.targetValue === undefined
        ? ''
        : formatIndicatorMetricValue(entry.targetValue, indicator.valueFormat),
      rateLabel: entry.attainmentRate === null || entry.attainmentRate === undefined
        ? ''
        : formatRate(entry.attainmentRate),
    }))
    .filter((entry) => entry.value !== null)

  if (!history.length) {
    return {
      width,
      height,
      points: [],
      polyline: '',
      areaPath: '',
      targetLine: null,
      gridStart: paddingLeft,
      gridEnd: width - paddingRight,
      labelY,
      mode,
      eyebrow: mode === 'line' ? 'Courbe mensuelle' : 'Historique',
      title: mode === 'line' ? 'Évolution mensuelle' : 'Historique des mesures',
      rangeLabel: 'Historique indisponible',
    }
  }

  const targetValue = normalizeMetricChartValue(indicator.targetValue, indicator.valueFormat)
  const historyTargetValues = history
    .map((entry) => entry.targetValue)
    .filter((value) => value !== null && value !== undefined)
  const scaleValues = [
    ...history.map((entry) => entry.value),
    ...(historyTargetValues.length ? historyTargetValues : targetValue !== null ? [targetValue] : []),
  ]
  const minValue = Math.min(...scaleValues)
  const maxValue = Math.max(...scaleValues)
  const spread = maxValue - minValue || Math.max(Math.abs(maxValue), 1)
  const padding = Math.max(spread * 0.16, 1)
  const scaleMin = Math.max(0, minValue - padding)
  const scaleMax = maxValue + padding
  const scaleSpread = scaleMax - scaleMin || 1

  const slotWidth = chartWidth / Math.max(history.length, 1)
  const barWidth = Math.min(34, Math.max(14, slotWidth * 0.52))

  const points = history.map((entry, index) => {
    const x = history.length === 1
      ? paddingLeft + chartWidth / 2
      : paddingLeft + (index / Math.max(history.length - 1, 1)) * chartWidth
    const y = paddingTop + (1 - (entry.value - scaleMin) / scaleSpread) * chartHeight

    return {
      ...entry,
      x,
      y,
      targetY: entry.targetValue === null || entry.targetValue === undefined
        ? null
        : paddingTop + (1 - (entry.targetValue - scaleMin) / scaleSpread) * chartHeight,
      tooltipMeta: [
        entry.rateLabel ? `Taux ${entry.rateLabel}` : '',
        entry.targetLabel ? `Cible ${entry.targetLabel}` : '',
      ].filter(Boolean).join(' - '),
      barX: x - barWidth / 2,
      barY: y,
      barWidth,
      barHeight: Math.max(height - paddingBottom - y, 2),
      hitX: x - slotWidth / 2,
      hitY: paddingTop,
      hitWidth: slotWidth,
      hitHeight: labelY - paddingTop + 8,
    }
  })

  const polyline = points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')
  const areaPath = points.length
    ? `M ${points[0].x.toFixed(2)} ${baseline.toFixed(2)} L ${points
        .map((point) => `${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
        .join(' L ')} L ${points.at(-1).x.toFixed(2)} ${baseline.toFixed(2)} Z`
    : ''
  const targetPoints = points.filter((point) => point.targetY !== null && point.targetY !== undefined)
  const fallbackTargetY = targetValue !== null
    ? paddingTop + (1 - (targetValue - scaleMin) / scaleSpread) * chartHeight
    : null
  const targetLine = targetPoints.length
    ? {
        points: targetPoints.map((point) => `${point.x.toFixed(2)},${point.targetY.toFixed(2)}`).join(' '),
        x: targetPoints.at(-1).x,
        y: targetPoints.at(-1).targetY,
        label: targetPoints.at(-1).targetLabel || formatIndicatorTarget(indicator),
      }
    : fallbackTargetY !== null
      ? {
          points: `${paddingLeft.toFixed(2)},${fallbackTargetY.toFixed(2)} ${(width - paddingRight).toFixed(2)},${fallbackTargetY.toFixed(2)}`,
          x: width - paddingRight,
          y: fallbackTargetY,
          label: formatIndicatorTarget(indicator),
        }
      : null

  return {
    width,
    height,
    points,
    polyline,
    areaPath,
    targetLine,
    gridStart: paddingLeft,
    gridEnd: width - paddingRight,
    labelY,
    mode,
    eyebrow: mode === 'line' ? 'Courbe mensuelle' : 'Historique',
    title: mode === 'line' ? 'Évolution mensuelle' : 'Historique des mesures',
    rangeLabel:
      points.length > 1
        ? `${points[0].label} - ${points.at(-1).label}`
        : points[0].label,
  }
}

function averageNumeric(values) {
  const numericValues = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value))

  if (!numericValues.length) {
    return null
  }

  return numericValues.reduce((total, value) => total + value, 0) / numericValues.length
}

function sumNumeric(values) {
  const numericValues = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value))

  if (!numericValues.length) {
    return null
  }

  return numericValues.reduce((total, value) => total + value, 0)
}

function aggregateIndicatorValues(values, method) {
  return method === 'sum' ? sumNumeric(values) : averageNumeric(values)
}

function indicatorSummaryEntries(indicator) {
  return [...(indicator?.history ?? [])]
    .filter((entry) => entry?.value !== null && entry?.value !== undefined)
    .sort(comparePeriodEntries)
}

function defaultSummaryRange(indicator) {
  const entries = indicatorSummaryEntries(indicator)
  const windowSize = historyWindowSize(indicator?.periodicity)
  const visibleEntries = entries.slice(-windowSize)

  return {
    start: visibleEntries[0]?.period ?? '',
    end: visibleEntries.at(-1)?.period ?? '',
  }
}

function summaryRangeForIndicator(indicator) {
  const entries = indicatorSummaryEntries(indicator)
  const periods = new Set(entries.map((entry) => entry.period))
  const savedRange = summaryRangeByIndicator.value[indicator?.code] ?? {}
  const fallbackRange = defaultSummaryRange(indicator)
  let start = periods.has(savedRange.start) ? savedRange.start : fallbackRange.start
  let end = periods.has(savedRange.end) ? savedRange.end : fallbackRange.end
  const startOrder = parsePeriodParts(start)?.order ?? 0
  const endOrder = parsePeriodParts(end)?.order ?? 0

  if (startOrder > endOrder) {
    ;[start, end] = [end, start]
  }

  return { start, end }
}

function summaryRangeEntries(indicator, range) {
  const startOrder = parsePeriodParts(range?.start)?.order
  const endOrder = parsePeriodParts(range?.end)?.order

  if (!startOrder || !endOrder) {
    return []
  }

  return indicatorSummaryEntries(indicator).filter((entry) => {
    const order = parsePeriodParts(entry.period)?.order
    return order && order >= startOrder && order <= endOrder
  })
}

function summaryRangeLabel(entries) {
  if (!entries.length) {
    return 'Période indisponible'
  }

  const firstLabel = String(entries[0]?.periodLabel ?? entries[0]?.period ?? '')
  const lastLabel = String(entries.at(-1)?.periodLabel ?? entries.at(-1)?.period ?? '')

  return firstLabel === lastLabel ? firstLabel : `${firstLabel} - ${lastLabel}`
}

function compactSummaryPeriodLabel(entry) {
  const label = String(entry?.periodLabel ?? entry?.period ?? '')
  const year = parsePeriodParts(entry?.period)?.year ?? extractYearFromText(label)
  const compactLabel = year ? label.replace(new RegExp(`\\s*${year}\\s*$`), '').trim() : label

  return compactLabel || label
}

function summaryPeriodGroupLayout(options) {
  const labels = options.map((option) => String(option.shortLabel ?? ''))

  if (labels.length <= 4 && labels.every((label) => /^T\d$/i.test(label))) {
    return 'quarters'
  }

  if (labels.length <= 2 && labels.every((label) => /^S\d$/i.test(label))) {
    return 'semesters'
  }

  if (labels.length === 1 && labels.every((label) => /^20\d{2}$/.test(label))) {
    return 'years'
  }

  return 'default'
}

function buildSummaryPeriodGroups(entries) {
  const groupsByYear = new Map()

  entries.forEach((entry) => {
    const year = String(parsePeriodParts(entry?.period)?.year ?? extractYearFromText(entry?.periodLabel) ?? '')

    if (!year) {
      return
    }

    if (!groupsByYear.has(year)) {
      groupsByYear.set(year, {
        year,
        options: [],
      })
    }

    groupsByYear.get(year).options.push({
      value: entry.period,
      label: String(entry.periodLabel ?? entry.period ?? ''),
      shortLabel: compactSummaryPeriodLabel(entry),
    })
  })

  return Array.from(groupsByYear.values()).map((group) => ({
    ...group,
    layout: summaryPeriodGroupLayout(group.options),
  }))
}

function indicatorSummaryMethod(indicator) {
  const savedMethod = summaryMethodByIndicator.value[indicator?.code]

  if (indicator?.valueFormat !== 'number') {
    return 'average'
  }

  return ['sum', 'average'].includes(savedMethod) ? savedMethod : 'sum'
}

function summaryMethodLabel(method) {
  return method === 'sum' ? 'Somme' : 'Moyenne'
}

function formatSummaryMetricValue(value, indicator, method) {
  if (value === null || value === undefined) {
    return 'N/A'
  }

  if (method === 'average' && indicator?.valueFormat === 'number') {
    const roundedValue = Math.round(Number(value))

    return Number.isFinite(roundedValue) ? formatNumber(roundedValue) : 'N/A'
  }

  return formatIndicatorMetricValue(value, indicator.valueFormat)
}

function buildIndicatorSummaryRows(indicator, method, range) {
  const entries = summaryRangeEntries(indicator, range)
  const value = aggregateIndicatorValues(entries.map((entry) => entry.value), method)
  const targetValues = entries
    .map((entry) => entry.targetValue)
    .filter((targetValue) => targetValue !== null && targetValue !== undefined)
  const hasCompleteTargets = entries.length > 0 && targetValues.length === entries.length
  const target = hasCompleteTargets ? aggregateIndicatorValues(targetValues, method) : null
  const rate = attainmentRateForValue(value, target)

  return {
    title: 'Synthèse',
    range,
    rangeLabel: summaryRangeLabel(entries),
    entries,
    rows: [
      {
        key: 'method',
        label: 'Méthode',
        value: summaryMethodLabel(method),
      },
      {
        key: 'value',
        label: method === 'sum' ? 'Valeur cumulée' : 'Valeur moyenne',
        value: formatSummaryMetricValue(value, indicator, method),
      },
      {
        key: 'target',
        label: method === 'sum' ? 'Cible cumulée' : 'Cible moyenne',
        value: formatSummaryMetricValue(target, indicator, method),
      },
      {
        key: 'rate',
        label: "Taux d'atteinte",
        value: formatRate(rate),
      },
    ],
  }
}

const selectedIndicatorAnalysis = computed(() => {
  const indicator = selectedIndicator.value

  if (!indicator) {
    return null
  }

  const rate = indicator.attainmentRate
  const status = indicator.status
  const targetLabel = formatIndicatorTarget(indicator)
  const currentValueLabel = formatIndicatorMetricValue(indicator.latestValue, indicator.valueFormat)
  const rateLabel = formatRate(rate)
  const historyChart = buildIndicatorHistoryChart(indicator)
  const summaryMethod = indicatorSummaryMethod(indicator)
  const summaryRange = summaryRangeForIndicator(indicator)
  const summaryEntries = indicatorSummaryEntries(indicator)
  const summary = buildIndicatorSummaryRows(indicator, summaryMethod, summaryRange)
  const summaryPeriodGroups = buildSummaryPeriodGroups(summaryEntries)
  const summaryRangeLayout = summaryPeriodGroups.some((group) => group.layout === 'default' || group.layout === 'quarters')
    ? 'wide'
    : 'compact'
  const insight = rate === null || rate === undefined
    ? "Cet indicateur n'a pas encore de taux d'atteinte comparable."
    : `Cet indicateur est ${status.shortLabel.toLowerCase()} : il atteint ${rateLabel} de sa cible.`

  return {
    ...indicator,
    currentValueLabel,
    targetLabel,
    historyChart,
    summary,
    summaryMethod,
    summaryPeriodGroups,
    summaryRangeLayout,
    canChangeSummaryMethod: indicator.valueFormat === 'number',
    rateLabel,
    insight,
    gaugeStyle: rateGaugeStyle(rate, status),
  }
})

watch(filteredIndicators, (items) => {
  if (!selectedIndicatorCode.value) {
    return
  }

  if (!items.some((indicator) => indicator.code === selectedIndicatorCode.value)) {
    selectedIndicatorCode.value = items[0]?.code ?? ''
  }
})

function selectIndicatorForAnalysis(code) {
  selectedIndicatorCode.value = code
  openSummaryControl.value = null
}

function closeSummaryControl(event) {
  if (!event?.currentTarget?.contains(event.relatedTarget)) {
    openSummaryControl.value = null
  }
}

function toggleSummaryControl(control) {
  openSummaryControl.value = openSummaryControl.value === control ? null : control
}

function selectSummaryBoundary(boundary, period) {
  const indicator = selectedIndicator.value

  if (!indicator) {
    return
  }

  const currentRange = summaryRangeForIndicator(indicator)
  const nextRange = {
    ...currentRange,
    [boundary]: period,
  }
  const startOrder = parsePeriodParts(nextRange.start)?.order ?? 0
  const endOrder = parsePeriodParts(nextRange.end)?.order ?? 0

  if (startOrder > endOrder) {
    if (boundary === 'start') {
      nextRange.end = period
    } else {
      nextRange.start = period
    }
  }

  summaryRangeByIndicator.value = {
    ...summaryRangeByIndicator.value,
    [indicator.code]: nextRange,
  }
}

function selectSummaryMethod(method) {
  const indicator = selectedIndicator.value

  if (!indicator || indicator.valueFormat !== 'number') {
    return
  }

  summaryMethodByIndicator.value = {
    ...summaryMethodByIndicator.value,
    [indicator.code]: method,
  }
}

const indicatorTableStyle = computed(() => ({
  '--indicator-column-width': indicatorColumnWidth.value ? `${indicatorColumnWidth.value}px` : '42%',
  '--indicator-table-width': indicatorColumnWidth.value
    ? `${indicatorColumnWidth.value + 560}px`
    : '100%',
}))

function stopIndicatorColumnResize() {
  indicatorColumnResize = null
  window.removeEventListener('pointermove', resizeIndicatorColumn)
  window.removeEventListener('pointerup', stopIndicatorColumnResize)
}

function resizeIndicatorColumn(event) {
  if (!indicatorColumnResize) {
    return
  }

  const nextWidth = indicatorColumnResize.startWidth + event.clientX - indicatorColumnResize.startX
  indicatorColumnWidth.value = Math.round(
    Math.max(indicatorColumnResize.minWidth, Math.min(indicatorColumnResize.maxWidth, nextWidth)),
  )
}

function startIndicatorColumnResize(event) {
  const table = event.currentTarget.closest('table')
  const header = event.currentTarget.closest('th')

  if (!table || !header) {
    return
  }

  const tableWidth = table.getBoundingClientRect().width
  const startWidth = header.getBoundingClientRect().width

  indicatorColumnResize = {
    startX: event.clientX,
    startWidth,
    minWidth: 180,
    maxWidth: Math.max(820, tableWidth * 0.9),
  }

  indicatorColumnWidth.value = Math.round(startWidth)
  window.addEventListener('pointermove', resizeIndicatorColumn)
  window.addEventListener('pointerup', stopIndicatorColumnResize)
}
</script>

<template>
  <DashboardStateCard
    v-if="!hasIndicators"
    title="Indicateurs cl&eacute;s indisponibles"
    message="Les cartes et graphiques appara&icirc;tront ici d&egrave;s que des indicateurs et leurs valeurs seront disponibles."
  />

  <section v-else class="kpi-page">
    <header class="kpi-header">
      <div class="kpi-header__copy">
        <h1>Indicateurs de Performance</h1>
        <p>Vue d&apos;ensemble par axe strat&eacute;gique</p>
        <p class="kpi-header__print-period">P&eacute;riode analys&eacute;e : {{ analysisPeriodLabel }}</p>
      </div>

      <div
        class="kpi-header__actions"
        @focusout="closeHeaderActionMenu"
        @keydown.escape="openHeaderActionMenu = null"
      >
        <div class="kpi-action-group">
          <button
            type="button"
            class="kpi-action-chip"
            :class="{ 'is-open': openHeaderActionMenu === 'year' }"
            :aria-expanded="openHeaderActionMenu === 'year'"
            aria-haspopup="menu"
            @click="toggleHeaderActionMenu('year')"
          >
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <rect x="3.5" y="4" width="13" height="12" rx="2.2" />
              <path d="M6.5 2.8v3.1M13.5 2.8v3.1M3.5 7.2h13" />
            </svg>
            <span class="kpi-action-chip__copy">
              <small>P&eacute;riode</small>
              <strong>{{ analysisPeriodLabel }}</strong>
            </span>
            <svg class="kpi-action-chip__chevron" viewBox="0 0 20 20" aria-hidden="true">
              <path d="m6 8 4 4 4-4" />
            </svg>
          </button>

          <div
            v-if="openHeaderActionMenu === 'year'"
            class="kpi-action-popover kpi-action-popover--year"
            role="menu"
          >
            <span class="kpi-action-popover__eyebrow">P&eacute;riode d&apos;analyse</span>
            <button
              type="button"
              class="kpi-action-menu-item"
              :class="{ 'is-selected': analysisPeriodMode === 'latest' }"
              role="menuitem"
              @click="selectLatestAnalysisPeriod"
            >
              <span>Derni&egrave;re p&eacute;riode disponible</span>
              <small>Utilise la derni&egrave;re valeur connue de chaque indicateur</small>
            </button>

            <div class="kpi-period-picker">
              <span class="kpi-period-picker__label">Ann&eacute;e</span>
              <div class="kpi-period-picker__years">
                <button
                  v-for="option in availableYearOptions"
                  :key="option.value"
                  type="button"
                  class="kpi-period-picker__year"
                  :class="{ 'is-selected': analysisPeriodMode === 'month' && analysisYear === option.value }"
                  @click="selectHeaderYear(option.value)"
                >
                  {{ option.value }}
                </button>
              </div>
            </div>

            <div v-if="analysisPeriodMode === 'month'" class="kpi-period-picker">
              <span class="kpi-period-picker__label">Mois de l&apos;ann&eacute;e {{ analysisYear }}</span>
              <div class="kpi-period-picker__months">
                <button
                  v-for="month in MONTH_OPTIONS"
                  :key="month.value"
                  type="button"
                  class="kpi-period-picker__month"
                  :class="{ 'is-selected': Number(analysisMonth) === month.value }"
                  @click="selectHeaderMonth(month.value)"
                >
                  {{ month.shortLabel }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="kpi-action-group">
          <button
            type="button"
            class="kpi-action-chip"
            :class="{ 'is-open': openHeaderActionMenu === 'export' }"
            :aria-expanded="openHeaderActionMenu === 'export'"
            aria-haspopup="menu"
            @click="toggleHeaderActionMenu('export')"
          >
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="M10 3.2v8.7M6.7 8.9 10 12.3l3.3-3.4M4 14.2v2.3h12v-2.3" />
            </svg>
            <span class="kpi-action-chip__copy">
              <small>Rapport</small>
              <strong>Exporter</strong>
            </span>
            <svg class="kpi-action-chip__chevron" viewBox="0 0 20 20" aria-hidden="true">
              <path d="m6 8 4 4 4-4" />
            </svg>
          </button>

          <div
            v-if="openHeaderActionMenu === 'export'"
            class="kpi-action-popover kpi-action-popover--export"
            role="menu"
          >
            <span class="kpi-action-popover__eyebrow">Exporter la vue</span>
            <button type="button" class="kpi-action-menu-item" role="menuitem" @click="exportFilteredIndicatorsCsv">
              <span>Excel / CSV</span>
              <small>{{ formatNumber(filteredIndicators.length) }} indicateurs filtr&eacute;s</small>
            </button>
            <button type="button" class="kpi-action-menu-item" role="menuitem" @click="exportFilteredIndicatorsJson">
              <span>Donn&eacute;es JSON</span>
              <small>Snapshot technique de la vue</small>
            </button>
            <button type="button" class="kpi-action-menu-item" role="menuitem" @click="printKeyIndicators">
              <span>PDF / impression</span>
              <small>Pr&eacute;pare une vue propre pour le PDF</small>
            </button>
          </div>
        </div>
      </div>
    </header>

    <section class="kpi-summary-grid">
      <article
        v-for="card in metricCards"
        :key="card.key"
        class="kpi-summary-card"
        :style="summaryCardStyle(card)"
      >
        <span class="kpi-summary-card__icon" aria-hidden="true">
          <svg
            v-if="card.icon === 'axes'"
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="10" cy="33" r="4.6" fill="currentColor" stroke="none" />
            <circle cx="24" cy="16" r="4.6" fill="currentColor" stroke="none" />
            <circle cx="38" cy="33" r="4.6" fill="currentColor" stroke="none" />
            <path d="M13 30.6 21 20.1M27 20.1l8 10.5M24 20.6v12.2" />
          </svg>

          <svg
            v-else-if="card.icon === 'bars'"
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 38V23M18 38V16M27 38V10M36 38V19M8 38h30" />
            <path d="m13 14 7-4 6 5 10-7" />
          </svg>

          <svg
            v-else-if="card.icon === 'target'"
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="24" cy="24" r="14" />
            <circle cx="24" cy="24" r="7" />
            <path d="M24 10V4m0 40v-6m14-14h6M4 24h6m20.2-9.8L40 8m-7.2 15L24 24" />
          </svg>

          <svg
            v-else-if="card.icon === 'check'"
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="24" cy="24" r="16" />
            <path d="m17 24 5 5 10-11" />
          </svg>

          <svg
            v-else-if="card.icon === 'warning'"
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M24 8 40 37H8z" />
            <path d="M24 18v9m0 4.6v.2" />
          </svg>

          <svg
            v-else
            width="28"
            height="28"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="24" cy="24" r="16" />
            <path d="m18 18 12 12M30 18 18 30" />
          </svg>
        </span>

        <div class="kpi-summary-card__content">
          <span class="kpi-summary-card__label">{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.detail }}</small>
        </div>
      </article>
    </section>

    <div class="kpi-main-grid">
      <section class="panel panel--kpi-surface">
        <div class="panel__header panel__header--space">
          <div>
            <h2>Performance par Axe Strat&eacute;gique</h2>
          </div>

          <div class="panel__meta">{{ formatNumber(axisRows.length) }} axes suivis</div>
        </div>

        <div class="kpi-table-wrap">
          <table class="kpi-table kpi-table--axis">
            <thead>
              <tr>
                <th>Axe strat&eacute;gique</th>
                <th>Indicateurs</th>
                <th>Taux d&apos;atteinte moyen</th>
                <th>Statut</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="row in axisRows"
                :key="row.code"
                class="kpi-table__interactive-row"
                :class="{ 'is-active': selectedAxisCode === String(row.code) }"
                :style="{ '--axis-row-accent': row.accent }"
                role="button"
                tabindex="0"
                :aria-pressed="selectedAxisCode === String(row.code)"
                :title="`Filtrer les indicateurs de ${row.label}`"
                @click="toggleAxisFilter(row.code)"
                @keydown.enter.prevent="toggleAxisFilter(row.code)"
                @keydown.space.prevent="toggleAxisFilter(row.code)"
              >
                <td>
                  <div class="axis-name-cell">
                    <span
                      class="axis-name-cell__tag"
                      :style="{ backgroundColor: `${row.accent}18`, color: row.accent }"
                    >
                      {{ row.order }}
                    </span>

                    <div class="axis-name-cell__copy">
                      <strong>{{ row.label }}</strong>
                    </div>
                  </div>
                </td>

                <td class="kpi-table__muted">{{ formatNumber(row.totalIndicators) }}</td>

                <td>
                  <div class="axis-rate-cell">
                    <div class="axis-rate-cell__track">
                      <span
                        class="axis-rate-cell__fill"
                        :style="progressFillStyle(row.averageRate, row.status)"
                      />
                    </div>
                    <strong>{{ formatRate(row.averageRate) }}</strong>
                  </div>
                </td>

                <td>
                  <span
                    class="status-pill"
                    :style="{ backgroundColor: row.status.soft, color: row.status.color }"
                  >
                    {{ row.status.shortLabel }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="kpi-side-grid">
        <section class="panel panel--kpi-surface">
          <div class="panel__header">
            <h2>Atteinte des cibles (Global)</h2>
          </div>

          <div class="kpi-donut-top-legend">
            <button
              v-for="segment in donutSegments"
              :key="`${segment.key}-top-legend`"
              type="button"
              class="kpi-donut-top-legend__item"
              :class="{
                'is-active': activeBreakdownKey === segment.key,
                'is-selected': selectedBreakdownKey === segment.key,
              }"
              @mouseenter="showDonutTooltip(segment.key, $event)"
              @mousemove="moveDonutTooltip($event)"
              @mouseleave="hideDonutTooltip(segment.key)"
              @focus="activateBreakdown(segment.key)"
              @blur="clearBreakdown(segment.key)"
              @click="toggleBreakdown(segment.key)"
              :aria-pressed="selectedBreakdownKey === segment.key"
            >
              <span class="kpi-donut-top-legend__dot" :style="{ backgroundColor: segment.color }" />
              <span class="kpi-donut-top-legend__copy">
                <strong>{{ segment.shortLabel }}</strong>
                <small>{{ segment.criterionLabel }}</small>
              </span>
            </button>
          </div>

          <div class="kpi-donut-layout">
            <div class="kpi-donut-shell">
              <div class="kpi-donut-stage">
                <svg
                  class="kpi-donut-svg"
                  :viewBox="`0 0 ${DONUT_STAGE_WIDTH} ${DONUT_STAGE_HEIGHT}`"
                  preserveAspectRatio="xMidYMid meet"
                  aria-hidden="true"
                >
                  <circle
                    class="kpi-donut-track"
                    :cx="DONUT_CENTER_X"
                    :cy="DONUT_CENTER_Y"
                    :r="(DONUT_OUTER_RADIUS + DONUT_INNER_RADIUS) / 2"
                  />

                  <g
                    v-for="segment in donutSegments"
                    :key="segment.key"
                    class="kpi-donut-segment"
                    :class="{
                      'is-active': activeBreakdownKey === segment.key,
                      'is-selected': selectedBreakdownKey === segment.key,
                    }"
                    @mouseenter="showDonutTooltip(segment.key, $event)"
                    @mousemove="moveDonutTooltip($event)"
                    @mouseleave="hideDonutTooltip(segment.key)"
                    @click="toggleBreakdown(segment.key)"
                  >
                    <path
                      :d="segment.path"
                      :fill="segment.color"
                      :opacity="segment.opacity"
                    />
                  </g>

                  <g
                    v-for="segment in donutSegments"
                    :key="`${segment.key}-label`"
                    class="kpi-donut-label"
                    :class="{
                      'is-active': activeBreakdownKey === segment.key,
                      'is-selected': selectedBreakdownKey === segment.key,
                    }"
                    @mouseenter="showDonutTooltip(segment.key, $event)"
                    @mousemove="moveDonutTooltip($event)"
                    @mouseleave="hideDonutTooltip(segment.key)"
                    @click="toggleBreakdown(segment.key)"
                  >
                    <path
                      class="kpi-donut-label__line"
                      :d="segment.connectorPath"
                      :style="{ stroke: activeBreakdownKey === segment.key ? segment.color : '#aec0d4' }"
                    />
                    <text
                      class="kpi-donut-label__text"
                      :x="segment.labelX"
                      :y="segment.labelY"
                      :text-anchor="segment.labelAnchor"
                    >
                      <tspan
                        class="kpi-donut-label__title"
                        font-size="18"
                        font-weight="900"
                      >
                        {{ segment.shortLabel }}
                      </tspan>
                      <tspan
                        class="kpi-donut-label__criteria"
                        :x="segment.labelX"
                        dy="17"
                        font-size="15"
                        font-weight="900"
                      >
                        {{ segment.criterionLabel }}
                      </tspan>
                      <tspan
                        class="kpi-donut-label__value"
                        :x="segment.labelX"
                        dy="17"
                        font-size="17"
                        font-weight="900"
                      >
                        {{ formatNumber(segment.total) }}
                      </tspan>
                    </text>
                  </g>
                </svg>

                <div class="kpi-donut__center" :style="donutCenterStyle">
                  <strong>{{ formatNumber(targetedBreakdownTotal) }}</strong>
                  <span>Indicateurs</span>
                </div>
              </div>
            </div>
          </div>

          <p v-if="noTargetIndicators > 0" class="kpi-donut-note">
            {{ formatNumber(noTargetIndicators) }} indicateurs sans cible ne sont pas inclus dans cette r&eacute;partition.
          </p>
        </section>

        <article
          v-if="activeBreakdown && donutTooltip.visible"
          class="kpi-donut-tooltip-card"
          :style="{
            ...donutTooltipStyle(activeBreakdown),
            left: `${donutTooltip.x}px`,
            top: `${donutTooltip.y}px`,
          }"
        >
          <span class="kpi-donut-tooltip-card__label">
            {{ activeBreakdown.shortLabel }} {{ activeBreakdown.criterionLabel }}
          </span>
          <span class="kpi-donut-tooltip-card__count">
            {{ formatNumber(activeBreakdown.total) }} indicateurs
          </span>
          <strong>{{ formatPercent(activeBreakdown.percentage) }}</strong>
        </article>

        <section class="panel panel--kpi-surface">
          <div class="panel__header">
            <h2>&Eacute;volution du taux d&apos;atteinte moyen</h2>
          </div>

          <div v-if="trendChart.points.length" class="trend-chart">
            <svg
              class="trend-chart__svg"
              :viewBox="`0 0 ${trendChart.width} ${trendChart.height}`"
              preserveAspectRatio="xMidYMid meet"
              aria-hidden="true"
            >
              <g v-for="tick in trendChart.ticks" :key="tick.value">
                <line
                  stroke="rgba(214, 224, 235, 0.96)"
                  stroke-width="1"
                  stroke-dasharray="4 4"
                  :x1="trendChart.gridStart"
                  :y1="tick.y"
                  :x2="trendChart.gridEnd"
                  :y2="tick.y"
                />
              </g>

              <path :d="trendChart.areaPath" fill="rgba(47, 123, 232, 0.08)" />
              <polyline
                :points="trendChart.polyline"
                fill="none"
                stroke="#2f7be8"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

              <g
                v-for="point in trendChart.points"
                :key="point.label"
                class="trend-chart__point"
                @mouseenter="showTrendTooltip(point, $event)"
                @mousemove="moveTrendTooltip(point, $event)"
                @mouseleave="hideTrendTooltip()"
              >
                <circle
                  class="trend-chart__hit"
                  :cx="point.x"
                  :cy="point.y"
                  r="13"
                  fill="transparent"
                />
                <circle
                  :cx="point.x"
                  :cy="point.y"
                  r="4.5"
                  fill="#2f7be8"
                  stroke="rgba(255, 255, 255, 0.98)"
                  stroke-width="2.5"
                />
                <text
                  :x="point.x"
                  :y="point.y - 10"
                  fill="#17314c"
                  font-size="11"
                  font-weight="800"
                  text-anchor="middle"
                >
                  {{ point.valueLabel }}
                </text>
                <text
                  :x="point.x"
                  :y="trendChart.baseline + 22"
                  fill="#667f9a"
                  font-size="11"
                  font-weight="700"
                  text-anchor="end"
                  :transform="`rotate(-38 ${point.x} ${trendChart.baseline + 22})`"
                >
                  {{ point.label }}
                </text>
              </g>
            </svg>
          </div>

          <div v-else class="kpi-empty-state">
            Pas assez d&apos;historique pour tracer une &eacute;volution consolid&eacute;e.
          </div>
        </section>

        <article
          v-if="trendTooltip.visible"
          class="trend-chart-tooltip"
          :style="{ left: `${trendTooltip.x}px`, top: `${trendTooltip.y}px` }"
        >
          <span>{{ trendTooltip.label }}</span>
          <strong>{{ trendTooltip.value }}</strong>
        </article>
      </div>
    </div>

    <div class="kpi-bottom-grid">
      <section class="panel panel--kpi-surface panel--indicator-preview">
        <div class="panel__header panel__header--space">
          <div>
            <h2>Aper&ccedil;u des Indicateurs ({{ formatNumber(filteredIndicators.length) }})</h2>
          </div>

          <div class="panel__meta">
            <span v-if="hasActiveIndicatorFilters">
              {{ formatNumber(filteredIndicators.length) }} indicateurs correspondent aux filtres
            </span>
            <span v-else>
              {{ formatNumber(previewIndicators.length) }} lignes affich&eacute;es
            </span>
          </div>
        </div>

        <div class="indicator-filter-controls" aria-label="Filtres des indicateurs">
          <div class="indicator-filter-control" @focusout="closeIndicatorFilterMenu">
            <span class="indicator-filter-control__label">Axe strat&eacute;gique</span>
            <span class="indicator-filter-control__shell" :class="{ 'is-active': selectedAxisCode }">
              <button
                type="button"
                class="indicator-filter-select"
                :class="{ 'is-open': openIndicatorFilter === 'axis' }"
                :aria-expanded="openIndicatorFilter === 'axis'"
                aria-haspopup="listbox"
                @click="toggleIndicatorFilterMenu('axis', $event)"
                @keydown.escape.prevent="openIndicatorFilter = null"
              >
                <span>{{ selectedAxisFilterLabel }}</span>
              </button>

              <button
                v-if="selectedAxisCode"
                type="button"
                class="indicator-filter-clear"
                aria-label="R&eacute;initialiser le filtre axe"
                @click.prevent.stop="resetAxisFilter"
              >
                &times;
              </button>

              <div
                v-if="openIndicatorFilter === 'axis'"
                class="indicator-filter-menu"
                :class="{ 'is-up': indicatorFilterMenuPlacement.axis.direction === 'up' }"
                :style="{ '--filter-menu-max-height': `${indicatorFilterMenuPlacement.axis.maxHeight}px` }"
                role="listbox"
                aria-label="Choisir un axe stratégique"
              >
                <button
                  v-for="option in axisFilterOptions"
                  :key="option.value || 'all-axis'"
                  type="button"
                  class="indicator-filter-option"
                  :class="{ 'is-selected': selectedAxisCode === option.value }"
                  role="option"
                  :aria-selected="selectedAxisCode === option.value"
                  :style="{ '--option-accent': option.accent ?? '#2f7be8' }"
                  @click="selectAxisFilter(option.value)"
                >
                  <span class="indicator-filter-option__dot" aria-hidden="true" />
                  <span>{{ option.label }}</span>
                </button>
              </div>
            </span>
          </div>

          <div class="indicator-filter-control" @focusout="closeIndicatorFilterMenu">
            <span class="indicator-filter-control__label">Statut</span>
            <span class="indicator-filter-control__shell" :class="{ 'is-active': selectedBreakdownKey }">
              <button
                type="button"
                class="indicator-filter-select"
                :class="{ 'is-open': openIndicatorFilter === 'status' }"
                :aria-expanded="openIndicatorFilter === 'status'"
                aria-haspopup="listbox"
                @click="toggleIndicatorFilterMenu('status', $event)"
                @keydown.escape.prevent="openIndicatorFilter = null"
              >
                <span>{{ selectedStatusFilterLabel }}</span>
              </button>

              <button
                v-if="selectedBreakdownKey"
                type="button"
                class="indicator-filter-clear"
                aria-label="R&eacute;initialiser le filtre statut"
                @click.prevent.stop="resetBreakdownFilter"
              >
                &times;
              </button>

              <div
                v-if="openIndicatorFilter === 'status'"
                class="indicator-filter-menu indicator-filter-menu--status"
                :class="{ 'is-up': indicatorFilterMenuPlacement.status.direction === 'up' }"
                :style="{ '--filter-menu-max-height': `${indicatorFilterMenuPlacement.status.maxHeight}px` }"
                role="listbox"
                aria-label="Choisir un statut"
              >
                <button
                  v-for="option in statusFilterOptions"
                  :key="option.value || 'all-status'"
                  type="button"
                  class="indicator-filter-option"
                  :class="{ 'is-selected': selectedBreakdownKey === option.value }"
                  role="option"
                  :aria-selected="selectedBreakdownKey === option.value"
                  :style="{ '--option-accent': option.accent ?? '#2f7be8' }"
                  @click="selectBreakdownFilter(option.value)"
                >
                  <span class="indicator-filter-option__dot" aria-hidden="true" />
                  <span>{{ option.label }}</span>
                </button>
              </div>
            </span>
          </div>
        </div>

        <div class="kpi-table-wrap kpi-table-wrap--indicator-preview">
          <table class="kpi-table kpi-table--indicators" :style="indicatorTableStyle">
            <thead>
              <tr>
                <th class="indicator-resizable-header">
                  <span>Indicateur</span>
                  <button
                    type="button"
                    class="indicator-resize-handle"
                    aria-label="Ajuster la largeur de la colonne Indicateur"
                    @pointerdown.prevent="startIndicatorColumnResize"
                  />
                </th>
                <th>P&eacute;riode</th>
                <th>Valeur</th>
                <th>Atteinte</th>
                <th>Statut</th>
              </tr>
            </thead>

            <tbody>
              <tr v-if="!previewIndicators.length">
                <td colspan="5">
                  <div class="kpi-filter-empty">
                    Aucun indicateur ne correspond aux filtres actifs.
                  </div>
                </td>
              </tr>

              <tr
                v-for="indicator in previewIndicators"
                :key="indicator.code"
                class="kpi-table__interactive-row indicator-preview-row"
                :class="{ 'is-active': selectedIndicatorCode === indicator.code }"
                :style="{ '--axis-row-accent': indicator.accent }"
                role="button"
                tabindex="0"
                :aria-pressed="selectedIndicatorCode === indicator.code"
                :title="`Analyser ${indicator.code}`"
                @click="selectIndicatorForAnalysis(indicator.code)"
                @keydown.enter.prevent="selectIndicatorForAnalysis(indicator.code)"
                @keydown.space.prevent="selectIndicatorForAnalysis(indicator.code)"
              >
                <td>
                  <div class="indicator-name-cell">
                    <strong class="indicator-name-cell__label" :title="`${indicator.code} ${indicator.label}`">
                      {{ indicator.code }} {{ indicator.label }}
                    </strong>
                  </div>
                </td>

                <td class="kpi-table__muted">{{ indicator.latestPeriodLabel ?? 'N/A' }}</td>

                <td>
                  <strong class="indicator-value-cell">
                    {{ formatIndicatorMetricValue(indicator.latestValue, indicator.valueFormat) }}
                  </strong>
                </td>

                <td>
                  <div class="indicator-rate-cell">
                    <span
                      class="indicator-rate-cell__gauge"
                      :style="rateGaugeStyle(indicator.attainmentRate, indicator.status)"
                    >
                      <svg viewBox="0 0 120 70" aria-hidden="true">
                        <defs>
                          <linearGradient
                            :id="`indicator-rate-gradient-${indicator.code}`"
                            x1="0%"
                            y1="0%"
                            x2="100%"
                            y2="0%"
                          >
                            <stop offset="0%" :stop-color="indicator.status.color" />
                            <stop offset="100%" :stop-color="indicator.status.colorEnd" />
                          </linearGradient>
                        </defs>
                        <path
                          class="indicator-rate-cell__track"
                          d="M 16 56 A 44 44 0 0 1 104 56"
                          pathLength="100"
                        />
                        <path
                          class="indicator-rate-cell__fill"
                          d="M 16 56 A 44 44 0 0 1 104 56"
                          pathLength="100"
                          :stroke="`url(#indicator-rate-gradient-${indicator.code})`"
                        />
                      </svg>
                      <strong>{{ formatRate(indicator.attainmentRate) }}</strong>
                    </span>
                  </div>
                </td>

                <td>
                  <span
                    class="status-pill"
                    :style="{ backgroundColor: indicator.status.soft, color: indicator.status.color }"
                  >
                    {{ indicator.status.shortLabel }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section
        class="panel panel--kpi-surface panel--indicator-analysis"
        :class="{ 'is-summary-open': openSummaryControl === 'range' }"
      >
        <div class="panel__header">
          <h2>Analyse d&apos;un indicateur</h2>
        </div>

        <div v-if="selectedIndicatorAnalysis" class="indicator-analysis-card">
          <div class="indicator-analysis-card__hero">
            <h3>{{ selectedIndicatorAnalysis.label }}</h3>
            <div class="indicator-analysis-card__meta">
              <span :style="{ '--meta-accent': selectedIndicatorAnalysis.accent }">
                {{ selectedIndicatorAnalysis.axisLabel }}
              </span>
              <span>{{ selectedIndicatorAnalysis.latestPeriodLabel ?? 'Période N/A' }}</span>
            </div>
          </div>

          <div class="indicator-analysis-insight">
            <span aria-hidden="true">i</span>
            <p>{{ selectedIndicatorAnalysis.insight }}</p>
          </div>

          <div class="indicator-analysis-card__body">
            <div class="indicator-analysis-gauge">
              <span
                class="status-pill"
                :style="{
                  backgroundColor: selectedIndicatorAnalysis.status.soft,
                  color: selectedIndicatorAnalysis.status.color,
                }"
              >
                {{ selectedIndicatorAnalysis.status.shortLabel }}
              </span>

              <span
                class="indicator-analysis-gauge__visual"
                :style="selectedIndicatorAnalysis.gaugeStyle"
              >
                <svg viewBox="0 0 150 150" aria-hidden="true">
                  <defs>
                    <linearGradient
                      :id="`indicator-analysis-gradient-${selectedIndicatorAnalysis.code}`"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="0%"
                    >
                      <stop offset="0%" :stop-color="selectedIndicatorAnalysis.status.color" />
                      <stop offset="100%" :stop-color="selectedIndicatorAnalysis.status.colorEnd" />
                    </linearGradient>
                  </defs>
                  <circle
                    class="indicator-analysis-gauge__track"
                    cx="75"
                    cy="75"
                    r="54"
                    pathLength="100"
                  />
                  <circle
                    class="indicator-analysis-gauge__fill"
                    cx="75"
                    cy="75"
                    r="54"
                    pathLength="100"
                    :stroke="`url(#indicator-analysis-gradient-${selectedIndicatorAnalysis.code})`"
                  />
                </svg>
                <strong>{{ selectedIndicatorAnalysis.rateLabel }}</strong>
              </span>
            </div>

            <div class="indicator-analysis-metrics">
              <article>
                <span>Valeur</span>
                <strong>{{ selectedIndicatorAnalysis.currentValueLabel }}</strong>
              </article>
              <article>
                <span>Cible</span>
                <strong>{{ selectedIndicatorAnalysis.targetLabel }}</strong>
              </article>
              <div class="indicator-summary-table" @focusout="closeSummaryControl">
                <div class="indicator-summary-table__header">
                  <span>{{ selectedIndicatorAnalysis.summary.title }}</span>
                  <div class="indicator-summary-range">
                    <button
                      type="button"
                      class="indicator-summary-range__trigger"
                      :class="{ 'is-open': openSummaryControl === 'range' }"
                      :aria-expanded="openSummaryControl === 'range'"
                      aria-haspopup="dialog"
                      @click="toggleSummaryControl('range')"
                      @keydown.escape.prevent="openSummaryControl = null"
                    >
                      {{ selectedIndicatorAnalysis.summary.rangeLabel }}
                    </button>

                      <div
                        v-if="openSummaryControl === 'range'"
                        class="indicator-summary-range__menu"
                        :class="{ 'indicator-summary-range__menu--compact': selectedIndicatorAnalysis.summaryRangeLayout === 'compact' }"
                        role="dialog"
                        aria-label="Choisir la plage de synthèse"
                      >
                      <div class="indicator-summary-range__group">
                        <div class="indicator-summary-range__group-title">
                          <span>Début</span>
                          <small>{{ selectedIndicatorAnalysis.summary.entries.length }} mesures</small>
                        </div>

                        <section
                          v-for="group in selectedIndicatorAnalysis.summaryPeriodGroups"
                          :key="`summary-start-year-${group.year}`"
                          class="indicator-summary-range__year"
                        >
                          <strong>{{ group.year }}</strong>
                          <div
                            class="indicator-summary-range__chips"
                            :class="{
                              'indicator-summary-range__chips--quarters': group.layout === 'quarters',
                              'indicator-summary-range__chips--semesters': group.layout === 'semesters',
                              'indicator-summary-range__chips--years': group.layout === 'years',
                            }"
                          >
                            <button
                              v-for="option in group.options"
                              :key="`summary-start-${option.value}`"
                              type="button"
                              :title="option.label"
                              :class="{ 'is-selected': selectedIndicatorAnalysis.summary.range.start === option.value }"
                              @click="selectSummaryBoundary('start', option.value)"
                            >
                              {{ option.shortLabel }}
                            </button>
                          </div>
                        </section>
                      </div>

                      <div class="indicator-summary-range__group">
                        <div class="indicator-summary-range__group-title">
                          <span>Fin</span>
                          <small>{{ selectedIndicatorAnalysis.summary.entries.length }} mesures</small>
                        </div>

                        <section
                          v-for="group in selectedIndicatorAnalysis.summaryPeriodGroups"
                          :key="`summary-end-year-${group.year}`"
                          class="indicator-summary-range__year"
                        >
                          <strong>{{ group.year }}</strong>
                          <div
                            class="indicator-summary-range__chips"
                            :class="{
                              'indicator-summary-range__chips--quarters': group.layout === 'quarters',
                              'indicator-summary-range__chips--semesters': group.layout === 'semesters',
                              'indicator-summary-range__chips--years': group.layout === 'years',
                            }"
                          >
                            <button
                              v-for="option in group.options"
                              :key="`summary-end-${option.value}`"
                              type="button"
                              :title="option.label"
                              :class="{ 'is-selected': selectedIndicatorAnalysis.summary.range.end === option.value }"
                              @click="selectSummaryBoundary('end', option.value)"
                            >
                              {{ option.shortLabel }}
                            </button>
                          </div>
                        </section>
                      </div>
                    </div>
                  </div>
                </div>
                <dl>
                  <template
                    v-for="row in selectedIndicatorAnalysis.summary.rows"
                    :key="row.label"
                  >
                    <dt>{{ row.label }}</dt>
                    <dd v-if="row.key === 'method'" class="indicator-summary-method">
                      <button
                        type="button"
                        :class="{ 'is-selected': selectedIndicatorAnalysis.summaryMethod === 'average' }"
                        :disabled="!selectedIndicatorAnalysis.canChangeSummaryMethod"
                        @click="selectSummaryMethod('average')"
                      >
                        Moyenne
                      </button>
                      <button
                        v-if="selectedIndicatorAnalysis.canChangeSummaryMethod"
                        type="button"
                        :class="{ 'is-selected': selectedIndicatorAnalysis.summaryMethod === 'sum' }"
                        @click="selectSummaryMethod('sum')"
                      >
                        Somme
                      </button>
                    </dd>
                    <dd v-else>{{ row.value }}</dd>
                  </template>
                </dl>
              </div>
            </div>
          </div>

          <div class="indicator-history-chart">
            <div class="indicator-history-chart__header">
              <div>
                <span>{{ selectedIndicatorAnalysis.historyChart.eyebrow }}</span>
              </div>
              <small>{{ selectedIndicatorAnalysis.historyChart.rangeLabel }}</small>
            </div>

            <div
              v-if="selectedIndicatorAnalysis.historyChart.points.length"
              class="indicator-history-chart__canvas"
              :class="`indicator-history-chart__canvas--${selectedIndicatorAnalysis.historyChart.mode}`"
              @mouseenter="showIndicatorHistoryCanvasTooltip(selectedIndicatorAnalysis.historyChart, $event)"
              @mousemove="moveIndicatorHistoryCanvasTooltip(selectedIndicatorAnalysis.historyChart, $event)"
              @mouseleave="hideIndicatorHistoryTooltip()"
            >
              <svg
                :viewBox="`0 0 ${selectedIndicatorAnalysis.historyChart.width} ${selectedIndicatorAnalysis.historyChart.height}`"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <polyline
                  v-if="selectedIndicatorAnalysis.historyChart.targetLine"
                  class="indicator-history-chart__target"
                  :points="selectedIndicatorAnalysis.historyChart.targetLine.points"
                />
                <text
                  v-if="selectedIndicatorAnalysis.historyChart.targetLine"
                  class="indicator-history-chart__target-label"
                  :x="Math.min(selectedIndicatorAnalysis.historyChart.targetLine.x + 38, selectedIndicatorAnalysis.historyChart.width - 20)"
                  :y="selectedIndicatorAnalysis.historyChart.targetLine.y - 6"
                  text-anchor="end"
                >
                  Cible {{ selectedIndicatorAnalysis.historyChart.targetLine.label }}
                </text>

                <path
                  v-if="selectedIndicatorAnalysis.historyChart.mode === 'line'"
                  class="indicator-history-chart__area"
                  :d="selectedIndicatorAnalysis.historyChart.areaPath"
                />
                <polyline
                  v-if="selectedIndicatorAnalysis.historyChart.mode === 'line'"
                  class="indicator-history-chart__line"
                  :points="selectedIndicatorAnalysis.historyChart.polyline"
                />

                <g
                  v-for="(point, index) in selectedIndicatorAnalysis.historyChart.points"
                  :key="`${point.period}-${index}`"
                  class="indicator-history-chart__point"
                  @mouseenter="showIndicatorHistoryTooltip(point, $event)"
                  @mousemove="moveIndicatorHistoryTooltip(point, $event)"
                  @mouseleave="hideIndicatorHistoryTooltip()"
                >
                  <rect
                    class="indicator-history-chart__hover-zone"
                    :x="point.hitX"
                    :y="point.hitY"
                    :width="point.hitWidth"
                    :height="point.hitHeight"
                    @mouseenter="showIndicatorHistoryTooltip(point, $event)"
                    @mousemove="moveIndicatorHistoryTooltip(point, $event)"
                    @mouseleave="hideIndicatorHistoryTooltip()"
                  />
                  <rect
                    v-if="selectedIndicatorAnalysis.historyChart.mode === 'history'"
                    class="indicator-history-chart__bar"
                    :x="point.barX"
                    :y="point.barY"
                    :width="point.barWidth"
                    :height="point.barHeight"
                    rx="8"
                  />
                  <circle class="indicator-history-chart__hit" :cx="point.x" :cy="point.y" r="14" />
                  <circle
                    v-if="selectedIndicatorAnalysis.historyChart.mode === 'line'"
                    :cx="point.x"
                    :cy="point.y"
                    r="4.2"
                  />
                  <text
                    class="indicator-history-chart__value"
                    :x="point.x"
                    :y="point.y - 9"
                    text-anchor="middle"
                  >
                    {{ point.valueLabel }}
                  </text>
                  <text
                    class="indicator-history-chart__label"
                    :x="point.x"
                    :y="selectedIndicatorAnalysis.historyChart.labelY"
                    text-anchor="end"
                    :transform="`rotate(-28 ${point.x} ${selectedIndicatorAnalysis.historyChart.labelY})`"
                  >
                    {{ point.label }}
                  </text>
                </g>
              </svg>
            </div>

            <div v-else class="indicator-history-chart__empty">
              Pas assez d&apos;historique pour afficher cette visualisation.
            </div>
          </div>

          <Teleport to="body">
            <article
              v-if="indicatorHistoryTooltip.visible"
              class="indicator-history-tooltip"
              :style="{ left: `${indicatorHistoryTooltip.x}px`, top: `${indicatorHistoryTooltip.y}px` }"
            >
              <span>{{ indicatorHistoryTooltip.label }}</span>
              <strong>{{ indicatorHistoryTooltip.value }}</strong>
              <small v-if="indicatorHistoryTooltip.meta">{{ indicatorHistoryTooltip.meta }}</small>
            </article>
          </Teleport>
        </div>

        <div v-else class="indicator-analysis-empty">
          <div class="indicator-analysis-empty__icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 34h30M14 29V17m10 12V11m10 18V21" />
              <path d="M11 39h26a3 3 0 0 0 3-3V10a3 3 0 0 0-3-3H11a3 3 0 0 0-3 3v26a3 3 0 0 0 3 3Z" />
            </svg>
          </div>
          <h3>S&eacute;lectionnez un indicateur</h3>
          <p>Cliquez sur une ligne du tableau pour afficher son taux, sa cible, son historique et une lecture rapide.</p>
        </div>
      </section>
    </div>

  </section>
</template>

<style scoped>
.kpi-page {
  display: grid;
  gap: 1rem;
}

.kpi-header {
  position: relative;
  z-index: 120;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.kpi-header__copy h1 {
  margin: 0;
  color: #17314c;
  font-family: 'Arial Black', Arial, sans-serif;
  font-size: clamp(2rem, 3vw, 2.8rem);
  line-height: 0.98;
  letter-spacing: -0.04em;
}

.kpi-header__copy p {
  margin: 0.42rem 0 0;
  color: #607896;
  font-size: 1rem;
  line-height: 1.5;
}

.kpi-header__print-period {
  display: none;
}

.kpi-header__actions {
  position: relative;
  z-index: 130;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.42rem;
  padding: 0.38rem;
  border: 1px solid rgba(211, 225, 241, 0.74);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 18px 34px rgba(22, 46, 73, 0.08);
  backdrop-filter: blur(18px);
}

.kpi-action-group {
  position: relative;
}

.kpi-action-chip {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 0.62rem;
  min-height: 54px;
  padding: 0.66rem 0.78rem;
  border: 1px solid transparent;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.96),
    0 10px 22px rgba(22, 46, 73, 0.055);
  color: #1d3554;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease,
    background 180ms ease;
}

.kpi-action-chip:hover,
.kpi-action-chip.is-open {
  border-color: rgba(47, 123, 232, 0.36);
  background: rgba(255, 255, 255, 1);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.98),
    0 16px 30px rgba(47, 123, 232, 0.13);
  transform: translateY(-1px);
}

.kpi-action-chip svg {
  width: 16px;
  height: 16px;
  stroke: #5c7ea8;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.75;
  fill: none;
  flex: 0 0 auto;
}

.kpi-action-chip__copy {
  display: grid;
  gap: 0.04rem;
}

.kpi-action-chip__copy small {
  color: #6b829e;
  font-size: 0.68rem;
  font-weight: 850;
  letter-spacing: 0.06em;
  line-height: 1;
  text-transform: uppercase;
  white-space: nowrap;
}

.kpi-action-chip__copy strong {
  color: #132e4b;
  font-size: 0.95rem;
  font-weight: 950;
  line-height: 1.08;
  white-space: nowrap;
}

.kpi-action-chip__chevron {
  width: 14px !important;
  height: 14px !important;
  margin-left: 0.02rem;
  transition: transform 180ms ease;
}

.kpi-action-chip.is-open .kpi-action-chip__chevron {
  transform: rotate(180deg);
}

.kpi-action-popover {
  position: absolute;
  top: calc(100% + 0.7rem);
  right: 0;
  z-index: 300;
  display: grid;
  gap: 0.62rem;
  width: 260px;
  padding: 0.82rem;
  border: 1px solid rgba(199, 216, 235, 0.92);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 24px 48px rgba(22, 46, 73, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}

.kpi-action-popover::before {
  content: '';
  position: absolute;
  top: -7px;
  right: 28px;
  width: 14px;
  height: 14px;
  border-left: 1px solid rgba(199, 216, 235, 0.92);
  border-top: 1px solid rgba(199, 216, 235, 0.92);
  background: rgba(255, 255, 255, 0.98);
  transform: rotate(45deg);
}

.kpi-action-popover--export {
  width: 286px;
}

.kpi-action-popover__header {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: start;
}

.kpi-action-popover__header strong {
  display: block;
  margin-top: 0.12rem;
  color: #17314c;
  font-size: 1rem;
  font-weight: 950;
}

.kpi-action-popover__eyebrow {
  color: #6a839f;
  font-size: 0.72rem;
  font-weight: 950;
  letter-spacing: 0.08em;
  line-height: 1.1;
  text-transform: uppercase;
}

.kpi-action-menu-item {
  appearance: none;
  display: grid;
  gap: 0.16rem;
  width: 100%;
  padding: 0.72rem 0.78rem;
  border: 1px solid rgba(217, 227, 239, 0.9);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  color: #17314c;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 170ms ease,
    background 170ms ease,
    transform 170ms ease;
}

.kpi-action-menu-item:hover,
.kpi-action-menu-item.is-selected {
  border-color: rgba(47, 123, 232, 0.35);
  background: rgba(255, 255, 255, 0.96);
  transform: translateX(2px);
}

.kpi-action-menu-item span {
  font-size: 0.95rem;
  font-weight: 950;
  line-height: 1.2;
}

.kpi-action-menu-item small {
  color: #6a839f;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.2;
}

.kpi-period-picker {
  display: grid;
  gap: 0.42rem;
  padding: 0.58rem;
  border: 1px solid rgba(217, 227, 239, 0.82);
  border-radius: 18px;
  background: rgba(246, 250, 254, 0.72);
}

.kpi-period-picker__label {
  color: #6a839f;
  font-size: 0.72rem;
  font-weight: 950;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.kpi-period-picker__years,
.kpi-period-picker__months {
  display: grid;
  gap: 0.34rem;
}

.kpi-period-picker__years {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kpi-period-picker__months {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-period-picker__year,
.kpi-period-picker__month {
  appearance: none;
  min-height: 34px;
  border: 1px solid rgba(205, 220, 238, 0.88);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  color: #17314c;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 900;
  cursor: pointer;
  transition:
    background 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 160ms ease;
}

.kpi-period-picker__year:hover,
.kpi-period-picker__month:hover,
.kpi-period-picker__year.is-selected,
.kpi-period-picker__month.is-selected {
  border-color: rgba(47, 123, 232, 0.45);
  background: rgba(235, 244, 255, 0.94);
  box-shadow: 0 8px 18px rgba(47, 123, 232, 0.12);
  color: #236ed9;
  transform: translateY(-1px);
}

.kpi-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.78rem;
}

.kpi-summary-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.85rem;
  min-width: 0;
  padding: 1rem 1.02rem;
  border: 1px solid rgba(219, 228, 238, 0.96);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, var(--summary-accent-soft), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(247, 250, 254, 0.96));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    0 14px 28px rgba(22, 46, 73, 0.05);
}

.kpi-summary-card__icon {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: var(--summary-accent-soft);
  color: var(--summary-accent);
}

.kpi-summary-card__icon svg {
  width: 28px;
  height: 28px;
  stroke: currentColor;
  stroke-width: 2.1;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}

.kpi-summary-card__content {
  display: grid;
  gap: 0.16rem;
  min-width: 0;
}

.kpi-summary-card__label {
  color: #627995;
  font-size: 0.79rem;
  font-weight: 700;
  line-height: 1.35;
}

.kpi-summary-card__content strong {
  color: #17314c;
  font-size: clamp(1.8rem, 2.4vw, 2.25rem);
  line-height: 0.95;
  letter-spacing: -0.04em;
}

.kpi-summary-card__content small {
  color: #607895;
  font-size: 0.92rem;
  line-height: 1.4;
}

.kpi-main-grid,
.kpi-bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(340px, 0.95fr);
  gap: 0.95rem;
}

.kpi-side-grid {
  display: grid;
  gap: 0.95rem;
}

.panel--kpi-surface {
  overflow: hidden;
  padding: 1rem 1.02rem;
  border-color: rgba(214, 226, 240, 0.92);
  background:
    radial-gradient(circle at top right, rgba(89, 130, 186, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 249, 253, 0.97));
  box-shadow:
    0 18px 38px rgba(22, 46, 73, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
}

.panel--indicator-preview {
  overflow: visible;
}

.panel--kpi-surface .panel__header {
  margin-bottom: 0.82rem;
}

.panel--kpi-surface h2 {
  margin: 0;
  color: #17314c;
  font-size: 1.35rem;
  line-height: 1.2;
}

.kpi-table-wrap {
  overflow-x: auto;
}

.kpi-table-wrap--indicator-preview {
  max-height: 660px;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-color: rgba(118, 143, 171, 0.7) rgba(226, 234, 243, 0.78);
  scrollbar-width: thin;
}

.kpi-table-wrap--indicator-preview thead th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: rgba(244, 248, 252, 0.98);
  backdrop-filter: blur(10px);
}

.kpi-table {
  width: 100%;
  border-collapse: collapse;
}

.kpi-table--indicators {
  table-layout: fixed;
  width: max(100%, var(--indicator-table-width, 100%));
}

.kpi-table thead th {
  padding: 0.72rem 0.65rem;
  border-bottom: 1px solid rgba(220, 228, 238, 0.96);
  color: #5f7895;
  font-size: 0.77rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}

.kpi-table--axis thead th:nth-child(2),
.kpi-table--axis tbody td:nth-child(2) {
  text-align: center;
}

.kpi-table tbody td {
  padding: 0.82rem 0.65rem;
  border-bottom: 1px solid rgba(226, 233, 241, 0.96);
  color: #17314c;
  font-size: 0.94rem;
  line-height: 1.45;
  vertical-align: middle;
}

.kpi-table tbody tr:last-child td {
  border-bottom: none;
}

.kpi-table__interactive-row {
  cursor: pointer;
  outline: none;
}

.kpi-table__interactive-row td {
  transition:
    background 170ms ease,
    box-shadow 170ms ease,
    transform 170ms ease;
}

.kpi-table__interactive-row:hover td,
.kpi-table__interactive-row:focus-visible td {
  background: rgba(47, 123, 232, 0.045);
}

.kpi-table__interactive-row.is-active td {
  background: rgba(47, 123, 232, 0.075);
}

.kpi-table__interactive-row.is-active td:first-child {
  box-shadow: inset 4px 0 0 var(--axis-row-accent, #2f7be8);
}

.kpi-table__muted {
  color: #647c97;
}

.kpi-table--indicators th:first-child,
.kpi-table--indicators td:first-child {
  width: var(--indicator-column-width, 42%);
  min-width: 180px;
}

.kpi-table--indicators td:first-child {
  overflow: hidden;
}

.indicator-resizable-header {
  position: relative;
}

.indicator-resizable-header span {
  display: inline-flex;
  align-items: center;
}

.indicator-resize-handle {
  position: absolute;
  top: 0.48rem;
  right: 0;
  bottom: 0.48rem;
  width: 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  cursor: col-resize;
}

.indicator-resize-handle::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 3px;
  height: 70%;
  border-radius: 999px;
  background: rgba(118, 143, 171, 0.35);
  transform: translate(-50%, -50%);
  transition:
    background 160ms ease,
    box-shadow 160ms ease;
}

.indicator-resize-handle:hover::after,
.indicator-resize-handle:focus-visible::after {
  background: rgba(47, 123, 232, 0.78);
  box-shadow: 0 0 0 4px rgba(47, 123, 232, 0.12);
}

.indicator-filter-controls {
  position: relative;
  z-index: 30;
  display: grid;
  grid-template-columns: minmax(220px, 1.25fr) minmax(180px, 0.75fr);
  gap: 0.72rem;
  align-items: end;
  margin: -0.12rem 0 0.8rem;
}

.indicator-filter-control {
  display: grid;
  gap: 0.38rem;
  min-width: 0;
}

.indicator-filter-control__label {
  color: #637c98;
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.indicator-filter-control__shell {
  position: relative;
  display: block;
  min-width: 0;
  border-radius: 18px;
}

.indicator-filter-control__shell::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background: rgba(241, 246, 252, 0.92);
  box-shadow:
    0 14px 26px rgba(22, 46, 73, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.indicator-filter-control__shell.is-active::before {
  background: rgba(235, 243, 252, 0.96);
  box-shadow:
    0 16px 30px rgba(47, 123, 232, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.indicator-filter-select {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  width: 100%;
  min-height: 50px;
  border: 1px solid rgba(199, 216, 235, 0.88);
  border-radius: 17px;
  padding: 0.68rem 3.45rem 0.68rem 0.94rem;
  background: rgba(255, 255, 255, 0.94);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    inset 0 -14px 24px rgba(218, 229, 241, 0.2);
  color: #17314c;
  cursor: pointer;
  font: inherit;
  font-size: 0.93rem;
  font-weight: 900;
  text-align: left;
  outline: none;
  transition:
    border-color 170ms ease,
    box-shadow 170ms ease,
    transform 170ms ease;
}

.indicator-filter-select::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 1.08rem;
  width: 8px;
  height: 8px;
  border-right: 2px solid #557391;
  border-bottom: 2px solid #557391;
  transform: translateY(-65%) rotate(45deg);
  pointer-events: none;
}

.indicator-filter-select span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-filter-select:hover,
.indicator-filter-select:focus-visible,
.indicator-filter-select.is-open {
  border-color: rgba(47, 123, 232, 0.62);
  box-shadow:
    0 0 0 4px rgba(47, 123, 232, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}

.indicator-filter-clear {
  position: absolute;
  z-index: 2;
  top: 50%;
  right: 2.12rem;
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 50%;
  background: rgba(222, 232, 244, 0.96);
  color: #58718c;
  cursor: pointer;
  font: inherit;
  font-size: 1.05rem;
  font-weight: 900;
  line-height: 1;
  transform: translateY(-50%);
  transition:
    background 160ms ease,
    color 160ms ease,
    transform 160ms ease,
    box-shadow 160ms ease;
}

.indicator-filter-clear:hover,
.indicator-filter-clear:focus-visible {
  outline: none;
  background: #e24b43;
  color: #fff;
  box-shadow: 0 8px 16px rgba(226, 75, 67, 0.22);
  transform: translateY(-50%) scale(1.04);
}

.indicator-filter-menu {
  position: absolute;
  z-index: 40;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  display: grid;
  gap: 0.22rem;
  max-height: var(--filter-menu-max-height, 292px);
  padding: 0.42rem;
  overflow: auto;
  border: 1px solid rgba(198, 216, 236, 0.94);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.995);
  box-shadow:
    0 24px 46px rgba(22, 46, 73, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
  scrollbar-color: rgba(118, 143, 171, 0.65) transparent;
  scrollbar-width: thin;
  transform-origin: top center;
  animation: filter-menu-drop 150ms ease both;
}

.indicator-filter-menu.is-up {
  top: auto;
  bottom: calc(100% + 0.5rem);
  transform-origin: bottom center;
  animation-name: filter-menu-rise;
}

.indicator-filter-option {
  display: flex;
  gap: 0.58rem;
  align-items: center;
  width: 100%;
  min-height: 42px;
  padding: 0.58rem 0.68rem;
  border: 0;
  border-radius: 13px;
  background: transparent;
  color: #17314c;
  cursor: pointer;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 850;
  line-height: 1.2;
  text-align: left;
  transition:
    background 150ms ease,
    color 150ms ease,
    transform 150ms ease,
    box-shadow 150ms ease;
}

.indicator-filter-option__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--option-accent, #2f7be8);
  box-shadow: 0 0 0 4px rgba(229, 237, 246, 0.92);
  flex: 0 0 auto;
  opacity: 0.86;
}

.indicator-filter-option:hover,
.indicator-filter-option:focus-visible,
.indicator-filter-option.is-selected {
  outline: none;
  background: rgba(47, 123, 232, 0.1);
  color: #0f2f57;
  transform: translateX(2px);
}

.indicator-filter-option.is-selected {
  box-shadow: inset 3px 0 0 var(--option-accent, #2f7be8);
}

@keyframes filter-menu-drop {
  from {
    opacity: 0;
    transform: translateY(-6px) scale(0.985);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes filter-menu-rise {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.985);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.kpi-table--indicators thead th:not(:first-child),
.kpi-table--indicators tbody td:not(:first-child) {
  text-align: center;
}

.kpi-table--indicators th:nth-child(4),
.kpi-table--indicators td:nth-child(4) {
  min-width: 148px;
}

.axis-name-cell {
  display: flex;
  gap: 0.72rem;
  align-items: center;
  min-width: 0;
}

.axis-name-cell__tag {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 800;
  flex: 0 0 auto;
}

.axis-name-cell__copy {
  min-width: 0;
}

.axis-name-cell__copy strong,
.indicator-name-cell strong {
  color: #17314c;
}

.axis-rate-cell,
.indicator-rate-cell {
  display: flex;
  gap: 0.7rem;
  align-items: center;
}

.axis-rate-cell__track {
  width: 100%;
  max-width: 132px;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(224, 232, 241, 0.96);
}

.axis-rate-cell__fill {
  display: block;
  height: 100%;
  border-radius: 999px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0.34rem 0.68rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  white-space: nowrap;
}

.kpi-donut-layout {
  display: block;
}

.kpi-donut-top-legend {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.42rem;
  align-items: center;
  justify-content: center;
  margin: -0.1rem 0 -0.9rem;
  padding: 0 0.1rem;
}

.kpi-donut-top-legend__item {
  display: inline-flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0.34rem;
  min-width: 0;
  min-height: 34px;
  padding: 0.26rem 0.42rem;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: #405a76;
  cursor: pointer;
  font: inherit;
  text-align: left;
  line-height: 1;
  transition:
    color 160ms ease,
    transform 160ms ease;
}

.kpi-donut-top-legend__item:hover,
.kpi-donut-top-legend__item:focus-visible,
.kpi-donut-top-legend__item.is-active {
  color: #17314c;
  outline: none;
  transform: translateY(-1px);
}

.kpi-donut-top-legend__item.is-selected {
  border-color: rgba(47, 123, 232, 0.28);
  background:
    radial-gradient(circle at left, rgba(47, 123, 232, 0.14), transparent 62%),
    rgba(255, 255, 255, 0.88);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.96),
    0 10px 20px rgba(22, 46, 73, 0.08);
}

.kpi-donut-top-legend__dot {
  width: 11px;
  height: 11px;
  margin-top: 0.18rem;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(232, 239, 247, 0.9);
  flex: 0 0 auto;
}

.kpi-donut-top-legend__item.is-selected .kpi-donut-top-legend__dot {
  transform: scale(1.18);
  box-shadow:
    0 0 0 4px rgba(255, 255, 255, 0.96),
    0 0 0 8px rgba(47, 123, 232, 0.16),
    0 8px 16px rgba(22, 46, 73, 0.12);
}

.kpi-donut-top-legend__copy {
  display: grid;
  gap: 0.12rem;
  min-width: 0;
}

.kpi-donut-top-legend__copy strong {
  color: inherit;
  font-size: 0.86rem;
  font-weight: 900;
  line-height: 1.05;
  white-space: nowrap;
}

.kpi-donut-top-legend__copy small {
  color: #7187a1;
  font-size: 0.78rem;
  font-weight: 900;
  line-height: 1.05;
  white-space: nowrap;
}

.kpi-donut-shell {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: -0.55rem;
}

.kpi-donut-stage {
  position: relative;
  width: min(100%, 560px);
  aspect-ratio: 560 / 360;
  margin: 0 auto;
}

.kpi-donut-svg {
  width: 100%;
  height: 100%;
  display: block;
  overflow: visible;
}

.kpi-donut-track {
  fill: none;
  stroke: rgba(224, 232, 241, 0.98);
  stroke-width: 48;
}

.kpi-donut-segment {
  cursor: pointer;
  outline: none;
}

.kpi-donut-segment path {
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    filter 180ms ease;
  stroke: rgba(255, 255, 255, 0.98);
  stroke-width: 6;
  stroke-linejoin: round;
  filter: drop-shadow(0 12px 20px rgba(22, 46, 73, 0.12));
  transform-box: fill-box;
  transform-origin: center;
}

.kpi-donut-segment.is-active path {
  filter: drop-shadow(0 16px 24px rgba(22, 46, 73, 0.18));
  transform: scale(1.02);
}

.kpi-donut-segment.is-selected path {
  stroke: rgba(255, 255, 255, 1);
  stroke-width: 9;
  filter:
    drop-shadow(0 0 0 rgba(255, 255, 255, 1))
    drop-shadow(0 16px 26px rgba(22, 46, 73, 0.22))
    drop-shadow(0 0 18px rgba(47, 123, 232, 0.2));
  transform: scale(1.055);
}

.kpi-donut-label {
  cursor: pointer;
  outline: none;
}

.kpi-donut-label__line {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: square;
  stroke-linejoin: miter;
  opacity: 0.74;
  transition:
    stroke 180ms ease,
    opacity 180ms ease;
}

.kpi-donut-label__text {
  fill: #3f5875;
  dominant-baseline: hanging;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.94);
  stroke-linejoin: round;
  stroke-width: 3.2px;
}

.kpi-donut-label__title {
  font-weight: 900;
}

.kpi-donut-label__criteria {
  font-weight: 900;
}

.kpi-donut-label__value {
  font-weight: 900;
}

.kpi-donut-label.is-active .kpi-donut-label__text {
  fill: #17314c;
}

.kpi-donut-label.is-selected .kpi-donut-label__text {
  fill: #102b47;
  stroke: rgba(255, 255, 255, 1);
  stroke-width: 4.2px;
}

.kpi-donut-label.is-active .kpi-donut-label__line {
  opacity: 1;
  stroke-width: 2.6;
}

.kpi-donut-label.is-selected .kpi-donut-label__line {
  opacity: 1;
  stroke-width: 4;
  filter: drop-shadow(0 7px 10px rgba(22, 46, 73, 0.16));
}

.kpi-donut__center {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0;
  padding: 0.5rem;
  border-radius: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.995), rgba(247, 250, 255, 0.97));
  box-shadow:
    inset 0 0 0 2px rgba(223, 231, 240, 0.92),
    0 10px 20px rgba(22, 46, 73, 0.08);
  text-align: center;
}

.kpi-donut__center strong {
  color: #17314c;
  font-size: clamp(2.55rem, 3.15vw, 3.15rem);
  line-height: 0.84;
  letter-spacing: -0.04em;
  margin: 0;
}

.kpi-donut__center span {
  color: #59728e;
  font-weight: 800;
  line-height: 1;
  margin-top: -0.2rem;
  font-size: clamp(0.9rem, 1.15vw, 1.05rem);
}

.kpi-donut-tooltip-card {
  position: fixed;
  z-index: 80;
  display: grid;
  gap: 0.2rem;
  place-items: center;
  min-width: 128px;
  padding: 0.72rem 0.9rem 0.78rem;
  border: 1px solid rgba(214, 226, 240, 0.96);
  border-radius: 18px;
  background:
    linear-gradient(90deg, var(--donut-tooltip-accent) 0 4px, transparent 4px),
    radial-gradient(circle at top right, var(--donut-tooltip-soft) 0, rgba(255, 255, 255, 0) 62%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.985), rgba(246, 249, 253, 0.97));
  box-shadow:
    0 18px 34px rgba(22, 46, 73, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  color: #17314c;
  pointer-events: none;
}

.kpi-donut-tooltip-card__label {
  color: #566f8c;
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.12;
  text-align: center;
  white-space: nowrap;
}

.kpi-donut-tooltip-card__count {
  color: #17314c;
  font-size: 0.95rem;
  font-weight: 900;
  line-height: 1.1;
  text-align: center;
  white-space: nowrap;
}

.kpi-donut-tooltip-card strong {
  color: #17314c;
  font-size: 1.46rem;
  line-height: 1;
  letter-spacing: 0;
  margin-top: 0.04rem;
}

.kpi-donut-note {
  margin: 0.25rem 0 0;
  color: #6a839f;
  font-size: 0.84rem;
  line-height: 1.5;
}

.trend-chart {
  min-height: 268px;
}

.trend-chart__svg {
  display: block;
  width: 100%;
  height: auto;
}

.trend-chart__point {
  cursor: pointer;
}

.trend-chart__point circle:not(.trend-chart__hit) {
  transition:
    r 160ms ease,
    filter 160ms ease;
}

.trend-chart__point:hover circle:not(.trend-chart__hit) {
  r: 6;
  filter: drop-shadow(0 8px 14px rgba(47, 123, 232, 0.26));
}

.trend-chart__grid-line {
  stroke: rgba(214, 224, 235, 0.96);
  stroke-width: 1;
  stroke-dasharray: 4 4;
}

.trend-chart__tick {
  fill: #6f86a0;
  font-size: 11px;
  font-weight: 700;
}

.trend-chart__area {
  fill: rgba(47, 123, 232, 0.08);
}

.trend-chart__line {
  fill: none;
  stroke: #2f7be8;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.trend-chart__dot {
  fill: #2f7be8;
  stroke: rgba(255, 255, 255, 0.98);
  stroke-width: 2.5;
}

.trend-chart__value {
  fill: #17314c;
  font-size: 11px;
  font-weight: 800;
  text-anchor: middle;
}

.trend-chart__label {
  fill: #667f9a;
  font-size: 11px;
  font-weight: 700;
  text-anchor: middle;
}

.trend-chart-tooltip {
  position: fixed;
  z-index: 80;
  display: grid;
  gap: 0.18rem;
  min-width: 112px;
  padding: 0.62rem 0.78rem;
  border: 1px solid rgba(195, 216, 245, 0.95);
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(47, 123, 232, 0.16), transparent 58%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 248, 253, 0.97));
  box-shadow: 0 16px 30px rgba(22, 46, 73, 0.14);
  color: #17314c;
  pointer-events: none;
}

.trend-chart-tooltip span {
  color: #637d99;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.1;
  white-space: nowrap;
}

.trend-chart-tooltip strong {
  color: #17314c;
  font-size: 1.32rem;
  line-height: 1;
}

.kpi-empty-state {
  display: grid;
  place-items: center;
  min-height: 220px;
  color: #6c839d;
  text-align: center;
}

.indicator-name-cell {
  display: block;
  max-width: 100%;
  min-width: 0;
}

.indicator-name-cell__label {
  display: -webkit-box;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-height: 1.32;
}

.indicator-value-cell {
  color: #17314c;
  font-size: 1.18rem;
  font-weight: 900;
  line-height: 1;
}

.indicator-rate-cell__gauge {
  position: relative;
  display: grid;
  place-items: center;
  width: 108px;
  height: 64px;
}

.indicator-rate-cell__gauge svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.indicator-rate-cell__track,
.indicator-rate-cell__fill {
  fill: none;
  stroke-width: 12;
  stroke-linecap: round;
}

.indicator-rate-cell__track {
  stroke: rgba(226, 234, 242, 0.96);
}

.indicator-rate-cell__fill {
  stroke-dasharray: var(--rate-gauge-dash);
  filter: drop-shadow(0 5px 8px rgba(22, 46, 73, 0.08));
}

.indicator-rate-cell__gauge strong {
  position: relative;
  z-index: 1;
  align-self: end;
  margin-bottom: 0.52rem;
  color: #17314c;
  font-size: 0.9rem;
  font-weight: 900;
  line-height: 1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.72);
}

.kpi-filter-empty {
  display: grid;
  place-items: center;
  min-height: 92px;
  border: 1px dashed rgba(182, 202, 224, 0.88);
  border-radius: 18px;
  background: rgba(246, 250, 254, 0.86);
  color: #67809c;
  font-weight: 800;
  text-align: center;
}

.panel--indicator-analysis {
  position: relative;
  z-index: 2;
  min-width: 0;
  min-height: 620px;
  overflow: visible;
}

.panel--indicator-analysis.is-summary-open {
  z-index: 120;
}

.panel--indicator-analysis.is-summary-open .indicator-analysis-card,
.panel--indicator-analysis.is-summary-open .indicator-analysis-card__body,
.panel--indicator-analysis.is-summary-open .indicator-analysis-metrics,
.panel--indicator-analysis.is-summary-open .indicator-summary-table {
  overflow: visible;
}

.indicator-analysis-card {
  display: grid;
  gap: 0.82rem;
  min-width: 0;
  min-height: 540px;
  max-width: 100%;
}

.indicator-analysis-card__hero {
  display: grid;
  gap: 0.58rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid rgba(207, 222, 239, 0.86);
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(47, 123, 232, 0.12), transparent 44%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(244, 249, 254, 0.9));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 16px 32px rgba(22, 46, 73, 0.08);
}

.indicator-analysis-card__hero h3 {
  margin: 0;
  color: #17314c;
  font-size: clamp(0.98rem, 1.22vw, 1.12rem);
  line-height: 1.22;
  overflow-wrap: anywhere;
}

.indicator-analysis-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.48rem;
  align-items: center;
}

.indicator-analysis-card__meta span {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-height: 28px;
  padding: 0.24rem 0.56rem;
  border-radius: 999px;
  background: rgba(232, 240, 249, 0.92);
  color: #5e7895;
  font-size: 0.78rem;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-analysis-card__meta span:first-child {
  background:
    linear-gradient(90deg, var(--meta-accent, #2f7be8) 0 4px, transparent 4px),
    rgba(232, 240, 249, 0.92);
  color: #17314c;
  padding-left: 0.72rem;
}

.indicator-analysis-card__body {
  display: grid;
  grid-template-columns: minmax(170px, 0.78fr) minmax(0, 1.22fr);
  gap: 0.82rem;
  align-items: stretch;
  min-width: 0;
}

.indicator-analysis-gauge,
.indicator-analysis-metrics article,
.indicator-summary-table,
.indicator-analysis-insight,
.indicator-history-chart,
.indicator-analysis-empty {
  border: 1px solid rgba(211, 225, 241, 0.88);
  background:
    radial-gradient(circle at top right, rgba(47, 123, 232, 0.08), transparent 44%),
    rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92);
}

.indicator-analysis-gauge {
  display: grid;
  gap: 0.58rem;
  place-items: center;
  padding: 0.92rem 0.75rem;
  border-radius: 24px;
}

.indicator-analysis-gauge__visual {
  position: relative;
  display: grid;
  place-items: center;
  width: min(100%, 158px);
  aspect-ratio: 1;
}

.indicator-analysis-gauge__visual svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.indicator-analysis-gauge__track,
.indicator-analysis-gauge__fill {
  fill: none;
  stroke-width: 15;
  stroke-linecap: round;
}

.indicator-analysis-gauge__track {
  stroke: rgba(224, 233, 243, 0.96);
}

.indicator-analysis-gauge__fill {
  stroke-dasharray: var(--rate-gauge-dash);
  transform: rotate(-90deg);
  transform-box: fill-box;
  transform-origin: center;
  filter: drop-shadow(0 9px 13px rgba(22, 46, 73, 0.1));
}

.indicator-analysis-gauge__visual strong {
  position: relative;
  z-index: 1;
  color: #17314c;
  font-size: clamp(1.34rem, 2.28vw, 1.88rem);
  font-weight: 950;
  line-height: 1;
  letter-spacing: -0.04em;
}

.indicator-analysis-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.72rem;
  min-width: 0;
}

.indicator-analysis-metrics article {
  display: grid;
  gap: 0.26rem;
  align-content: center;
  min-height: 64px;
  padding: 0.58rem 0.72rem;
  border-radius: 20px;
}

.indicator-analysis-metrics article > span {
  color: #6a839f;
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.indicator-analysis-metrics strong {
  color: #17314c;
  font-size: clamp(0.98rem, 1.28vw, 1.12rem);
  font-weight: 950;
  line-height: 1.18;
}

.indicator-summary-table {
  display: grid;
  grid-column: 1 / -1;
  gap: 0.62rem;
  min-width: 0;
  padding: 0.78rem;
  border-radius: 20px;
}

.indicator-summary-table__header {
  display: flex;
  justify-content: space-between;
  gap: 0.72rem;
  align-items: baseline;
  min-width: 0;
}

.indicator-summary-table__header span {
  color: #17314c;
  font-size: 0.9rem;
  font-weight: 950;
  line-height: 1.15;
}

.indicator-summary-range {
  position: relative;
  display: inline-flex;
  min-width: 0;
}

.indicator-summary-range__trigger {
  appearance: none;
  max-width: 190px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #6b849f;
  cursor: pointer;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 900;
  line-height: 1.2;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.indicator-summary-range__trigger:hover,
.indicator-summary-range__trigger:focus-visible,
.indicator-summary-range__trigger.is-open {
  outline: none;
  color: #2f6fd0;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}

.indicator-summary-range__menu {
  position: absolute;
  top: calc(100% + 0.48rem);
  right: 0;
  z-index: 70;
  display: grid;
  grid-template-columns: repeat(2, minmax(190px, 1fr));
  gap: 0.72rem;
  width: min(520px, calc(100vw - 3rem));
  padding: 0.72rem;
  border: 1px solid rgba(198, 216, 236, 0.94);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.995);
  box-shadow:
    0 22px 42px rgba(22, 46, 73, 0.17),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}

.indicator-summary-range__menu--compact {
  grid-template-columns: repeat(2, minmax(136px, 1fr));
  gap: 0.42rem;
  width: min(340px, calc(100vw - 3rem));
}

.indicator-summary-range__group {
  display: grid;
  align-content: start;
  gap: 0.58rem;
  max-height: min(330px, calc(100vh - 9rem));
  overflow: auto;
  padding: 0 0.12rem 0.08rem 0;
  scrollbar-color: rgba(118, 143, 171, 0.65) transparent;
  scrollbar-width: thin;
}

.indicator-summary-range__group-title {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: center;
  padding: 0.14rem 0 0.24rem;
  background: rgba(250, 253, 255, 0.98);
}

.indicator-summary-range__group-title span {
  color: #6a839f;
  font-size: 0.68rem;
  font-weight: 950;
  letter-spacing: 0.08em;
  line-height: 1.1;
  text-transform: uppercase;
}

.indicator-summary-range__group-title small {
  color: #8ba1b8;
  font-size: 0.62rem;
  font-weight: 900;
  line-height: 1.1;
  white-space: nowrap;
}

.indicator-summary-range__year {
  display: grid;
  gap: 0.32rem;
}

.indicator-summary-range__year strong {
  color: #17314c;
  font-size: 0.76rem;
  font-weight: 950;
  letter-spacing: 0.01em;
  line-height: 1;
}

.indicator-summary-range__chips {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.3rem;
}

.indicator-summary-range__chips--quarters {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.indicator-summary-range__chips--semesters {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.indicator-summary-range__chips--years {
  grid-template-columns: minmax(0, 1fr);
}

.indicator-summary-range__chips--quarters,
.indicator-summary-range__chips--semesters {
  max-width: 224px;
}

.indicator-summary-range__chips--years {
  max-width: 106px;
}

.indicator-summary-range__chips button {
  appearance: none;
  min-height: 30px;
  min-width: 0;
  padding: 0.38rem 0.32rem;
  border: 1px solid rgba(217, 227, 239, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
  color: #17314c;
  cursor: pointer;
  font: inherit;
  font-size: 0.76rem;
  font-weight: 850;
  line-height: 1.15;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.indicator-summary-range__chips button:hover,
.indicator-summary-range__chips button:focus-visible,
.indicator-summary-range__chips button.is-selected {
  outline: none;
  border-color: rgba(47, 123, 232, 0.42);
  background: rgba(235, 244, 255, 0.94);
  color: #236ed9;
}

.indicator-summary-range__chips button.is-selected {
  box-shadow:
    0 10px 18px rgba(47, 123, 232, 0.12),
    inset 0 0 0 1px rgba(47, 123, 232, 0.18);
}

.indicator-summary-table dl {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.42rem 0.72rem;
  margin: 0;
}

.indicator-summary-table dt,
.indicator-summary-table dd {
  margin: 0;
  padding-top: 0.42rem;
  border-top: 1px solid rgba(218, 228, 240, 0.78);
  line-height: 1.18;
}

.indicator-summary-table dt {
  color: #6a839f;
  font-size: 0.74rem;
  font-weight: 850;
}

.indicator-summary-table dd {
  color: #17314c;
  font-size: 0.82rem;
  font-weight: 950;
  text-align: right;
}

.indicator-summary-method {
  display: inline-flex;
  justify-content: flex-end;
  gap: 0.22rem;
  min-width: 0;
}

.indicator-summary-method button {
  appearance: none;
  min-height: 24px;
  padding: 0.18rem 0.42rem;
  border: 1px solid rgba(211, 225, 241, 0.9);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #5f7895;
  cursor: pointer;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 950;
  line-height: 1;
}

.indicator-summary-method button.is-selected {
  border-color: rgba(47, 123, 232, 0.35);
  background: rgba(47, 123, 232, 0.12);
  color: #236ed9;
}

.indicator-summary-method button:disabled {
  cursor: default;
}

.indicator-analysis-insight {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.56rem;
  align-items: center;
  min-width: 0;
  padding: 0.82rem 0.9rem;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(47, 123, 232, 0.16), transparent 42%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(242, 248, 255, 0.88));
  color: #4f6f95;
  line-height: 1.28;
}

.indicator-analysis-insight span {
  display: inline-grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #2f7be8;
  color: #fff;
  font-weight: 900;
  font-style: italic;
}

.indicator-analysis-insight p {
  margin: 0;
  color: #4f6f95;
  font-size: clamp(0.82rem, 1.03vw, 0.95rem);
  font-weight: 850;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-history-chart {
  display: grid;
  gap: 0.52rem;
  min-width: 0;
  max-width: 100%;
  padding: 0.86rem 0.92rem 0.78rem;
  border-radius: 22px;
  overflow: hidden;
}

.indicator-history-chart__header {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: start;
  min-width: 0;
}

.indicator-history-chart__header > div {
  min-width: 0;
}

.indicator-history-chart__header span {
  color: #6a839f;
  font-size: 0.82rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.indicator-history-chart__header h3 {
  margin: 0.08rem 0 0;
  color: #17314c;
  font-size: 1rem;
  line-height: 1.1;
}

.indicator-history-chart__header small {
  color: #6b849f;
  font-size: 0.74rem;
  font-weight: 850;
  line-height: 1.25;
  max-width: 46%;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-history-chart__canvas {
  height: 226px;
  border-radius: 18px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(47, 123, 232, 0.06), transparent 58%),
    rgba(246, 250, 254, 0.82);
}

.indicator-history-chart__canvas--history {
  background:
    radial-gradient(circle at 50% 0%, rgba(47, 123, 232, 0.12), transparent 42%),
    linear-gradient(180deg, rgba(47, 123, 232, 0.05), rgba(255, 255, 255, 0.76));
}

.indicator-history-chart__canvas svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.indicator-history-chart__target {
  fill: none;
  stroke: rgba(95, 120, 149, 0.48);
  stroke-width: 1.4;
  stroke-dasharray: 5 5;
}

.indicator-history-chart__target-label {
  fill: #6b849f;
  font-size: 11px;
  font-weight: 850;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.9);
  stroke-width: 3px;
}

.indicator-history-chart__area {
  fill: rgba(47, 123, 232, 0.13);
}

.indicator-history-chart__line {
  fill: none;
  stroke: #2f7be8;
  stroke-width: 3.4;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 8px 12px rgba(47, 123, 232, 0.18));
}

.indicator-history-chart__bar {
  fill: rgba(47, 123, 232, 0.72);
  stroke: rgba(255, 255, 255, 0.8);
  stroke-width: 1;
  filter: drop-shadow(0 10px 14px rgba(47, 123, 232, 0.14));
  transition:
    fill 160ms ease,
    opacity 160ms ease,
    filter 160ms ease;
}

.indicator-history-chart__hover-zone {
  fill: transparent;
  pointer-events: all;
}

.indicator-history-chart__point circle {
  fill: #2f7be8;
  stroke: #fff;
  stroke-width: 2.4;
}

.indicator-history-chart__point {
  cursor: pointer;
  pointer-events: all;
}

.indicator-history-chart__hit {
  fill: transparent !important;
  stroke: transparent !important;
  stroke-width: 0 !important;
}

.indicator-history-chart__point:hover circle:not(.indicator-history-chart__hit) {
  r: 6.2;
  filter: drop-shadow(0 8px 14px rgba(47, 123, 232, 0.28));
}

.indicator-history-chart__point:hover .indicator-history-chart__bar {
  fill: rgba(47, 123, 232, 0.92);
  filter: drop-shadow(0 12px 18px rgba(47, 123, 232, 0.24));
}

.indicator-history-chart__point:hover .indicator-history-chart__value {
  fill: #0f2e4a;
  font-size: 11.5px;
}

.indicator-history-chart__value {
  fill: #17314c;
  font-size: 10px;
  font-weight: 900;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.92);
  stroke-width: 3px;
}

.indicator-history-chart__label {
  fill: #6d849f;
  font-size: 9.8px;
  font-weight: 850;
}

.indicator-history-chart__empty {
  display: grid;
  place-items: center;
  min-height: 132px;
  border-radius: 18px;
  background: rgba(246, 250, 254, 0.86);
  color: #6c839d;
  font-weight: 800;
  text-align: center;
}

.indicator-history-tooltip {
  position: fixed;
  z-index: 9999;
  display: grid;
  gap: 0.22rem;
  min-width: 118px;
  padding: 0.66rem 0.82rem;
  border: 1px solid rgba(195, 216, 245, 0.95);
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(47, 123, 232, 0.16), transparent 58%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.985), rgba(244, 248, 253, 0.97));
  box-shadow: 0 16px 30px rgba(22, 46, 73, 0.15);
  color: #17314c;
  pointer-events: none;
}

.indicator-history-tooltip span {
  color: #637d99;
  font-size: 0.78rem;
  font-weight: 850;
  line-height: 1.1;
  white-space: nowrap;
}

.indicator-history-tooltip strong {
  color: #17314c;
  font-size: 1.32rem;
  line-height: 1;
}

.indicator-history-tooltip small {
  color: #58708b;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1.15;
  white-space: nowrap;
}

.indicator-analysis-empty {
  display: grid;
  gap: 0.72rem;
  place-items: center;
  min-height: 520px;
  padding: 1.4rem;
  border-radius: 28px;
  color: #607b99;
  text-align: center;
}

.indicator-analysis-empty__icon {
  display: grid;
  place-items: center;
  width: 82px;
  height: 82px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(47, 123, 232, 0.2), transparent 54%),
    rgba(235, 243, 252, 0.98);
  color: #2f7be8;
}

.indicator-analysis-empty__icon svg {
  width: 44px;
  height: 44px;
}

.indicator-analysis-empty h3 {
  margin: 0;
  color: #17314c;
  font-size: 1.24rem;
}

.indicator-analysis-empty p {
  max-width: 340px;
  margin: 0;
  line-height: 1.55;
}

@media print {
  @page {
    size: A4 landscape;
    margin: 10mm;
  }

  :global(html),
  :global(body),
  :global(#app) {
    min-height: 0 !important;
    background: #ffffff !important;
  }

  :global(body) {
    color: #17314c !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  :global(.shell) {
    display: block !important;
    min-height: 0 !important;
    padding: 0 !important;
  }

  :global(.sidebar),
  :global(.hero-anchor) {
    display: none !important;
  }

  :global(.workspace),
  :global(.content-grid),
  :global(.content-main) {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
  }

  .kpi-header__actions,
  .kpi-action-popover,
  .indicator-filter-controls,
  .indicator-resize-handle,
  .kpi-donut-tooltip-card,
  .trend-chart-tooltip,
  .indicator-history-tooltip {
    display: none !important;
  }

  .kpi-page {
    display: block;
    color: #17314c;
  }

  .kpi-header {
    display: block;
    margin-bottom: 5mm;
    padding-bottom: 3mm;
    border-bottom: 1px solid #cbd7e5;
  }

  .kpi-header__copy h1 {
    font-size: 22pt;
    letter-spacing: -0.03em;
  }

  .kpi-header__copy p {
    margin-top: 1mm;
    font-size: 9pt;
  }

  .kpi-header__print-period {
    display: block;
    color: #17314c !important;
    font-weight: 800;
  }

  .kpi-summary-grid,
  .kpi-main-grid,
  .kpi-bottom-grid {
    gap: 4mm;
    margin-bottom: 4mm;
  }

  .kpi-summary-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .kpi-main-grid {
    grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
    align-items: start;
  }

  .kpi-bottom-grid {
    grid-template-columns: 1fr;
  }

  .kpi-side-grid {
    gap: 4mm;
  }

  .panel--kpi-surface,
  .kpi-summary-card {
    border: 1px solid #cbd7e5 !important;
    background: #ffffff !important;
    box-shadow: none !important;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .panel--kpi-surface {
    padding: 4mm;
    border-radius: 6mm;
  }

  .panel--indicator-preview {
    break-inside: auto;
    page-break-inside: auto;
  }

  .panel--indicator-analysis {
    min-height: 0;
  }

  .kpi-summary-card {
    gap: 2.5mm;
    padding: 3.5mm;
    border-radius: 5mm;
  }

  .kpi-summary-card__icon {
    width: 11mm;
    height: 11mm;
    border-radius: 4mm;
  }

  .kpi-summary-card__content strong {
    font-size: 18pt;
  }

  .kpi-summary-card__content small,
  .kpi-summary-card__label,
  .panel__meta,
  .kpi-table tbody td,
  .kpi-table thead th {
    font-size: 8pt;
  }

  .panel--kpi-surface h2 {
    font-size: 13pt;
  }

  .kpi-table-wrap,
  .kpi-table-wrap--indicator-preview {
    max-height: none !important;
    overflow: visible !important;
  }

  .kpi-table-wrap--indicator-preview thead th {
    position: static;
  }

  .kpi-table--indicators {
    width: 100% !important;
    table-layout: fixed;
  }

  .kpi-table--indicators th:first-child,
  .kpi-table--indicators td:first-child {
    width: 40% !important;
    min-width: 0 !important;
  }

  .kpi-table tbody td {
    padding: 2.4mm 2mm;
  }

  .indicator-name-cell strong {
    -webkit-line-clamp: 2;
  }

  .indicator-rate-cell__gauge {
    width: 24mm;
    height: 14mm;
  }

  .status-pill {
    padding: 1.5mm 2.4mm;
    white-space: nowrap;
  }

  .kpi-donut-top-legend {
    gap: 2mm;
  }

  .kpi-donut-top-legend__copy strong,
  .kpi-donut-top-legend__copy small {
    font-size: 7.5pt;
  }

  .kpi-donut-stage {
    width: min(100%, 112mm);
    margin: 0 auto;
  }

  .trend-chart {
    min-height: 58mm;
  }

  .trend-chart__svg {
    max-height: 58mm;
  }

  .indicator-analysis-card,
  .indicator-analysis-card__body,
  .indicator-analysis-metrics,
  .indicator-history-chart {
    min-width: 0;
  }

  .indicator-analysis-card__hero {
    padding: 4mm;
  }

  .indicator-analysis-card__hero h3 {
    font-size: 14pt;
  }

  .indicator-analysis-card__body {
    grid-template-columns: 42mm minmax(0, 1fr);
    gap: 4mm;
  }

  .indicator-analysis-gauge {
    min-height: 42mm;
  }

  .indicator-analysis-gauge__visual {
    width: 33mm;
    height: 33mm;
  }

  .indicator-analysis-gauge__visual strong {
    font-size: 15pt;
  }

  .indicator-history-chart__canvas {
    height: 52mm;
  }
}

@media (max-width: 1440px), (max-height: 860px) {
  .kpi-page {
    gap: 0.82rem;
  }

  .kpi-header {
    gap: 0.82rem;
  }

  .kpi-header__copy h1 {
    font-size: clamp(1.76rem, 2.45vw, 2.42rem);
  }

  .kpi-header__copy p {
    margin-top: 0.3rem;
    font-size: 0.94rem;
  }

  .kpi-header__actions {
    gap: 0.32rem;
    padding: 0.32rem;
    border-radius: 20px;
  }

  .kpi-action-chip {
    min-height: 48px;
    padding: 0.58rem 0.7rem;
    border-radius: 16px;
  }

  .kpi-action-chip__copy strong {
    font-size: 0.9rem;
  }

  .kpi-action-popover {
    gap: 0.52rem;
    padding: 0.72rem;
    border-radius: 18px;
  }

  .kpi-action-menu-item {
    padding: 0.62rem 0.68rem;
  }

  .kpi-period-picker__years {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .kpi-period-picker__months {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .kpi-period-picker__year,
  .kpi-period-picker__month {
    min-height: 32px;
    padding: 0.46rem 0.5rem;
  }

  .kpi-summary-grid {
    gap: 0.62rem;
  }

  .kpi-summary-card {
    gap: 0.7rem;
    padding: 0.84rem 0.88rem;
    border-radius: 18px;
  }

  .kpi-summary-card__icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
  }

  .kpi-summary-card__icon svg {
    width: 24px;
    height: 24px;
  }

  .kpi-summary-card__label {
    font-size: 0.75rem;
  }

  .kpi-summary-card__content strong {
    font-size: clamp(1.52rem, 1.9vw, 1.92rem);
  }

  .kpi-summary-card__content small {
    font-size: 0.84rem;
  }

  .kpi-main-grid,
  .kpi-bottom-grid {
    grid-template-columns: minmax(0, 1.42fr) minmax(300px, 0.88fr);
    gap: 0.76rem;
  }

  .kpi-side-grid {
    gap: 0.76rem;
  }

  .panel--kpi-surface {
    padding: 0.84rem 0.88rem;
    border-radius: 22px;
  }

  .panel--kpi-surface .panel__header {
    margin-bottom: 0.66rem;
  }

  .panel--kpi-surface h2 {
    font-size: 1.24rem;
  }

  .kpi-table-wrap--indicator-preview {
    max-height: 560px;
  }

  .kpi-donut-stage {
    width: min(100%, 500px);
  }

  .indicator-filter-controls {
    grid-template-columns: minmax(200px, 1fr) minmax(160px, 0.74fr);
    gap: 0.58rem;
    margin-bottom: 0.66rem;
  }

  .indicator-filter-select {
    min-height: 46px;
    padding: 0.58rem 3rem 0.58rem 0.84rem;
    font-size: 0.88rem;
  }

  .indicator-filter-select::after {
    right: 0.98rem;
  }
}

@media (max-width: 1100px) {
  .kpi-summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .kpi-main-grid,
  .kpi-bottom-grid,
  .kpi-donut-layout {
    grid-template-columns: 1fr;
  }

  .kpi-donut-shell {
    justify-self: center;
  }

  .kpi-donut-stage {
    margin-left: 0;
  }
}

@media (max-width: 820px) {
  .kpi-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .status-bars {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .indicator-filter-controls {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .kpi-header,
  .kpi-header__actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .kpi-donut-stage {
    width: 220px;
    height: 220px;
  }

  .kpi-donut__center {
    inset: 48px;
  }

  .kpi-summary-grid,
  .status-bars {
    grid-template-columns: 1fr;
  }

  .kpi-summary-card {
    grid-template-columns: auto 1fr;
  }

  .panel--kpi-surface {
    padding: 0.92rem;
  }
}
</style>
