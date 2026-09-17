// Frontend tests — authentication flow and component rendering
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../context/AuthContext'
import Login from '../../pages/Login'
import Register from '../../pages/Register'

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }))

// Mock auth service
vi.mock('../../services/auth', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    saveSession: vi.fn(),
    clearSession: vi.fn(),
    getStoredUser: vi.fn().mockReturnValue(null),
    isAuthenticated: vi.fn().mockReturnValue(false),
  },
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  )
}

describe('Login Page', () => {
  it('renders login form with email and password fields', () => {
    renderWithProviders(<Login />)
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    renderWithProviders(<Login />)
    expect(screen.getByRole('link', { name: /create one/i })).toBeInTheDocument()
  })

  it('shows validation error for empty form submission', async () => {
    renderWithProviders(<Login />)
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText(/email and password are required/i)).toBeInTheDocument()
    })
  })

  it('fills demo admin credentials when button clicked', () => {
    renderWithProviders(<Login />)
    fireEvent.click(screen.getByRole('button', { name: /admin account/i }))
    const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement
    expect(emailInput.value).toBe('admin@darukaa.earth')
  })
})

describe('Register Page', () => {
  it('renders registration form with all required fields', () => {
    renderWithProviders(<Register />)
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
  })

  it('shows error when passwords do not match', async () => {
    renderWithProviders(<Register />)

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'SecurePass123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'DifferentPass123' } })

    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('shows error for short password', async () => {
    renderWithProviders(<Register />)

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Test' } })
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'abc' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'abc' } })

    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('has link back to login page', () => {
    renderWithProviders(<Register />)
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()
  })
})
