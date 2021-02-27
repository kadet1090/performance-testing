.PHONY: all rr fpm builtin apache ppm dev

%.Dockerfile:
	docker build -f $@ -t symfony-demo:$(basename $@) .

rr.Dockerfile: base.Dockerfile
fpm.Dockerfile: base.Dockerfile
builtin.Dockerfile: base.Dockerfile
php-pm.Dockerfile: base.Dockerfile
php-pm.Dockerfile: dev.Dockerfile

rr: rr.Dockerfile
fpm: fpm.Dockerfile
builtin: builtin.Dockerfile
apache: apache.Dockerfile
ppm: php-pm.Dockerfile
dev: dev.Dockerfile

all: rr fpm builtin ppm dev apache
