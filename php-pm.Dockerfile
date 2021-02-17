FROM php:7.4-cli-alpine

RUN apk add --no-cache autoconf openssl-dev g++ make pcre-dev icu-dev zlib-dev libzip-dev git && \
    docker-php-ext-install bcmath intl opcache zip sockets pcntl && \
    apk del --purge autoconf g++ make;

ARG PPM_VERSION

ENV APP_ENV=prod
ENV DATABASE_URL="sqlite:////var/db/app.db"
ENV MAILER_DSN="smtp://localhost:25"
ENV PATH=$PATH:/var/www/bin:/var/www/vendor/bin

WORKDIR /var/www

COPY --from=symfony-demo:base /var/www .
COPY --from=symfony-demo:base /var/db /var/db

# Timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Warsaw /etc/localtime && \
    echo "date.timezone = Europe/Warsaw" >> /usr/local/etc/php/conf.d/datetime.ini;

EXPOSE 8080
CMD ["./bin/docker-init.sh", "ppm", "start", "--app-env", "prod", "--bootstrap", "symfony", "--host", "0.0.0.0"]
