const envApiUrl = (globalThis as { process?: { env?: Record<string, string | undefined> } })
  .process?.env?.NEXT_PUBLIC_API_URL

const BACKEND_BASE_URL = (envApiUrl ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export function buildBackendUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${BACKEND_BASE_URL}${normalized}`
}

export function relayResponse(upstream: Response): Response {
  const headers = new Headers(upstream.headers)
  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  })
}

export async function proxyJsonRequest(
  req: Request,
  path: string,
  method: string,
): Promise<Response> {
  const payload = await req.json()
  const authorization = req.headers.get('authorization')

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (authorization) {
    headers.Authorization = authorization
  }

  const upstream = await fetch(buildBackendUrl(path), {
    method,
    headers,
    body: JSON.stringify(payload),
    cache: 'no-store',
  })

  return relayResponse(upstream)
}

export async function proxyFormDataRequest(
  req: Request,
  path: string,
  method: string,
): Promise<Response> {
  const formData = await req.formData()
  const authorization = req.headers.get('authorization')

  const headers: HeadersInit = {}
  if (authorization) {
    headers.Authorization = authorization
  }

  const upstream = await fetch(buildBackendUrl(path), {
    method,
    headers,
    body: formData,
    cache: 'no-store',
  })

  return relayResponse(upstream)
}
