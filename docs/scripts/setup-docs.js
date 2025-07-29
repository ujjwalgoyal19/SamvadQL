#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Setup script for SamvadQL documentation
 */
class DocsSetup {
  constructor() {
    this.docsPath = __dirname + '/..';
    this.rootPath = path.join(__dirname, '../..');
  }

  async setup() {
    console.log('🚀 Setting up SamvadQL documentation...\n');

    try {
      await this.checkPrerequisites();
      await this.installDependencies();
      await this.createDirectories();
      await this.generateInitialDocs();
      await this.createGitHooks();
      await this.showCompletionMessage();
    } catch (error) {
      console.error('❌ Setup failed:', error.message);
      process.exit(1);
    }
  }

  async checkPrerequisites() {
    console.log('🔍 Checking prerequisites...');

    // Check Node.js version
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    if (majorVersion < 18) {
      throw new Error(`Node.js 18+ required, found ${nodeVersion}`);
    }
    console.log(`✅ Node.js ${nodeVersion}`);

    // Check if we're in the right directory
    const packageJsonPath = path.join(this.docsPath, 'package.json');
    if (!await fs.pathExists(packageJsonPath)) {
      throw new Error('package.json not found. Run this script from the docs directory.');
    }
    console.log('✅ Documentation directory structure');

    // Check if backend and frontend directories exist
    const backendPath = path.join(this.rootPath, 'backend');
    const frontendPath = path.join(this.rootPath, 'frontend');

    if (!await fs.pathExists(backendPath)) {
      console.warn('⚠️  Backend directory not found - API docs will be limited');
    } else {
      console.log('✅ Backend directory found');
    }

    if (!await fs.pathExists(frontendPath)) {
      console.warn('⚠️  Frontend directory not found - Component docs will be limited');
    } else {
      console.log('✅ Frontend directory found');
    }

    console.log();
  }

  async installDependencies() {
    console.log('📦 Installing dependencies...');

    try {
      // Check if pnpm is available, fallback to npm
      let packageManager = 'npm';
      try {
        execSync('pnpm --version', { stdio: 'ignore' });
        packageManager = 'pnpm';
      } catch {
        try {
          execSync('npm --version', { stdio: 'ignore' });
        } catch {
          throw new Error('Neither pnpm nor npm found. Please install Node.js package manager.');
        }
      }

      console.log(`Using ${packageManager} for installation...`);
      execSync(`${packageManager} install`, {
        cwd: this.docsPath,
        stdio: 'inherit'
      });

      console.log('✅ Dependencies installed successfully\n');
    } catch (error) {
      throw new Error(`Failed to install dependencies: ${error.message}`);
    }
  }

  async createDirectories() {
    console.log('📁 Creating documentation directories...');

    const directories = [
      'docs/architecture',
      'docs/development',
      'docs/features',
      'docs/api/backend',
      'docs/api/models',
      'docs/api/services',
      'docs/components/ui',
      'docs/components/hooks',
      'docs/components/services',
      'static/img',
      'blog'
    ];

    for (const dir of directories) {
      const fullPath = path.join(this.docsPath, dir);
      await fs.ensureDir(fullPath);
      console.log(`✅ Created ${dir}`);
    }

    console.log();
  }

  async generateInitialDocs() {
    console.log('📝 Generating initial documentation...');

    try {
      const APIDocGenerator = require('./generate-api-docs');
      const ComponentDocGenerator = require('./generate-component-docs');

      const apiGenerator = new APIDocGenerator();
      const componentGenerator = new ComponentDocGenerator();

      await Promise.all([
        apiGenerator.generateDocs(),
        componentGenerator.generateDocs()
      ]);

      console.log('✅ Initial documentation generated\n');
    } catch (error) {
      console.warn('⚠️  Could not generate initial docs:', error.message);
      console.log('   You can generate them later with: npm run generate-all-docs\n');
    }
  }

  async createGitHooks() {
    console.log('🔗 Setting up Git hooks...');

    const gitHooksPath = path.join(this.rootPath, '.git/hooks');

    if (!await fs.pathExists(gitHooksPath)) {
      console.log('⚠️  Git repository not found, skipping hooks setup');
      return;
    }

    // Pre-commit hook to regenerate docs
    const preCommitHook = `#!/bin/sh
# Auto-generate documentation before commit

echo "🔄 Regenerating documentation..."
cd docs && npm run generate-all-docs

# Add generated docs to commit
git add docs/docs/api/ docs/docs/components/
`;

    const preCommitPath = path.join(gitHooksPath, 'pre-commit');
    await fs.writeFile(preCommitPath, preCommitHook);
    await fs.chmod(preCommitPath, '755');

    console.log('✅ Git hooks configured\n');
  }

  showCompletionMessage() {
    console.log('🎉 Documentation setup complete!\n');

    console.log('🐳 Docker Commands (Recommended):');
    console.log('   ./scripts/dev-docs.sh (Linux/Mac) or scripts\\dev-docs.bat (Windows)');
    console.log('   docker-compose up -d docs     - Start documentation container');
    console.log('   docker-compose logs -f docs   - View documentation logs');
    console.log('   docker-compose stop docs      - Stop documentation container\n');

    console.log('📚 Mintlify Commands:');
    console.log('   mintlify dev              - Start Mintlify development server');
    console.log('   mintlify build            - Build static documentation');
    console.log('   mintlify preview          - Preview built documentation');
    console.log('   npm run generate-all-docs - Generate API & component docs');
    console.log('   npm run generate-api-docs - Generate API documentation');
    console.log('   npm run generate-component-docs - Generate component docs');
    console.log('   node scripts/watch-and-generate.js - Watch files and auto-generate\n');

    console.log('🌐 Next steps:');
    console.log('   1. Run "./scripts/dev-docs.sh" to start with Docker (recommended)');
    console.log('   2. Open http://localhost:3001 to view documentation');
    console.log('   3. Edit .mdx files in docs/ to customize content');
    console.log('   4. Documentation auto-updates when you modify source code\n');

    console.log('📖 Documentation will be available at:');
    console.log('   - Development (Docker): http://localhost:3001');
    console.log('   - Development (Local): http://localhost:3000');
    console.log('   - Production build: docs/_site/\n');
  }
}

// Run setup
if (require.main === module) {
  const setup = new DocsSetup();
  setup.setup().catch(console.error);
}

module.exports = DocsSetup;