<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { OsmElement } from '../types'
import { elementKey } from '../types'

const props = defineProps<{
  elements: OsmElement[]
  languages: string[]
  edits: Record<string, Record<string, string>>
  selectedKey: string | null
}>()

const emit = defineEmits<{
  edit: [key: string, tagKey: string, value: string]
  select: [element: OsmElement]
}>()

interface Column {
  key: string
  label: string
}

const DEFAULT_WIDTH = 160
const DEFAULT_WIDTHS: Record<string, number> = { type: 80, id: 100 }

const columns = computed<Column[]>(() => [
  { key: 'type', label: 'Type' },
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'name' },
  ...props.languages.map((l) => ({ key: `name:${l}`, label: `name:${l}` })),
])

function valueFor(el: OsmElement, col: string): string {
  if (col === 'type') return el.osm_type
  if (col === 'id') return String(el.osm_id)
  const key = elementKey(el)
  return props.edits[key]?.[col] ?? el.tags[col] ?? ''
}

function isDirty(el: OsmElement): boolean {
  const key = elementKey(el)
  return Object.keys(props.edits[key] ?? {}).length > 0
}

function onInput(el: OsmElement, col: string, event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('edit', elementKey(el), col, value)
}

// Trim only on blur, not on every keystroke - trimming while typing would
// strip a trailing space the instant you type it, breaking multi-word names.
function onBlur(el: OsmElement, col: string, event: Event) {
  const input = event.target as HTMLInputElement
  const trimmed = input.value.trim()
  if (trimmed !== input.value) {
    emit('edit', elementKey(el), col, trimmed)
  }
}

function osmUrl(el: OsmElement): string {
  return `https://www.openstreetmap.org/${el.osm_type}/${el.osm_id}`
}

// --- sorting ---

const sortColumn = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('asc')

function toggleSort(col: string) {
  if (sortColumn.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = col
    sortDir.value = 'asc'
  }
}

const sortedElements = computed(() => {
  if (!sortColumn.value) return props.elements
  const col = sortColumn.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...props.elements].sort(
    (a, b) => dir * valueFor(a, col).localeCompare(valueFor(b, col), undefined, { numeric: true, sensitivity: 'base' }),
  )
})

// --- column resizing ---

const columnWidths = reactive<Record<string, number>>({})

function widthFor(col: string): number {
  return columnWidths[col] ?? DEFAULT_WIDTHS[col] ?? DEFAULT_WIDTH
}

let resizing: { col: string; startX: number; startWidth: number } | null = null

function startResize(col: string, event: MouseEvent) {
  resizing = { col, startX: event.clientX, startWidth: widthFor(col) }
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', stopResize)
}

function onResizeMove(event: MouseEvent) {
  if (!resizing) return
  const delta = event.clientX - resizing.startX
  columnWidths[resizing.col] = Math.max(40, resizing.startWidth + delta)
}

function stopResize() {
  resizing = null
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
}
</script>

<template>
  <div class="table-wrap">
    <table v-if="elements.length">
      <colgroup>
        <col v-for="col in columns" :key="col.key" :style="{ width: widthFor(col.key) + 'px' }" />
      </colgroup>
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key">
            <span class="th-label" @click="toggleSort(col.key)">
              {{ col.label }}
              <span v-if="sortColumn === col.key" class="sort-indicator">{{
                sortDir === 'asc' ? '▲' : '▼'
              }}</span>
            </span>
            <span class="resize-handle" @mousedown.stop.prevent="startResize(col.key, $event)"></span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="el in sortedElements"
          :key="elementKey(el)"
          :class="{ dirty: isDirty(el), selected: elementKey(el) === selectedKey }"
          @click="emit('select', el)"
        >
          <td v-for="col in columns" :key="col.key">
            <a
              v-if="col.key === 'id'"
              :href="osmUrl(el)"
              target="_blank"
              rel="noopener"
              :title="valueFor(el, col.key)"
              >{{ valueFor(el, col.key) }}</a
            >
            <span v-else-if="col.key === 'type'" :title="valueFor(el, col.key)">{{
              valueFor(el, col.key)
            }}</span>
            <input
              v-else
              type="text"
              :value="valueFor(el, col.key)"
              :title="valueFor(el, col.key)"
              @input="onInput(el, col.key, $event)"
              @blur="onBlur(el, col.key, $event)"
            />
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">No objects fetched yet.</p>
  </div>
</template>

<style scoped>
.table-wrap {
  flex: 1;
  overflow: auto;
}
table {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  font-size: 0.85rem;
}
th,
td {
  border: 1px solid var(--border);
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
}
th {
  padding: 0.25rem 0.4rem;
  position: sticky;
  top: 0;
  background: var(--surface);
  z-index: 1;
}
/* td itself carries no padding - the input/a/span inside it is stretched to
   fill the entire cell and carries the padding instead, so every pixel of
   the cell is part of the clickable/focusable/editable element. */
td {
  padding: 0;
}
.th-label {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  user-select: none;
}
.sort-indicator {
  font-size: 0.7em;
}
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 2;
}
.resize-handle:hover {
  background: var(--accent);
  opacity: 0.4;
}
tr.selected {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
tr.dirty td {
  background: var(--dirty-bg);
}
td a,
td span {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: 0.25rem 0.4rem;
  overflow: hidden;
  text-overflow: ellipsis;
}
input[type='text'] {
  display: block;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid transparent;
  background: transparent;
  padding: 0.25rem 0.4rem;
  font: inherit;
  text-overflow: ellipsis;
  cursor: text;
}
input[type='text']:focus {
  border-color: var(--accent);
  background: var(--surface);
  outline: none;
}
.empty {
  padding: 1rem;
  color: var(--muted);
}
</style>
