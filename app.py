from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 1. The front door: shows the form
@app.route("/")
def home():
    return render_template("index.html")

# 2. The button: this is where we WILL send the STK push later
@app.route("/pay", methods=["POST"])
def pay():
    phone = request.form.get("phone")
    amount = request.form.get("amount")
    return f"Received phone: {phone}, amount: {amount}. (STK Push goes here later)"

# 3. The mailbox: Safaricom will POST the receipt here
@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print("RECEIVED CALLBACK:", data)
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

if __name__ == "__main__":
    app.run(port=5000)
