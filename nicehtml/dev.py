import os
import time
from flask import Flask, render_template_string, Response
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread

# Flask setup
app = Flask(__name__)

# Store connected clients
clients = []

# Function to read index.nh and generate HTML content
def get_html_content():
    # Run the build.py script to generate the HTML content from index.nh
    os.system("python build.py")  # Ensure the index.html is generated
    # Now read the generated index.html content
    with open("index.html", "r") as f:
        return f.read()

# Serve the generated HTML page from index.nh (via build.py)
@app.route('/')
def home():
    html_content = get_html_content()
    return render_template_string(html_content)

# SSE Stream function
@app.route('/events')
def sse():
    def generate():
        while True:
            if hasattr(sse, 'should_update') and sse.should_update:
                yield 'data: reload\n\n'  # Send an event to reload the page
                sse.should_update = False
            time.sleep(1)

    return Response(generate(), content_type='text/event-stream')

# Function to watch for changes in index.nh
class Watcher:
    def __init__(self, path_to_watch):
        self.path_to_watch = path_to_watch
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_modified = self.on_modified
        self.observer = Observer()

    def on_modified(self, event):
        if event.src_path.endswith("index.nh"):
            print(f"File {event.src_path} has been modified, regenerating HTML...")
            os.system("python build.py")  # Run the build script to regenerate HTML
            # Notify all clients about the update
            self.notify_clients()

    def start(self):
        self.observer.schedule(self.event_handler, self.path_to_watch, recursive=False)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def notify_clients(self):
        # Notify all connected clients to refresh the page
        for client in clients:
            client.put("reload")

# Function to run the Flask app
def run_flask_app():
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)  # Disable the reloader

# Start Flask server in a separate thread
flask_thread = Thread(target=run_flask_app)
flask_thread.start()

# Watch for changes in the index.nh file
watcher = Watcher(path_to_watch='.')
watcher.start()

# Function to handle new SSE clients
@app.after_request
def after_request(response):
    # Keep track of each connected SSE client
    if 'text/event-stream' in response.content_type:
        clients.append(response)
    return response

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down server and file watcher...")
    watcher.stop()
    flask_thread.join()
