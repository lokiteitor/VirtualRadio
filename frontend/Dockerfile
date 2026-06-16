FROM oven/bun:1 AS base
WORKDIR /app

# Install dependencies (cached layer)
COPY package.json ./
RUN bun install

# Build the Nuxt app. The API base must be reachable from the BROWSER, so it
# defaults to the host-published backend port; override with --build-arg.
COPY . .
ARG NUXT_PUBLIC_API_BASE=http://localhost:5000/api/v1
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
RUN bun run build

EXPOSE 3000
ENV HOST=0.0.0.0 PORT=3000
# Nitro server output (serves the SPA + handles runtime config)
CMD ["node", ".output/server/index.mjs"]
