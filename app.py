from flask import Flask, request, jsonify
import os
from send_offer_letter import send_offer_letter_html
from flask import Flask, request, render_template_string
import requests
from dotenv import load_dotenv
import threading
from flask_cors import CORS
load_dotenv()

app = Flask(__name__)
CORS(app)

# @app.route("/send-offer-letter", methods=["POST"])
# def send_offer_letter():
#     data = request.json or {}
#     if not data:
#         return jsonify({"status": False, "error": "Missing JSON payload"}), 400

#     try:
#         send_offer_letter_html(data)   # your function that builds PDF + sends email
#         return jsonify({"status": True, "message": "Offer letter email sent"}), 200
#     except Exception as e:
#         print("Error:", e)
#         return jsonify({"status": False, "error": str(e)}), 500

@app.route("/send-offer-letter", methods=["POST"])
def send_offer_letter():
    data = request.json or {}
    candidateId = data.get("candidateId")
    hiring_stage = "offer_letter_sent"
    if not data:
        return jsonify({"status": False, "error": "Missing JSON payload"}), 400
    # Call external API to update hiring stage
    api_url = "https://cerebree.com/server/chatbotapi/updateHiringStage"
    payload = {
        "candidateId": candidateId,
        "hiring_stage": hiring_stage,
        "botSecretCode": os.getenv("BS1") + "#" + os.getenv("BS2")
    }
    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        print("Hiring stage update response:", resp.status_code, resp.text)
    except Exception as e:
        print("Error calling updateHiringStage API:", e)

    # Launch the mail send in a background thread
    threading.Thread(target=send_offer_letter_html, args=(data,), daemon=True).start()

    # Return immediately
    return jsonify({"status": True, "message": "Offer letter queued"}), 200


@app.route("/accept_offer", methods=["GET"])
def accept_offer():
    candidateId = request.args.get("candidateId")
    hiring_stage = request.args.get("hiring_stage")
    print("Ping received for offer acceptance:")
    print(candidateId,hiring_stage)

    # Call external API to update hiring stage
    api_url = "https://cerebree.com/server/chatbotapi/updateHiringStage"
    payload = {
        "candidateId": candidateId,
        "hiring_stage": hiring_stage,
        "botSecretCode": os.getenv("BS1") + "#" + os.getenv("BS2")
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        print("Hiring stage update response:", resp.status_code, resp.text)
    except Exception as e:
        print("Error calling updateHiringStage API:", e)

    # Render thank you page
    html = f"""
    <html>
    <head>
        <title>Offer Accepted</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f9f9f9;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: #333;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            h1 {{ color: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Thank you!</h1>
            <p>We have received your acceptance.</p>
            <p>Our HR team will get back to you soon.</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/health", methods=["GET"])
def health_check():

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
