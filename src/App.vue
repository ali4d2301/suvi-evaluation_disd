<script setup>
import './assets/dashboard.css'

import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import LoginView from './components/LoginView.vue'
import ActivitiesTableSection from './components/dashboard/ActivitiesTableSection.vue'
import ActivityDistributionSection from './components/dashboard/ActivityDistributionSection.vue'
import DashboardHero from './components/dashboard/DashboardHero.vue'
import DashboardSidebar from './components/dashboard/DashboardSidebar.vue'
import DashboardStateCard from './components/dashboard/DashboardStateCard.vue'
import ExecutiveOverviewSection from './components/dashboard/ExecutiveOverviewSection.vue'
import KeyIndicatorsSection from './components/dashboard/KeyIndicatorsSection.vue'
import StrategicAxesSection from './components/dashboard/StrategicAxesSection.vue'
import UserManagementSection from './components/dashboard/UserManagementSection.vue'
import { ApiError, fetchCurrentUser, fetchDashboard, login, logout as logoutUser } from './services/api'
import { emptySummary, navItems as baseNavItems } from './utils/dashboardConstants'
import {
  buildAvailablePlannedYears,
  deriveDashboardSummary,
  filterActivitiesByActPeriod,
  filterActivitiesByAxisPeriod,
  normalizeDashboardText,
} from './utils/dashboardActivityFilters'
import {
  buildExecutiveCards,
  buildServiceStatusBreakdown,
  buildStatusBreakdown,
} from './utils/dashboardPresentation'

const USER_CACHE_KEY = 'dashboard-current-user'
const DASHBOARD_CACHE_KEY = 'dashboard-data'
const VIEW_CACHE_KEY = 'dashboard-active-view'
const USERS_CACHE_KEY = 'dashboard-users'
const DASHBOARD_REFRESH_INTERVAL_MS = 60000

function canUserManageUsers(user) {
  return user?.role === 'admin' || user?.isAdmin === true
}

function readCachedUser() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const rawUser = window.localStorage.getItem(USER_CACHE_KEY)
    const user = rawUser ? JSON.parse(rawUser) : null

    return user && typeof user === 'object' ? user : null
  } catch {
    return null
  }
}

function cacheCurrentUser(user) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(USER_CACHE_KEY, JSON.stringify(user))
  } catch {
    // The cookie remains the source of truth; cache failures should not block the dashboard.
  }
}

function clearCachedUser() {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.removeItem(USER_CACHE_KEY)
  } catch {
    // Ignore storage failures and keep the auth flow controlled by the backend session.
  }
}

function readCachedDashboard() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const rawDashboard = window.localStorage.getItem(DASHBOARD_CACHE_KEY)
    const cachedDashboard = rawDashboard ? JSON.parse(rawDashboard) : null

    return cachedDashboard && typeof cachedDashboard === 'object' ? cachedDashboard : null
  } catch {
    return null
  }
}

function cacheDashboard(nextDashboard) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(nextDashboard))
  } catch {
    // Keep rendering the live data even if the browser refuses to persist it.
  }
}

function clearCachedDashboard() {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.removeItem(DASHBOARD_CACHE_KEY)
  } catch {
    // Nothing to clean if storage is unavailable.
  }
}

function readCachedActiveView(user) {
  if (typeof window === 'undefined') {
    return 'ACT'
  }

  try {
    const cachedCode = window.localStorage.getItem(VIEW_CACHE_KEY)
    const isKnownView = baseNavItems.some((item) => item.code === cachedCode)

    if (!isKnownView || (cachedCode === 'USR' && !canUserManageUsers(user))) {
      return 'ACT'
    }

    return cachedCode
  } catch {
    return 'ACT'
  }
}

function cacheActiveView(code) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(VIEW_CACHE_KEY, code)
  } catch {
    // The active view can safely fall back to ACT on the next page load.
  }
}

function clearCachedActiveView() {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.removeItem(VIEW_CACHE_KEY)
  } catch {
    // Ignore storage failures.
  }
}

function clearCachedUsers() {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.removeItem(USERS_CACHE_KEY)
  } catch {
    // Ignore storage failures.
  }
}

