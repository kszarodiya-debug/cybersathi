import { render, screen } from '@testing-library/react'

import App from './App'
import { AuthProvider } from './auth/AuthContext'

describe('CyberSathi landing page', () => {
  it('introduces the platform and its purpose', () => {
    render(
      <AuthProvider>
        <App />
      </AuthProvider>,
    )

    expect(screen.getByRole('heading', { name: /your digital safety companion/i })).toBeInTheDocument()
    expect(screen.getByText(/Built for safer campuses/i)).toBeInTheDocument()
    expect(screen.getByText(/Pause\. Verify\. Protect\./i)).toBeInTheDocument()
    expect(screen.getByText('Kunal Sanjay Zarodiya')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /follow on instagram/i })).toHaveAttribute(
      'href',
      'https://www.instagram.com/kunal_zarodiya?igsi=MXJraHB6aGkxM2x6dw==',
    )
  })
})
