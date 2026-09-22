export type ObjectType = 'streets' | 'poi' | 'relations' | 'named' | 'named_no_highway'
export type OsmType = 'node' | 'way' | 'relation'

export interface OsmElement {
  osm_type: OsmType
  osm_id: number
  lat: number | null
  lon: number | null
  version: number
  tags: Record<string, string>
}

export interface FetchRequest {
  admin_id: number
  object_types: ObjectType[]
  languages: string[]
}

export interface FetchResponse {
  elements: OsmElement[]
}

export interface AuthStatus {
  logged_in: boolean
  username: string | null
  environment: string
}

export interface UploadElement {
  osm_type: OsmType
  osm_id: number
  tags: Record<string, string>
}

export interface UploadElementResult {
  osm_type: OsmType
  osm_id: number
  success: boolean
  new_version: number | null
  error: string | null
}

export interface UploadResponse {
  changeset_id: number
  results: UploadElementResult[]
}

export function elementKey(el: { osm_type: OsmType; osm_id: number }): string {
  return `${el.osm_type}/${el.osm_id}`
}