const cachedUser = readCachedUser()
const cachedDashboard = cachedUser ? readCachedDashboard() : null
const currentUser = ref(cachedUser)
const isSessionLoading = ref(!cachedUser)
const isLoginSubmitting = ref(false)
const authErrorMessage = ref('')
const dashboard = ref(cachedDashboard)
const isLoading = ref(Boolean(cachedUser && !cachedDashboard))
const errorMessage = ref('')
const isSidebarCollapsed = ref(false)
const activeView = ref(readCachedActiveView(cachedUser))
const activeStatusFilter = ref('')
const activeServiceFilter = ref('')
const actPeriodSelection = ref({
  year: '',
  quarterStart: 1,
  quarterEnd: 4,
})
const axisPeriodSelection = ref({
  startYear: '',
  endYear: '',
})
let dashboardRefreshIntervalId = null

function resolveErrorMessage(error, fallback) {
  return error instanceof Error ? error.message : fallback
}

async function loadDashboard({ authFailureMessage = '', silent = false } = {}) {
  if (!silent) {
    isLoading.value = true
    errorMessage.value = ''
  }

  try {
    const freshDashboard = await fetchDashboard()
    dashboard.value = freshDashboard
    cacheDashboard(freshDashboard)
    return true
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      currentUser.value = null
      dashboard.value = null
      clearCachedUser()
      clearCachedDashboard()
      clearCachedActiveView()
      clearCachedUsers()
      authErrorMessage.value = authFailureMessage
      return false
    }

    if (!silent || !dashboard.value) {
      errorMessage.value = resolveErrorMessage(error, 'Erreur inattendue.')
    }
    return false
  } finally {
    if (!silent) {
      isLoading.value = false
    }
  }
}

function clearDashboardRefreshInterval() {
  if (typeof window === 'undefined' || dashboardRefreshIntervalId === null) {
    return
  }

  window.clearInterval(dashboardRefreshIntervalId)
  dashboardRefreshIntervalId = null
}

function refreshDashboardSilently() {
  if (!currentUser.value || isLoading.value) {
    return
  }

  void loadDashboard({ silent: true })
}

function ensureDashboardRefreshInterval() {
  if (typeof window === 'undefined' || dashboardRefreshIntervalId !== null) {
    return
  }

  dashboardRefreshIntervalId = window.setInterval(() => {
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
      return
    }

    refreshDashboardSilently()
  }, DASHBOARD_REFRESH_INTERVAL_MS)
}

function handleDocumentVisibilityChange() {
  if (typeof document === 'undefined' || document.visibilityState !== 'visible' || !currentUser.value) {
    return
  }

  refreshDashboardSilently()
}

async function initializeSession() {
  isSessionLoading.value = !currentUser.value
  authErrorMessage.value = ''

  try {
    const payload = await fetchCurrentUser()
    currentUser.value = payload.user
    cacheCurrentUser(payload.user)
    if (activeView.value === 'USR' && !canUserManageUsers(payload.user)) {
      activeView.value = 'ACT'
      cacheActiveView('ACT')
    }
    isSessionLoading.value = false
    await loadDashboard()
  } catch (error) {
    currentUser.value = null
    dashboard.value = null
    clearCachedUser()
    clearCachedDashboard()
    clearCachedActiveView()
    clearCachedUsers()
    isLoading.value = false

    if (!(error instanceof ApiError && error.status === 401)) {
      authErrorMessage.value = resolveErrorMessage(error, 'Impossible de verifier la session.')
    }
  } finally {
    isSessionLoading.value = false
  }
}

async function handleLogin(credentials) {
  isLoginSubmitting.value = true
  authErrorMessage.value = ''

  try {
    const payload = await login(credentials.username, credentials.password)
    currentUser.value = payload.user
    cacheCurrentUser(payload.user)
    activeView.value = 'ACT'
    cacheActiveView('ACT')
    await loadDashboard({
      authFailureMessage:
        "Connexion validee, mais la session n'a pas ete conservee par le navigateur. Rechargez la page puis reessayez.",
    })
  } catch (error) {
    authErrorMessage.value = resolveErrorMessage(error, 'Connexion impossible.')
  } finally {
    isLoginSubmitting.value = false
  }
}

async function handleLogout() {
  try {
    await logoutUser()
  } finally {
    currentUser.value = null
    dashboard.value = null
    clearCachedUser()
    clearCachedDashboard()
    clearCachedActiveView()
    clearCachedUsers()
    errorMessage.value = ''
    authErrorMessage.value = ''
    activeView.value = 'ACT'
    activeStatusFilter.value = ''
    activeServiceFilter.value = ''
    isSidebarCollapsed.value = false
  }
}

