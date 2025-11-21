from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sock import Sock
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from urllib.parse import urlparse
import threading
import websocket  # pip install websocket-client
from simple_websocket import ConnectionClosed
from browser_cloud.config import Config

app = Flask(__name__, static_folder='static')
CORS(app)
sock = Sock(app)  # Initialize WebSocket support

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = Config()

# Selenium Grid Configuration
GRID_URL = config.get('grid_url', 'http://10.160.24.88:31590')
VNC_PASSWORD = config.get('vnc_password', 'secret')
REGISTRATION_SECRET = config.get('registration_secret', '')

parsed_grid = urlparse(GRID_URL)
# We will use this internal URL for the backend to connect to
GRID_WS_HOST = f"{parsed_grid.netloc}"


class GridManager:
    """Selenium Grid Manager Logic"""

    def __init__(self, grid_url: str):
        self.grid_url = grid_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def get_status(self) -> Dict:
        """Get Grid status and availability"""
        try:
            response = self.session.get(f"{self.grid_url}/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get grid status: {e}")
            return {}  # Return empty dict on failure to prevent crash

    def create_session(self, capabilities: Dict) -> Dict:
        """Create a new browser session with specified capabilities"""
        try:
            response = self.session.post(
                f"{self.grid_url}/session",
                json=capabilities,
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return {"success": False, "error": str(e)}

    def get_session(self, session_id: str) -> Dict:
        """Get session details by session ID"""
        try:
            response = self.session.get(
                f"{self.grid_url}/session/{session_id}",
                timeout=5
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return {"success": False, "error": str(e)}

    def delete_session(self, session_id: str) -> bool:
        """Delete a browser session"""
        try:
            response = self.session.delete(
                f"{self.grid_url}/session/{session_id}",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the grid"""
        try:
            headers = {'X-REGISTRATION-SECRET': REGISTRATION_SECRET}
            response = self.session.delete(
                f"{self.grid_url}/se/grid/distributor/node/{node_id}",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to remove node {node_id}: {e}")
            return False

    def drain_node(self, node_id: str) -> bool:
        """Drain a node (prevent new sessions)"""
        try:
            headers = {'X-REGISTRATION-SECRET': REGISTRATION_SECRET}
            response = self.session.post(
                f"{self.grid_url}/se/grid/distributor/node/{node_id}/drain",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to drain node {node_id}: {e}")
            return False

    def get_session_queue(self) -> Dict:
        """Get the current session queue"""
        try:
            response = self.session.get(
                f"{self.grid_url}/se/grid/newsessionqueue/queue",
                timeout=5
            )
            return response.json()
        except Exception:
            return {"value": {"requests": []}}

    def clear_session_queue(self) -> bool:
        """Clear all pending session requests from the queue"""
        try:
            headers = {'X-REGISTRATION-SECRET': REGISTRATION_SECRET}
            self.session.delete(
                f"{self.grid_url}/se/grid/newsessionqueue/queue",
                headers=headers,
                timeout=5
            )
            return True
        except Exception:
            return False

    def get_node_info(self, node_id: str) -> Dict:
        """Get detailed information about a specific node"""
        try:
            response = self.session.get(
                f"{self.grid_url}/se/grid/distributor/node/{node_id}/status",
                timeout=5
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Failed to get node info {node_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_all_sessions(self) -> List[Dict]:
        """Get all active sessions across all nodes"""
        try:
            status = self.get_status()
            sessions = []
            nodes = status.get("value", {}).get("nodes", [])

            for node in nodes:
                for slot in node.get("slots", []):
                    if slot.get("session"):
                        sessions.append({
                            "sessionId": slot["session"].get("sessionId"),
                            "nodeId": node.get("id"),
                            "nodeUri": node.get("uri"),
                            "capabilities": slot["session"].get("capabilities", {}),
                            "startTime": slot["session"].get("start", ""),
                            "stereotype": slot.get("stereotype", {})
                        })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get all sessions: {e}")
            return []

    def parse_grid_data(self, status: Dict) -> Dict:
        """Parses the complex Grid JSON into a frontend-friendly format"""
        value = status.get("value", {})
        nodes = value.get("nodes", [])

        parsed_nodes = []
        active_sessions = []
        total_slots = 0
        available_slots = 0

        for node in nodes:
            node_id = node.get("id", "")
            node_uri = node.get("uri", "")
            slots = node.get("slots", [])

            node_info = {
                "id": node_id,
                "uri": node_uri,
                "availability": node.get("availability", "UNKNOWN"),
                "slots": []
            }

            for slot in slots:
                total_slots += 1
                slot_info = {
                    "id": slot.get("id", {}).get("id", ""),
                    "stereotype": slot.get("stereotype", {}),
                    "session": None
                }

                if slot.get("session"):
                    session = slot["session"]
                    session_id = session.get("sessionId", "")

                    slot_info["session"] = {
                        "sessionId": session_id,
                        "capabilities": session.get("capabilities", {}),
                        "startTime": session.get("start", ""),
                        "uri": session.get("uri", "")
                    }

                    active_sessions.append({
                        "sessionId": session_id,
                        "nodeId": node_id,
                        "nodeUri": node_uri,
                        "capabilities": session.get("capabilities", {}),
                        "startTime": session.get("start", ""),
                        "stereotype": slot.get("stereotype", {})
                    })
                else:
                    available_slots += 1

                node_info["slots"].append(slot_info)

            parsed_nodes.append(node_info)

        return {
            "nodes": parsed_nodes,
            "sessions": active_sessions,
            "statistics": {
                "totalNodes": len(nodes),
                "totalSlots": total_slots,
                "availableSlots": available_slots,
                "activeSessions": len(active_sessions)
            },
            "gridUrl": self.grid_url,
            "vncPassword": VNC_PASSWORD
        }


grid_manager = GridManager(GRID_URL)


# ==========================================
#  WEBSOCKET PROXY (The Solution)
# ==========================================

def bridge_vnc_traffic(client_ws, grid_ws):
    """Reads from Grid, writes to Client (Background Thread)"""
    try:
        while True:
            data = grid_ws.recv()
            if not data:
                break
            client_ws.send(data)
    except Exception:
        pass
    finally:
        try:
            client_ws.close()
        except:
            pass


@sock.route('/vnc/<session_id>')
def vnc_proxy(client_ws, session_id):
    """
    The browser connects here. We connect to the Grid.
    We bridge the traffic.
    """
    # Determine if Grid is ws:// or wss:// based on GRID_URL configuration
    grid_scheme = 'wss' if parsed_grid.scheme == 'https' else 'ws'

    # Internal URL to the specific Session VNC endpoint
    grid_ws_url = f"{grid_scheme}://{GRID_WS_HOST}/session/{session_id}/se/vnc"

    grid_ws = None
    try:
        # 1. Connect Flask to Grid
        grid_ws = websocket.create_connection(grid_ws_url)

        # 2. Start thread to pipe Grid -> Client
        t = threading.Thread(target=bridge_vnc_traffic, args=(client_ws, grid_ws))
        t.daemon = True
        t.start()

        # 3. Main Loop: Pipe Client -> Grid
        while True:
            data = client_ws.receive()
            if data is None:
                break
            grid_ws.send(data)

    except ConnectionClosed:
        pass  # Normal disconnect
    except Exception as e:
        logger.error(f"VNC Proxy Error for {session_id}: {e}")
    finally:
        if grid_ws:
            grid_ws.close()


# ==========================================
#  STANDARD API ROUTES
# ==========================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/v1/browser_cloud/status', methods=['GET'])
def get_status():
    """Get Grid status with parsed data"""
    try:
        status = grid_manager.get_status()
        parsed_data = grid_manager.parse_grid_data(status)
        return jsonify({"success": True, "data": parsed_data})
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/sessions', methods=['GET'])
def get_all_sessions():
    """Get all active sessions"""
    try:
        sessions = grid_manager.get_all_sessions()
        return jsonify({"success": True, "data": sessions})
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/session', methods=['POST'])
def create_session():
    """Create a new browser session"""
    try:
        capabilities = request.get_json()
        result = grid_manager.create_session(capabilities)
        if result.get("success"):
            return jsonify(result), 201
        return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/session/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get details of a specific session"""
    try:
        result = grid_manager.get_session(session_id)
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a browser session"""
    try:
        if grid_manager.delete_session(session_id):
            return jsonify({"success": True, "message": f"Session {session_id} deleted"})
        return jsonify({"success": False, "error": "Failed to delete session"}), 500
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/node/<node_id>', methods=['GET'])
def get_node_info(node_id):
    """Get information about a specific node"""
    try:
        result = grid_manager.get_node_info(node_id)
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error getting node info {node_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/node/<node_id>', methods=['DELETE'])
def remove_node(node_id):
    """Remove a node from the grid"""
    try:
        if grid_manager.remove_node(node_id):
            return jsonify({"success": True, "message": f"Node {node_id} removed"})
        return jsonify({"success": False, "error": "Failed to remove node"}), 500
    except Exception as e:
        logger.error(f"Error removing node {node_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/node/<node_id>/drain', methods=['POST'])
def drain_node(node_id):
    """Drain a node (prevent new sessions)"""
    try:
        if grid_manager.drain_node(node_id):
            return jsonify({"success": True, "message": f"Node {node_id} drained"})
        return jsonify({"success": False, "error": "Failed to drain node"}), 500
    except Exception as e:
        logger.error(f"Error draining node {node_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/queue', methods=['GET'])
def get_queue():
    """Get the current session queue"""
    try:
        queue_data = grid_manager.get_session_queue()
        return jsonify({"success": True, "data": queue_data})
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/queue', methods=['DELETE'])
def clear_queue():
    """Clear all pending session requests from the queue"""
    try:
        if grid_manager.clear_session_queue():
            return jsonify({"success": True, "message": "Queue cleared"})
        return jsonify({"success": False, "error": "Failed to clear queue"}), 500
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/config', methods=['GET'])
def get_config():
    """Get current Grid configuration"""
    try:
        return jsonify({
            "success": True,
            "data": {
                "gridUrl": GRID_URL,
                "vncPassword": VNC_PASSWORD,
                "wsHost": GRID_WS_HOST
            }
        })
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/browser_cloud/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Try to get grid status to verify connectivity
        status = grid_manager.get_status()
        if status:
            return jsonify({
                "success": True,
                "status": "healthy",
                "grid_accessible": True,
                "timestamp": datetime.utcnow().isoformat()
            })
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "grid_accessible": False,
            "timestamp": datetime.utcnow().isoformat()
        }), 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    # Threading must be enabled for the WebSocket proxy
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
