const STATUS_DONE = 'Réalisée'
const STATUS_NOT_STARTED = 'Non démarrée'
const STATUS_CANCELLED = 'Annulée'

export const statusSequence = [STATUS_DONE, 'En cours', STATUS_NOT_STARTED, 'Suspendue', STATUS_CANCELLED]

export const navItems = [
  { code: 'ACT', label: 'Suivi des activités' },
  { code: 'AXE', label: 'Axes stratégiques' },
  { code: 'KPI', label: 'Indicateurs clés' },
  { code: 'USR', label: 'Utilisateurs' },
]

export const statusPalette = {
  [STATUS_DONE]: { solid: '#5bb85d', soft: 'rgba(91, 184, 93, 0.14)' },
  'En cours': { solid: '#f2b544', soft: 'rgba(242, 181, 68, 0.18)' },
  [STATUS_NOT_STARTED]: { solid: '#8ea2bc', soft: 'rgba(142, 162, 188, 0.18)' },
  Suspendue: { solid: '#ee8f4d', soft: 'rgba(238, 143, 77, 0.2)' },
  [STATUS_CANCELLED]: { solid: '#d95c70', soft: 'rgba(217, 92, 112, 0.18)' },
}

export const emptySummary = {
  totalActivities: 0,
  coveredProjects: 0,
  registeredProjects: 0,
  coveredAxes: 0,
  registeredAxes: 0,
  servicesInCharge: 0,
  completedActivities: 0,
  startedActivities: 0,
  inProgressActivities: 0,
  notStartedActivities: 0,
  suspendedActivities: 0,
  cancelledActivities: 0,
  activitiesWithoutEndDate: 0,
  plannedBudget: 0,
  spentBudget: 0,
  overdueActivities: 0,
  completionRate: 0,
  kickoffRate: 0,
  projectCoverageRate: 0,
  axisCoverageRate: 0,
  planningCompletenessRate: 0,
  budgetConsumptionRate: 0,
}