onMounted(() => {
  initializeSession()

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', handleDocumentVisibilityChange)
  }
})

onUnmounted(() => {
  clearDashboardRefreshInterval()

  if (typeof document !== 'undefined') {
    document.removeEventListener('visibilitychange', handleDocumentVisibilityChange)
  }
})

function normalizeTextValue(value) {
  return normalizeDashboardText(value)
}

function buildRawStatusCounts(activities) {
  const totals = new Map()

  activities.forEach((activity) => {
    const label = String(activity.status ?? '').trim()

    if (!label) {
      return
    }

    totals.set(label, (totals.get(label) ?? 0) + 1)
  })

  return [...totals.entries()].map(([label, total]) => ({ label, total }))
}

function buildRawServiceStatusCounts(activities) {
  const serviceTotals = new Map()

  activities.forEach((activity) => {
    const serviceLabel = String(activity.service ?? '').trim() || 'Non renseigné'
    const statusLabel = String(activity.status ?? '').trim()

    if (!statusLabel) {
      return
    }

    if (!serviceTotals.has(serviceLabel)) {
      serviceTotals.set(serviceLabel, new Map())
    }

    const statusTotals = serviceTotals.get(serviceLabel)
    statusTotals.set(statusLabel, (statusTotals.get(statusLabel) ?? 0) + 1)
  })

  return [...serviceTotals.entries()].map(([label, statuses]) => ({
    label,
    statuses: [...statuses.entries()].map(([statusLabel, total]) => ({
      label: statusLabel,
      total,
    })),
  }))
}

const summary = computed(() => dashboard.value?.summary ?? emptySummary)
const activities = computed(() => dashboard.value?.activities ?? [])
const availablePlannedYears = computed(() => buildAvailablePlannedYears(activities.value))
const actPeriodActivities = computed(() =>
  filterActivitiesByActPeriod(activities.value, actPeriodSelection.value),
)
const axisPeriodActivities = computed(() =>
  filterActivitiesByAxisPeriod(activities.value, axisPeriodSelection.value),
)
const actSummary = computed(() => deriveDashboardSummary(actPeriodActivities.value, summary.value))
const axisSummary = computed(() => deriveDashboardSummary(axisPeriodActivities.value, summary.value))
const heroSummary = computed(() => {
  if (activeView.value === 'AXE') {
    return axisSummary.value
  }

  if (activeView.value === 'ACT') {
    return actSummary.value
  }

  return summary.value
})
const lastDataUpdatedAt = computed(() => String(dashboard.value?.lastDataUpdatedAt ?? '').trim())
const executiveCards = computed(() => buildExecutiveCards(actSummary.value))
const canManageUsers = computed(() => canUserManageUsers(currentUser.value))
const sidebarNavItems = computed(() =>
  baseNavItems
    .filter((item) => item.code !== 'USR' || canManageUsers.value)
    .map((item) => ({
      ...item,
      active: item.code === activeView.value,
    })),
)
const serviceOptions = computed(() =>
  buildServiceStatusBreakdown(buildRawServiceStatusCounts(actPeriodActivities.value)).map((item) => item.label),
)
const chartActivities = computed(() =>
  actPeriodActivities.value.filter(
    (activity) =>
      !activeServiceFilter.value ||
      normalizeTextValue(activity.service) === normalizeTextValue(activeServiceFilter.value),
  ),
)
const statusBreakdown = computed(() => buildStatusBreakdown(buildRawStatusCounts(chartActivities.value)))
const serviceStatusBreakdown = computed(() =>
  buildServiceStatusBreakdown(buildRawServiceStatusCounts(chartActivities.value)),
)

watch(
  availablePlannedYears,
  (years) => {
    const latestYear = String(years.at(-1) ?? '').trim()

    if (!latestYear) {
      return
    }

    const currentYear = String(actPeriodSelection.value.year ?? '').trim()
    const hasCurrentYear = years.some((year) => String(year ?? '').trim() === currentYear)

    if (hasCurrentYear) {
      return
    }

    actPeriodSelection.value = {
      year: latestYear,
      quarterStart: 1,
      quarterEnd: 4,
    }
  },
  { immediate: true },
)

