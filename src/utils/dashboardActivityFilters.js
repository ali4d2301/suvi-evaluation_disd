import { emptySummary } from './dashboardConstants'

export function normalizeDashboardText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

export function parsePlannedStartParts(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value ?? '').trim())

  if (!match) {
    return null
  }

  const year = Number(match[1])
  const month = Number(match[2])

  if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
    return null
  }

  return {
    year,
    month,
    quarter: Math.ceil(month / 3),
  }
}

export function buildAvailablePlannedYears(activities = []) {
  const years = new Set()

  activities.forEach((activity) => {
    const parts = parsePlannedStartParts(activity?.plannedStart)

    if (parts) {
      years.add(String(parts.year))
    }
  })

  return [...years].sort((left, right) => Number(left) - Number(right))
}

export function filterActivitiesByActPeriod(activities = [], selection = {}) {
  const selectedYear = String(selection?.year ?? '').trim()

  if (!selectedYear) {
    return activities
  }

  const quarterStart = Math.max(1, Math.min(4, Number(selection?.quarterStart ?? 1)))
  const quarterEnd = Math.max(quarterStart, Math.min(4, Number(selection?.quarterEnd ?? 4)))

  return activities.filter((activity) => {
    const parts = parsePlannedStartParts(activity?.plannedStart)

    return (
      parts &&
      String(parts.year) === selectedYear &&
      parts.quarter >= quarterStart &&
      parts.quarter <= quarterEnd
    )
  })
}

export function filterActivitiesByAxisPeriod(activities = [], selection = {}) {
  const startYear = String(selection?.startYear ?? '').trim()
  const endYear = String(selection?.endYear ?? '').trim()

  if (!startYear && !endYear) {
    return activities
  }

  const lower = Number(startYear || endYear)
  const upper = Number(endYear || startYear)

  if (!Number.isFinite(lower) || !Number.isFinite(upper)) {
    return activities
  }

  const minYear = Math.min(lower, upper)
  const maxYear = Math.max(lower, upper)

  return activities.filter((activity) => {
    const parts = parsePlannedStartParts(activity?.plannedStart)

    return parts && parts.year >= minYear && parts.year <= maxYear
  })
}

function isCompletedStatus(label) {
  const normalized = normalizeDashboardText(label)
  return normalized === 'realisee' || normalized === 'terminee'
}

function isInProgressStatus(label) {
  return normalizeDashboardText(label) === 'en cours'
}

function isCancelledStatus(label) {
  return normalizeDashboardText(label).includes('annul')
}

function isNotStartedStatus(label) {
  return normalizeDashboardText(label).includes('non demarr')
}

function isSuspendedStatus(label) {
  return normalizeDashboardText(label).includes('suspend')
}

function isStartedStatus(label) {
  return isCompletedStatus(label) || isInProgressStatus(label)
}

function isOverdueActivity(activity, todayKey) {
  return (
    Boolean(activity?.plannedEnd) &&
    String(activity.plannedEnd) < todayKey &&
    !isCompletedStatus(activity?.status) &&
    !isCancelledStatus(activity?.status) &&
    !isSuspendedStatus(activity?.status)
  )
}

export function deriveDashboardSummary(activities = [], baseSummary = emptySummary) {
  const todayKey = new Date().toISOString().slice(0, 10)
  const projects = new Set()
  const axes = new Set()
  const services = new Set()
  let completedActivities = 0
  let startedActivities = 0
  let inProgressActivities = 0
  let notStartedActivities = 0
  let suspendedActivities = 0
  let cancelledActivities = 0
  let activitiesWithoutEndDate = 0
  let plannedBudget = 0
  let spentBudget = 0
  let overdueActivities = 0

  activities.forEach((activity) => {
    const status = String(activity?.status ?? '').trim()
    const project = String(activity?.project ?? '').trim()
    const axis = String(activity?.axeLabel ?? '').trim()
    const service = String(activity?.service ?? '').trim()

    if (project) {
      projects.add(project)
    }

    if (axis) {
      axes.add(axis)
    }

    if (service) {
      services.add(service)
    }

    if (isCompletedStatus(status)) {
      completedActivities += 1
    }

    if (isStartedStatus(status)) {
      startedActivities += 1
    }

    if (isInProgressStatus(status)) {
      inProgressActivities += 1
    }

    if (isNotStartedStatus(status)) {
      notStartedActivities += 1
    }

    if (isSuspendedStatus(status)) {
      suspendedActivities += 1
    }

    if (isCancelledStatus(status)) {
      cancelledActivities += 1
    }

    if (!activity?.plannedEnd) {
      activitiesWithoutEndDate += 1
    }

    plannedBudget += Number(activity?.plannedBudget ?? 0)
    spentBudget += Number(activity?.spentBudget ?? 0)

    if (isOverdueActivity(activity, todayKey)) {
      overdueActivities += 1
    }
  })

  const totalActivities = activities.length
  const coveredProjects = projects.size
  const coveredAxes = axes.size
  const servicesInCharge = services.size

  return {
    ...baseSummary,
    totalActivities,
    coveredProjects,
    coveredAxes,
    servicesInCharge,
    completedActivities,
    startedActivities,
    inProgressActivities,
    notStartedActivities,
    suspendedActivities,
    cancelledActivities,
    activitiesWithoutEndDate,
    plannedBudget,
    spentBudget,
    overdueActivities,
    completionRate: totalActivities ? (completedActivities / totalActivities) * 100 : 0,
    kickoffRate: totalActivities ? (startedActivities / totalActivities) * 100 : 0,
    projectCoverageRate: baseSummary.registeredProjects
      ? (coveredProjects / Number(baseSummary.registeredProjects)) * 100
      : 0,
    axisCoverageRate: baseSummary.registeredAxes
      ? (coveredAxes / Number(baseSummary.registeredAxes)) * 100
      : 0,
    planningCompletenessRate: totalActivities
      ? ((totalActivities - activitiesWithoutEndDate) / totalActivities) * 100
      : 0,
    budgetConsumptionRate: plannedBudget > 0 ? (spentBudget / plannedBudget) * 100 : 0,
  }
}
