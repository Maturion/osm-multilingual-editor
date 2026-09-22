<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { OsmElement } from '../types'
import { elementKey } from '../types'

const props = defineProps<{
  elements: OsmElement[]
  selectedKey: string | null
}>()

const emit = defineEmits<{
  select: [element: OsmElement]
}>()

const mapContainer = ref<HTMLDivElement | null>(null)
let map: L.Map
const markers = new Map<string, L.Marker>()

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

onMounted(() => {
  map = L.map(mapContainer.value!).setView([0, 0], 2)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)
  renderMarkers()
})

onBeforeUnmount(() => {
  map?.remove()
})

function renderMarkers() {
  markers.forEach((m) => m.remove())
  markers.clear()

  const points: L.LatLngExpression[] = []
  for (const el of props.elements) {
    if (el.lat == null || el.lon == null) continue
    const key = elementKey(el)
    const marker = L.marker([el.lat, el.lon], { icon: defaultIcon })
      .addTo(map)
      .bindPopup(el.tags.name ?? `${el.osm_type}/${el.osm_id}`)
      .on('click', () => emit('select', el))
    markers.set(key, marker)
    points.push([el.lat, el.lon])
  }

  if (points.length) {
    map.fitBounds(L.latLngBounds(points), { padding: [20, 20], maxZoom: 16 })
  }
}

watch(() => props.elements, renderMarkers)

watch(
  () => props.selectedKey,
  (key) => {
    if (!key) return
    const marker = markers.get(key)
    if (marker) {
      map.flyTo(marker.getLatLng(), Math.max(map.getZoom(), 16))
      marker.openPopup()
    }
  },
)
</script>

<template>
  <div ref="mapContainer" class="map"></div>
</template>

<style scoped>
.map {
  height: 100%;
  width: 100%;
}
</style>
