FROM 10.160.16.60/bases/openldap-base:latest

VOLUME /var/lib/ldap

ENTRYPOINT  echo "Running Openldap Server.." \
            && service slapd start \
            && sleep infinity
