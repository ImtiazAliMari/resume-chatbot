from flask import Flask, request, jsonify, render_template_string
import fitz  # PyMuPDF
import requests
import json

app = Flask(__name__)

# === Replace with your Gemini API key ===
GEMINI_API_KEY = "AIzaSyBxwBFaCxAn0ssEaxZANUmIXi4WrdA9A3o"

# === PDF to Text ===
PDF_PATH = "cv.pdf"  # Make sure this file is uploaded to your Replit project

def extract_resume_text(path):
    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()[:16000]  # Gemini limit
    except Exception as e:
        print(f"[ERROR] Couldn't read PDF: {e}")
        return "Error reading resume."

RESUME_TEXT = extract_resume_text(PDF_PATH)

# === HTML Page ===
html_page = """
<!DOCTYPE html>
<html>
<head>
  <title>🤖 Resume Chatbot</title>
  <style>
    body { font-family: Arial; background: #eef2f7; padding: 40px; }
    .chat-box { max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .message { margin: 10px 0; }
    .user { font-weight: bold; color: #007bff; }
    .bot { color: #212529; }
    input[type="text"] { width: 80%; padding: 10px; border-radius: 8px; border: 1px solid #ccc; }
    button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; }
    #chat { max-height: 300px; overflow-y: auto; }
  </style>
</head>
<body>
  <div class="chat-box">
    <h2>🤖 Ask About Me (Resume Chatbot)</h2>
    <div id="chat"></div>
    <input type="text" id="userInput" placeholder="Ask a question..." />
    <button onclick="sendMessage()">Ask</button>
  </div>

  <script>
    async function sendMessage() {
      const input = document.getElementById("userInput");
      const message = input.value;
      if (!message) return;

      const chat = document.getElementById("chat");
      chat.innerHTML += `<div class='message user'>👤 You: ${message}</div>`;

      const res = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
      });

      const data = await res.json();
      chat.innerHTML += `<div class='message bot'>🤖 Bot: ${data.reply}</div>`;
      input.value = "";
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_page)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("message", "")
    print("\n=== [QUESTION] ===")
    print(question)

    prompt = f"""
You are a smart AI recruiter assistant. Use the following resume content to answer the recruiter's question:

Resume Content:
{RESUME_TEXT}

Question: {question}
Answer:
"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            answer = result['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            answer = "Sorry, there was an issue with the Gemini API."

        return jsonify({"reply": answer})

    except Exception as e:
        print(f"[EXCEPTION] Gemini error: {e}")
        return jsonify({"reply": "Sorry, something went wrong."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # Needed for Replit
