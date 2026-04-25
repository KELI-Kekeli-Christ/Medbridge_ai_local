'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getModels } from '@/services/model-api'
import { Header } from '@/components/layout/Header'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { ModelSelector } from '@/components/ui/ModelSelector'
import type { ModelInfo, ApiError } from '@/types'

const statusVariant: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  available: 'success',
  model_file_missing: 'default',
}

const typeLabel: Record<string, string> = {
  whisper: 'ASR (Reconnaissance vocale)',
  omni: 'ASR (Reconnaissance vocale)',
  nllb: 'Traduction NLLB',
  seq2seq: 'Traduction locale',
  classification: 'Détection de langue',
}

const typeGroup: Record<string, string> = {
  whisper: 'asr',
  omni: 'asr',
  nllb: 'translation',
  seq2seq: 'translation',
  classification: 'detection',
}

const groupLabel: Record<string, string> = {
  asr: 'Reconnaissance vocale (ASR)',
  translation: 'Traduction',
  detection: 'Détection de langue',
}

export default function StatusPage() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({})

  const fetchModels = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getModels()
      setModels(res)
    } catch (e) {
      setError(e as ApiError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchModels()
    if (typeof window !== 'undefined') {
      const stored: Record<string, string> = {}
      ;['ee', 'ar', 'fr'].forEach((lang) => {
        const selected = localStorage.getItem(`selected_model_${lang}`)
        if (selected) stored[lang] = selected
      })
      setSelectedModels(stored)
    }
  }, [])

  // Grouper par catégorie fonctionnelle (asr / translation / detection)
  const groupedByCategory = models.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    const group = typeGroup[m.type] ?? m.type
    acc[group] = [...(acc[group] ?? []), m]
    return acc
  }, {})

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">Statut des modèles IA</h1>
          <Button variant="secondary" size="sm" onClick={fetchModels} loading={loading}>
            Actualiser
          </Button>
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        )}

        {error && <ErrorMessage error={error} />}

        {!loading && !error && models.length === 0 && (
          <Card className="py-8 text-center text-slate-400 text-sm">
            Aucun modèle détecté — le backend est peut-être injoignable.
          </Card>
        )}

        {!loading && models.length > 0 && (
          <div className="space-y-6">
            {/* Statut des modèles par catégorie */}
            {Object.entries(groupedByCategory).map(([group, groupModels]) => (
              <Card key={group}>
                <CardHeader>
                  <CardTitle>{groupLabel[group] ?? group}</CardTitle>
                </CardHeader>
                <div className="divide-y divide-slate-100">
                  {groupModels.map((m) => (
                    <div key={m.model_id} className="flex items-center justify-between px-6 py-3">
                      <div>
                        <p className="text-sm font-medium text-slate-800">
                          {m.name ?? m.model_id}
                        </p>
                        <p className="text-xs text-slate-400 font-mono mt-0.5">{m.path_configured}</p>
                      </div>
                      <Badge variant={statusVariant[m.status] ?? 'default'}>
                        {m.loaded ? 'disponible' : 'fichier manquant'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </Card>
            ))}

            {/* Sélection des modèles ASR par langue */}
            <Card>
              <CardHeader>
                <CardTitle>Modèle ASR actif par langue</CardTitle>
              </CardHeader>
              <div className="space-y-6 p-6">

                {/* Ewe — choix whisper_ewe ou omni_ewe */}
                <div className="border-l-4 border-blue-500 pl-4">
                  <div className="mb-3">
                    <h3 className="text-base font-semibold text-slate-800">Ewe (ee)</h3>
                    {selectedModels['ee'] && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Actif : <span className="font-medium text-blue-700">{selectedModels['ee']}</span>
                      </p>
                    )}
                  </div>
                  <ModelSelector
                    language="ee"
                    onModelSelect={(id) => setSelectedModels((prev) => ({ ...prev, ee: id }))}
                  />
                </div>

                <div className="border-t pt-6" />

                {/* Arabe */}
                <div className="border-l-4 border-green-500 pl-4">
                  <div className="mb-3">
                    <h3 className="text-base font-semibold text-slate-800">Arabe (ar)</h3>
                    {selectedModels['ar'] && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Actif : <span className="font-medium text-green-700">{selectedModels['ar']}</span>
                      </p>
                    )}
                  </div>
                  <ModelSelector
                    language="ar"
                    onModelSelect={(id) => setSelectedModels((prev) => ({ ...prev, ar: id }))}
                  />
                </div>

                <div className="border-t pt-6" />

                {/* Français */}
                <div className="border-l-4 border-orange-500 pl-4">
                  <div className="mb-3">
                    <h3 className="text-base font-semibold text-slate-800">Français (fr)</h3>
                    {selectedModels['fr'] && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Actif : <span className="font-medium text-orange-700">{selectedModels['fr']}</span>
                      </p>
                    )}
                  </div>
                  <ModelSelector
                    language="fr"
                    onModelSelect={(id) => setSelectedModels((prev) => ({ ...prev, fr: id }))}
                  />
                </div>
              </div>
            </Card>

            {/* Info traduction */}
            <Card>
              <CardHeader>
                <CardTitle>Modèles de traduction NLLB</CardTitle>
              </CardHeader>
              <div className="divide-y divide-slate-100">
                {[
                  { label: 'Ewe → Français', key: 'nllb_ewe_fr', desc: 'Utilisé automatiquement pour les patients parlant Ewe' },
                  { label: 'Arabe → Français', key: 'nllb_ar_fr', desc: 'Utilisé automatiquement pour les patients parlant Arabe' },
                ].map(({ label, key, desc }) => {
                  const m = models.find((x) => x.model_id === key)
                  return (
                    <div key={key} className="flex items-center justify-between px-6 py-3">
                      <div>
                        <p className="text-sm font-medium text-slate-800">{label}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                      </div>
                      {m ? (
                        <Badge variant={statusVariant[m.status] ?? 'default'}>
                          {m.loaded ? 'disponible' : 'fichier manquant'}
                        </Badge>
                      ) : (
                        <Badge variant="default">inconnu</Badge>
                      )}
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        )}

        <div className="mt-8 text-center">
          <Link href="/">
            <Button variant="ghost" size="sm">← Retour à l'accueil</Button>
          </Link>
        </div>
      </main>
    </div>
  )
}
