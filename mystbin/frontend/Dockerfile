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

FROM node:16-alpine AS runner

ENV NODE_ENV=production
COPY --from=builder /app/package.json ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

CMD [ "yarn", "run", "start"]