FROM ubuntu

RUN apt-get update \
  && apt-get install -y \
  bind9 \
  bind9utils \
  bind9-doc \
  && sed -i 's/OPTIONS=.*/OPTIONS="-4 -u bind"/' /etc/default/named
COPY named.conf.options /etc/bind/
COPY named.conf.local /etc/bind/
COPY db.cloudsolutionsqa.com /etc/bind/zones/

ENTRYPOINT  echo "Running Openldap Server.." \
            && service named start \
            && sleep infinity