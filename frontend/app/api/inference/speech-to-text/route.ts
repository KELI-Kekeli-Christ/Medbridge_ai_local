import { proxyFormDataRequest } from '@/lib/backend'

export async function POST(req: Request) {
  return proxyFormDataRequest(req, '/api/inference/speech-to-text/', 'POST')
}
