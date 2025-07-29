# SamvadQL Documentation

This directory contains the Mintlify-based documentation for SamvadQL, including automated documentation generation from source code.

## Quick Start

### Docker Approach (Recommended)

1. **Start documentation with Docker**

   ```bash
   # From project root
   ./scripts/dev-docs.sh    # Linux/Mac
   scripts\dev-docs.bat     # Windows

   # Or directly with Docker Compose
   docker-compose up -d docs
   ```

2. **View documentation**
   Open http://localhost:3001 in your browser

### Local Development Approach

1. **Setup documentation environment**

   ```bash
   cd docs
   node scripts/setup-docs.js
   ```

2. **Start development server**

   ```bash
   npm start
   ```

3. **View documentation**
   Open http://localhost:3000 in your browser

## Features

### 📚 Comprehensive Documentation

- **Getting Started**: Installation, quick start, and configuration guides
- **Architecture**: System design and component overview
- **API Reference**: Auto-generated from backend Python code
- **Component Docs**: Auto-generated from frontend React components
- **Development**: Setup, testing, and deployment guides

### 🤖 Automated Generation

- **API Documentation**: Generated from Python docstrings and type hints
- **Component Documentation**: Generated from React component props and JSDoc
- **File Watching**: Auto-regenerate docs when source code changes
- **Git Hooks**: Automatically update docs before commits

### 🎨 Modern Documentation Site

- **Mintlify**: Modern documentation platform with beautiful UI
- **Interactive API Docs**: Built-in API reference with request/response examples
- **Code Highlighting**: Syntax highlighting for Python, TypeScript, SQL, and more
- **Search**: Built-in full-text search functionality
- **Responsive**: Mobile-friendly design with dark mode support

## Available Scripts

### Development

```bash
mintlify dev                # Start Mintlify development server
npm start                   # Alias for mintlify dev
mintlify build              # Build static site for production
mintlify preview            # Preview production build locally
```

### Documentation Generation

```bash
npm run generate-all-docs        # Generate all documentation
npm run generate-api-docs        # Generate API docs from backend
npm run generate-component-docs  # Generate component docs from frontend
```

### Automation

```bash
node scripts/watch-and-generate.js  # Watch files and auto-generate docs
node scripts/setup-docs.js          # Initial setup script
```

## Directory Structure

```
docs/
├── docs/                    # Documentation content
│   ├── intro.md            # Homepage content
│   ├── getting-started/    # Installation and setup guides
│   ├── architecture/       # System architecture docs
│   ├── api/               # Auto-generated API reference
│   ├── components/        # Auto-generated component docs
│   ├── development/       # Development guides
│   └── features/          # Feature documentation
├── src/                   # Docusaurus theme customization
│   └── css/              # Custom styles
├── static/               # Static assets (images, files)
├── scripts/              # Documentation generation scripts
│   ├── generate-api-docs.js      # API documentation generator
│   ├── generate-component-docs.js # Component documentation generator
│   ├── watch-and-generate.js     # File watcher for auto-generation
│   └── setup-docs.js            # Initial setup script
├── docusaurus.config.js  # Docusaurus configuration
├── sidebars.js           # Sidebar navigation structure
└── package.json          # Dependencies and scripts
```

## Automated Documentation Generation

### API Documentation

The system automatically generates API documentation from your Python backend:

- **Endpoints**: Extracted from FastAPI route definitions
- **Models**: Generated from Pydantic model definitions
- **Services**: Documented from class methods and docstrings
- **Examples**: Auto-generated request/response examples

### Component Documentation

Frontend component documentation is generated from:

- **Props**: TypeScript interface definitions
- **Hooks**: Custom hook signatures and usage
- **Services**: API client methods and types
- **Examples**: Code examples from JSDoc comments

### File Watching

The documentation system can watch your source files and automatically regenerate docs:

```bash
# Start file watcher
node scripts/watch-and-generate.js

# The watcher monitors:
# - apps/api-backend/**/*.py (for API docs)
# - apps/web-frontend/src/**/*.{ts,tsx} (for component docs)
```

## Customization

### Adding New Documentation

1. Create markdown files in the appropriate `docs/` subdirectory
2. Update `sidebars.js` to include new pages in navigation
3. Use frontmatter for metadata:
   ```markdown
   ---
   title: Page Title
   description: Page description
   ---
   ```

### Styling

- Edit `src/css/custom.css` for global styles
- Use CSS variables for theme customization
- Follow Docusaurus theming guidelines

### Configuration

- Edit `docusaurus.config.js` for site configuration
- Update navigation in `sidebars.js`
- Configure search, analytics, and other features

## Deployment

### Static Site Generation

```bash
npm run build
```

Generates static files in `build/` directory.

### Deployment Options

- **GitHub Pages**: Configure in `docusaurus.config.js`
- **Netlify**: Connect repository and set build command to `npm run build`
- **Vercel**: Import project and configure build settings
- **Self-hosted**: Serve files from `build/` directory

### Continuous Integration

The documentation can be automatically built and deployed:

```yaml
# .github/workflows/docs.yml
name: Deploy Documentation
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: cd docs && npm install
      - run: cd docs && npm run generate-all-docs
      - run: cd docs && npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/build
```

## Contributing

### Writing Documentation

- Use clear, concise language
- Include code examples where helpful
- Add diagrams for complex concepts
- Follow the existing structure and style

### Improving Generation Scripts

- Enhance `generate-api-docs.js` for better Python parsing
- Improve `generate-component-docs.js` for React component analysis
- Add support for additional file types or frameworks

### Reporting Issues

- Documentation bugs: Create issues with "docs" label
- Generation script problems: Include sample code that fails
- Feature requests: Describe the desired functionality

## Troubleshooting

### Common Issues

**Build failures**

- Clear cache: `npm run clear`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Node.js version (18+ required)

**Generation script errors**

- Verify source file paths in scripts
- Check for syntax errors in source files
- Ensure required dependencies are installed

**Missing content**

- Run generation scripts manually: `npm run generate-all-docs`
- Check file watcher is monitoring correct directories
- Verify source files contain proper documentation

### Getting Help

- Check [Docusaurus documentation](https://docusaurus.io/docs)
- Review generation script logs for errors
- Ask questions in project discussions
