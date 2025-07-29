#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const chokidar = require('chokidar');
const APIDocGenerator = require('./generate-api-docs');
const ComponentDocGenerator = require('./generate-component-docs');

/**
 * Watch for file changes and automatically regenerate documentation
 */
class DocumentationWatcher {
  constructor() {
    this.apiGenerator = new APIDocGenerator();
    this.componentGenerator = new ComponentDocGenerator();
    this.debounceTimeout = null;
    this.isGenerating = false;
  }

  async start() {
    console.log('🔍 Starting documentation watcher...');

    // Determine source paths (Docker vs local)
    const backendPath = fs.existsSync('/source/backend') ? '/source/backend' : '../backend';
    const frontendPath = fs.existsSync('/source/frontend') ? '/source/frontend/src' : '../frontend/src';

    // Watch backend files for API documentation
    const backendWatcher = chokidar.watch(`${backendPath}/**/*.py`, {
      ignored: ['**/__pycache__/**', '**/*.pyc', '**/.*'],
      persistent: true
    });

    // Watch frontend files for component documentation
    const frontendWatcher = chokidar.watch(`${frontendPath}/**/*.{ts,tsx}`, {
      ignored: ['**/node_modules/**', '**/.*'],
      persistent: true
    });

    backendWatcher.on('change', (filePath) => {
      console.log(`📝 Backend file changed: ${filePath}`);
      this.debouncedGenerate('api');
    });

    frontendWatcher.on('change', (filePath) => {
      console.log(`📝 Frontend file changed: ${filePath}`);
      this.debouncedGenerate('components');
    });

    // Initial generation
    await this.generateAll();

    console.log('✅ Documentation watcher started successfully!');
    console.log('   - Watching backend files for API docs');
    console.log('   - Watching frontend files for component docs');
    console.log('   - Press Ctrl+C to stop');
  }

  debouncedGenerate(type) {
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }

    this.debounceTimeout = setTimeout(async () => {
      if (this.isGenerating) {
        console.log('⏳ Generation already in progress, skipping...');
        return;
      }

      this.isGenerating = true;
      try {
        if (type === 'api') {
          await this.apiGenerator.generateDocs();
        } else if (type === 'components') {
          await this.componentGenerator.generateDocs();
        }
      } catch (error) {
        console.error(`❌ Error generating ${type} docs:`, error);
      } finally {
        this.isGenerating = false;
      }
    }, 2000); // 2 second debounce
  }

  async generateAll() {
    console.log('🚀 Generating all documentation...');

    try {
      await Promise.all([
        this.apiGenerator.generateDocs(),
        this.componentGenerator.generateDocs()
      ]);
      console.log('✅ All documentation generated successfully!');
    } catch (error) {
      console.error('❌ Error generating documentation:', error);
    }
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Stopping documentation watcher...');
  process.exit(0);
});

// Start the watcher
if (require.main === module) {
  const watcher = new DocumentationWatcher();
  watcher.start().catch(console.error);
}

module.exports = DocumentationWatcher;