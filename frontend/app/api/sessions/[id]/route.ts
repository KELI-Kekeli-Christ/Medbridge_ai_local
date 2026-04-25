import { buildBackendUrl, relayResponse } from '@/lib/backend'

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const upstream = await fetch(buildBackendUrl(`/api/sessions/${id}/`), {
    method: 'GET',
    cache: 'no-store',
  })

  return relayResponse(upstream)
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const upstream = await fetch(buildBackendUrl(`/api/sessions/${id}/`), {
    method: 'DELETE',
    cache: 'no-store',
  })

  return relayResponse(upstream)
}
