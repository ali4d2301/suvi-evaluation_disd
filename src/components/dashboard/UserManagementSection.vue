<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { createUser, fetchUsers, updateUser, updateUserPassword } from '../../services/api'

const props = defineProps({
  currentUser: {
    type: Object,
    required: true,
  },
})

const USERS_CACHE_KEY = 'dashboard-users'

function readCachedUsers() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const rawUsers = window.localStorage.getItem(USERS_CACHE_KEY)
    const cachedUsers = rawUsers ? JSON.parse(rawUsers) : null

    return Array.isArray(cachedUsers) ? cachedUsers : null
  } catch {
    return null
  }
}

function cacheUsers(nextUsers) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(USERS_CACHE_KEY, JSON.stringify(nextUsers))
  } catch {
    // The API response stays authoritative if the browser cannot persist the list.
  }
}

const cachedUsers = readCachedUsers()
const users = ref(cachedUsers ?? [])
const isLoading = ref(!cachedUsers)
const isCreating = ref(false)
const activeUserActionId = ref(null)
const errorMessage = ref('')
const successMessage = ref('')
const resetPasswordUserId = ref(null)

const form = reactive({
  displayName: '',
  username: '',
  password: '',
})

const passwordForm = reactive({
  password: '',
})

const currentUserId = computed(() => Number(props.currentUser?.id ?? 0))

