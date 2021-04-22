FROM node:latest

RUN mkdir -p /app
WORKDIR /app

COPY . /app

RUN yarn install --production
RUN yarn add --dev typescript @types/node

CMD ["yarn", "run", "dev"]