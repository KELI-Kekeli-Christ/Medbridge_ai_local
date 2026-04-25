'use client'

import { useEffect, useState } from 'react'
import type { ModelInfo } from '@/services/model-selection-api'
import { getSttModelsForLanguage } from '@/services/model-selection-api'

interface ModelSelectorProps {
  language: string
  onModelSelect?: (modelId: string) => void
}

export function ModelSelector({
  language,
  onModelSelect,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<string | undefined>(undefined)

  // Charger les modèles et le modèle sélectionné au montage
  useEffect(() => {
    const loadModels = async () => {
      setLoading(true)
      try {
        const availableModels = await getSttModelsForLanguage(language)
        setModels(availableModels)

        // Charger depuis localStorage le modèle sélectionné pour cette langue
        if (typeof window !== 'undefined') {
          const storedModel = localStorage.getItem(`selected_model_${language}`)
          if (storedModel && availableModels.some((m) => m.id === storedModel)) {
            setSelected(storedModel)
          } else if (availableModels.length > 0) {
            // Sinon, sélectionner le premier modèle (priorité 1)
            const defaultModel = availableModels[0]
            setSelected(defaultModel.id)
            localStorage.setItem(`selected_model_${language}`, defaultModel.id)
          }
        }
      } catch (error) {
        console.error('Failed to load models:', error)
      } finally {
        setLoading(false)
      }
    }

    loadModels()
  }, [language])

  const handleSelect = (modelId: string) => {
    setSelected(modelId)
    if (typeof window !== 'undefined') {
      localStorage.setItem(`selected_model_${language}`, modelId)
    }
    onModelSelect?.(modelId)
  }

  if (loading) {
    return <div className="text-sm text-gray-500">Chargement des modèles...</div>
  }

  if (models.length === 0) {
    return <div className="text-sm text-gray-500">Aucun modèle disponible</div>
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Modèle de reconnaissance vocale
      </label>
      <div className="space-y-2">
        {models.map((model) => (
          <label key={model.id} className="flex items-center space-x-3">
            <input
              type="radio"
              name={`stt-model-${language}`}
              value={model.id}
              checked={selected === model.id}
              onChange={() => handleSelect(model.id)}
              className="h-4 w-4 text-blue-600"
            />
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-900">
                {model.name}
              </span>
              <span className="text-xs text-gray-500">{model.description}</span>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
