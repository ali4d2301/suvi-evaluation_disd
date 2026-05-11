<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  error: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <div class="state-card" :class="{ 'state-card--error': props.error }">
    <div>
      <h2>{{ props.title }}</h2>
      <p>{{ props.message }}</p>
    </div>
  </div>
</template>
