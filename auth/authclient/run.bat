@echo off
SET CONCURRENT=1

SET CLOSE_CONNECTION=no
SET URL=https://2ssmtlwe.fortiauthenticator.forticloud.com/api/v1/auth/

SET REPEAT=1
SET AUTHMODE=saml
SET RESOURCE_POOL_NAME=faccloud
SET REQUEST_POOL_SIZE=2
SET USE_TAAS=yes

SET FAC_ADMIN_USER=ftc.manual.znie@gmail.com
SET FAC_ADMIN_TOKEN=46O1mtZqUOt5R24KyAM32pwShFXxvxdK4SaHjNoY

SET AUTH_SERVER_IP=2ssmtlwe.fortiauthenticator.forticloud.com
SET OAUTH_CLIENT_ID=QSGF7UszuHfWFw32ERVlb0WhivmOFTjeFMxqlDid
SET OAUTH_CLIENT_SECRET=qO5FMBCvu4uRQafyJeEaoCvVloN43k5EumB1zblcdMlEHr6kA3LygZJLkRA9tTHy4zVDuKQ7CuQkK4MFfKjlao8hHwA5WfPmmfwcSCRonu3yM2Sx45lgk1MkHMBkRhe0
authclient.exe