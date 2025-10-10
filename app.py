from flask import Flask, request, jsonify
import os
from send_offer_letter import send_offer_letter_html, send_welcome_mail
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
    api_url = os.getenv("API_URL")
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
    api_url = os.getenv("API_URL")
    payload = {
        "candidateId": candidateId,
        "hiring_stage": hiring_stage,
        "botSecretCode": os.getenv("BS1") + "#" + os.getenv("BS2")
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        data = resp.json()
        print(data)
    except Exception as e:
        print("Error calling updateHiringStage API:", e)
        return render_template_string("<h2>Server Error. Try again later.</h2>")

    # Handle different response cases
    if data.get("message") == "user_already_exist":
        html = """
        <html><body style='font-family:sans-serif;text-align:center;margin-top:10%;'>
        <h1 style='color:#E67E22;'>Already Registered</h1>
        <p>You have already been registered in our system.</p>
        <p>If you believe this is an error, please contact HR.</p>
        </body></html>
        """
        return render_template_string(html)

    elif data.get("message") == "candidate_not_found":
        html = """
        <html><body style='font-family:sans-serif;text-align:center;margin-top:10%;'>
        <h1 style='color:#C0392B;'>No Record Found</h1>
        <p>Sorry, we could not find your record. Please contact the admin.</p>
        </body></html>
        """
        return render_template_string(html)

    elif data.get("status") is True and data.get("code") == 200:
        emp = data["data"]
        threading.Thread(target=send_welcome_mail, args=(emp,), daemon=True).start()

        html = f"""
        <html><body style='font-family:sans-serif;text-align:center;margin-top:10%;'>
        <h1 style='color:#2ECC71;'>Welcome {emp["fullname"]}!</h1>
        <p>Your account has been created successfully.</p>
        <p>Login using the credentials sent to your email.</p>
        </body></html>
        """
        return render_template_string(html)

    else:
        html = """
        <html><body style='font-family:sans-serif;text-align:center;margin-top:10%;'>
        <h1 style='color:#7F8C8D;'>Unexpected Response</h1>
        <p>Something went wrong. Please contact support.</p>
        </body></html>
        """
        return render_template_string(html)


@app.route("/health", methods=["GET"])
def health_check():

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
