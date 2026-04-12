import traceback
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
# LOGGING
# -----------------------------
def log(msg):
    print(f"[LOG] {msg}", flush=True)

def log_error(msg):
    print(f"[ERROR] {msg}", flush=True)
    traceback.print_exc()


# -----------------------------
# DISCORD BOT FUNCTION (FIXED)
# -----------------------------
def botSendMessage(msg, CHANNEL_ID):
    try:
        if not msg or not CHANNEL_ID:
            log("Discord skipped: empty message or channel ID")
            return

        url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        headers = {
            "Authorization": f"Bot {DISCORD_KEY}",
            "Content-Type": "application/json"
        }

        r = requests.post(url, json={"content": msg}, headers=headers)

        log(f"Discord status: {r.status_code}")
        log(f"Discord response: {r.text}")

        if r.status_code >= 300:
            raise Exception(f"Discord API failed: {r.status_code} {r.text}")

    except Exception as e:
        log_error(f"Discord send failed: {e}")


# -----------------------------
# LOAD PREVIOUS DATA (DICT SAFE)
# -----------------------------
try:
    with open("previous_data.dat", "rb") as f:
        previous_emails = pickle.load(f)
        if not isinstance(previous_emails, dict):
            previous_emails = {}
except:
    previous_emails = {}


# -----------------------------
# LOAD GOOGLE SHEETS CSV
# -----------------------------
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfFwitdOSUI52bDmb4f7dCVRl6komI8SdzH_qm9PdsbvuWcvb_199vwXUVH6oZG6wu-xCqiZIfPDm5/pub?gid=0&single=true&output=csv"

response = requests.get(url, timeout=15)
if response.status_code != 200:
    raise Exception("Failed to fetch Google Sheet CSV")

csv_data = response.text
reader = csv.DictReader(StringIO(csv_data))

attendants = []
current_emails = {}  # id -> email


# -----------------------------
# PARSE SHEET
# -----------------------------
for row in reader:
    try:
        participant_id = row["id"].strip()
        email = row["email"].strip().lower()

        if not participant_id or not email:
            continue

        current_emails[participant_id] = email

        raw_date = row["created_at"]
        try:
            dt = datetime.strptime(raw_date, "%m/%d/%Y %H:%M:%S")
            formatted_date = dt.strftime("%B %d, %Y")
        except:
            formatted_date = raw_date

        attendants.append({
            "id": participant_id,
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

    except Exception as e:
        log_error(f"Skipping row: {e}")


# -----------------------------
# FIND NEW ENTRIES
# -----------------------------
new_emails = {
    pid: email
    for pid, email in current_emails.items()
    if pid not in previous_emails
}

log("---- DEBUG ----")
log(f"Current: {len(current_emails)}")
log(f"Previous: {len(previous_emails)}")
log(f"New: {len(new_emails)}")
log(f"New IDs: {list(new_emails.keys())}")
log("----------------")

botSendMessage(
f"""---- DEBUG ----
Current: {len(current_emails)}
Previous: {len(previous_emails)}
New: {len(new_emails)}
New IDs: {list(new_emails.keys())}
----------------""",
EMAIL_CHANNEL_ID
)


if not new_emails:
    log("No new entries. Exiting.")
    botSendMessage("No new entries. Exiting.", EMAIL_CHANNEL_ID)
    exit()


# -----------------------------
# SMTP CONFIG
# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"

botmsg = ""


# -----------------------------
# SEND EMAILS
# -----------------------------
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for person in attendants:
        if person["id"] in new_emails:

            participant_id = person["id"]

            qr = qrcode.make(str(participant_id))

            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)

            msg = EmailMessage()
            msg["Subject"] = f"You're in, {person['first_name']} 🚀 | GlobeHack"
            msg["From"] = f"GlobeHack <{EMAIL_ADDRESS}>"
            msg["To"] = person["email"]

            msg.set_content("Your email client does not support HTML.")

            msg.add_alternative(f"""
<html>
<body>
<h2>Hi {person['first_name']}</h2>
<p>You're registered for GlobeHack.</p>
<img src="cid:qr_image">
</body>
</html>
""", subtype="html")

            msg.add_attachment(
                buffer.read(),
                maintype="image",
                subtype="png",
                filename="qr.png",
                cid="qr_image"
            )

            server.send_message(msg)

            log(f"Sent to {person['email']} | ID: {participant_id}")
            botmsg += f"Sent to {person['email']} | ID: {participant_id}\n"


# -----------------------------
# SEND FINAL DISCORD MESSAGE (SAFE)
# -----------------------------
if botmsg.strip():
    botSendMessage(botmsg, EMAIL_CHANNEL_ID)


# -----------------------------
# SAVE STATE SAFELY
# -----------------------------
log("Saving state...")

tmp_file = "previous_data.tmp"

with open(tmp_file, "wb") as f:
    pickle.dump(current_emails, f)

os.replace(tmp_file, "previous_data.dat")