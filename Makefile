.PHONY: all rr fpm builtin apache

%.Dockerfile:
	docker build -f $@ -t symfony-demo:$(basename $@) .

rr.Dockerfile: base.Dockerfile
fpm.Dockerfile: base.Dockerfile
builtin.Dockerfile: base.Dockerfile
apache.Dockerfile: base.Dockerfile

rr: rr.Dockerfile
fpm: fpm.Dockerfile
builtin: builtin.Dockerfile
apache: apache.Dockerfile

all: rr fpm builtin
