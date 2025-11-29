import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Set up authentication
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock_token')
    })

    // Mock auth endpoint
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user1',
          username: 'testuser',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          email: 'test@example.com',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          is_active: true,
        }),
      })
    })

    // Mock stats endpoints
    await page.route('**/api/v1/documents/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 150,
          success: 135,
          failed: 5,
          pending_approval: 10,
          success_rate: 0.9,
          avg_processing_time_ms: 1200,
          avg_confidence: 0.85,
        }),
      })
    })

    await page.route('**/api/v1/queue/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          queued: 8,
          processing: 2,
          completed: 120,
          failed: 3,
          total: 133,
        }),
      })
    })

    await page.route('**/api/v1/documents?limit=10&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '1',
              user_id: 'user1',
              paperless_document_id: 101,
              processed_at: new Date().toISOString(),
              status: 'success',
              confidence_score: 0.95,
              processing_time_ms: 1200,
              reprocess_count: 0,
            },
            {
              id: '2',
              user_id: 'user1',
              paperless_document_id: 102,
              processed_at: new Date(Date.now() - 3600000).toISOString(),
              status: 'failed',
              error_message: 'OCR failed',
              reprocess_count: 1,
            },
          ],
          total: 2,
          limit: 10,
          offset: 0,
        }),
      })
    })

    await page.goto('/')
  })

  test('displays dashboard title and description', async ({ page }) => {
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText(/overview of your document processing/i)).toBeVisible()
  })

  test('displays all stat cards with correct values', async ({ page }) => {
    await expect(page.getByText('Total Documents')).toBeVisible()
    await expect(page.getByText('150')).toBeVisible()

    await expect(page.getByText('Success Rate')).toBeVisible()
    await expect(page.getByText('90%')).toBeVisible()

    await expect(page.getByText('Failed')).toBeVisible()
    await expect(page.getByText('5')).toBeVisible()

    await expect(page.getByText('Queue')).toBeVisible()
    await expect(page.getByText('8')).toBeVisible()
  })

  test('displays queue status section', async ({ page }) => {
    await expect(page.getByText('Processing Queue')).toBeVisible()
    await expect(page.getByText('Real-time queue status')).toBeVisible()

    // Check queue stats
    const queueSection = page.locator('text=Processing Queue').locator('..')
    await expect(queueSection.getByText('Queued')).toBeVisible()
    await expect(queueSection.getByText('Processing')).toBeVisible()
    await expect(queueSection.getByText('Completed')).toBeVisible()
  })

  test('shows progress bar for queue', async ({ page }) => {
    await expect(page.getByText('Overall Progress')).toBeVisible()

    // Progress should be visible
    const progressBar = page.locator('[role="progressbar"]').first()
    await expect(progressBar).toBeVisible()
  })

  test('displays recent activity with documents', async ({ page }) => {
    await expect(page.getByText('Recent Activity')).toBeVisible()
    await expect(page.getByText('Last 10 processed documents')).toBeVisible()

    await expect(page.getByText('Document #101')).toBeVisible()
    await expect(page.getByText('Document #102')).toBeVisible()
  })

  test('shows status badges in recent activity', async ({ page }) => {
    await expect(page.getByText('Success')).toBeVisible()
    await expect(page.getByText('Failed')).toBeVisible()
  })

  test('displays alert for failed documents', async ({ page }) => {
    await expect(page.getByText('Alerts')).toBeVisible()
    await expect(page.getByText('Failed Processing Jobs')).toBeVisible()
    await expect(page.getByText(/5 documents failed to process/i)).toBeVisible()
  })

  test('shows confidence score in recent activity', async ({ page }) => {
    await expect(page.getByText(/confidence.*95%/i)).toBeVisible()
  })

  test('shows processing time for documents', async ({ page }) => {
    await expect(page.getByText('1200ms')).toBeVisible()
  })

  test('navigation sidebar is visible', async ({ page }) => {
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('History')).toBeVisible()
    await expect(page.getByText('Settings')).toBeVisible()
  })

  test('can navigate to History page', async ({ page }) => {
    // Mock history page data
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [],
          total: 0,
          limit: 50,
          offset: 0,
        }),
      })
    })

    await page.click('text=History')
    await expect(page).toHaveURL(/\/history/)
    await expect(page.getByText('Processing History')).toBeVisible()
  })

  test('can navigate to Settings page', async ({ page }) => {
    // Mock config endpoint
    await page.route('**/api/v1/settings/config', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ai: { model: 'llama3.2:latest' },
          processing: { polling_interval: 60 },
          naming: { title_template: '{date} - {correspondent}' },
        }),
      })
    })

    await page.click('text=Settings')
    await expect(page).toHaveURL(/\/settings/)
    await expect(page.getByText('Settings')).toBeVisible()
  })

  test('can logout from dashboard', async ({ page }) => {
    await page.route('**/api/v1/auth/logout', async (route) => {
      await route.fulfill({ status: 200 })
    })

    // Open user menu
    const userButton = page.locator('button[aria-label="User menu"]').or(
      page.locator('button').filter({ hasText: 'testuser' })
    ).first()

    if (await userButton.isVisible()) {
      await userButton.click()
      await page.click('text=Logout')

      // Should redirect to login
      await expect(page).toHaveURL('/login')
    }
  })

  test('displays loading state while fetching data', async ({ page }) => {
    // Create a new page to intercept initial load
    const newPage = await page.context().newPage()

    await newPage.addInitScript(() => {
      localStorage.setItem('access_token', 'mock_token')
    })

    // Delay the stats response
    await newPage.route('**/api/v1/documents/stats', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 150,
          success: 135,
          failed: 5,
          pending_approval: 10,
          success_rate: 0.9,
        }),
      })
    })

    await newPage.goto('/')

    // Should show loading skeleton
    const skeletons = newPage.getByTestId(/skeleton/i)
    const count = await skeletons.count()
    expect(count).toBeGreaterThan(0)

    await newPage.close()
  })
})

test.describe('Dashboard - Empty States', () => {
  test('shows empty state when no recent documents', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock_token')
    })

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user1',
          username: 'testuser',
          role: 'user',
          paperless_url: 'http://paperless.local',
          paperless_username: 'paperlessuser',
          email: 'test@example.com',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
          is_active: true,
        }),
      })
    })

    await page.route('**/api/v1/documents/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 0,
          success: 0,
          failed: 0,
          pending_approval: 0,
          success_rate: 0,
        }),
      })
    })

    await page.route('**/api/v1/queue/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          queued: 0,
          processing: 0,
          completed: 0,
          failed: 0,
          total: 0,
        }),
      })
    })

    await page.route('**/api/v1/documents?limit=10&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [],
          total: 0,
          limit: 10,
          offset: 0,
        }),
      })
    })

    await page.goto('/')

    await expect(page.getByText('No recent documents')).toBeVisible()
  })
})
