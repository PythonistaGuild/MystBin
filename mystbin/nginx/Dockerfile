FROM nginx:latest

COPY .env /etc/.mystbin-env
COPY sites-enabled/* /etc/nginx/sites-enabled/
COPY ssl.sh /.ssl.sh
COPY docker-entrypoint.sh /.mystbin-entrypoint.sh

RUN chmod u+x /.mystbin-entrypoint.sh /.ssl.sh
ENTRYPOINT [ "/.mystbin-entrypoint.sh" ]
CMD [ "nginx", "-g", "daemon off;" ]
