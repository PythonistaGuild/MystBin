#!/usr/bin/env sh

SSL_CERT_FILE='/etc/ssl/certs/cert.pem'
SSL_KEY_FILE='/etc/ssl/keys/key.pem'
SSL_COMBINED_FILE='/etc/ssl/certs/combined.pem'
SSL_KEY_LENGTH='4096'
SSL_CERT_COUNTRY='AU'
SSL_CERT_STATE='QLD'
SSL_CERT_CITY='QLD'
SSL_CERT_DEPARTMENT='IT'
SSL_DHPARAM2048_FILE='/etc/ssl/keys/dhparam2048.pem'

for d in "/etc/ssl/certs/" \
    "/etc/ssl/keys/"; do
    [ -d ${d} ] || mkdir -p ${d}
done

if [ ! -f ${SSL_CERT_FILE} ] || [ ! -f ${SSL_KEY_FILE} ]; then
    echo "Generating SSL data."
    openssl req -x509 -nodes -sha256 -days 3650 \
        -subj "/C=${SSL_CERT_COUNTRY}/ST=${SSL_CERT_STATE}/L=${SSL_CERT_CITY}/O=${SSL_CERT_DEPARTMENT}/CN=${HOSTNAME}/emailAddress=${EMAIL_ADDRESS}" \
        -newkey rsa:${SSL_KEY_LENGTH} \
        -out ${SSL_CERT_FILE} \
        -keyout ${SSL_KEY_FILE}

    cat ${SSL_CERT_FILE} ${SSL_KEY_FILE} > ${SSL_COMBINED_FILE}
fi
chmod 0644 ${SSL_CERT_FILE} ${SSL_KEY_FILE} ${SSL_COMBINED_FILE}

# Create dh param.
if [ ! -f ${SSL_DHPARAM2048_FILE} ]; then
    echo "Generating dh param file: ${SSL_DHPARAM2048_FILE}. It make take a long time."
    openssl dhparam -out ${SSL_DHPARAM2048_FILE} 2048 >/dev/null
fi
chmod 0644 ${SSL_DHPARAM2048_FILE}
