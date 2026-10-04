from flask import Flask, render_template, request, jsonify
import requests
import base64
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# 1. Load your secrets from the .env file
load_dotenv()

# 2. Initialize the Flask app
app = Flask(__name__)

# ==========================================
# DARAJA HELPER FUNCTIONS
# ==========================================

def get_access_token():
    """Goes to Safaricom and asks for the wristband."""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    # Combine key and secret, scramble them in base64
    encoded = base64.b64encode(
        f"{os.getenv('CONSUMER_KEY')}:{os.getenv('CONSUMER_SECRET')}".encode()
    ).decode()
    
    headers = {"Authorization": f"Basic {encoded}"}
    response = requests.get(url, headers=headers)
    
    # Return just the token string
    return response.json()["access_token"]

def send_stk_push(phone, amount):
    """Orders the pizza (sends the STK Push)."""
    token = get_access_token()
    
    # Safaricom requires a specific timestamp format
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # The password is a combination of Shortcode + Passkey + Timestamp
    password = base64.b64encode(
        f"{os.getenv('SHORTCODE')}{os.getenv('PASSKEY')}{timestamp}".encode()
    ).decode()

    # This is the payload (the order form) we send to Safaricom
    payload = {
        "BusinessShortCode": os.getenv("SHORTCODE"),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": os.getenv("SHORTCODE"),
        "PhoneNumber": phone,
        "CallBackURL": os.getenv("CALLBACK_URL"),
        "AccountReference": "TestPay",
        "TransactionDesc": "Test Payment"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    # Send the request and return the JSON response
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ==========================================
# FLASK ROUTES (The Doors)
# ==========================================

@app.route("/")
def home():
    """The Front Door: Shows the HTML form."""
    return render_template("index.html")

@app.route("/pay", methods=["POST"])
def pay():
    """The Action Door: Receives the form data and triggers the STK Push."""
    # Get the data the user typed into the HTML form
    phone = request.form.get("phone")
    amount = request.form.get("amount")
    
    # Call our Daraja function
    result = send_stk_push(phone, amount)
    
    # Send the result back to the browser so we can see it
    return f"STK Push triggered. Safaricom says: {result}"

@app.route("/callback", methods=["POST"])
def callback():
    print("Hello from callback url")
    """The Mailbox: Safaricom POSTs the receipt here."""
    data = request.get_json()
    
    # Print it to the terminal so we can see the raw JSON
    print("\n--- RECEIVED CALLBACK ---")
    print(data)
    print("-------------------------\n")

    try:
        # 1.Extract the data we care about from safaricom nested JSON
        stk_callback = data['Body']['stkCallback']
        result_code = stk_callback['ResultCode']
        # Only save to DB if the transaction was successful
        if result_code == 0:
            metadata = stk_callback['CallbackMetadata']['Item']
            # safaricom sends a list of items. we need to find those we want
            # this is a dictionary comprehension to make it easier to read
            items = {item['Name']: item.get('Value') for item in metadata}

            receipt = items.get('MpesaReceiptNumber')
            amount = items.get('Amount')
            phone = items.get('PhoneNumber')
            checkout_id = stk_callback['CheckoutRequestID']

            # 2. Connect to SQLite databse (it will create the file if it doesn't exist)
            conn = sqlite3.connect('payments.db')
            cursor = conn.cursor()

            # 3. Create table with UNIQUE receipt number (Idempotency)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mpesa_transaction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number TEXT UNIQUE,
                    amount REAL,
                    phone_number TEXT,
                    checkout_request_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEAFAULT CURRENT_TIMESTAMP
                )           
                
            ''')
            # 4. Insert the transaction
            cursor.execute('''
                INSERT INTO mpesa_transaction (receipt_number, amount, phone_number, checkout_request_id, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (receipt, amount, phone, checkout_id, 'SUCCESS'))

            # Save changes and close connection
            conn.commit()
            conn.close()

            print(f"SAVED TO DATABASE: Receipt {receipt} for KSH {amount}")
    except sqlite3.IntegrityError:
        # This catches the UNIQUE constraint violation. It means the receipt already exists
        print("DUPLICATE CALLBACK RECEIVED. Ignoring.")
    except Exception as e:
        print(f"Error processing callback: {e}")            
    # Tell Safaricom we received it
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

# ==========================================
# RUN THE APP
# ==========================================
if __name__ == "__main__":
    app.run(port=5000,debug=False, use_reloader=False)
