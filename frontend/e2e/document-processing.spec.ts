import { test, expect } from '@playwright/test'

test.describe('Document Processing Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Set up authentication
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
  })

  test('displays document history table', async ({ page }) => {
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '1',
              user_id: 'user1',
              paperless_document_id: 101,
              processed_at: '2025-01-15T10:30:00Z',
              status: 'success',
              confidence_score: 0.95,
              processing_time_ms: 1200,
              reprocess_count: 0,
            },
            {
              id: '2',
              user_id: 'user1',
              paperless_document_id: 102,
              processed_at: '2025-01-14T15:45:00Z',
              status: 'failed',
              error_message: 'OCR processing failed',
              processing_time_ms: 500,
              reprocess_count: 1,
            },
          ],
          total: 2,
          limit: 50,
          offset: 0,
        }),
      })
    })

    await page.goto('/history')

    await expect(page.getByText('Processing History')).toBeVisible()
    await expect(page.getByText('Showing 2 of 2 documents')).toBeVisible()

    // Check table headers
    await expect(page.getByText('Document ID')).toBeVisible()
    await expect(page.getByText('Processed Date')).toBeVisible()
    await expect(page.getByText('Status')).toBeVisible()
    await expect(page.getByText('Confidence')).toBeVisible()
    await expect(page.getByText('Processing Time')).toBeVisible()

    // Check table data
    await expect(page.getByText('#101')).toBeVisible()
    await expect(page.getByText('#102')).toBeVisible()
  })

  test('can filter documents by status', async ({ page }) => {
    // Initial load
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '1',
              user_id: 'user1',
              paperless_document_id: 101,
              processed_at: '2025-01-15T10:30:00Z',
              status: 'success',
              confidence_score: 0.95,
              reprocess_count: 0,
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      })
    })

    // Filter by success
    await page.route('**/api/v1/documents?status=success&limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '1',
              user_id: 'user1',
              paperless_document_id: 101,
              processed_at: '2025-01-15T10:30:00Z',
              status: 'success',
              confidence_score: 0.95,
              reprocess_count: 0,
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      })
    })

    await page.goto('/history')

    // Click Success filter
    await page.click('button:has-text("Success")')

    await expect(page.getByText('#101')).toBeVisible()
  })

  test('can search documents', async ({ page }) => {
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

    await page.goto('/history')

    const searchInput = page.getByPlaceholder(/search by document id/i)
    await searchInput.fill('101')

    await expect(searchInput).toHaveValue('101')
  })

  test('can refresh document list', async ({ page }) => {
    let requestCount = 0

    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      requestCount++
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

    await page.goto('/history')

    expect(requestCount).toBe(1)

    await page.click('button:has-text("Refresh")')

    // Wait a bit for the request
    await page.waitForTimeout(500)
    expect(requestCount).toBeGreaterThanOrEqual(2)
  })

  test('opens document detail dialog', async ({ page }) => {
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '1',
              user_id: 'user1',
              paperless_document_id: 101,
              processed_at: '2025-01-15T10:30:00Z',
              status: 'success',
              confidence_score: 0.95,
              processing_time_ms: 1200,
              suggested_data: {
                title: 'Invoice 2025-01-15',
                correspondent: 'Acme Corp',
              },
              reprocess_count: 0,
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      })
    })

    await page.goto('/history')

    await page.click('button:has-text("View Details")')

    await expect(page.getByText('Document Details')).toBeVisible()
    await expect(page.getByText('Document #101')).toBeVisible()
    await expect(page.getByText('Suggested Data')).toBeVisible()
    await expect(page.getByText(/Invoice 2025-01-15/)).toBeVisible()
  })

  test('shows error message in detail dialog for failed documents', async ({ page }) => {
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '2',
              user_id: 'user1',
              paperless_document_id: 102,
              processed_at: '2025-01-14T15:45:00Z',
              status: 'failed',
              error_message: 'OCR processing failed',
              processing_time_ms: 500,
              reprocess_count: 1,
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      })
    })

    await page.goto('/history')

    await page.click('button:has-text("View Details")')

    await expect(page.getByText('Error Message')).toBeVisible()
    await expect(page.getByText('OCR processing failed')).toBeVisible()
  })

  test('pagination works correctly', async ({ page }) => {
    // First page
    await page.route('**/api/v1/documents?limit=50&offset=0', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: Array.from({ length: 50 }, (_, i) => ({
            id: `${i + 1}`,
            user_id: 'user1',
            paperless_document_id: 100 + i,
            processed_at: '2025-01-15T10:30:00Z',
            status: 'success',
            reprocess_count: 0,
          })),
          total: 100,
          limit: 50,
          offset: 0,
        }),
      })
    })

    // Second page
    await page.route('**/api/v1/documents?limit=50&offset=50', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: Array.from({ length: 50 }, (_, i) => ({
            id: `${i + 51}`,
            user_id: 'user1',
            paperless_document_id: 150 + i,
            processed_at: '2025-01-15T10:30:00Z',
            status: 'success',
            reprocess_count: 0,
          })),
          total: 100,
          limit: 50,
          offset: 50,
        }),
      })
    })

    await page.goto('/history')

    await expect(page.getByText(/showing 1 to 50 of 100/i)).toBeVisible()

    const previousButton = page.getByRole('button', { name: /previous/i })
    const nextButton = page.getByRole('button', { name: /next/i })

    await expect(previousButton).toBeDisabled()
    await expect(nextButton).toBeEnabled()

    await nextButton.click()

    await expect(page.getByText(/showing 51 to 100 of 100/i)).toBeVisible()
    await expect(previousButton).toBeEnabled()
    await expect(nextButton).toBeDisabled()
  })

  test('shows empty state when no documents', async ({ page }) => {
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

    await page.goto('/history')

    await expect(page.getByText('No documents found')).toBeVisible()
  })
})
