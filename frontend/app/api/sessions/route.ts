import { buildBackendUrl, relayResponse } from '@/lib/backend'

export async function GET() {
  const upstream = await fetch(buildBackendUrl('/api/sessions/'), {
    method: 'GET',
    cache: 'no-store',
  })

  return relayResponse(upstream)
}

export async function POST() {
  const upstream = await fetch(buildBackendUrl('/api/sessions/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
    cache: 'no-store',
  })

  return relayResponse(upstream)
}
