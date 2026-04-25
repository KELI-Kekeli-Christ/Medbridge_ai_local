import { buildBackendUrl, relayResponse } from '@/lib/backend'

type Ctx = { params: Promise<{ path: string[] }> }

async function forward(req: Request, ctx: Ctx, method: string): Promise<Response> {
  const { path } = await ctx.params
  const suffix = path.join('/')
  const authorization = req.headers.get('authorization')

  const headers: HeadersInit = {}
  if (authorization) {
    headers.Authorization = authorization
  }

  const contentType = req.headers.get('content-type')
  if (contentType) {
    headers['Content-Type'] = contentType
  }

  const hasBody = method !== 'GET' && method !== 'DELETE'
  const body = hasBody ? await req.text() : undefined

  const upstream = await fetch(buildBackendUrl(`/api/auth/${suffix}/`), {
    method,
    headers,
    body,
    cache: 'no-store',
  })

  return relayResponse(upstream)
}

export async function GET(req: Request, ctx: Ctx) {
  return forward(req, ctx, 'GET')
}

export async function POST(req: Request, ctx: Ctx) {
  return forward(req, ctx, 'POST')
}

export async function PUT(req: Request, ctx: Ctx) {
  return forward(req, ctx, 'PUT')
}

export async function PATCH(req: Request, ctx: Ctx) {
  return forward(req, ctx, 'PATCH')
}

export async function DELETE(req: Request, ctx: Ctx) {
  return forward(req, ctx, 'DELETE')
}
