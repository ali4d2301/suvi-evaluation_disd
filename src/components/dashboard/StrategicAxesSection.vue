<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import {
  activityWindow,
  formatCurrency,
  formatNumber,
  formatPercent,
} from '../../utils/dashboardFormatters'
import { statusSequence } from '../../utils/dashboardConstants'
import { getStatusLegendColor, getStatusLegendSoftColor } from '../../utils/dashboardPresentation'

const props = defineProps({
  activities: {
    type: Array,
    required: true,
  },
  summary: {
    type: Object,
    required: true,
  },
})

const selectedAxisLabel = ref('')
const activeActivityStatusFilter = ref('')
const projectMetricPopoverRef = ref(null)
const projectMetricPopover = ref(createProjectMetricPopoverState())

let projectMetricPopoverAnchorElement = null

function createProjectMetricPopoverState() {
  return {
    visible: false,
    x: 0,
    y: 0,
    projectLabel: '',
    metricKey: '',
    metricLabel: '',
    count: 0,
    total: 0,
    activities: [],
    emptyMessage: '',
  }
}

function normalizeTextValue(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function resolveAxisLabel(value) {
  return String(value ?? '').trim() || 'Non renseigné'
}

function resolveProjectLabel(value) {
  return String(value ?? '').trim() || 'Projet non renseigné'
}

function resolveServiceLabel(value) {
  return String(value ?? '').trim() || 'Non renseigné'
}

function isCompletedStatus(label) {
  return normalizeTextValue(label) === 'realisee'
}

function isInProgressStatus(label) {
  return normalizeTextValue(label) === 'en cours'
}

function isNotStartedStatus(label) {
  return normalizeTextValue(label).includes('non demarr')
}

function isCancelledStatus(label) {
  return normalizeTextValue(label).includes('annul')
}

function isSuspendedStatus(label) {
  return normalizeTextValue(label).includes('suspend')
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

function compareActivitiesByPriority(left, right) {
  const leftPriority = left.isOverdue ? 0 : 1
  const rightPriority = right.isOverdue ? 0 : 1

  return (
    leftPriority - rightPriority ||
    String(left.plannedEnd ?? '9999-12-31').localeCompare(String(right.plannedEnd ?? '9999-12-31')) ||
    String(left.activity ?? '').localeCompare(String(right.activity ?? ''), 'fr-FR')
  )
}

function enrichActivities(activities, todayKey) {
  return [...activities]
    .map((activity) => ({
      ...activity,
      isOverdue: isOverdueActivity(activity, todayKey),
    }))
    .sort(compareActivitiesByPriority)
}

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

function incrementCount(map, label) {
  map.set(label, (map.get(label) ?? 0) + 1)
}

function buildStatusBreakdown(statusMap, total) {
  return statusSequence.map((label) => {
    const count = Number(statusMap.get(label) ?? 0)

    return {
      label,
      total: count,
      percentage: total ? (count / total) * 100 : 0,
      color: getStatusLegendColor(label),
      softColor: getStatusLegendSoftColor(label),
    }
  })
}

const strategicAxes = computed(() => {
  const todayKey = new Date().toISOString().slice(0, 10)
  const axisMap = new Map()

  props.activities.forEach((activity) => {
    const axisLabel = resolveAxisLabel(activity.axeLabel)
    const projectLabel = resolveProjectLabel(activity.project)
    const serviceLabel = resolveServiceLabel(activity.service)
    const statusLabel = String(activity.status ?? '').trim()

    if (!axisMap.has(axisLabel)) {
      axisMap.set(axisLabel, {
        label: axisLabel,
        activities: [],
        statusMap: new Map(),
        serviceMap: new Map(),
        projectMap: new Map(),
        total: 0,
        completed: 0,
        started: 0,
        inProgress: 0,
        notStarted: 0,
        overdue: 0,
        plannedBudget: 0,
        spentBudget: 0,
      })
    }

    const axis = axisMap.get(axisLabel)
    axis.activities.push(activity)
    axis.total += 1
    axis.plannedBudget += Number(activity.plannedBudget ?? 0)
    axis.spentBudget += Number(activity.spentBudget ?? 0)
    incrementCount(axis.statusMap, statusLabel)
    incrementCount(axis.serviceMap, serviceLabel)

    if (isCompletedStatus(statusLabel)) {
      axis.completed += 1
    }

    if (isStartedStatus(statusLabel)) {
      axis.started += 1
    }

    if (isInProgressStatus(statusLabel)) {
      axis.inProgress += 1
    }

    if (isNotStartedStatus(statusLabel)) {
      axis.notStarted += 1
    }

    if (isOverdueActivity(activity, todayKey)) {
      axis.overdue += 1
    }

    if (!axis.projectMap.has(projectLabel)) {
      axis.projectMap.set(projectLabel, {
        label: projectLabel,
        activities: [],
        total: 0,
        completed: 0,
        started: 0,
        overdue: 0,
        plannedBudget: 0,
        spentBudget: 0,
      })
    }

    const project = axis.projectMap.get(projectLabel)
    project.activities.push(activity)
    project.total += 1
    project.plannedBudget += Number(activity.plannedBudget ?? 0)
    project.spentBudget += Number(activity.spentBudget ?? 0)

    if (isCompletedStatus(statusLabel)) {
      project.completed += 1
    }

    if (isStartedStatus(statusLabel)) {
      project.started += 1
    }

    if (isOverdueActivity(activity, todayKey)) {
      project.overdue += 1
    }
  })

  return [...axisMap.values()]
    .map((axis) => {
      const total = Number(axis.total)
      const statusBreakdown = buildStatusBreakdown(axis.statusMap, total)

      const projects = [...axis.projectMap.values()]
        .map((project) => {
          const activities = enrichActivities(project.activities, todayKey)

          return {
            label: project.label,
            activities,
            total: Number(project.total),
            kickoffRate: project.total ? (project.started / project.total) * 100 : 0,
            completionRate: project.total ? (project.completed / project.total) * 100 : 0,
            overdue: Number(project.overdue),
            plannedBudget: Number(project.plannedBudget),
            spentBudget: Number(project.spentBudget),
            budgetConsumptionRate:
              project.plannedBudget > 0 ? (project.spentBudget / project.plannedBudget) * 100 : 0,
          }
        })
        .sort(
          (left, right) =>
            right.overdue - left.overdue ||
            right.total - left.total ||
            String(left.label).localeCompare(String(right.label), 'fr-FR'),
        )

      const activities = enrichActivities(axis.activities, todayKey)

      const completionRate = total ? (axis.completed / total) * 100 : 0
      const overdueRate = total ? (axis.overdue / total) * 100 : 0
      const budgetConsumptionRate = axis.plannedBudget > 0 ? (axis.spentBudget / axis.plannedBudget) * 100 : 0

      return {
        label: axis.label,
        total,
        share: props.summary.totalActivities ? (total / props.summary.totalActivities) * 100 : 0,
        projectCount: axis.projectMap.size,
        serviceCount: axis.serviceMap.size,
        completed: Number(axis.completed),
        started: Number(axis.started),
        inProgress: Number(axis.inProgress),
        notStarted: Number(axis.notStarted),
        overdue: Number(axis.overdue),
        plannedBudget: Number(axis.plannedBudget),
        spentBudget: Number(axis.spentBudget),
        kickoffRate: total ? (axis.started / total) * 100 : 0,
        completionRate,
        overdueRate,
        budgetConsumptionRate,
        statusBreakdown,
        projects,
        activities,
      }
    })
    .sort(
      (left, right) =>
        right.total - left.total ||
        right.overdue - left.overdue ||
        String(left.label).localeCompare(String(right.label), 'fr-FR'),
    )
})

watch(
  strategicAxes,
  (axes) => {
    if (!axes.length) {
      selectedAxisLabel.value = ''
      activeActivityStatusFilter.value = ''
      return
    }

    if (!axes.some((axis) => axis.label === selectedAxisLabel.value)) {
      selectedAxisLabel.value = axes[0].label
    }
  },
  { immediate: true },
)

watch(selectedAxisLabel, () => {
  activeActivityStatusFilter.value = ''
  closeProjectMetricPopover()
})

const selectedAxis = computed(
  () => strategicAxes.value.find((axis) => axis.label === selectedAxisLabel.value) ?? strategicAxes.value[0] ?? null,
)

const axisMeta = computed(() => {
  const coveredAxes = Number(props.summary.coveredAxes ?? strategicAxes.value.length)
  return `${formatNumber(coveredAxes)} axes actifs`
})

const axisGridColumns = computed(() => {
  const total = strategicAxes.value.length

  if (total <= 1) {
    return 1
  }

  if (total <= 5) {
    return total
  }

  const rows = Math.ceil(total / 5)

  return Math.ceil(total / rows)
})

const axisGridStyle = computed(() => ({
  '--axis-grid-columns': String(axisGridColumns.value),
}))

const axisSummaryMetrics = computed(() => {
  if (!selectedAxis.value) {
    return []
  }

  const axis = selectedAxis.value

  return [
    {
      label: 'Couverture',
      value: `${formatNumber(axis.total)} activités`,
      caption: `${formatNumber(axis.projectCount)} projets`,
    },
    {
      label: 'Démarrage effectif',
      value: formatPercent(axis.kickoffRate),
      caption: `${formatNumber(axis.started)} activités lancées`,
    },
    {
      label: 'Avancement',
      value: formatPercent(axis.completionRate),
      caption: `${formatNumber(axis.completed)} réalisées · ${formatNumber(axis.inProgress)} en cours`,
    },
    {
      label: 'Retards',
      value: formatNumber(axis.overdue),
      caption: axis.overdue > 0 ? 'activités à relancer' : 'aucune alerte majeure',
    },
    {
      label: 'Budget engagé',
      value: axis.plannedBudget > 0 || axis.spentBudget > 0 ? formatCurrency(axis.spentBudget) : '—',
      caption:
        axis.plannedBudget > 0
          ? `${formatCurrency(axis.plannedBudget)} prévus (${formatPercent(axis.budgetConsumptionRate)})`
          : 'budget non renseigné',
      variant: 'budget',
    },
  ]
})

const activityFilterPills = computed(() => {
  if (!selectedAxis.value) {
    return []
  }

  return [
    {
      label: 'Toutes',
      total: selectedAxis.value.total,
      color: '#5f7895',
      softColor: 'rgba(95, 120, 149, 0.12)',
      isAll: true,
    },
    ...selectedAxis.value.statusBreakdown,
  ]
})

const filteredAxisActivities = computed(() => {
  if (!selectedAxis.value) {
    return []
  }

  if (!activeActivityStatusFilter.value) {
    return selectedAxis.value.activities
  }

  return selectedAxis.value.activities.filter(
    (activity) => String(activity.status ?? '').trim() === activeActivityStatusFilter.value,
  )
})

function statusUiStyle(status) {
  return {
    color: status.color,
    background: status.softColor,
    '--status-badge-accent': status.color,
  }
}

function activityFlagLabel(activity) {
  const statusLabel = String(activity?.status ?? '').trim()

  if (isCancelledStatus(statusLabel) || isSuspendedStatus(statusLabel)) {
    return ''
  }

  return activity?.isOverdue ? 'Échéance dépassée' : 'Suivi normal'
}

function axisCardStyle(axis) {
  return {
    '--axis-accent': '#5f88bd',
    '--axis-accent-soft': hexToRgba('#5f88bd', 0.08),
    '--axis-accent-border': hexToRgba('#5f88bd', 0.18),
  }
}

function hasProjectMetricPopoverOpen(projectLabel, metricKey) {
  return (
    projectMetricPopover.value.visible &&
    projectMetricPopover.value.projectLabel === projectLabel &&
    projectMetricPopover.value.metricKey === metricKey
  )
}

function resolveProjectMetricPopoverContent(project, metricKey) {
  switch (metricKey) {
    case 'all':
      return {
        metricLabel: 'Activités du projet',
        activities: project.activities,
        emptyMessage: 'Aucune activité rattachée à ce projet.',
      }
    case 'overdue':
      return {
        metricLabel: 'Retards',
        activities: project.activities.filter((activity) => activity.isOverdue),
        emptyMessage: 'Aucune activité en retard pour ce projet.',
      }
    case 'started':
      return {
        metricLabel: 'Démarrage effectif',
        activities: project.activities.filter((activity) => isStartedStatus(activity.status)),
        emptyMessage: 'Aucune activité démarrée pour ce projet.',
      }
    case 'completed':
      return {
        metricLabel: "Taux d'achèvement",
        activities: project.activities.filter((activity) => isCompletedStatus(activity.status)),
        emptyMessage: 'Aucune activité achevée pour ce projet.',
      }
    default:
      return null
  }
}

function positionProjectMetricPopover(targetElement) {
  const popoverElement = projectMetricPopoverRef.value

  if (!targetElement || !popoverElement) {
    return
  }

  const targetRect = targetElement.getBoundingClientRect()
  const popoverRect = popoverElement.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const gap = 12
  const edgePadding = 16
  const horizontalCenter = targetRect.left + targetRect.width / 2 - popoverRect.width / 2
  const availableSpaces = {
    bottom: viewportHeight - targetRect.bottom - edgePadding,
    top: targetRect.top - edgePadding,
  }

  const placementCandidates = [
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

  projectMetricPopover.value.x = Math.round(Math.min(Math.max(edgePadding, bestPlacement.x), maxX))
  projectMetricPopover.value.y = Math.round(Math.min(Math.max(edgePadding, bestPlacement.y), maxY))
}

function openProjectMetricPopover(event, project, metricKey) {
  const targetElement = event?.currentTarget instanceof HTMLElement ? event.currentTarget : null
  const content = resolveProjectMetricPopoverContent(project, metricKey)

  if (!targetElement || !content) {
    return
  }

  if (hasProjectMetricPopoverOpen(project.label, metricKey)) {
    closeProjectMetricPopover()
    return
  }

  projectMetricPopoverAnchorElement = targetElement
  projectMetricPopover.value = {
    visible: true,
    x: 0,
    y: 0,
    projectLabel: project.label,
    metricKey,
    metricLabel: content.metricLabel,
    count: content.activities.length,
    total: project.total,
    activities: content.activities,
    emptyMessage: content.emptyMessage,
  }

  nextTick(() => {
    if (!hasProjectMetricPopoverOpen(project.label, metricKey)) {
      return
    }

    positionProjectMetricPopover(targetElement)
  })
}

function closeProjectMetricPopover() {
  projectMetricPopoverAnchorElement = null
  projectMetricPopover.value = createProjectMetricPopoverState()
}

function handleProjectMetricPointerDown(event) {
  const anchorElement = projectMetricPopoverAnchorElement
  const popoverElement = projectMetricPopoverRef.value

  if (anchorElement?.contains(event.target) || popoverElement?.contains(event.target)) {
    return
  }

  closeProjectMetricPopover()
}

function handleProjectMetricKeydown(event) {
  if (event.key === 'Escape') {
    closeProjectMetricPopover()
  }
}

function handleProjectMetricViewportChange() {
  if (!projectMetricPopover.value.visible || !projectMetricPopoverAnchorElement) {
    return
  }

  nextTick(() => {
    positionProjectMetricPopover(projectMetricPopoverAnchorElement)
  })
}

onMounted(() => {
  document.addEventListener('pointerdown', handleProjectMetricPointerDown)
  document.addEventListener('keydown', handleProjectMetricKeydown)
  window.addEventListener('resize', handleProjectMetricViewportChange)
  window.addEventListener('scroll', handleProjectMetricViewportChange, true)
})

onBeforeUnmount(() => {
  closeProjectMetricPopover()
  document.removeEventListener('pointerdown', handleProjectMetricPointerDown)
  document.removeEventListener('keydown', handleProjectMetricKeydown)
  window.removeEventListener('resize', handleProjectMetricViewportChange)
  window.removeEventListener('scroll', handleProjectMetricViewportChange, true)
})
</script>

<template>
  <section class="panel panel--axis-overview">
    <div class="panel__header panel__header--space panel__header--executive">
      <div>
        <p class="panel__eyebrow">Axes stratégiques</p>
        <h2>Lecture synthétique</h2>
      </div>

      <div class="panel__meta">{{ axisMeta }}</div>
    </div>

    <div v-if="strategicAxes.length" class="axis-grid" :style="axisGridStyle">
      <button
        v-for="axis in strategicAxes"
        :key="axis.label"
        type="button"
        class="axis-card"
        :class="{ 'axis-card--active': selectedAxis?.label === axis.label }"
        :style="axisCardStyle(axis)"
        @click="selectedAxisLabel = axis.label"
      >
        <div class="axis-card__header">
          <div>
            <h3>{{ axis.label }}</h3>
            <p class="axis-card__meta">{{ formatNumber(axis.total) }} activités · {{ formatNumber(axis.projectCount) }} projets</p>
          </div>
        </div>

        <div class="axis-card__metrics">
          <div class="axis-card__metric">
            <span>Achèvement</span>
            <strong>{{ formatPercent(axis.completionRate) }}</strong>
          </div>

          <div class="axis-card__metric">
            <span>Retards</span>
            <strong>{{ formatNumber(axis.overdue) }}</strong>
          </div>
        </div>
      </button>
    </div>

    <div v-else class="distribution-empty">
      <h3>Aucun axe exploitable pour l'instant</h3>
      <p>Les axes apparaîtront ici dès que les activités seront rattachées à un portefeuille stratégique.</p>
    </div>
  </section>

  <section v-if="selectedAxis" class="panel panel--axis-focus">
    <div class="panel__header panel__header--space panel__header--executive">
      <div>
        <p class="panel__eyebrow">Axe sélectionné</p>
        <h2>{{ selectedAxis.label }}</h2>
      </div>
    </div>

    <div class="axis-summary-grid">
      <article
        v-for="item in axisSummaryMetrics"
        :key="item.label"
        class="axis-summary-card"
        :class="{ 'axis-summary-card--budget': item.variant === 'budget' }"
      >
        <span class="axis-summary-card__label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.caption }}</small>
      </article>
    </div>

    <div class="axis-focus-grid">
      <article class="axis-focus-block axis-focus-block--wide">
        <div class="axis-focus-block__header">
          <div>
            <p class="axis-block-title">PROJETS DE L'AXE</p>
          </div>

          <span class="axis-focus-block__meta">{{ formatNumber(selectedAxis.projects.length) }} projets</span>
        </div>

        <div v-if="selectedAxis.projects.length" class="axis-project-list">
          <article v-for="project in selectedAxis.projects" :key="project.label" class="axis-project-row">
            <div class="axis-project-row__main">
              <div class="axis-project-row__title">
                <h3>{{ project.label }}</h3>
              </div>

              <div class="axis-project-row__meta">
                <button
                  type="button"
                  class="axis-project-row__meta-button"
                  :class="{ 'axis-project-row__meta-button--active': hasProjectMetricPopoverOpen(project.label, 'all') }"
                  @click="openProjectMetricPopover($event, project, 'all')"
                >
                  {{ formatNumber(project.total) }} activités
                </button>

                <span class="axis-project-row__meta-separator">·</span>

                <button
                  type="button"
                  class="axis-project-row__meta-button"
                  :class="{ 'axis-project-row__meta-button--active': hasProjectMetricPopoverOpen(project.label, 'overdue') }"
                  @click="openProjectMetricPopover($event, project, 'overdue')"
                >
                  {{ formatNumber(project.overdue) }} retards
                </button>
              </div>
            </div>

            <div class="axis-project-row__side">
              <button
                type="button"
                class="axis-project-row__info axis-project-row__info--primary-metric axis-project-row__trigger"
                :class="{ 'axis-project-row__trigger--active': hasProjectMetricPopoverOpen(project.label, 'started') }"
                @click="openProjectMetricPopover($event, project, 'started')"
              >
                <span>Démarrage effectif</span>
                <strong>{{ formatPercent(project.kickoffRate) }}</strong>
              </button>

              <button
                type="button"
                class="axis-project-row__info axis-project-row__info--primary-metric axis-project-row__trigger"
                :class="{ 'axis-project-row__trigger--active': hasProjectMetricPopoverOpen(project.label, 'completed') }"
                @click="openProjectMetricPopover($event, project, 'completed')"
              >
                <span>Taux d'achèvement</span>
                <strong>{{ formatPercent(project.completionRate) }}</strong>
              </button>

              <div class="axis-project-row__info axis-project-row__info--budget">
                <span>Taux d'absorption</span>
                <strong>{{ project.plannedBudget > 0 ? formatPercent(project.budgetConsumptionRate) : '—' }}</strong>
                <small>
                  {{
                    project.plannedBudget > 0
                      ? `${formatCurrency(project.spentBudget)} sur ${formatCurrency(project.plannedBudget)}`
                      : 'Budget non renseigné'
                  }}
                </small>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="distribution-empty distribution-empty--compact">
          <p>Aucun projet rattaché à cet axe pour l'instant.</p>
        </div>
      </article>
    </div>
  </section>

  <section v-if="selectedAxis" class="panel panel--axis-activities">
    <div class="panel__header panel__header--space">
      <div>
        <p class="panel__eyebrow">Répartition</p>
        <h2>Statuts et liste des activités</h2>
      </div>

      <div class="panel__meta">{{ formatNumber(filteredAxisActivities.length) }} activités affichées</div>
    </div>

    <div class="axis-activity-toolbar">
      <button
        v-for="status in activityFilterPills"
        :key="status.label"
        type="button"
        class="axis-status-pill axis-status-pill--filter"
        :class="{ 'axis-status-pill--active': (status.isAll && !activeActivityStatusFilter) || activeActivityStatusFilter === status.label }"
        :style="statusUiStyle(status)"
        @click="activeActivityStatusFilter = status.isAll ? '' : status.label"
      >
        <span class="axis-status-pill__dot" :style="{ background: status.color }" />
        <span class="axis-status-pill__label">{{ status.label }}</span>
        <strong>{{ formatNumber(status.total) }}</strong>
      </button>
    </div>

    <div v-if="filteredAxisActivities.length" class="axis-activity-list">
      <article v-for="activity in filteredAxisActivities" :key="activity.id" class="axis-activity-row">
        <div class="axis-activity-row__main">
          <strong>{{ activity.activity }}</strong>
          <p class="axis-activity-row__project">{{ activity.project }}</p>

          <div class="axis-activity-row__planning">
            <span class="axis-activity-row__planning-label">Période planifiée</span>
            <small>{{ activityWindow(activity) }}</small>
          </div>
        </div>

        <div class="axis-activity-row__side">
          <span class="status-badge status-badge--detail" :style="statusUiStyle({
            color: getStatusLegendColor(activity.status),
            softColor: getStatusLegendSoftColor(activity.status),
          })">
            <span class="status-badge__dot" />
            <span class="status-badge__label">{{ activity.status }}</span>
          </span>

          <span
            v-if="activityFlagLabel(activity)"
            class="axis-activity-row__flag"
            :class="{ 'axis-activity-row__flag--alert': activity.isOverdue }"
          >
            {{ activityFlagLabel(activity) }}
          </span>
        </div>
      </article>
    </div>

    <div v-else class="distribution-empty">
      <h3>Aucune activité pour ce filtre</h3>
      <p>Clique sur une autre pastille pour afficher une autre sélection.</p>
    </div>
  </section>

  <Teleport to="body">
    <transition name="activity-detail-fade">
      <div
        v-if="projectMetricPopover.visible"
        ref="projectMetricPopoverRef"
        class="activity-detail-popover axis-project-popover"
        :style="{
          left: `${projectMetricPopover.x}px`,
          top: `${projectMetricPopover.y}px`,
        }"
      >
        <div class="activity-detail-popover__header">
          <div class="activity-detail-popover__title-block">
            <span class="activity-detail-popover__eyebrow">{{ projectMetricPopover.metricLabel }}</span>
            <strong class="activity-detail-popover__title">{{ projectMetricPopover.projectLabel }}</strong>
          </div>

          <button
            type="button"
            class="activity-detail-popover__close"
            @click="closeProjectMetricPopover"
          >
            Fermer
          </button>
        </div>

        <div v-if="projectMetricPopover.activities.length" class="axis-project-popover__list">
          <article
            v-for="(activity, index) in projectMetricPopover.activities"
            :key="activity.id ?? `${projectMetricPopover.metricKey}-${projectMetricPopover.projectLabel}-${index}`"
            class="axis-project-popover__item"
          >
            <div class="axis-project-popover__item-top">
              <strong>{{ activity.activity }}</strong>
            </div>

            <small>{{ activityWindow(activity) }}</small>

            <span
              class="status-badge status-badge--detail"
              :style="statusUiStyle({
                color: getStatusLegendColor(activity.status),
                softColor: getStatusLegendSoftColor(activity.status),
              })"
            >
              <span class="status-badge__dot" />
              <span class="status-badge__label">{{ activity.status }}</span>
            </span>
          </article>
        </div>

        <p v-else class="axis-project-popover__empty">
          {{ projectMetricPopover.emptyMessage }}
        </p>
      </div>
    </transition>
  </Teleport>
</template>
