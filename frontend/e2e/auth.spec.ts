import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login')
  })

  test('displays login page correctly', async ({ page }) => {
    await expect(page.getByText('NGX Intelligence')).toBeVisible()
    await expect(page.getByText('Sign in to your account')).toBeVisible()
    await expect(page.getByLabel(/username/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('shows validation errors for empty fields', async ({ page }) => {
    await page.getByRole('button', { name: /sign in/i }).click()

    // HTML5 validation should prevent submission
    const usernameInput = page.getByLabel(/username/i)
    const isRequired = await usernameInput.getAttribute('required')
    expect(isRequired).not.toBeNull()
  })

  test('successfully logs in with valid credentials', async ({ page }) => {
    // Mock the API response
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          token_type: 'Bearer',
        }),
      })
    })

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          is_active: true,
        }),
      })
    })

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Should redirect to dashboard
    await expect(page).toHaveURL('/')
    await expect(page.getByText('Dashboard')).toBeVisible()
  })

  test('shows error message for invalid credentials', async ({ page }) => {
    // Mock failed login response
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid credentials',
        }),
      })
    })

    await page.fill('input[name="username"]', 'wronguser')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    // Should show error message
    await expect(page.getByText('Invalid credentials')).toBeVisible()

    // Should still be on login page
    await expect(page).toHaveURL('/login')
  })

  test('shows loading state during login', async ({ page }) => {
    // Delay the response to see loading state
    await page.route('**/api/v1/auth/login', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          token_type: 'Bearer',
        }),
      })
    })

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Should show loading state
    await expect(page.getByText(/signing in/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /signing in/i })).toBeDisabled()
  })

  test('navigates to registration page', async ({ page }) => {
    await page.click('text=Register')
    await expect(page).toHaveURL('/register')
    await expect(page.getByText(/create.*account/i)).toBeVisible()
  })

  test('registration form displays all required fields', async ({ page }) => {
    await page.goto('/register')

    await expect(page.getByLabel(/username/i)).toBeVisible()
    await expect(page.getByLabel(/^password$/i)).toBeVisible()
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/paperless.*url/i)).toBeVisible()
    await expect(page.getByLabel(/paperless.*username/i)).toBeVisible()
    await expect(page.getByLabel(/paperless.*token/i)).toBeVisible()
  })

  test('successfully registers new user', async ({ page }) => {
    await page.goto('/register')

    // Mock registration response
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'newuser1',
          username: 'newuser',
          email: 'new@example.com',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          created_at: '2025-01-15T00:00:00Z',
          updated_at: '2025-01-15T00:00:00Z',
          is_active: true,
        }),
      })
    })

    await page.fill('input[name="username"]', 'newuser')
    await page.fill('input[name="password"]', 'SecurePass123')
    await page.fill('input[name="email"]', 'new@example.com')
    await page.fill('input[name="paperless_url"]', 'http://paperless.local')
    await page.fill('input[name="paperless_username"]', 'paperlessuser')
    await page.fill('input[name="paperless_token"]', 'token123')

    await page.click('button[type="submit"]')

    // Should redirect to login page
    await expect(page).toHaveURL('/login')
    await expect(page.getByText(/registration successful/i)).toBeVisible()
  })
})

test.describe('Protected Routes', () => {
  test('redirects to login when accessing protected route without auth', async ({ page }) => {
    await page.goto('/')

    // Should be redirected to login
    await expect(page).toHaveURL('/login')
  })

  test('allows access to protected routes when authenticated', async ({ page }) => {
    // Set up auth token in localStorage (using correct key)
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', JSON.stringify('mock_token'))
      localStorage.setItem('refresh_token', JSON.stringify('mock_refresh_token'))
    })

    // Mock the current user endpoint
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          is_active: true,
        }),
      })
    })

    await page.goto('/')

    // Should stay on dashboard
    await expect(page).toHaveURL('/')
  })

  test('persists session after page refresh', async ({ page }) => {
    // First, log in
    await page.goto('/login')

    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          token_type: 'Bearer',
        }),
      })
    })

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          is_active: true,
        }),
      })
    })

    // Mock documents endpoint to prevent errors on dashboard
    await page.route('**/api/v1/documents**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, size: 10, pages: 0 }),
      })
    })

    // Mock queue endpoint
    await page.route('**/api/v1/queue**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0 }),
      })
    })

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for navigation to dashboard
    await expect(page).toHaveURL('/')

    // Refresh the page
    await page.reload()

    // Should still be on dashboard (not redirected to login)
    await expect(page).toHaveURL('/')
    await expect(page.getByText('Dashboard')).toBeVisible()

    // Verify auth token is still in localStorage
    const authToken = await page.evaluate(() => localStorage.getItem('auth_token'))
    expect(authToken).toBeTruthy()
  })

  test('clears session and redirects to login when token is invalid', async ({ page }) => {
    // Set up invalid auth token
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', JSON.stringify('invalid_token'))
      localStorage.setItem('refresh_token', JSON.stringify('invalid_refresh'))
    })

    // Mock unauthorized response
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid authentication credentials',
        }),
      })
    })

    await page.goto('/')

    // Should redirect to login and clear tokens
    await expect(page).toHaveURL('/login')

    // Tokens should be cleared from localStorage
    const authToken = await page.evaluate(() => localStorage.getItem('auth_token'))
    expect(authToken).toBeNull()
  })
})
