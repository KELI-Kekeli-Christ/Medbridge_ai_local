/**
 * Service pour la gestion des modèles disponibles
 */

import { buildBackendUrl } from '@/lib/backend'

export interface ModelInfo {
  id: string
  name: string
  type: string
  description: string
  priority: number
  path?: string
  available?: boolean
}

export interface SttModelsResponse {
  language: string
  models: ModelInfo[]
}

export interface TranslationModelsResponse {
  source_language: string
  target_language: string
  models: ModelInfo[]
}

/**
 * Récupère les modèles STT disponibles pour une langue
 */
export async function getSttModelsForLanguage(
  language: string,
): Promise<ModelInfo[]> {
  const url = buildBackendUrl(
    `/api/inference/models/stt/?language=${encodeURIComponent(language)}`,
  )

  const res = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  })

  if (!res.ok) {
    console.error('Failed to fetch STT models:', res.statusText)
    return []
  }

  const data = (await res.json()) as SttModelsResponse
  return data.models
}

/**
 * Récupère les modèles de traduction disponibles pour une paire de langues
 */
export async function getTranslationModelsForLanguagePair(
  sourceLanguage: string,
  targetLanguage: string,
): Promise<ModelInfo[]> {
  const url = buildBackendUrl(
    `/api/inference/models/translation/?source=${encodeURIComponent(sourceLanguage)}&target=${encodeURIComponent(targetLanguage)}`,
  )

  const res = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  })

  if (!res.ok) {
    console.error('Failed to fetch translation models:', res.statusText)
    return []
  }

  const data = (await res.json()) as TranslationModelsResponse
  return data.models
}

/**
 * Filtre les modèles disponibles (available === true)
 */
export function filterAvailableModels(models: ModelInfo[]): ModelInfo[] {
  return models.filter((m) => m.available !== false)
}

/**
 * Récupère le modèle par défaut (priorité 1)
 */
export function getDefaultModel(models: ModelInfo[]): ModelInfo | null {
  const sorted = models.sort((a, b) => a.priority - b.priority)
  return sorted.length > 0 ? sorted[0] : null
}
