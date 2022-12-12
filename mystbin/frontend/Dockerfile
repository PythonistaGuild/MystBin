FROM node:latest

RUN mkdir -p /app
WORKDIR /app

COPY . /app

RUN yarn install --production

ENV NODE_OPTIONS="--openssl-legacy-provider"
CMD ["yarn", "run", "launch"]
