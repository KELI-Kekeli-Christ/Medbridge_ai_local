/**
 * Hook pour gérer la sélection des modèles d'inférence
 */
'use client'

import { useState, useEffect, useCallback } from 'react'

export interface SelectedModels {
  ewe?: string
  arabic?: string
  french?: string
}

/**
 * Hook pour accéder aux modèles sélectionnés par l'utilisateur
 * Les valeurs sont lues depuis localStorage
 */
export function useSelectedModels() {
  const [selected, setSelected] = useState<SelectedModels>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Charger depuis localStorage au montage
    if (typeof window !== 'undefined') {
      const ewe = localStorage.getItem('selected_model_ee')
      const arabic = localStorage.getItem('selected_model_ar')
      const french = localStorage.getItem('selected_model_fr')

      setSelected({
        ewe: ewe || undefined,
        arabic: arabic || undefined,
        french: french || undefined,
      })
      setLoading(false)
    }
  }, [])

  // Écouter les changements dans localStorage
  const handleStorageChange = useCallback((e: StorageEvent) => {
    if (e.key?.startsWith('selected_model_')) {
      const lang = e.key.replace('selected_model_', '')
      setSelected((prev) => ({
        ...prev,
        [lang === 'ee' ? 'ewe' : lang === 'ar' ? 'arabic' : 'french']: e.newValue || undefined,
      }))
    }
  }, [])

  useEffect(() => {
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [handleStorageChange])

  const getSelectedModelForLanguage = useCallback((language: string): string | null => {
    const langKey = language.toLowerCase()
    if (langKey === 'ee' || langKey === 'ewe') return selected.ewe || null
    if (langKey === 'ar' || langKey === 'arabic') return selected.arabic || null
    if (langKey === 'fr' || langKey === 'french') return selected.french || null
    return null
  }, [selected])

  return {
    selected,
    loading,
    getSelectedModelForLanguage,
  }
}

/**
 * Hook simplifié pour accéder au modèle sélectionné pour une langue donnée
 */
export function useModelSelection() {
  const { getSelectedModelForLanguage } = useSelectedModels()

  return {
    getSelectedModel: (language: string): string | undefined => {
      const model = getSelectedModelForLanguage(language)
      return model || undefined
    },
  }
}
