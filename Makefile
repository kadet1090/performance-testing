.PHONY: all rr fpm builtin apache ppm

%.Dockerfile:
	docker build -f $@ -t symfony-demo:$(basename $@) .

rr.Dockerfile: base.Dockerfile
fpm.Dockerfile: base.Dockerfile
builtin.Dockerfile: base.Dockerfile
php-pm.Dockerfile: base.Dockerfile

rr: rr.Dockerfile
fpm: fpm.Dockerfile
builtin: builtin.Dockerfile
apache: apache.Dockerfile
ppm: php-pm.Dockerfile

all: rr fpm builtin ppm
