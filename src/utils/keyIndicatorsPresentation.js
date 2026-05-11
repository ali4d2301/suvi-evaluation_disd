import { clampText, formatNumber, formatPercent } from './dashboardFormatters'

export const trendMeta = {
  up: {
    label: 'En hausse',
    color: '#237245',
    softColor: 'rgba(35, 114, 69, 0.14)',
  },
  down: {
    label: 'En baisse',
    color: '#c85d55',
    softColor: 'rgba(200, 93, 85, 0.14)',
  },
  stable: {
    label: 'Stable',
    color: '#496886',
    softColor: 'rgba(73, 104, 134, 0.14)',
  },
  initial: {
    label: 'Cycle initial',
    color: '#8ea2bc',
    softColor: 'rgba(142, 162, 188, 0.18)',
  },
}

export const targetStatusMeta = {
  on_target: {
    label: 'A la cible',
    color: '#237245',
    softColor: 'rgba(35, 114, 69, 0.14)',
  },
  below_target: {
    label: 'Sous cible',
    color: '#c85d55',
    softColor: 'rgba(200, 93, 85, 0.14)',
  },
  no_target: {
    label: 'Sans cible',
    color: '#70849d',
    softColor: 'rgba(112, 132, 157, 0.16)',
  },
}

export const periodicityMeta = {
  Mensuelle: {
    label: 'Mensuelle',
    color: '#3e6df2',
    softColor: 'rgba(62, 109, 242, 0.16)',
  },
  Trimestrielle: {
    label: 'Trimestrielle',
    color: '#1d9388',
    softColor: 'rgba(29, 147, 136, 0.16)',
  },
  Semestrielle: {
    label: 'Semestrielle',
    color: '#b68030',
    softColor: 'rgba(182, 128, 48, 0.16)',
  },
  Annuelle: {
    label: 'Annuelle',
    color: '#58718c',
    softColor: 'rgba(88, 113, 140, 0.16)',
  },
}

function isRatioValue(value) {
  return Math.abs(Number(value ?? 0)) <= 1.2
}

export function formatIndicatorMetricValue(value, valueFormat) {
  if (value === null || value === undefined) {
    return 'N/A'
  }

  if (valueFormat === 'percent') {
    return formatPercent(isRatioValue(value) ? Number(value) * 100 : Number(value))
  }

  return formatNumber(value)
}

export function formatIndicatorTarget(indicator) {
  if (indicator?.targetValue === null || indicator?.targetValue === undefined) {
    return 'Cible indisponible'
  }

  return formatIndicatorMetricValue(indicator.targetValue, indicator.valueFormat)
}

export function formatIndicatorGap(indicator) {
  if (indicator?.targetGap === null || indicator?.targetGap === undefined) {
    return 'Pas de comparaison cible'
  }

  if (indicator.valueFormat === 'percent') {
    const gapValue = isRatioValue(indicator.targetGap) ? Number(indicator.targetGap) * 100 : Number(indicator.targetGap)
    const sign = gapValue > 0 ? '+' : ''

    return `${sign}${new Intl.NumberFormat('fr-FR', {
      maximumFractionDigits: Math.abs(gapValue) % 1 === 0 ? 0 : 1,
    }).format(gapValue)} pts`
  }

  const sign = Number(indicator.targetGap) > 0 ? '+' : ''
  return `${sign}${formatNumber(indicator.targetGap)}`
}

export function formatIndicatorDelta(indicator) {
  if (indicator?.delta === null || indicator?.delta === undefined) {
    return 'Cycle initial'
  }

  if (indicator.valueFormat === 'percent') {
    const deltaValue = isRatioValue(indicator.delta) ? Number(indicator.delta) * 100 : Number(indicator.delta)
    const sign = deltaValue > 0 ? '+' : ''

    return `${sign}${new Intl.NumberFormat('fr-FR', {
      maximumFractionDigits: Math.abs(deltaValue) % 1 === 0 ? 0 : 1,
    }).format(deltaValue)} pts`
  }

  if (indicator.deltaRatio !== null && indicator.deltaRatio !== undefined) {
    const sign = Number(indicator.deltaRatio) > 0 ? '+' : ''
    return `${sign}${formatPercent(indicator.deltaRatio)}`
  }

  const deltaValue = Number(indicator.delta)
  const sign = deltaValue > 0 ? '+' : ''
  return `${sign}${formatNumber(deltaValue)}`
}

export function formatIndicatorComparison(indicator) {
  if (!indicator?.previousPeriodLabel || indicator?.previousValue === null || indicator?.previousValue === undefined) {
    return `Lecture initiale sur ${indicator?.latestPeriodLabel ?? 'le cycle courant'}`
  }

  return `vs ${formatIndicatorMetricValue(indicator.previousValue, indicator.valueFormat)} sur ${indicator.previousPeriodLabel}`
}

export function buildSparklinePoints(history, width = 220, height = 72, padding = 8) {
  const numericHistory = (history ?? []).filter((item) => item?.value !== null && item?.value !== undefined)

  if (!numericHistory.length) {
    return ''
  }

  const values = numericHistory.map((item) => Number(item.value))
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const spread = maxValue - minValue || 1
  const innerWidth = Math.max(width - padding * 2, 1)
  const innerHeight = Math.max(height - padding * 2, 1)

  return numericHistory
    .map((item, index) => {
      const x = padding + (index / Math.max(numericHistory.length - 1, 1)) * innerWidth
      const y = height - padding - ((Number(item.value) - minValue) / spread) * innerHeight

      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

export function clampIndicatorLabel(value, limit = 92) {
  return clampText(value, limit)
}

export function resolveSignalTone(indicator) {
  if (indicator?.targetStatus === 'below_target' && indicator?.trend === 'down') {
    return {
      label: 'A arbitrer',
      color: '#c85d55',
      softColor: 'rgba(200, 93, 85, 0.14)',
    }
  }

  if (indicator?.targetStatus === 'on_target' && indicator?.trend === 'up') {
    return {
      label: "Point d'appui",
      color: '#237245',
      softColor: 'rgba(35, 114, 69, 0.14)',
    }
  }

  if (indicator?.targetStatus === 'below_target') {
    return {
      label: 'Sous pression',
      color: '#bd6c2f',
      softColor: 'rgba(189, 108, 47, 0.14)',
    }
  }

  return {
    label: 'A suivre',
    color: '#496886',
    softColor: 'rgba(73, 104, 134, 0.14)',
  }
}
