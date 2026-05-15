FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi


FROM deps AS dev
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]


FROM deps AS build
COPY . .
RUN mkdir -p public && npm run build


# Build-time verification target (no local Node required).
# - Used by docker compose profile "validate" to ensure lint+build succeeds in-container.
FROM deps AS check
COPY . .
RUN mkdir -p public && npm run lint && npm run build


FROM node:20-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production

# For Next.js runtime we need node_modules + build output + public assets.
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next

EXPOSE 3000

# "next start" binds to localhost by default; force 0.0.0.0 for container usage.
CMD ["node", "node_modules/next/dist/bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]
