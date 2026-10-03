import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: mode === 'test'
    ? { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://localhost:8000/api/v1') }
    : undefined,
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
}))
