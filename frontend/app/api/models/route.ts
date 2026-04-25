import { buildBackendUrl, relayResponse } from '@/lib/backend'

export async function GET() {
  const upstream = await fetch(buildBackendUrl('/api/models/'), {
    method: 'GET',
    cache: 'no-store',
  })

  return relayResponse(upstream)
}
