<script setup lang="ts">
import { ref } from 'vue'
import type { ObjectType } from '../types'

const emit = defineEmits<{
  search: [payload: { adminId: number; objectTypes: ObjectType[]; languages: string[] }]
}>()

defineProps<{ loading: boolean }>()

const adminId = ref<string>('')
const languages = ref<string>('en')
const objectTypeOptions: { value: ObjectType; label: string }[] = [
  { value: 'streets', label: 'Streets (highway=*)' },
  { value: 'poi', label: 'POIs' },
  { value: 'relations', label: 'Relations' },
  { value: 'named', label: 'Anything with a name tag' },
  { value: 'named_no_highway', label: 'Anything named, except streets' },
]
const selectedTypes = ref<ObjectType[]>(['streets', 'poi'])

function submit() {
  const id = parseInt(adminId.value, 10)
  if (!id || selectedTypes.value.length === 0) return
  const langs = languages.value
    .split(',')
    .map((l) => l.trim())
    .filter(Boolean)
  emit('search', { adminId: id, objectTypes: selectedTypes.value, languages: langs })
}
</script>

<template>
  <form class="search-form" @submit.prevent="submit">
    <label class="field">
      <span>Admin relation ID</span>
      <input v-model="adminId" type="number" placeholder="e.g. 1155954" required />
    </label>

    <fieldset class="field">
      <legend>Object types</legend>
      <label v-for="opt in objectTypeOptions" :key="opt.value" class="checkbox">
        <input type="checkbox" :value="opt.value" v-model="selectedTypes" />
        {{ opt.label }}
      </label>
    </fieldset>

    <label class="field">
      <span>Languages (comma-separated, in addition to "name")</span>
      <input v-model="languages" type="text" placeholder="ru,en,de" />
    </label>

    <button type="submit" :disabled="loading">{{ loading ? 'Fetching…' : 'Fetch' }}</button>
  </form>
</template>

<style scoped>
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  border: none;
  padding: 0;
  margin: 0;
}
.field input[type='text'],
.field input[type='number'] {
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  min-width: 12rem;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: normal;
}
fieldset.field {
  display: flex;
  flex-direction: row;
  gap: 0.75rem;
  flex-wrap: wrap;
}
button {
  padding: 0.4rem 1rem;
  border-radius: 4px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: white;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
