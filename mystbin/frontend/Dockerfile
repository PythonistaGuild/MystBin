FROM node:latest

RUN mkdir -p /app
WORKDIR /app

COPY . /app

RUN yarn install --production && yarn add --dev typescript @types/node

RUN yarn run build

CMD ["yarn", "run", "start"]