# Components Overview

SamvadQL frontend is built with React 18+ and TypeScript, using modern patterns and best practices.

## Architecture

The frontend follows a component-based architecture with clear separation of concerns:

- **UI Components**: Reusable interface elements built with shadcn/ui
- **Hooks**: Custom React hooks for state management and side effects
- **Services**: API clients and external service integrations
- **Types**: TypeScript definitions for type safety

## Design System

We use [shadcn/ui](https://ui.shadcn.com/) as our component library, built on top of:
- **Radix UI**: Accessible, unstyled components
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful, customizable icons

## Component Structure

```
src/
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── query/           # Query-related components
│   ├── schema/          # Schema browser components
│   └── chat/            # Chat interface components
├── hooks/               # Custom React hooks
├── services/            # API and WebSocket clients
├── types/               # TypeScript definitions
└── lib/                 # Utility functions
```

## Styling Conventions

- Use Tailwind CSS classes for styling
- Follow shadcn/ui patterns for component variants
- Use CSS variables for theme customization
- Responsive design with mobile-first approach

## State Management

- **Local State**: React useState and useReducer
- **Server State**: Custom hooks with React Query patterns
- **Global State**: Redux Toolkit for complex state
- **Form State**: React Hook Form with Zod validation

## Next Steps

- [UI Components](./ui/query-editor.md) - Interactive interface components
- [Hooks](./hooks/use-query.md) - Custom React hooks
- [Services](./services/api-client.md) - API and WebSocket clients
