import os
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_socketio.namespace import Namespace
from flask_socketio import SocketIO

from database.db import SQLiteDB
from core.reasoning import ReasoningEngine
from core.session import Session, InputMessage, MsgStatus
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")
app.socketio = socketio
# Workspace root for all sessions
WORKSPACE_ROOT = Path(__file__).parent / "workspace"


@app.route("/screenshot", methods=["POST"])
def take_screenshot():
    data = request.get_json()
    html_content = data.get("html_content")
    image_id = data.get("image_id")

    if not html_content or not image_id:
        return jsonify({"error": "Missing html_content or image_id"}), 400

    images_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(images_dir, exist_ok=True)
    image_path = os.path.join(images_dir, f"{image_id}.png")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            page.screenshot(path=image_path)
            browser.close()
        return jsonify({"message": f"Screenshot saved to {image_path}"}), 200
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return jsonify({"error": str(e)}), 500


class ChatNamespace(Namespace):
    """Socket.IO chat namespace at /chat (Flask-SocketIO)."""

    def __init__(self, namespace="/chat"):
        super().__init__(namespace)

    def on_connect(self):
        logger.info(f"[/chat] client connected")

    def on_disconnect(self):
        logger.info(f"[/chat] client disconnected")

    def on_chat(self, message: dict):
        logger.info(f"[/chat] on_chat: {message}")
        print(f"[/chat] on_chat: {message}")
        db = SQLiteDB()

        try:
            # Create session with app manager
            sess = Session(
                db=db, 
                workspace_root=str(WORKSPACE_ROOT),
                **message
            )
            sess.create()

            inp = InputMessage(db=db, **message)
            inp.publish()
        except Exception as e:
            logger.exception("Failed to initialize session/input message")
            socketio.emit("chat", {"error": f"Init error: {e}"}, namespace="/chat")
            return

        try:
            system_prompt = message.get("system_prompt", "You are a helpful assistant.")
            engine = ReasoningEngine(
                system_prompt=system_prompt,
                input_message=inp,
                session=sess,
            )

            engine.run()
        except Exception as e:
            logger.exception("Error creating ReasoningEngine")
            try:
                sess.output_message.update_status(MsgStatus.error)
            except Exception:
                pass
            socketio.emit("chat", {"error": str(e)}, namespace="/chat")


socketio.on_namespace(ChatNamespace("/chat"))


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    socketio.run(app, host=host, port=port)