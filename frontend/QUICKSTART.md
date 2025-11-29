# NGX Intelligence Frontend - Quick Start Guide

## Prerequisites

- Node.js 18+ installed
- Backend API running at `http://localhost:8000` (or configured URL)

## Installation

```bash
cd /Users/johnnyleek/ngx-intelligence/frontend
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## Project Commands

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run preview    # Preview production build
npm run lint       # Run ESLint
```

## Environment Configuration

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

Adjust the API URL to match your backend server.

## First Time Setup Checklist

1. ✅ Install dependencies: `npm install`
2. ✅ Configure environment: Create `.env` file
3. ✅ Start backend API (must be running)
4. ✅ Start frontend: `npm run dev`
5. ✅ Open browser: `http://localhost:5173`
6. ✅ Register a new user or login

## Application Routes

- `/login` - Login page
- `/register` - User registration
- `/` - Dashboard (protected)
- `/history` - Document history (protected)
- `/settings` - Settings (protected)

## Default User (if seeded in backend)

Check your backend for seed data or create a new user via `/register`

## Component Library

This project uses **shadcn/ui** components. All components are in:
```
src/components/ui/
```

### Adding New shadcn/ui Components

If you need additional components:

```bash
npx shadcn@latest add <component-name>
```

Example:
```bash
npx shadcn@latest add accordion
npx shadcn@latest add toast
npx shadcn@latest add tooltip
```

## Key Technologies

- **React 18.3** + TypeScript
- **Vite** - Build tool
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **Jotai** - State management
- **TanStack Query** - Data fetching
- **React Router v6** - Routing
- **Axios** - HTTP client

## File Structure

```
src/
├── components/
│   ├── ui/              # shadcn/ui components
│   └── layout/          # Layout components
├── pages/               # Route pages
├── api/                 # API client
├── hooks/               # Custom hooks
├── store/               # Jotai atoms
├── types/               # TypeScript types
└── lib/                 # Utilities
```

## Troubleshooting

### Port Already in Use

If port 5173 is taken, Vite will automatically try the next available port.

### API Connection Issues

1. Check backend is running
2. Verify `VITE_API_URL` in `.env`
3. Check browser console for CORS errors
4. Ensure backend allows CORS from frontend URL

### Build Errors

1. Clear node_modules: `rm -rf node_modules package-lock.json`
2. Reinstall: `npm install`
3. Try building again: `npm run build`

### TypeScript Errors

Run type checking:
```bash
npx tsc --noEmit
```

## Development Tips

### Hot Module Replacement (HMR)

Vite provides instant HMR. Changes to components will reflect immediately without full page reload.

### shadcn/ui Customization

Edit `src/components/ui/` components to customize appearance while maintaining functionality.

### Tailwind Configuration

Modify `tailwind.config.js` for custom colors, spacing, etc.

### Adding New Pages

1. Create page in `src/pages/`
2. Add route in `src/router.tsx`
3. Add navigation link in `src/components/layout/Sidebar.tsx`

## Production Deployment

### Using Docker

Build the Docker image:
```bash
docker build -t ngx-intelligence-frontend .
docker run -p 80:80 ngx-intelligence-frontend
```

### Using Nginx

1. Build the app: `npm run build`
2. Copy `dist/` contents to Nginx web root
3. Configure Nginx to handle client-side routing:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Environment Variables in Production

Set `VITE_API_URL` at build time or use runtime configuration.

## Support & Documentation

- **shadcn/ui Docs**: https://ui.shadcn.com/
- **React Docs**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **Jotai**: https://jotai.org/
- **TanStack Query**: https://tanstack.com/query/
