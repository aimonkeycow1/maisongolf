import { createServer } from 'vite'

const server = await createServer({
  server: { middlewareMode: true },
  appType: 'custom',
  logLevel: 'error',
})

try {
  const mod = await server.ssrLoadModule('/src/speech/interpret.check.ts')
  mod.runVoiceChecks()
  console.log('VOICE_CHECK_OK')
} finally {
  await server.close()
}
