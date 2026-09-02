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

# The lockfile is not optional and the install is not allowed to improvise:
# `npm ci` needs package-lock.json and installs it EXACTLY. The `|| npm install`
# that used to follow turned a missing or out-of-step lockfile — the one thing
# `npm ci` exists to catch — into a silent re-resolve, so the image could ship
# dependency versions no checkout ever saw and no CI run ever tested.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:alpine

COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf
# The security headers nginx.conf includes at server level and in every
# location with an add_header of its own — without this COPY the container does
# not start at all (nginx fails on a missing include), which is the failure mode
# we want: never a silent deploy that quietly drops the headers.
COPY --chown=nginx:nginx security-headers.conf /etc/nginx/security-headers.conf
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
