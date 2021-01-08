FROM nginx:latest

RUN mkdir -p /etc/mystbin

COPY .env /etc/mystbin/.env
COPY sites-enabled/* /etc/mystbin/sites-enabled/
COPY ssl.sh /etc/mystbin/ssl.sh
COPY docker-entrypoint.sh /etc/mystbin/mystbin-entrypoint.sh

RUN chmod u+x /etc/mystbin/mystbin-entrypoint.sh /etc/mystbin/ssl.sh
ENTRYPOINT [ "/etc/mystbin/mystbin-entrypoint.sh" ]
CMD [ "nginx", "-g", "daemon off;" ]