watch(
  currentUser,
  (user) => {
    if (user) {
      ensureDashboardRefreshInterval()
      return
    }

    clearDashboardRefreshInterval()
  },
  { immediate: true },
)

function setActiveView(code) {
  const nextCode = baseNavItems.some((item) => item.code === code) ? code : 'ACT'

  if (nextCode === 'USR' && !canManageUsers.value) {
    activeView.value = 'ACT'
    cacheActiveView('ACT')
    return
  }

  activeView.value = nextCode
  cacheActiveView(nextCode)
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

function selectView(code) {
  setActiveView(code)
}

function updateHeroPeriodSelection(nextSelection) {
  if (activeView.value === 'AXE') {
    axisPeriodSelection.value = {
      startYear: String(nextSelection?.startYear ?? '').trim(),
      endYear: String(nextSelection?.endYear ?? '').trim(),
    }
    return
  }

  actPeriodSelection.value = {
    year: String(nextSelection?.year ?? '').trim(),
    quarterStart: Math.max(1, Math.min(4, Number(nextSelection?.quarterStart ?? 1))),
    quarterEnd: Math.max(1, Math.min(4, Number(nextSelection?.quarterEnd ?? 4))),
  }
  activeStatusFilter.value = ''
  activeServiceFilter.value = ''
}
</script>

<template>
  <div v-if="isSessionLoading" class="auth-screen auth-screen--state">
    <DashboardStateCard
      title="Verification de la session"
      message="Le dashboard prepare votre espace de travail."
    />
  </div>

  <LoginView
    v-else-if="!currentUser"
    :error-message="authErrorMessage"
    :is-submitting="isLoginSubmitting"
    @submit="handleLogin"
  />

  <div v-else class="dashboard-shell">
  <div class="shell" :class="{ 'shell--sidebar-collapsed': isSidebarCollapsed }">
    <DashboardSidebar
      :is-collapsed="isSidebarCollapsed"
      :last-data-updated-at="lastDataUpdatedAt"
      :nav-items="sidebarNavItems"
      @logout="handleLogout"
      @toggle="toggleSidebar"
      @select="selectView"
    />

    <section class="workspace">
      <DashboardHero
        v-if="activeView !== 'KPI' && activeView !== 'USR'"
        :summary="heroSummary"
        :view="activeView"
        :available-years="availablePlannedYears"
        :period-selection="activeView === 'AXE' ? axisPeriodSelection : actPeriodSelection"
        @update:period-selection="updateHeroPeriodSelection"
      />

      <DashboardStateCard
        v-if="isLoading && !dashboard && activeView !== 'USR'"
        title="Chargement du tableau de bord"
        message="Les indicateurs et la liste des activités sont en cours de synchronisation."
      />

      <DashboardStateCard
        v-else-if="errorMessage && !dashboard && activeView !== 'USR'"
        title="Impossible de charger le dashboard"
        :message="errorMessage"
        error
      />

      <div v-else-if="dashboard || activeView === 'USR'" class="content-grid">
        <main class="content-main">
          <template v-if="activeView === 'ACT' && dashboard">
            <ExecutiveOverviewSection :cards="executiveCards" />

            <ActivityDistributionSection
              :status-breakdown="statusBreakdown"
              :service-status-breakdown="serviceStatusBreakdown"
              :active-status="activeStatusFilter"
              :active-service="activeServiceFilter"
              @update:active-status="activeStatusFilter = $event"
              @update:active-service="activeServiceFilter = $event"
            />

            <ActivitiesTableSection
              :activities="actPeriodActivities"
              :active-status="activeStatusFilter"
              :active-service="activeServiceFilter"
              :service-options="serviceOptions"
              @update:active-status="activeStatusFilter = $event"
              @update:active-service="activeServiceFilter = $event"
            />
          </template>

          <StrategicAxesSection
            v-else-if="activeView === 'AXE' && dashboard"
            :activities="axisPeriodActivities"
            :summary="axisSummary"
          />

          <UserManagementSection
            v-else-if="activeView === 'USR' && canManageUsers"
            :current-user="currentUser"
          />

          <KeyIndicatorsSection v-else-if="dashboard" :data="dashboard.keyIndicators" />
        </main>
      </div>
    </section>
  </div>
  </div>
</template>
