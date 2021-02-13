FROM php:7.4-apache

RUN apt-get update && apt-get -y install libicu-dev libzip-dev && \
    docker-php-ext-install bcmath intl opcache zip sockets;

ENV APP_ENV=prod
ENV DATABASE_URL="sqlite:////var/db/app.db"
ENV MAILER_DSN="smtp://localhost:25"
ENV PATH=$PATH:/var/www/bin

WORKDIR /var/www

COPY --from=symfony-demo:base /var/www .
COPY --from=symfony-demo:base /var/db /var/db

# Timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Warsaw /etc/localtime && \
    echo "date.timezone = Europe/Warsaw" >> /usr/local/etc/php/conf.d/datetime.ini;

RUN a2enmod rewrite
COPY ./docker/apache.conf /etc/apache2/sites-available/000-default.conf
RUN chown -R www-data:www-data /var/www

CMD ["./bin/docker-init.sh", "apache2-foreground"]
