from flask import Flask, request
import sqlite3, hmac, hashlib, json

app = Flask(__name__)
PAYME_SECRET_KEY = "SIZNING_PAYME_SECRET"

db = sqlite3.connect("cargo.db", check_same_thread=False)
cursor = db.cursor()

@app.route("/payme_callback", methods=["POST"])
def payme_callback():
    data = request.json
    signature = request.headers.get("X-Signature")
    
    raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode()
    sign = hmac.new(PAYME_SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
    if sign != signature:
        return {"error": "Invalid signature"}, 400

    if data.get("status") == "success":
        track_code = data.get("account")
        cursor.execute("UPDATE tracks SET paid=1 WHERE track_code=?", (track_code,))
        db.commit()
        return {"result": "OK"}
    return {"result": "ignored"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