function formatDate(value) {
  if (!value) {
    return 'Jamais'
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function resetMessages() {
  errorMessage.value = ''
  successMessage.value = ''
}

function resetCreateForm() {
  form.displayName = ''
  form.username = ''
  form.password = ''
}

function setUsers(nextUsers) {
  users.value = nextUsers
  cacheUsers(nextUsers)
}

function upsertUser(nextUser) {
  const existingIndex = users.value.findIndex((user) => user.id === nextUser.id)

  if (existingIndex === -1) {
    setUsers([nextUser, ...users.value])
    return
  }

  setUsers(users.value.map((user) => (user.id === nextUser.id ? nextUser : user)))
}

async function loadUsers(options = {}) {
  isLoading.value = true

  if (!options.silent) {
    resetMessages()
  }

  try {
    const payload = await fetchUsers()
    setUsers(payload.users)
  } catch (error) {
    if (!options.silent || !users.value.length) {
      errorMessage.value = error instanceof Error ? error.message : 'Impossible de charger les utilisateurs.'
    }
  } finally {
    isLoading.value = false
  }
}

async function submitUser() {
  resetMessages()
  isCreating.value = true

  try {
    const payload = await createUser({
      displayName: form.displayName.trim(),
      username: form.username.trim(),
      password: form.password,
    })
    upsertUser(payload.user)
    resetCreateForm()
    successMessage.value = 'Utilisateur cree.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Creation impossible.'
  } finally {
    isCreating.value = false
  }
}

async function toggleUser(user) {
  resetMessages()
  activeUserActionId.value = user.id

  try {
    const payload = await updateUser(user.id, { isActive: !user.isActive })
    upsertUser(payload.user)
    successMessage.value = payload.user.isActive ? 'Utilisateur reactive.' : 'Utilisateur desactive.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Mise a jour impossible.'
  } finally {
    activeUserActionId.value = null
  }
}

function openPasswordReset(userId) {
  resetMessages()
  resetPasswordUserId.value = userId
  passwordForm.password = ''
}

function closePasswordReset() {
  resetPasswordUserId.value = null
  passwordForm.password = ''
}

async function submitPasswordReset(user) {
  resetMessages()
  activeUserActionId.value = user.id

  try {
    await updateUserPassword(user.id, passwordForm.password)
    closePasswordReset()
    successMessage.value = 'Mot de passe mis a jour.'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Mot de passe non modifie.'
  } finally {
    activeUserActionId.value = null
  }
}

onMounted(() => loadUsers({ silent: Boolean(cachedUsers) }))
</script>

<template>
  <section class="panel panel--users">
    <div class="panel__header panel__header--space">
      <div class="section-title section-title--plain">
        <div class="section-title__copy">
          <span class="panel__eyebrow">Acces</span>
          <h2>Utilisateurs</h2>
          <p class="panel__meta">Les comptes standards consultent le dashboard. Seul l'administrateur gere les acces.</p>
        </div>
      </div>
    </div>

    <form class="user-create-form" @submit.prevent="submitUser">
      <label class="form-field">
        <span>Nom affiche</span>
        <input v-model="form.displayName" type="text" required />
      </label>

      <label class="form-field">
        <span>Identifiant</span>
        <input v-model="form.username" type="text" autocomplete="off" required />
      </label>

      <label class="form-field">
        <span>Mot de passe initial</span>
        <input v-model="form.password" type="password" autocomplete="new-password" minlength="8" required />
      </label>

      <button class="user-create-form__submit" type="submit" :disabled="isCreating">
        {{ isCreating ? 'Creation...' : 'Ajouter' }}
      </button>
    </form>

    <div v-if="errorMessage || successMessage" class="user-feedback">
      <p v-if="errorMessage" class="form-message form-message--error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="form-message form-message--success">{{ successMessage }}</p>
    </div>
  </section>

  <section class="panel panel--users-list">
    <div class="panel__header panel__header--space">
      <div class="section-title section-title--plain">
        <div class="section-title__copy">
          <span class="panel__eyebrow">Comptes</span>
          <h2>Acces actifs</h2>
        </div>
      </div>
      <button class="users-refresh" type="button" :disabled="isLoading" @click="loadUsers()">
        {{ isLoading && users.length ? 'Actualisation...' : 'Actualiser' }}
      </button>
    </div>

    <div v-if="isLoading && !users.length" class="users-empty">Chargement des utilisateurs...</div>
    <div v-else-if="!users.length" class="users-empty">Aucun utilisateur pour le moment.</div>

    <div v-else class="users-list">
      <article
        v-for="user in users"
        :key="user.id"
        class="user-row"
        :class="{ 'user-row--inactive': !user.isActive }"
      >
        <div class="user-row__identity">
          <span class="user-row__avatar">{{ user.displayName.slice(0, 2).toUpperCase() }}</span>
          <div>
            <strong>{{ user.displayName }}</strong>
            <small>{{ user.username }}</small>
          </div>
        </div>

        <div class="user-row__meta">
          <span :class="['user-role', user.role === 'admin' ? 'user-role--admin' : 'user-role--user']">
            {{ user.role === 'admin' ? 'Administrateur' : 'Utilisateur' }}
          </span>
          <span :class="['user-status', user.isActive ? 'user-status--active' : 'user-status--inactive']">
            {{ user.isActive ? 'Actif' : 'Inactif' }}
          </span>
          <small>Derniere connexion: {{ formatDate(user.lastLoginAt) }}</small>
        </div>

        <div class="user-row__actions">
          <button
            type="button"
            :disabled="activeUserActionId === user.id || (user.id === currentUserId && user.isActive)"
            @click="toggleUser(user)"
          >
            {{ user.isActive ? 'Desactiver' : 'Reactiver' }}
          </button>
          <button type="button" @click="openPasswordReset(user.id)">Mot de passe</button>
        </div>

        <form
          v-if="resetPasswordUserId === user.id"
          class="user-password-form"
          @submit.prevent="submitPasswordReset(user)"
        >
          <label class="form-field">
            <span>Nouveau mot de passe</span>
            <input v-model="passwordForm.password" type="password" minlength="8" autocomplete="new-password" required />
          </label>
          <div class="user-password-form__actions">
            <button type="submit" :disabled="activeUserActionId === user.id">Enregistrer</button>
            <button type="button" @click="closePasswordReset">Annuler</button>
          </div>
        </form>
      </article>
    </div>
  </section>
</template>
