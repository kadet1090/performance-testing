FROM node:latest as assets
WORKDIR /var/www

COPY ./assets/ ./assets/
COPY ./package.json webpack.config.js yarn.lock ./
RUN yarn install && yarn run build

FROM php:7.4-alpine

ENV APP_ENV=prod
ENV DATABASE_URL="sqlite:////var/db/app.db"
ENV MAILER_DSN="smtp://localhost:25"

WORKDIR /var/www

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
COPY . .
COPY --from=assets /var/www/public public

RUN composer install --prefer-dist --no-progress --no-interaction --ignore-platform-reqs && \
    composer dump-autoload --optimize && \
    php bin/console cache:warmup

RUN mkdir /var/db && \
    ./bin/console doctrine:schema:create && \
    ./bin/console doctrine:schema:update --force && \
    yes | APP_ENV=dev ./bin/console doctrine:fixtures:load
