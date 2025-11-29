# NGX Intelligence Frontend

Modern React frontend for the NGX Intelligence document processing system.

## Technology Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality component library
- **Jotai** - Atomic state management
- **TanStack Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Recharts** - Charts and data visualization
- **Lucide React** - Icon library

## Project Structure

```
src/
├── api/              # API client and service modules
│   ├── client.ts     # Axios instance with interceptors
│   ├── auth.ts       # Authentication endpoints
│   ├── documents.ts  # Document endpoints
│   ├── queue.ts      # Queue endpoints
│   └── settings.ts   # Settings/config endpoints
├── components/
│   ├── ui/          # shadcn/ui components
│   ├── auth/        # Authentication components
│   ├── dashboard/   # Dashboard components
│   ├── history/     # History page components
│   ├── settings/    # Settings components
│   └── layout/      # Layout components (Navbar, Sidebar)
├── hooks/           # React Query hooks
│   ├── useAuth.ts
│   ├── useDocuments.ts
│   ├── useQueue.ts
│   └── useSettings.ts
├── pages/           # Page components
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── Dashboard.tsx
│   ├── HistoryPage.tsx
│   └── SettingsPage.tsx
├── store/           # Jotai atoms
│   ├── auth.ts
│   ├── queue.ts
│   └── settings.ts
├── types/           # TypeScript type definitions
│   └── index.ts
├── utils/           # Utility functions
│   └── formatters.ts
├── App.tsx          # Main app component
├── main.tsx         # Entry point
└── router.tsx       # Route configuration
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Features

### Authentication
- Login/Register pages with form validation
- JWT token-based authentication
- Automatic token refresh
- Protected routes

### Dashboard
- Real-time statistics (documents processed, success rate)
- Queue status monitoring
- Recent activity feed
- Alert notifications

### Document History
- Filterable document table
- Status-based filtering
- Pagination
- Document detail view (modal)

### Settings
- User profile management
- Password change
- Paperless-ngx credentials
- AI configuration (admin only)
- Processing settings (admin only)
- Naming templates

## API Integration

The frontend communicates with the backend API through axios. The API client includes:

- Automatic JWT token injection
- Token refresh on 401 errors
- Request/response interceptors
- Error handling

API base URL is configured in `vite.config.ts` as a proxy to avoid CORS issues in development.

## State Management

### Jotai Atoms
- `authTokenAtom` - JWT access token (persisted to localStorage)
- `currentUserAtom` - Current user data
- `queueStatsAtom` - Queue statistics
- `configAtom` - Application configuration

### TanStack Query
All data fetching uses React Query for:
- Automatic caching
- Background refetching
- Optimistic updates
- Loading/error states

## Styling

The app uses Tailwind CSS with the shadcn/ui component library for a consistent, accessible design system.

Custom theme variables are defined in `src/index.css` using CSS custom properties for easy theming.

## Development

### Adding New Components

Use shadcn/ui CLI to add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

### Type Safety

All API responses and component props are fully typed. Types are defined in `src/types/index.ts` based on the backend Pydantic schemas.

### Code Quality

- ESLint for code linting
- TypeScript strict mode
- Prettier for code formatting (configure as needed)

## Environment Variables

Create a `.env.local` file for local development:

```env
VITE_API_URL=http://localhost:8000
```

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ JavaScript features
- CSS Grid and Flexbox

## License

See main project LICENSE file.
