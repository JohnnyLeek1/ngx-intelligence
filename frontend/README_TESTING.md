# Testing Guide - NGX Intelligence Frontend

This guide covers all testing approaches and best practices for the NGX Intelligence React frontend application.

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Coverage](#coverage)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Overview

The NGX Intelligence frontend uses a comprehensive testing strategy:

- **Unit Tests**: Component and hook testing with Vitest + React Testing Library
- **Integration Tests**: Page-level tests ensuring components work together
- **E2E Tests**: Full user workflow testing with Playwright

**Coverage Target**: >70% for lines, functions, branches, and statements

## Testing Stack

### Unit & Integration Tests
- **Vitest**: Fast, Vite-native test runner with built-in features
- **React Testing Library**: Component testing focused on user behavior
- **@testing-library/user-event**: Simulating real user interactions
- **@testing-library/jest-dom**: Custom matchers for DOM assertions

### E2E Tests
- **Playwright**: Cross-browser end-to-end testing
- **Chromium**: Primary test browser (configured in playwright.config.ts)

## Running Tests

### Unit & Integration Tests

```bash
# Run tests in watch mode (for development)
npm test

# Run tests once (for CI)
npm run test:run

# Run tests with UI (visual test explorer)
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

### E2E Tests

```bash
# Run E2E tests headless
npm run test:e2e

# Run E2E tests with UI (interactive mode)
npm run test:e2e:ui

# Run E2E tests headed (see browser)
npm run test:e2e:headed
```

### Run All Tests

```bash
# Run unit, integration, and E2E tests
npm run test:all
```

## Test Structure

```
frontend/
├── src/
│   ├── tests/
│   │   ├── setup.ts              # Global test setup
│   │   └── utils.tsx             # Custom render with providers
│   ├── pages/
│   │   └── __tests__/
│   │       ├── LoginPage.test.tsx
│   │       ├── Dashboard.test.tsx
│   │       ├── HistoryPage.test.tsx
│   │       └── SettingsPage.test.tsx
│   ├── hooks/
│   │   └── __tests__/
│   │       ├── useAuth.test.tsx
│   │       ├── useDocuments.test.tsx
│   │       └── useQueue.test.tsx
│   └── components/
│       └── __tests__/
│           └── [component tests]
├── e2e/
│   ├── auth.spec.ts              # Authentication flows
│   ├── dashboard.spec.ts         # Dashboard interactions
│   └── document-processing.spec.ts
├── vitest.config.ts              # Vitest configuration
└── playwright.config.ts          # Playwright configuration
```

## Writing Tests

### Component Tests

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('Clicked')).toBeInTheDocument()
  })
})
```

### Hook Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMyHook } from '../useMyHook'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useMyHook', () => {
  it('fetches data correctly', async () => {
    const { result } = renderHook(() => useMyHook(), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
  })
})
```

### E2E Tests

```typescript
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('/login')

  await page.fill('input[name="username"]', 'testuser')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')

  await expect(page).toHaveURL('/')
  await expect(page.getByText('Dashboard')).toBeVisible()
})
```

## Coverage

### Viewing Coverage Reports

After running `npm run test:coverage`, open:
```
coverage/index.html
```

### Coverage Thresholds

Configured in `vitest.config.ts`:
- Lines: 70%
- Functions: 70%
- Branches: 70%
- Statements: 70%

### Excluded from Coverage
- `node_modules/`
- `src/tests/` - Test utilities
- `**/*.d.ts` - Type definitions
- `**/*.config.*` - Configuration files
- `src/components/ui/**` - Third-party UI components (shadcn)
- `src/main.tsx` - Entry point

## Best Practices

### 1. Test Behavior, Not Implementation

```typescript
// ✅ Good - Tests user behavior
it('shows error when login fails', async () => {
  render(<LoginPage />)
  await user.click(screen.getByRole('button', { name: /sign in/i }))
  expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
})

// ❌ Bad - Tests implementation details
it('calls setError with message', () => {
  const setError = vi.fn()
  render(<LoginPage setError={setError} />)
  // Testing internal state management
})
```

### 2. Use Accessible Queries

```typescript
// ✅ Good - Accessible queries
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/username/i)
screen.getByText(/welcome/i)

// ❌ Bad - Implementation-dependent queries
screen.getByClassName('submit-btn')
screen.getByTestId('username-input')
```

### 3. Mock External Dependencies

```typescript
// Mock API calls
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn()
  }
}))

// Mock hooks
vi.mock('@/hooks/useAuth', () => ({
  useLogin: vi.fn()
}))
```

### 4. Clean Up After Tests

```typescript
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})
```

### 5. Use Custom Render with Providers

```typescript
// Always use custom render from tests/utils.tsx
import { render } from '@/tests/utils'

// This includes QueryClient and Router providers
render(<MyComponent />)
```

### 6. Test Loading and Error States

```typescript
it('shows loading state', () => {
  vi.mocked(useData).mockReturnValue({ isLoading: true })
  render(<MyComponent />)
  expect(screen.getByText(/loading/i)).toBeInTheDocument()
})

it('shows error state', () => {
  vi.mocked(useData).mockReturnValue({
    isError: true,
    error: new Error('Failed')
  })
  render(<MyComponent />)
  expect(screen.getByText(/failed/i)).toBeInTheDocument()
})
```

### 7. E2E Test Best Practices

```typescript
// Use beforeEach for common setup
test.beforeEach(async ({ page }) => {
  await page.goto('/login')
})

// Mock API responses
await page.route('**/api/v1/**', async (route) => {
  await route.fulfill({
    status: 200,
    body: JSON.stringify({ data: 'mock' })
  })
})

// Use accessible locators
await page.getByRole('button', { name: 'Submit' })
await page.getByLabel('Username')

// Wait for navigation
await expect(page).toHaveURL('/dashboard')
```

## Test Categories

### 1. Component Tests (`src/components/__tests__/`)
- Individual component rendering
- Props handling
- User interactions
- Conditional rendering

### 2. Page Tests (`src/pages/__tests__/`)
- Full page rendering
- Multiple components working together
- Navigation
- Data fetching integration

### 3. Hook Tests (`src/hooks/__tests__/`)
- Custom hook logic
- API integration
- State management
- React Query integration

### 4. E2E Tests (`e2e/`)
- Complete user workflows
- Cross-page interactions
- Authentication flows
- Real browser behavior

## Common Testing Patterns

### Testing Forms

```typescript
it('submits form with valid data', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()

  render(<MyForm onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText(/email/i), 'test@example.com')
  await user.type(screen.getByLabelText(/password/i), 'password123')
  await user.click(screen.getByRole('button', { name: /submit/i }))

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    })
  })
})
```

### Testing Tables

```typescript
it('renders table with data', () => {
  render(<DocumentTable data={mockData} />)

  expect(screen.getByRole('table')).toBeInTheDocument()
  expect(screen.getAllByRole('row')).toHaveLength(mockData.length + 1) // +1 for header
  expect(screen.getByText('Document #101')).toBeInTheDocument()
})
```

### Testing Modals/Dialogs

```typescript
it('opens and closes dialog', async () => {
  const user = userEvent.setup()
  render(<MyComponent />)

  await user.click(screen.getByRole('button', { name: /open/i }))
  expect(screen.getByRole('dialog')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /close/i }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})
```

### Testing Async Operations

```typescript
it('loads and displays data', async () => {
  vi.mocked(fetchData).mockResolvedValue({ items: [1, 2, 3] })

  render(<MyComponent />)

  expect(screen.getByText(/loading/i)).toBeInTheDocument()

  await waitFor(() => {
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
  })

  expect(screen.getByText('Item 1')).toBeInTheDocument()
})
```

## Debugging Tests

### Vitest

```bash
# Run tests in debug mode
node --inspect-brk ./node_modules/.bin/vitest

# Use VS Code debugger with this launch.json:
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest Tests",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "test"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

### Playwright

```bash
# Run with headed browser
npm run test:e2e:headed

# Run with Playwright Inspector
npx playwright test --debug

# Run specific test
npx playwright test auth.spec.ts --debug
```

### Common Issues

**Issue**: Tests timeout
```typescript
// Increase timeout
test('slow operation', async () => {
  // ...
}, { timeout: 10000 })
```

**Issue**: Can't find element
```typescript
// Use screen.debug() to see current DOM
screen.debug()

// Or debug specific element
screen.debug(screen.getByRole('button'))
```

**Issue**: Async state updates
```typescript
// Always use waitFor for async updates
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})
```