# Multi-stage Dockerfile for kurrentschrift admin app on Cloud Run.
# Pattern mirrors ~/projects/anyplot/app/Dockerfile. Placeholder for v1.

FROM node:20-alpine AS builder

# In production an env var would tell the frontend where to find the API.
# v1 same-origin reverse proxy (nginx below), so no build arg needed yet.

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:alpine

COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
