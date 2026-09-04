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

# The origin gate's maps, which need the shared secret — and nginx cannot read
# the environment. The base image already ships the official entrypoint's
# 20-envsubst-on-templates.sh, which renders /etc/nginx/templates/*.template
# into /etc/nginx/conf.d/ before nginx starts, so this costs no start script of
# our own. The `00-` prefix puts the rendered maps ahead of default.conf in the
# conf.d glob, where a reader expects to meet them.
COPY --chown=nginx:nginx origin-gate.conf.template /etc/nginx/templates/00-origin-gate.conf.template

# Two defaults that have to exist as real ENVIRONMENT variables rather than as a
# documented meaning of "unset". envsubst substitutes only names it finds in the
# environment: with neither set, `${ORIGIN_SECRET}` would survive into the
# rendered config as a literal, nginx would read it as a reference to a variable
# it does not know, and the container would refuse to start. With them set, a
# service that declares neither means "gate off, no secret" — which is the
# default state this change ships in and the rollback it rolls back to.
#
# NGINX_ENVSUBST_FILTER keeps envsubst away from everything else: without it,
# envsubst rewrites every `$name` in the template whose name happens to exist in
# the environment, and `$host` and `$uri` in there are nginx's variables, not the
# shell's. The filter is a regex over variable NAMES; `^ORIGIN_` is exactly
# ORIGIN_GATE and ORIGIN_SECRET.
ENV ORIGIN_GATE=off \
    NGINX_ENVSUBST_FILTER="^ORIGIN_"

# On its own instruction so the exception below excuses this line and nothing
# else. DL3064 reads the NAME and warns that a secret may be baked into the
# image; the value here is the empty string, and it is declared for the opposite
# reason — so that a service which supplies no secret renders a config that
# refuses everyone, rather than one nginx cannot parse. The real value arrives at
# runtime from Secret Manager and never reaches a layer. Renaming the variable
# would silence the rule and break the contract instead: the API service, the
# Worker binding, the GitHub repository secret and the Secret Manager entry all
# carry this name.
# hadolint ignore=DL3064
ENV ORIGIN_SECRET=""

COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
