# SamvadQL Frontend

A React-based frontend for the SamvadQL Text-to-SQL conversational interface.

## Technology Stack

- **React 18+** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern component library
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls
- **Socket.io** - Real-time WebSocket communication

## Development

### Prerequisites

- Node.js 18+
- pnpm (recommended) or npm

### Getting Started

1. **Install dependencies**

   ```bash
   pnpm install
   ```

2. **Start development server**

   ```bash
   pnpm dev
   ```

3. **Build for production**

   ```bash
   pnpm build
   ```

4. **Preview production build**
   ```bash
   pnpm preview
   ```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up frontend

# Or build standalone
docker build -f Dockerfile.dev -t samvadql-frontend-dev .
docker run -p 3000:3000 samvadql-frontend-dev
```

## Project Structure

```

```

src/
├── components/ # React components
│ ├── ui/ # shadcn/ui components
│ ├── layout/ # Layout components
│ │ ├── AppLayout.tsx # Authenticated app layout with sidebar
│ │ ├── AuthLayout.tsx # Clean auth pages layout
│ │ └── Navbar.tsx # Navigation component
│ └── QueryEditor.tsx # Query input component
├── pages/ # Page components
│ └── HomePage.tsx # Main page
├── services/ # API and WebSocket services
│ ├── api.ts # REST API client
│ └── websocket.ts # WebSocket service

```
├── types/             # TypeScript type definitions
├── hooks/             # Custom React hooks
├── lib/               # Utility functions
├── App.tsx            # Main app component
├── main.tsx           # Application entry point
└── index.css          # Global styles
```

## Key Features

- **Modern React Architecture** - Uses functional components and hooks
- **Type Safety** - Full TypeScript integration
- **Real-time Communication** - WebSocket support for streaming responses
- **Responsive Design** - Mobile-first approach with Tailwind CSS
- **Component Library** - shadcn/ui for consistent UI components
- **Fast Development** - Vite for instant hot reload

## Migration from Next.js

This project was migrated from Next.js to a standard React application to simplify the architecture and remove unnecessary features. Key changes:

- Replaced Next.js with Vite for build tooling
- Converted App Router structure to standard React Router
- Updated environment variables from `NEXT_PUBLIC_*` to `VITE_*`
- Simplified Docker configuration
- Removed server-side rendering (not needed for this use case)

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build
- `pnpm lint` - Run ESLint
- `pnpm type-check` - Run TypeScript compiler check
