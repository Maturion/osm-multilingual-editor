<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import SearchForm from './components/SearchForm.vue'
import NameTable from './components/NameTable.vue'
import MapView from './components/MapView.vue'
import { fetchElements, getAuthStatus, loginUrl, logout, uploadChanges } from './api'
import type { AuthStatus, ObjectType, OsmElement, UploadElement, UploadResponse } from './types'
import { elementKey } from './types'

const elements = ref<OsmElement[]>([])
const languages = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedKey = ref<string | null>(null)
const edits = reactive<Record<string, Record<string, string>>>({})

const auth = ref<AuthStatus>({ logged_in: false, username: null, environment: '…' })
const confirming = ref(false)
const uploading = ref(false)
const uploadResult = ref<UploadResponse | null>(null)
const comment = ref('Add/update multilingual names')

const dirtyElements = computed<UploadElement[]>(() =>
  elements.value
    .filter((el) => Object.keys(edits[elementKey(el)] ?? {}).length > 0)
    .map((el) => {
      const trimmedEdits = Object.fromEntries(
        Object.entries(edits[elementKey(el)]).map(([k, v]) => [k, v.trim()]),
      )
      return {
        osm_type: el.osm_type,
        osm_id: el.osm_id,
        tags: { ...el.tags, ...trimmedEdits },
      }
    }),
)

onMounted(refreshAuth)

async function refreshAuth() {
  try {
    auth.value = await getAuthStatus()
  } catch (e) {
    error.value = `Could not reach backend: ${(e as Error).message}`
  }
}

async function onSearch(payload: { adminId: number; objectTypes: ObjectType[]; languages: string[] }) {
  loading.value = true
  error.value = null
  uploadResult.value = null
  try {
    const res = await fetchElements({
      admin_id: payload.adminId,
      object_types: payload.objectTypes,
      languages: payload.languages,
    })
    elements.value = res.elements
    languages.value = payload.languages
    selectedKey.value = null
    for (const key of Object.keys(edits)) delete edits[key]
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function onEdit(key: string, tagKey: string, value: string) {
  if (!edits[key]) edits[key] = {}
  edits[key][tagKey] = value
}

function onSelect(el: OsmElement) {
  selectedKey.value = elementKey(el)
}

async function onLogout() {
  await logout()
  await refreshAuth()
}

async function confirmUpload() {
  uploading.value = true
  error.value = null
  try {
    uploadResult.value = await uploadChanges(comment.value, dirtyElements.value)
    for (const key of Object.keys(edits)) delete edits[key]
    confirming.value = false
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="app">
    <header class="topbar">
      <h1>OSM Multilingual Name Editor</h1>
      <div class="topbar-right">
        <span class="env" :class="auth.environment">{{ auth.environment }}</span>
        <template v-if="auth.logged_in">
          <span>{{ auth.username }}</span>
          <button @click="onLogout">Log out</button>
        </template>
        <a v-else class="login-link" :href="loginUrl()">Login with OpenStreetMap</a>
      </div>
    </header>

    <SearchForm :loading="loading" @search="onSearch" />

    <p v-if="error" class="error">{{ error }}</p>

    <div class="save-bar" v-if="dirtyElements.length">
      <span>{{ dirtyElements.length }} object(s) with unsaved changes</span>
      <button :disabled="!auth.logged_in" @click="confirming = true">
        {{ auth.logged_in ? 'Save changes…' : 'Log in to save' }}
      </button>
    </div>

    <div v-if="uploadResult" class="upload-result">
      Uploaded as changeset
      <a
        :href="`https://www.openstreetmap.org/changeset/${uploadResult.changeset_id}`"
        target="_blank"
        rel="noopener"
        >#{{ uploadResult.changeset_id }}</a
      >:
      <span
        v-for="r in uploadResult.results"
        :key="`${r.osm_type}/${r.osm_id}`"
        :class="r.success ? 'ok' : 'fail'"
      >
        {{ r.osm_type }}/{{ r.osm_id }} {{ r.success ? 'ok' : `failed: ${r.error}` }}
      </span>
    </div>

    <main class="content">
      <NameTable
        :elements="elements"
        :languages="languages"
        :edits="edits"
        :selected-key="selectedKey"
        @edit="onEdit"
        @select="onSelect"
      />
      <MapView :elements="elements" :selected-key="selectedKey" @select="onSelect" />
    </main>

    <div v-if="confirming" class="modal-backdrop" @click.self="confirming = false">
      <div class="modal">
        <h2>Confirm changeset</h2>
        <label class="field">
          <span>Changeset comment</span>
          <input v-model="comment" type="text" />
        </label>
        <ul class="diff-list">
          <li v-for="el in dirtyElements" :key="`${el.osm_type}/${el.osm_id}`">
            <strong>{{ el.osm_type }}/{{ el.osm_id }}</strong>
            <span
              v-for="(val, key) in edits[`${el.osm_type}/${el.osm_id}`]"
              :key="key"
            >
              {{ key }} → "{{ val }}"
            </span>
          </li>
        </ul>
        <div class="modal-actions">
          <button @click="confirming = false" :disabled="uploading">Cancel</button>
          <button @click="confirmUpload" :disabled="uploading">
            {{ uploading ? 'Uploading…' : 'Upload to OpenStreetMap' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
:root {
  --border: #d8d8d8;
  --surface: #ffffff;
  --accent: #2563eb;
  --muted: #777;
  --dirty-bg: #fff7d6;
}
* {
  box-sizing: border-box;
}
html,
body,
#app {
  height: 100%;
  margin: 0;
}
body {
  font-family: system-ui, sans-serif;
}
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--border);
}
.topbar h1 {
  font-size: 1.1rem;
  margin: 0;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.env {
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  text-transform: uppercase;
  background: #eee;
}
.env.prod {
  background: #fde2e2;
}
.env.dev {
  background: #e2f0fd;
}
.login-link {
  color: var(--accent);
}
.error {
  color: #b00020;
  padding: 0 1rem;
}
.save-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: var(--dirty-bg);
}
.upload-result {
  padding: 0.5rem 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  background: #eef;
}
.upload-result .ok {
  color: #0a7a0a;
}
.upload-result .fail {
  color: #b00020;
}
.content {
  flex: 1;
  display: flex;
  min-height: 0;
}
.content > *:first-child {
  flex: 2;
  min-width: 0;
}
.content > *:last-child {
  flex: 1;
  border-left: 1px solid var(--border);
}
button {
  padding: 0.35rem 0.9rem;
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
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal {
  background: var(--surface);
  padding: 1.5rem;
  border-radius: 8px;
  max-width: 32rem;
  width: 90%;
  max-height: 80vh;
  overflow: auto;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
}
.field input {
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
}
.diff-list {
  list-style: none;
  padding: 0;
  font-size: 0.85rem;
}
.diff-list li {
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
</style>
