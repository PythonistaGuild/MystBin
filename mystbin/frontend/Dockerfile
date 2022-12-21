FROM node:16-alpine as dep

# avoid rebuilding the node modules on every single file change, instead only when our deps change.
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

FROM node:16-alpine AS builder

ENV NODE_ENV=production
WORKDIR /app
COPY . .
COPY --from=dep /app/node_modules ./node_modules
RUN yarn build

CMD ["./node_modules/.bin/next", "start"]