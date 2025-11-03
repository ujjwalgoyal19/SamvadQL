FROM node:20-alpine AS pruner
RUN npm install -g turbo pnpm@10.13.1
COPY . .
RUN turbo prune --scope=@samvadql/web --docker

FROM node:20-alpine AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml .
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=pruner /app/out/full/ .
COPY --from=installer /app/node_modules ./node_modules
RUN corepack enable pnpm && pnpm turbo run build --filter=@samvadql/web

FROM node:20-alpine AS runtime
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/apps/web-frontend/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
