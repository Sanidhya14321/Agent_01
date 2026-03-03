FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json turbo.json* ./
COPY apps/web ./apps/web
COPY packages ./packages
RUN npm install --legacy-peer-deps
RUN npm run build --workspace=apps/web

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "run", "start", "--workspace=apps/web"]
