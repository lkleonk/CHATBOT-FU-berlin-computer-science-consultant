FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN echo "frontend build: installing npm dependencies" \
 && npm ci \
 && echo "frontend build: npm dependencies installed"

FROM node:22-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_ENABLE_DEV_TOOLS=false
ARG NEXT_PUBLIC_LEGAL_NAME
ARG NEXT_PUBLIC_LEGAL_STREET
ARG NEXT_PUBLIC_LEGAL_CITY
ARG NEXT_PUBLIC_LEGAL_COUNTRY
ARG NEXT_PUBLIC_LEGAL_EMAIL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_ENABLE_DEV_TOOLS=$NEXT_PUBLIC_ENABLE_DEV_TOOLS
ENV NEXT_PUBLIC_LEGAL_NAME=$NEXT_PUBLIC_LEGAL_NAME
ENV NEXT_PUBLIC_LEGAL_STREET=$NEXT_PUBLIC_LEGAL_STREET
ENV NEXT_PUBLIC_LEGAL_CITY=$NEXT_PUBLIC_LEGAL_CITY
ENV NEXT_PUBLIC_LEGAL_COUNTRY=$NEXT_PUBLIC_LEGAL_COUNTRY
ENV NEXT_PUBLIC_LEGAL_EMAIL=$NEXT_PUBLIC_LEGAL_EMAIL

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN test -n "$NEXT_PUBLIC_API_BASE_URL" \
 && echo "frontend build: running Next.js production build" \
 && npm run build \
 && echo "frontend build: Next.js build completed"

FROM caddy:2-alpine AS static-server

COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=builder /app/out /srv

EXPOSE 80
