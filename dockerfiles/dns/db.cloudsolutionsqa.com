$TTL    604800

@       IN      SOA     ns.cloudsolutionsqa.com. root.cloudsolutionsqa.com. (
                              6         ; Serial
                         604820         ; Refresh
                          86600         ; Retry
                        2419600         ; Expire
                         604600 )       ; Negative Cache TTL

;Name Server Information
@       IN      NS      ns.cloudsolutionsqa.com.

;IP address of Your Domain Name Server(DNS)
@       IN       A      10.160.13.13
ns      IN       A      10.160.13.13

;Mail Server MX (Mail exchanger) Record
cloudsolutionsqa.com. IN  MX  10  mail.cloudsolutionsqa.com.

;A Record for Host names
mail    IN       A       10.160.13.20
