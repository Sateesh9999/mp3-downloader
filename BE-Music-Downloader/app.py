import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS # Import the CORS extension

# --- Configuration ---
DEST_DIR = "C:/Users/thakk/Music" 
BACKEND_PORT = 5000

# Create the Flask application instance
app = Flask(__name__)

# Initialize CORS
# This allows requests from your frontend's address (http://localhost:5173)
# Replace the origin URL below if your frontend is not on localhost.
CORS(app, resources={r"/download": {"origins": "http://localhost:5173"}}) 


# --- SPOTDL LOGIC INTEGRATION (Simplified) ---

# NOTE: For a real server, this function should be run asynchronously 
# (e.g., using Celery) to prevent blocking the entire server for the duration 
# of the download. For a small/personal app, this setup is quicker.
def run_spotdl_download(url, output_dir):
    """Executes the SpotDL command."""
    
    # 1. Ensure directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. Define the command (you can add --log-level debug here if needed)
    command = [
        "spotdl", 
        "download", 
        url, 
        "--output", 
        output_dir
    ]
    
    print(f"Executing SpotDL for URL: {url}")

    try:
        # Run the command
        subprocess.run(
            command, 
            check=True, 
            text=True, 
            capture_output=True,
            timeout=300 # Set a timeout (5 minutes) to prevent infinite blocking
        )
        return True, "Download initiated and finished successfully."
    
    except subprocess.CalledProcessError as e:
        return False, f"SpotDL failed with exit code {e.returncode}. Error: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "Download timed out (exceeded 5 minutes)."
    except FileNotFoundError:
        return False, "Error: 'spotdl' command not found. Is it installed and in PATH?"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"


# --- API Endpoint ---

@app.route('/download', methods=['POST'])
def handle_download_request():
    """
    Receives the JSON body from the frontend, extracts the URL, and starts the download.
    """
    
    # Check if the request body is valid JSON
    if not request.is_json:
        return jsonify({"message": "Invalid request format. Must be JSON."}), 400
        
    data = request.get_json()
    
    # Extract the URL. The frontend must send data with the key 'spotify_url'.
    url = data.get('spotify_url')
    
    if not url:
        return jsonify({"message": "Error: 'spotify_url' key is missing in the request data."}), 400
        
    # --- Execute Download Logic ---
    # For robust production servers, this call should be asynchronous (Celery/RQ)
    success, message = run_spotdl_download(url, DEST_DIR)

    if success:
        return jsonify({
            "status": "success",
            "message": message,
            "url": url
        }), 200 
    else:
        return jsonify({
            "status": "error",
            "message": message,
            "url": url
        }), 500 # 500 status code for internal server error

# --- Run the Server ---
if __name__ == '__main__':
    print(f"Flask Server running on http://127.0.0.1:{BACKEND_PORT}")
    app.run(port=BACKEND_PORT)