import { afterEach, describe, expect, it, vi } from 'vitest'

import { apiRequest } from './api'

describe('apiRequest availability handling', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('returns a controlled error when the API cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network unavailable')))

    await expect(apiRequest('/health')).rejects.toMatchObject({
      status: 0,
      message: 'The service is unavailable. Please try again.',
    })
  })

  it('returns a controlled timeout instead of loading forever', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    })))

    const request = apiRequest('/slow')
    const assertion = expect(request).rejects.toMatchObject({
      status: 504,
      message: 'The service took too long to respond. Please try again.',
    })
    await vi.advanceTimersByTimeAsync(15_000)

    await assertion
  })
})
