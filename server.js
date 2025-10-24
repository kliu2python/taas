const fs = require('fs');
const https = require('https');
const express = require('express');
const path = require('path');

const app = express();

// Load TLS cert and key (mounted from Kubernetes secret)
const key = fs.readFileSync('/etc/tls/tls.key');
const cert = fs.readFileSync('/etc/tls/tls.crt');

// Serve static React files
app.use(express.static(path.join(__dirname, 'build')));

// SPA fallback
app.get('*', (_, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Start HTTPS server
https.createServer({ key, cert }, app).listen(3000, () => {
  console.log('✅ HTTPS server running on port 3000');
});