#!/bin/bash
# Bash script for automated first-time development setup
# Run this script: ./scripts/dev-setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 SamvadQL Development Setup${NC}"
echo -e "${CYAN}================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker installed: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo -e "${RED}  Please install Docker from https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if Docker daemon is running
if docker ps &> /dev/null; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo -e "${RED}  Please start Docker${NC}"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose installed: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi

# Check if user is in docker group (Linux-specific)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if groups | grep -q docker; then
        echo -e "${GREEN}✓ User is in docker group${NC}"
    else
        echo -e "${YELLOW}⚠ User is not in docker group${NC}"
        echo -e "${YELLOW}  Run: sudo usermod -aG docker \$USER && newgrp docker${NC}"
    fi
fi

# Check disk space
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))

if [ $AVAILABLE_GB -lt 20 ]; then
    echo -e "${YELLOW}⚠ Warning: Only ${AVAILABLE_GB}GB free disk space${NC}"
    echo -e "${YELLOW}  Recommended: 20+ GB for Docker images and volumes${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo -e "\n${GREEN}✓ All prerequisites met!${NC}\n"

# Enable BuildKit
echo -e "${YELLOW}🔧 Enabling BuildKit for faster builds...${NC}"
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Determine shell config file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

# Add to shell config if not already present
if [ -f "$SHELL_RC" ]; then
    if ! grep -q "DOCKER_BUILDKIT" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Docker BuildKit (added by SamvadQL setup)" >> "$SHELL_RC"
        echo "export DOCKER_BUILDKIT=1" >> "$SHELL_RC"
        echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> "$SHELL_RC"
        echo -e "${GREEN}✓ BuildKit enabled and added to $SHELL_RC${NC}"
    else
        echo -e "${GREEN}✓ BuildKit already configured in $SHELL_RC${NC}"
    fi
else
    touch "$SHELL_RC"
    echo "# Docker BuildKit (added by SamvadQL setup)" >> "$SHELL_RC"
    echo "export DOCKER_BUILDKIT=1" >> "$SHELL_RC"
    echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> "$SHELL_RC"
    echo -e "${GREEN}✓ BuildKit enabled and shell config created${NC}"
fi

# Setup environment file
echo -e "\n${YELLOW}📝 Setting up environment configuration...${NC}"

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created from template${NC}"
    else
        echo -e "${GREEN}✓ Using existing .env file${NC}"
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
fi

# Prompt for required API keys
echo -e "\n${YELLOW}🔑 API Keys Configuration${NC}"
echo "Please provide your API keys (press Enter to skip):"
echo

read -p "OpenAI API Key: " OPENAI_KEY
if [ -n "$OPENAI_KEY" ]; then
    sed -i.bak "s/your-openai-api-key-here/$OPENAI_KEY/" .env
fi

read -p "Anthropic API Key (optional): " ANTHROPIC_KEY
if [ -n "$ANTHROPIC_KEY" ]; then
    sed -i.bak "s/your-anthropic-api-key-here/$ANTHROPIC_KEY/" .env
fi

# Generate secure SECRET_KEY
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
sed -i.bak "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
rm -f .env.bak
echo -e "${GREEN}✓ Generated secure SECRET_KEY${NC}"

echo -e "\n${GREEN}✓ Environment configuration complete!${NC}\n"

# Build images
echo -e "${YELLOW}🏗️  Building Docker images...${NC}"
echo -e "${CYAN}This will take 10-15 minutes on first run (downloads dependencies)${NC}\n"

BUILD_START=$(date +%s)
if docker-compose build; then
    BUILD_END=$(date +%s)
    BUILD_TIME=$((($BUILD_END - $BUILD_START) / 60))
    echo -e "\n${GREEN}✓ Images built successfully in ${BUILD_TIME} minutes${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Start services
echo -e "\n${YELLOW}🚀 Starting services...${NC}"
if docker-compose up -d; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be healthy
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check backend health
MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        BACKEND_HEALTHY=true
        break
    fi
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ "$BACKEND_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ Backend is healthy at http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠ Backend health check timed out - check logs: docker-compose logs backend${NC}"
fi

# Check frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is ready at http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not responding yet - may still be starting${NC}"
fi

# Display success message
echo
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo -e "${GREEN}==================${NC}\n"

echo -e "${CYAN}Access your application:${NC}"
echo -e "  • Frontend:      http://localhost:3000"
echo -e "  • Backend API:   http://localhost:8000"
echo -e "  • API Docs:      http://localhost:8000/docs"
echo -e "  • Documentation: http://localhost:3001\n"

echo -e "${CYAN}Useful commands:${NC}"
echo -e "  • View logs:     docker-compose logs -f backend"
echo -e "  • Stop services: docker-compose down"
echo -e "  • Restart:       docker-compose restart backend\n"

echo -e "${YELLOW}📖 Read docs/DEV_WORKFLOW.md for daily development workflow and troubleshooting.${NC}\n"

read -p "Press Enter to view backend logs (Ctrl+C to exit)..."
docker-compose logs -f backend
