import { buildBackendUrl, relayResponse } from '@/lib/backend'

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const upstream = await fetch(buildBackendUrl(`/api/prescriptions/${id}/pdf/`), {
    method: 'GET',
    cache: 'no-store',
  })

  return relayResponse(upstream)
}
