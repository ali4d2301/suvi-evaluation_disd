<script setup>
import { computed, reactive } from 'vue'

import disdLogo from '../assets/disd-logo.png'

const props = defineProps({
  errorMessage: {
    type: String,
    default: '',
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit'])

const form = reactive({
  username: '',
  password: '',
})

const canSubmit = computed(() => Boolean(form.username.trim() && form.password && !props.isSubmitting))

function submitLogin() {
  if (!canSubmit.value) {
    return
  }

  emit('submit', {
    username: form.username.trim(),
    password: form.password,
  })
}
</script>

<template>
  <main class="auth-screen">
    <section class="auth-panel" aria-label="Connexion au dashboard">
      <div class="auth-panel__brand">
        <img
          class="auth-panel__logo"
          :src="disdLogo"
          alt="Direction de l'Informatique et de la Sante Digitale"
        />

        <div class="auth-panel__title">
          <span>Dashboard DISD</span>
          <h1>Connexion</h1>
          <p>Planification et Suivi-Evaluation</p>
        </div>
      </div>

      <form class="auth-form" @submit.prevent="submitLogin">
        <label class="form-field">
          <span>Identifiant</span>
          <input v-model="form.username" type="text" autocomplete="username" required />
        </label>

        <label class="form-field">
          <span>Mot de passe</span>
          <input v-model="form.password" type="password" autocomplete="current-password" required />
        </label>

        <p v-if="props.errorMessage" class="form-message form-message--error">
          {{ props.errorMessage }}
        </p>

        <button class="auth-form__submit" type="submit" :disabled="!canSubmit">
          {{ props.isSubmitting ? 'Connexion...' : 'Se connecter' }}
        </button>
      </form>
    </section>
  </main>
</template>
