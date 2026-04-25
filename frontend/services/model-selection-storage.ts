/**
 * Service pour gérer les modèles sélectionnés par l'utilisateur
 */

const MODEL_SELECTION_KEY_PREFIX = 'selected_model_'

/**
 * Récupère le modèle sélectionné pour une langue
 */
export function getSelectedModel(language: string): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(`${MODEL_SELECTION_KEY_PREFIX}${language}`)
}

/**
 * Définit le modèle sélectionné pour une langue
 */
export function setSelectedModel(language: string, modelId: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(`${MODEL_SELECTION_KEY_PREFIX}${language}`, modelId)
}

/**
 * Récupère tous les modèles sélectionnés
 */
export function getAllSelectedModels(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  
  const models: Record<string, string> = {}
  const keys = Object.keys(localStorage)
  
  for (const key of keys) {
    if (key.startsWith(MODEL_SELECTION_KEY_PREFIX)) {
      const language = key.replace(MODEL_SELECTION_KEY_PREFIX, '')
      const modelId = localStorage.getItem(key)
      if (modelId) {
        models[language] = modelId
      }
    }
  }
  
  return models
}

/**
 * Efface le modèle sélectionné pour une langue
 */
export function clearSelectedModel(language: string): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(`${MODEL_SELECTION_KEY_PREFIX}${language}`)
}
