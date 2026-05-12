export function formatNumber(value) {
  return new Intl.NumberFormat('fr-FR').format(Number(value ?? 0))
}

export function formatPercent(value) {
  const numericValue = Number(value ?? 0)

  return `${new Intl.NumberFormat('fr-FR', {
    maximumFractionDigits: numericValue % 1 === 0 ? 0 : 1,
  }).format(numericValue)}%`
}

export function formatCurrency(value) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'XOF',
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0))
}

export function formatDateTimeLabel(value) {
  if (!value) {
    return ''
  }

  const normalizedValue = String(value).trim().replace(' ', 'T')
  const directMatch = normalizedValue.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/)

  if (directMatch) {
    const [, year, month, day, hours, minutes, seconds = '00'] = directMatch
    return `${day}/${month}/${year} à ${hours}:${minutes}:${seconds}`
  }

  const parsedDate = new Date(normalizedValue)

  if (Number.isNaN(parsedDate.getTime())) {
    return ''
  }

  const parts = new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(parsedDate)

  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${values.day}/${values.month}/${values.year} à ${values.hour}:${values.minute}:${values.second}`
}

export function formatDate(value) {
  if (!value) {
    return 'A renseigner'
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export function activityWindow(activity) {
  if (activity.plannedStart && activity.plannedEnd) {
    return `${formatDate(activity.plannedStart)} - ${formatDate(activity.plannedEnd)}`
  }

  if (activity.plannedStart) {
    return `Début ${formatDate(activity.plannedStart)}`
  }

  return 'Planification à compléter'
}

export function initials(value) {
  const tokens = String(value ?? '')
    .split(/\s+/)
    .map((token) => token.trim())
    .filter(Boolean)

  return (tokens[0]?.[0] ?? '') + (tokens[1]?.[0] ?? '') || 'NA'
}

export function clampText(value, limit = 120) {
  if (!value) {
    return ''
  }

  return value.length > limit ? `${value.slice(0, limit - 1)}…` : value
}
