import { emptySummary, statusPalette, statusSequence } from './dashboardConstants'
import { formatCurrency, formatNumber, formatPercent } from './dashboardFormatters'

function pluralize(count, singular, plural = `${singular}s`) {
  return Number(count) === 1 ? singular : plural
}

function hasOwn(object, key) {
  return Object.prototype.hasOwnProperty.call(object ?? {}, key)
}

function resolvePercentage(item, total, count) {
  if (hasOwn(item, 'percentage')) {
    const explicitPercentage = Number(item?.percentage)

    if (Number.isFinite(explicitPercentage)) {
      return explicitPercentage
    }
  }

  return total > 0 ? (count / total) * 100 : 0
}

export function buildStatusBreakdown(rawItems = []) {
  const totals = new Map(rawItems.map((item) => [item.label, item]))
  const totalCount = rawItems.reduce((sum, item) => sum + Number(item.total ?? 0), 0)

  return statusSequence.map((label) => {
    const item = totals.get(label)
    const count = Number(item?.total ?? 0)

    return {
      label,
      total: count,
      percentage: resolvePercentage(item, totalCount, count),
    }
  })
}

export function buildStatusOptions(summary = emptySummary, statusBreakdown = []) {
  return [
    { label: 'Tous', total: summary.totalActivities },
    ...statusSequence.map((label) => ({
      label,
      total: statusBreakdown.find((item) => item.label === label)?.total ?? 0,
    })),
  ]
}

export function buildExecutiveCards(summary = emptySummary) {
  const totalActivities = formatNumber(summary.totalActivities)
  const startedActivities = formatNumber(summary.startedActivities)
  const overdueActivities = formatNumber(summary.overdueActivities)
  const overdueEligibleActivities = Math.max(
    0,
    Number(summary.totalActivities) - Number(summary.cancelledActivities) - Number(summary.suspendedActivities),
  )
  const overdueBaseActivities = formatNumber(overdueEligibleActivities)
  const overdueRate = overdueEligibleActivities
    ? (summary.overdueActivities / overdueEligibleActivities) * 100
    : 0
  const startedActivityLabel = pluralize(summary.startedActivities, 'activité', 'activités')
  const launchedLabel = pluralize(summary.startedActivities, 'lancée', 'lancées')
  const overdueActivityLabel = pluralize(summary.overdueActivities, 'activité', 'activités')
  const dueReference = pluralize(summary.overdueActivities, 'son échéance', 'leur échéance')

  return [
    {
      label: 'Démarrage effectif',
      value: formatPercent(summary.kickoffRate),
      caption: `${startedActivities} ${startedActivityLabel} ${launchedLabel} sur ${totalActivities}`,
      progress: summary.kickoffRate,
      color: '#237245',
      neutralChrome: true,
    },
    {
      label: 'Retards identifiés',
      value: formatPercent(overdueRate),
      caption: `${overdueActivities} ${overdueActivityLabel} au-delà de ${dueReference} sur ${overdueBaseActivities}`,
      progress: overdueRate,
      color: '#d95c70',
      neutralChrome: true,
    },
    {
      label: 'Budget engagé',
      value: formatCurrency(summary.spentBudget),
      caption:
        summary.plannedBudget > 0
          ? `${formatCurrency(summary.plannedBudget)} prévus (${formatPercent(summary.budgetConsumptionRate)})`
          : 'Aucun budget prévisionnel saisi',
      progress: summary.budgetConsumptionRate,
      color: '#2a4f73',
      compactValue: true,
      neutralChrome: true,
    },
    {
      label: 'Services de pilotage',
      value: formatNumber(summary.servicesInCharge),
      caption: 'services responsables désignés',
      progress: 100,
      color: '#c7cfd9',
    },
  ]
}

export function buildServiceStatusBreakdown(rawItems = []) {
  return rawItems
    .map((item) => {
      const statusesByLabel = new Map((item.statuses ?? []).map((status) => [status.label, status]))
      const rawStatuses = statusSequence.map((label) => {
        const status = statusesByLabel.get(label)

        return {
          label,
          total: Number(status?.total ?? 0),
          source: status,
        }
      })
      const statusesTotal = rawStatuses.reduce((sum, status) => sum + status.total, 0)
      const declaredTotal = Number(item.total ?? 0)
      const total = declaredTotal > 0 ? declaredTotal : statusesTotal
      const statuses = rawStatuses.map((status) => ({
        label: status.label,
        total: status.total,
        percentage: resolvePercentage(status.source, total, status.total),
      }))

      return {
        label: item.label ?? 'Non renseigne',
        total,
        statuses,
      }
    })
    .sort(
      (left, right) =>
        right.total - left.total || String(left.label).localeCompare(String(right.label), 'fr-FR'),
    )
}

export function getStatusColor(label) {
  return statusPalette[label]?.solid ?? '#6f8297'
}

export function getStatusSoftColor(label) {
  return statusPalette[label]?.soft ?? 'rgba(111, 130, 151, 0.16)'
}

function normalizeStatusLabel(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

export function getStatusLegendColor(label) {
  const normalized = normalizeStatusLabel(label)

  if (normalized === 'en cours') {
    return '#4c7dff'
  }

  if (normalized.includes('annul')) {
    return '#8f2f44'
  }

  return getStatusColor(label)
}

export function getStatusLegendSoftColor(label) {
  const normalized = normalizeStatusLabel(label)

  if (normalized === 'en cours') {
    return 'rgba(76, 125, 255, 0.14)'
  }

  if (normalized.includes('annul')) {
    return 'rgba(143, 47, 68, 0.16)'
  }

  return getStatusSoftColor(label)
}
