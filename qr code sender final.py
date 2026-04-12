import requests
import csv
import smtplib
import qrcode
import io
from io import StringIO
from email.message import EmailMessage
from datetime import datetime
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_KEY = os.getenv("DISCORD_KEY")
EMAIL_CHANNEL_ID = os.getenv("EMAIL_CHANNEL_ID")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# -----------------------------
# DISCORD BOT FUNCTION
# -----------------------------
def botSendMessage(msg, CHANNEL_ID):
    if not msg or not CHANNEL_ID:
        return

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    data = {"content": msg}
    headers = {
        "Authorization": f"Bot {DISCORD_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=data, headers=headers)
    print("Discord:", r.status_code)


# -----------------------------
# LOAD PREVIOUS EMAIL STATE
# -----------------------------
try:
    with open("previous_data.dat", "rb") as f:
        previous_emails = pickle.load(f)
except:
    previous_emails = set()


# -----------------------------
# LOAD GOOGLE SHEETS CSV
# -----------------------------
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfFwitdOSUI52bDmb4f7dCVRl6komI8SdzH_qm9PdsbvuWcvb_199vwXUVH6oZG6wu-xCqiZIfPDm5/pub?gid=0&single=true&output=csv"

response = requests.get(url, timeout=15)
if response.status_code != 200:
    raise Exception("Failed to fetch Google Sheet CSV")
csv_data = response.content.decode("utf-8")
reader = csv.DictReader(StringIO(csv_data))



attendants = []
current_emails = set()

# -----------------------------
# PARSE SHEET
# -----------------------------
for row in reader:
    email = row["email"].strip().lower()
    current_emails.add(email)

    # format date safely
    raw_date = row["created_at"]
    try:
        dt = datetime.strptime(raw_date, "%m/%d/%Y %H:%M:%S")
        formatted_date = dt.strftime("%B %d, %Y")
    except:
        formatted_date = raw_date

    attendants.append({
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": email,
        "major": row["major"],
        "t_shirt_size": row["t_shirt_size"],
        "dietary_preference": row["dietary_preference"],
        "dietary_other": row["dietary_other"],
        "team_preference": row["team_preference"],
        "created_at": formatted_date
    })


# -----------------------------
# FIND NEW EMAILS (FIXED CORE LOGIC)
# -----------------------------
newemails = current_emails - previous_emails

print("NEW EMAILS:", newemails)

if not newemails:
    print("No new entries. Exiting.")
    botSendMessage("No new entries. Exiting.", EMAIL_CHANNEL_ID)
    exit()


# -----------------------------
# SMTP CONFIG
# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"



# -----------------------------
# SEND EMAILS
# -----------------------------
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for person in attendants:
        if person["email"] in newemails:

            participant_id = person["id"]

            # QR CODE
            qr = qrcode.make(str(participant_id))

            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)
            img_data = buffer.read()

            # EMAIL
            msg = EmailMessage()
            msg["Subject"] = f"You're in, {person['first_name']} 🚀 | GlobeHack"
            msg["From"] = f"Globehack <{EMAIL_ADDRESS}>"
            msg["To"] = person["email"]

            msg.set_content("Your email client does not support HTML.")

            msg.add_alternative(f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial; background:#fdf8f4; margin:0;">

<div style="max-width:600px; margin:auto; background:white; padding:30px;">

<div style="background:#f3f4f6; padding:20px; text-align:center; border-left:4px solid #991b1b;">
    <h2>Your Check-In QR Code</h2>
    <img src="cid:qr_image" style="max-width:200px;">
</div>

<h1>Hi {person['first_name']},</h1>

<p>You are officially registered for <b>GlobeHack Season 1</b>.</p>

<div style="background:#f9fafb; padding:20px; margin-top:20px;">
    <h3>Your Registration Details</h3>
    <p><b>Name:</b> {person['first_name']} {person['last_name']}</p>
    <p><b>Email:</b> {person['email']}</p>
    <p><b>Major:</b> {person['major']}</p>
    <p><b>T-Shirt Size:</b> {person['t_shirt_size']}</p>
    <p><b>Dietary Preference:</b> {person['dietary_preference']}</p>
    <p><b>Other Dietary Notes:</b> {person['dietary_other']}</p>
    <p><b>Team Preference:</b> {person['team_preference']}</p>
    <p><b>Registered On:</b> {person['created_at']}</p>
</div>

<div style="margin-top:20px;">
    <h3>Next Steps</h3>
    <p>1. Join Discord</p>
    <a href="https://discord.gg/PA3XaxjxVH"
       style="display:block; background:#1e3a8a; color:white; padding:10px; text-align:center;">
       Join Server
    </a>

    <p>2. Build in Public → Use <b>#GlobeHackS1</b></p>
    <p>3. Stay tuned for updates</p>
</div>

<p style="margin-top:30px;"><b>April 18–19 · ASU Tempe</b></p>

<div style="margin-top:30px; background:#1e3a8a; color:white; text-align:center; padding:20px;">
    GlobeHack 2026 🚀
</div>

</div>
</body>
</html>
""", subtype="html")

            # attach QR
            msg.add_attachment(
                img_data,
                maintype="image",
                subtype="png",
                filename="qr.png",
                disposition="inline",
                cid="qr_image"
            )

            server.send_message(msg)
            print(f"Sent to {person['email']} | ID: {participant_id}")
            botSendMessage(f"Sent to {person['email']} | ID: {participant_id}", EMAIL_CHANNEL_ID)


# -----------------------------
# SAVE STATE SAFELY
# -----------------------------
print("saving current data...")

with open("previous_data.dat", "wb") as f:
    pickle.dump(current_emails, f)