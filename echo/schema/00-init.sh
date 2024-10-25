#!/bin/sh
set -euf -o pipefail

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
    CREATE ROLE echo WITH login;
    CREATE DATABASE echo WITH OWNER echo;
EOSQL
