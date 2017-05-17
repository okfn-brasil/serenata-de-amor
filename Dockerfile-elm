FROM node:6.9.1

RUN npm install yarn
RUN ln -s /node_modules/yarn/bin/yarn.js /usr/bin/yarn
WORKDIR /code

COPY yarn.lock yarn.lock
COPY package.json package.json
COPY elm-package.json elm-package.json
COPY gulpfile.js gulpfile.js
RUN yarn install --pure-lockfile

COPY jarbas jarbas
CMD ["yarn", "assets"]
