FROM node:18-alpine

WORKDIR /app

COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --frozen-lockfile

COPY frontend .

RUN yarn build

EXPOSE 3000

CMD ["yarn", "dev"]