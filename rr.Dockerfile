FROM node:latest as assets
WORKDIR /var/www

COPY . .
RUN yarn install && yarn run build

FROM php:7.4-alpine

ENV APP_ENV=prod
ENV DATABASE_URL="sqlite:////var/db/app.db"
ENV MAILER_DSN="smtp://localhost:25"
ENV PATH=$PATH:/var/www/bin

WORKDIR /var/www

RUN mkdir /var/db

RUN apk add --no-cache autoconf openssl-dev g++ make pcre-dev icu-dev zlib-dev libzip-dev git && \
    docker-php-ext-install bcmath intl opcache zip sockets && \
    apk del --purge autoconf g++ make;

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
COPY . .
COPY --from=assets /var/www/public public

RUN composer install --prefer-dist --no-progress --no-interaction && \
    composer dump-autoload --optimize && \
    composer check-platform-reqs && \
    php bin/console cache:warmup

RUN ./bin/console doctrine:schema:create && \
    ./bin/console doctrine:schema:update --force && \
    yes | APP_ENV=dev ./bin/console doctrine:fixtures:load

# Timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Warsaw /etc/localtime && \
    echo "date.timezone = Europe/Warsaw" >> /usr/local/etc/php/conf.d/datetime.ini;

RUN ./vendor/bin/rr get-binary --location /usr/local/bin

EXPOSE 8080
CMD ["./bin/docker-init.sh", "rr", "serve"]
