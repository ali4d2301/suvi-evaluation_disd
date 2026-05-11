<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, Teleport } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Selectionner',
  },
})

const emit = defineEmits(['update:modelValue'])

const rootRef = ref(null)
const panelRef = ref(null)
const isOpen = ref(false)
const panelReady = ref(false)
const panelStyle = ref({
  left: '0px',
  top: '0px',
  minWidth: '0px',
})

const selectedOption = computed(
  () => props.options.find((option) => String(option.value) === String(props.modelValue)) ?? null,
)

function updatePlacement() {
  const rootElement = rootRef.value
  const panelElement = panelRef.value

  if (!rootElement || !panelElement || typeof window === 'undefined') {
    return
  }

  const rootRect = rootElement.getBoundingClientRect()
  const panelRect = panelElement.getBoundingClientRect()
  const gap = 8
  const viewportPadding = 16
  const openUp =
    window.innerHeight - rootRect.bottom < panelRect.height + gap + viewportPadding &&
    rootRect.top > window.innerHeight - rootRect.bottom
  const alignEnd =
    window.innerWidth - rootRect.left < panelRect.width + viewportPadding &&
    rootRect.right > window.innerWidth - rootRect.left

  let left = alignEnd ? rootRect.right - panelRect.width : rootRect.left
  let top = openUp ? rootRect.top - panelRect.height - gap : rootRect.bottom + gap

  left = Math.min(
    Math.max(viewportPadding, left),
    Math.max(viewportPadding, window.innerWidth - panelRect.width - viewportPadding),
  )
  top = Math.min(
    Math.max(viewportPadding, top),
    Math.max(viewportPadding, window.innerHeight - panelRect.height - viewportPadding),
  )

  panelStyle.value = {
    left: `${Math.round(left)}px`,
    top: `${Math.round(top)}px`,
    minWidth: `${Math.round(rootRect.width)}px`,
  }
  panelReady.value = true
}

function openPanel() {
  isOpen.value = true
  panelReady.value = false

  nextTick(() => {
    updatePlacement()
  })
}

function closePanel() {
  isOpen.value = false
  panelReady.value = false
}

function togglePanel() {
  if (isOpen.value) {
    closePanel()
    return
  }

  openPanel()
}

function selectOption(optionValue) {
  emit('update:modelValue', optionValue)
  closePanel()
}

function handleTriggerKeydown(event) {
  if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openPanel()
  }

  if (event.key === 'Escape') {
    closePanel()
  }
}

function handleDocumentPointerDown(event) {
  const rootElement = rootRef.value
  const panelElement = panelRef.value

  if (rootElement?.contains(event.target) || panelElement?.contains(event.target)) {
    return
  }

  closePanel()
}

function handleWindowChange() {
  if (!isOpen.value) {
    return
  }

  nextTick(() => {
    updatePlacement()
  })
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  window.addEventListener('resize', handleWindowChange)
  window.addEventListener('scroll', handleWindowChange, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  window.removeEventListener('resize', handleWindowChange)
  window.removeEventListener('scroll', handleWindowChange, true)
})
</script>

<template>
  <div ref="rootRef" class="refined-select">
    <button
      type="button"
      class="refined-select__trigger"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click="togglePanel"
      @keydown="handleTriggerKeydown"
    >
      <span class="refined-select__value" :class="{ 'refined-select__value--placeholder': !selectedOption }">
        {{ selectedOption?.label ?? placeholder }}
      </span>
      <span class="refined-select__chevron" aria-hidden="true" />
    </button>

    <Teleport to="body">
      <transition name="refined-select-fade">
        <div
          v-if="isOpen"
          ref="panelRef"
          class="refined-select__panel"
          :style="[panelStyle, { visibility: panelReady ? 'visible' : 'hidden' }]"
        >
          <button
            v-for="option in props.options"
            :key="`${option.value}`"
            type="button"
            class="refined-select__option"
            :class="{ 'refined-select__option--active': String(option.value) === String(props.modelValue) }"
            @click="selectOption(option.value)"
          >
            <span>{{ option.label }}</span>
            <span
              v-if="String(option.value) === String(props.modelValue)"
              class="refined-select__check"
              aria-hidden="true"
            />
          </button>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.refined-select {
  position: relative;
  width: 100%;
  min-width: 0;
}

.refined-select__trigger {
  width: 100%;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
  padding: 0.62rem 0.74rem;
  border: 1px solid rgba(173, 188, 206, 0.96);
  border-radius: 12px;
  background: rgba(255, 255, 255, 1);
  color: #17314c;
  font: inherit;
  text-align: left;
  box-shadow:
    inset 0 1px 1px rgba(234, 239, 244, 0.88),
    0 1px 2px rgba(23, 49, 76, 0.04);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.refined-select__trigger:hover {
  border-color: rgba(121, 140, 164, 0.72);
  background: rgba(251, 253, 255, 1);
}

.refined-select__trigger:focus-visible {
  outline: none;
  border-color: rgba(73, 95, 123, 0.86);
  box-shadow:
    0 0 0 3px rgba(74, 96, 124, 0.14),
    inset 0 1px 1px rgba(234, 239, 244, 0.88);
}

.refined-select__value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.refined-select__value--placeholder {
  color: #5e7590;
}

.refined-select__chevron {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-right: 1.7px solid rgba(66, 86, 111, 0.98);
  border-bottom: 1.7px solid rgba(66, 86, 111, 0.98);
  transform: translateY(-2px) rotate(45deg);
  transition: transform 0.18s ease;
}

.refined-select__trigger[aria-expanded='true'] .refined-select__chevron {
  transform: translateY(1px) rotate(-135deg);
}

.refined-select__panel {
  position: fixed;
  z-index: 120;
  width: max-content;
  max-width: min(320px, calc(100vw - 2rem));
  display: grid;
  gap: 0.2rem;
  padding: 0.42rem;
  border: 1px solid rgba(185, 199, 216, 0.98);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.995);
  box-shadow:
    0 20px 46px rgba(15, 35, 60, 0.14),
    0 4px 12px rgba(15, 35, 60, 0.06);
  backdrop-filter: blur(12px);
}

.refined-select__option {
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.62rem 0.74rem;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #17314c;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.refined-select__option:hover,
.refined-select__option:focus-visible {
  outline: none;
  background: rgba(237, 242, 247, 0.96);
}

.refined-select__option--active {
  background: rgba(228, 235, 243, 0.98);
  color: #112a45;
  font-weight: 700;
}

.refined-select__check {
  width: 10px;
  height: 6px;
  flex: 0 0 auto;
  border-left: 1.8px solid currentColor;
  border-bottom: 1.8px solid currentColor;
  transform: rotate(-45deg);
}

.refined-select-fade-enter-active,
.refined-select-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.refined-select-fade-enter-from,
.refined-select-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
