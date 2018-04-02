FROM node:9.7.1-slim

WORKDIR /code

COPY package.json package.json
COPY package-lock.json package-lock.json
COPY elm-package.json elm-package.json
COPY gulpfile.js gulpfile.js

RUN npm install

COPY ./jarbas /code/jarbas

CMD ["npm", "run", "assets"]
