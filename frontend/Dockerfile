FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# The /api proxy target is baked in at build time (next.config.ts rewrites), so it's a build arg.
ARG API_URL=http://backend:8000
ARG NEXT_PUBLIC_CLINIC_TZ=Asia/Yangon
ENV API_URL=$API_URL NEXT_PUBLIC_CLINIC_TZ=$NEXT_PUBLIC_CLINIC_TZ
RUN npm run build && npm prune --omit=dev

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000

COPY --from=build --chown=node /app/package.json /app/next.config.ts ./
COPY --from=build --chown=node /app/node_modules ./node_modules
COPY --from=build --chown=node /app/.next ./.next
USER node

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000/login > /dev/null || exit 1
CMD ["sh", "-c", "exec node_modules/.bin/next start -H 0.0.0.0 -p ${PORT}"]
