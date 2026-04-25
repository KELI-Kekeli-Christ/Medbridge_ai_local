import { proxyJsonRequest } from '@/lib/backend'

export async function POST(req: Request) {
  return proxyJsonRequest(req, '/api/prescriptions/', 'POST')
}
