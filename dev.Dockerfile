FROM symfony-demo:base

ENV PATH=$PATH:/var/www/bin

RUN apk add --no-cache autoconf openssl-dev g++ make pcre-dev icu-dev zlib-dev libzip-dev git && \
    docker-php-ext-install bcmath pcntl intl opcache zip sockets && \
    apk del --purge autoconf g++ make;

EXPOSE 8080
CMD ["./bin/docker-init.sh", "php", "-S", "0.0.0.0:8080", "-t", "public"]
