<script setup>
import { computed } from 'vue'

import disdLogo from '../../assets/disd-logo.png'
import { formatDateTimeLabel } from '../../utils/dashboardFormatters'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    required: true,
  },
  navItems: {
    type: Array,
    required: true,
  },
  lastDataUpdatedAt: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['toggle', 'select', 'logout'])
const lastUpdateLabel = computed(() => formatDateTimeLabel(props.lastDataUpdatedAt))
const showLastUpdate = computed(() => !props.isCollapsed && Boolean(lastUpdateLabel.value))

function toggleSidebar() {
  emit('toggle')
}

function selectView(code) {
  emit('select', code)
}

function logout() {
  emit('logout')
}
</script>

<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': props.isCollapsed }">
    <div class="sidebar__header">
      <div class="service-card" aria-label="Service référent de la plateforme">
        <span class="service-card__eyebrow">Service référent</span>
        <p class="service-card__name">Planification et Suivi-Évaluation</p>
      </div>

      <div class="sidebar__toggle-row">
        <button
          class="sidebar__toggle"
          type="button"
          :aria-label="props.isCollapsed ? 'Développer la barre latérale' : 'Réduire la barre latérale'"
          @click="toggleSidebar"
        >
          <span class="sidebar__toggle-bar" />
          <span class="sidebar__toggle-bar" />
          <span class="sidebar__toggle-bar" />
        </button>
      </div>
    </div>

    <div class="profile-card" aria-label="Direction de l'Informatique et de la Santé Digitale">
      <img
        class="profile-card__logo"
        :src="disdLogo"
        alt="Direction de l'Informatique et de la Santé Digitale"
      />
    </div>

    <nav class="sidebar__nav">
      <button
        v-for="item in props.navItems"
        :key="item.code"
        class="nav-link"
        :class="{ 'nav-link--active': item.active }"
        type="button"
        :aria-current="item.active ? 'page' : undefined"
        @click="selectView(item.code)"
      >
        <span class="nav-link__tag">{{ item.code }}</span>
        <span class="nav-link__label">{{ item.label }}</span>
      </button>
    </nav>

    <div class="sidebar__footer">
      <div v-if="showLastUpdate" class="sidebar__update-note" aria-live="polite">
        <span class="sidebar__update-eyebrow">Données</span>
        <p class="sidebar__update-text">Mise à jour le {{ lastUpdateLabel }}</p>
      </div>

      <button class="sidebar__logout" type="button" @click="logout">
        <span class="sidebar__logout-tag">OUT</span>
        <span class="sidebar__logout-label">Déconnexion</span>
      </button>
    </div>
  </aside>
</template>
