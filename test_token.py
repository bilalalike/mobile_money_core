import requests
import base64
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("CONSUMER_KEY")
secret = os.getenv("CONSUMER_SECRET")

#COMBINE THE KEY AND SECRET ENCODE IN BASE64
encoded = base64.b64encode(f"{key}:{secret}".encode()).decode()
#GO TO THE BOUNCER (SAFARICOM) AND ASK FOR A WRISTBAND
url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
headers = {"Authorization": f"Basic {encoded}"}

response = requests.get(url, headers=headers)
print(response.json())
