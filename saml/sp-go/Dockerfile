FROM ubuntu:20.04

RUN mkdir -p /sp-go/pki
COPY start.sh /sp-go/
COPY sp /sp-go/
COPY pki /sp-go/pki
RUN chmod +x /sp-go/sp
RUN chmod +x /sp-go/start.sh
WORKDIR /sp-go

CMD ["/bin/bash", "/sp-go/start.sh"]
