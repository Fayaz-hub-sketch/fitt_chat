import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_SYSTEM_PROMPT, MODEL_NAME

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

client = genai.Client(api_key=api_key)


def build_contents(history, message):
    contents = []

    for item in history[-20:]:
        role = item.get("role")
        text = item.get("text", "").strip()

        if role in {"user", "model"} and text:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=text)],
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )
    )

    return contents


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if not isinstance(history, list):
        history = []

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=CHATBOT_SYSTEM_PROMPT,
                thinking_level="minimal",
                max_output_tokens=800,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return jsonify({"error": "I couldn't generate a response. Please try again."}), 502

        return jsonify({"reply": answer})

    except Exception:
        app.logger.exception("Gemini API request failed.")
        return jsonify({
            "error": "Something went wrong while contacting the fitness assistant."
        }), 500


if __name__ == "__main__":
    app.run()
