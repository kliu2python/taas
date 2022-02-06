package main

import (
	"context"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"net/url"
	"os"

	"github.com/crewjam/saml/samlsp"
)

var metdataUrl = os.Getenv("METADATA_URL")
var signingCert = "./pki/cert.pem"
var signingKey = "./pki/key.pem"
var serverKey = "./pki/key.pem"
var serverCert = "./pki/cert.pem"
var serverIP = os.Getenv("SERVER_IP")
var serverPort = getEnv("SERVER_PORT", "8080")
var serverUrl = fmt.Sprintf("https://%s:%s", serverIP, serverPort)
var entityId = fmt.Sprintf("http://%s:%s", serverIP, serverPort)
var listenAddr = fmt.Sprintf("0.0.0.0:%s", serverPort)

var samlMiddleware *samlsp.Middleware

func hello(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Login Successful, %s!", samlsp.AttributeFromContext(r.Context(), "displayName"))
}

func getEnv(key, defaultValue string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return defaultValue
}

func logout(w http.ResponseWriter, r *http.Request) {
	nameID := samlsp.AttributeFromContext(r.Context(), "urn:oasis:names:tc:SAML:attribute:subject-id")
	url, err := samlMiddleware.ServiceProvider.MakeRedirectLogoutRequest(nameID, "")
	if err != nil {
		panic(err)
	}

	err = samlMiddleware.Session.DeleteSession(w, r)
	if err != nil {
		panic(err)
	}

	w.Header().Add("Location", url.String())
	w.WriteHeader(http.StatusFound)
}

func main() {
	fmt.Println("Starting SP Service..")
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}

	keyPair, err := tls.LoadX509KeyPair(signingCert, signingKey)
	if err != nil {
		panic(err)
	}
	keyPair.Leaf, err = x509.ParseCertificate(keyPair.Certificate[0])
	if err != nil {
		panic(err)
	}

	idpMetadataURL, err := url.Parse(metdataUrl)
	if err != nil {
		panic(err)
	}
	idpMetadata, err := samlsp.FetchMetadata(context.Background(), http.DefaultClient,
		*idpMetadataURL)
	if err != nil {
		fmt.Println("MetaDataURL could have issue, Used Metadata URL:", metdataUrl)
		panic(err)
	}

	rootURL, err := url.Parse(serverUrl)
	if err != nil {
		panic(err) // TODO handle error
	}

	samlMiddleware, _ = samlsp.New(samlsp.Options{
		URL:         *rootURL,
		Key:         keyPair.PrivateKey.(*rsa.PrivateKey),
		Certificate: keyPair.Leaf,
		IDPMetadata: idpMetadata,
		SignRequest: true, // some IdP require the SLO request to be signed
		EntityID:    entityId,
	})
	app := http.HandlerFunc(hello)
	slo := http.HandlerFunc(logout)
	http.Handle("/", samlMiddleware.RequireAccount(app))
	http.Handle("/saml/acs", samlMiddleware)
	http.Handle("/logout", slo)
	http.ListenAndServeTLS(listenAddr, serverCert, serverKey, nil)
}
