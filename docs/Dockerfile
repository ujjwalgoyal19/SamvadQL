FROM node:18-alpine AS base

# Install Mintlify CLI globally
RUN npm install -g mintlify@latest

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate documentation from source code
RUN npm run generate-all-docs

# Build the documentation with Mintlify
RUN mintlify build

# Production image, copy all the files and run nginx
FROM nginx:alpine AS runner
WORKDIR /usr/share/nginx/html

# Copy the built documentation
COPY --from=builder /app/_site .

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]