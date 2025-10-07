import requests
import json

ACCESS_TOKEN = "EAA8I2M1DnTwBPgnZAx7iZCV8EH4Rm0nXHVkzX7fLUVDWOgilwibAC6yqTPQj7gZCuyaHoWZBZBss6LnA3q4pZCr0WeaMJLAS9kVGAMwa3KibyoLEa27eEKlFsGdSBJxkm4T9t4yjJW1ZCZBwKcWZAzau5ZCWYJZA7EGp8SW2FApCbRHPe5qP5j0e23BqFiWydbmhXCGEpDlaEdPHAHdr31bogyE7fg3A5MmIK1YFzaosQLIDy61zmQiaLq3j1hLsbcOgAZDZD"
PHONE_NUMBER_ID = "676833102178464"

def send_whatsapp_text(recipient_number, message_text):
    recipient_number = recipient_number.lstrip('+')
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message_text}
    }

    print("Sending payload:", json.dumps(payload, indent=2))
    response = requests.post(url, headers=headers, json=payload)

    print(f"Status: {response.status_code}")
    print("Response:", response.text)

    if response.ok:
        print(f"✅ Message sent to {recipient_number}")
    else:
        print(f"❌ Failed with error: {response.text}")

    return response

# Test call
send_whatsapp_text("919995324638", "Hello! This is a test message from Jezt AI.")
