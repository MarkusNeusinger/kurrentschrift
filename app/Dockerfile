# Multi-stage Dockerfile for kurrentschrift admin app on Cloud Run.
# Pattern mirrors ~/projects/anyplot/app/Dockerfile. Placeholder for v1.

# Node >= 22 is load-bearing since the schriftkunde:md prebuild step: it
# imports a .ts renderer via Node's native type stripping (>= 22.18 without a
# flag; node:20 fails with ERR_UNKNOWN_FILE_EXTENSION). Also overdue anyway:
# package.json declares engines.node >= 22, CI builds on 22, Node 20 is EOL.
FROM node:22-alpine AS builder

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
