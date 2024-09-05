import os
import subprocess
from flask import Flask, jsonify, Response, stream_with_context
from thread_handler import ThreadHandler

app = Flask(__name__)

# Initialize the ThreadHandler singleton
thread_handler = ThreadHandler.get_instance()

def server_func():
    # Set the OLLAMA_HOST environment variable
    os.environ["OLLAMA_HOST"] = "0.0.0.0:11434"
    
    # Run the CLI command `ollama serve` as a subprocess
    try:
        subprocess.run(["ollama", "serve"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Server process failed: {e}")

# Route to start the server thread
@app.route('/run', methods=['POST'])
def run_script():
    if thread_handler.is_running():
        return "Another instance is already running", 409

    def generate():
        try:
            # Start the server thread
            thread_handler.start_thread(target=server_func)
            yield "Server started...\n"
        except Exception as e:
            print(str(e))
            yield "Error occurred: " + str(e)
        finally:
            if not thread_handler.is_running():
                yield "Server thread finished\n"

    return Response(stream_with_context(generate()), content_type='text/plain; charset=utf-8')

# Route to stop the server thread and start a new one
@app.route('/restart', methods=['GET'])
def restart():
    def generate():
        try:
            yield "Stopping...\n"
            
            # List processes before stopping
            yield "Current processes:\n"
            try:
                yield subprocess.check_output("ps aux | grep 'ollama serve'", shell=True).decode()
            except subprocess.CalledProcessError:
                yield "Failed to list processes.\n"
            
            # Force stop the existing server process
            try:
                subprocess.run("pkill -9 -f 'ollama serve'", shell=True, check=True)
                yield "Server stopped successfully.\n"
            except subprocess.CalledProcessError as e:
                yield f"Failed to stop server: {e}\n"

            # List processes after stopping
            yield "Processes after stop attempt:\n"
            try:
                yield subprocess.check_output("ps aux | grep 'ollama serve'", shell=True).decode()
            except subprocess.CalledProcessError:
                yield "Failed to list processes.\n"

            # Ensure that the thread is properly stopped (if needed)
            thread_handler.stop_thread()

            # Start a new server thread
            yield "Starting a new server thread...\n"
            thread_handler.start_thread(target=server_func)
            yield "Server restarted successfully.\n"
        except Exception as e:
            yield "Error occurred: " + str(e)

    return Response(stream_with_context(generate()), content_type='text/plain; charset=utf-8')


# Route to check if the server thread is running
@app.route('/status', methods=['GET'])
def check_status():
    running = thread_handler.is_running()
    return jsonify({"running": running}), 200

if __name__ == '__main__':
    # Start the server thread by default when the app starts
    if not thread_handler.is_running():
        thread_handler.start_thread(target=server_func)

    # Run the Flask app
    app.run(host="0.0.0.0", debug=True, port=11435)  # Specify the port number here
