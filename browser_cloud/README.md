# Browser Cloud Microservice

A Flask-based microservice for managing Selenium Grid with VNC support.

## Features

- **Grid Status Monitoring**: Real-time monitoring of Selenium Grid status, nodes, and sessions
- **Session Management**: Create, view, and delete browser sessions
- **Node Management**: Drain or remove nodes from the grid
- **VNC Proxy**: WebSocket proxy for VNC connections to browser sessions
- **Queue Management**: View and clear the session request queue
- **Web Dashboard**: Interactive web interface for grid management
- **REST API**: Comprehensive RESTful API for programmatic access

## API Endpoints

### Grid Status & Health
- `GET /api/v1/browser_cloud/status` - Get grid status with all nodes and sessions
- `GET /api/v1/browser_cloud/health` - Health check endpoint
- `GET /api/v1/browser_cloud/config` - Get current configuration

### Session Management
- `GET /api/v1/browser_cloud/sessions` - Get all active sessions
- `POST /api/v1/browser_cloud/session` - Create a new browser session
- `GET /api/v1/browser_cloud/session/<session_id>` - Get session details
- `DELETE /api/v1/browser_cloud/session/<session_id>` - Delete a session

### Node Management
- `GET /api/v1/browser_cloud/node/<node_id>` - Get node information
- `DELETE /api/v1/browser_cloud/node/<node_id>` - Remove a node
- `POST /api/v1/browser_cloud/node/<node_id>/drain` - Drain a node

### Queue Management
- `GET /api/v1/browser_cloud/queue` - Get session request queue
- `DELETE /api/v1/browser_cloud/queue` - Clear the queue

### VNC Access
- `WS /vnc/<session_id>` - WebSocket proxy for VNC connection

## Configuration

Edit `browser_cloud/config.yml` to configure:

```yaml
grid_url: "http://10.160.24.88:31590"
vnc_password: "secret"
registration_secret: ""
host: "0.0.0.0"
port: 5000
debug: false
```

Or use environment variables:
- `GRID_URL` - Selenium Grid URL
- `VNC_PASSWORD` - VNC password
- `REGISTRATION_SECRET` - Grid registration secret
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)
- `DEBUG` - Debug mode (default: false)

## Running Locally

```bash
cd browser_cloud
pip install -r ../dockerfiles/browser_cloud/api/requirements
python app.py
```

Then open http://localhost:5000 in your browser.

## Running with Docker

```bash
cd dockerfiles/browser_cloud/api
docker build -t browser-cloud .
docker run -p 5000:5000 \
  -e GRID_URL=http://your-grid:4444 \
  -e VNC_PASSWORD=secret \
  browser-cloud
```

## Architecture

- **Flask**: Web framework and REST API
- **Flask-Sock**: WebSocket support for VNC proxy
- **Flask-CORS**: Cross-origin resource sharing
- **websocket-client**: WebSocket client for Grid connection
- **requests**: HTTP client for Grid API

## Usage Examples

### Create a Chrome Session

```bash
curl -X POST http://localhost:5000/api/v1/browser_cloud/session \
  -H "Content-Type: application/json" \
  -d '{
    "desiredCapabilities": {
      "browserName": "chrome",
      "browserVersion": "latest"
    }
  }'
```

### Get All Sessions

```bash
curl http://localhost:5000/api/v1/browser_cloud/sessions
```

### Delete a Session

```bash
curl -X DELETE http://localhost:5000/api/v1/browser_cloud/session/abc123
```

### Drain a Node

```bash
curl -X POST http://localhost:5000/api/v1/browser_cloud/node/node-id/drain
```

## Web Dashboard

Access the web dashboard at http://localhost:5000 to:
- View real-time grid statistics
- Monitor active sessions and nodes
- Delete sessions
- Drain or remove nodes
- Clear the session queue
- Access VNC for active sessions

## License

Copyright Fortinet
