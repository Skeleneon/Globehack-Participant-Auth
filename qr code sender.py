import requests
import csv
import smtplib
import qrcode
import io
from io import StringIO
from email.message import EmailMessage
from email.mime.image import MIMEImage

# -----------------------------
# Load Google Sheets CSV
# -----------------------------
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfFwitdOSUI52bDmb4f7dCVRl6komI8SdzH_qm9PdsbvuWcvb_199vwXUVH6oZG6wu-xCqiZIfPDm5/pub?gid=0&single=true&output=csv"

attendants_file = {}

response = requests.get(url)
csv_data = response.content.decode("utf-8")
reader = csv.DictReader(StringIO(csv_data))

for row in reader:
    crInt = 0
    fInt = 0
    lInt = 0

    for n in row["created_at"]:
        if n.isdigit():
            crInt += int(n)

    for n in row["first_name"]:
        fInt += ord(n)

    for n in row["last_name"]:
        lInt += ord(n)

    participant_id = crInt + fInt + lInt
    attendants_file[participant_id] = row["email"]


# -----------------------------
# SMTP SETUP
# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"
EMAIL_PASSWORD = "mlle muud zyfc mity"


# -----------------------------
# SEND EMAILS WITH QR CODES
# -----------------------------
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for participant_id, email in attendants_file.items():

        # -------------------------
        # Create QR (in memory)
        # -------------------------
        qr_data = f"id={participant_id}&email={email}"
        qr = qrcode.make(qr_data)

        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # -------------------------
        # Build email
        # -------------------------
        msg = EmailMessage()
        msg["Subject"] = "Your Unique QR Code"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email

        msg.set_content("Your email client does not support HTML.")

        msg.add_alternative(f"""
        <html>
            <body>
                <h2>Your Unique QR Code</h2>
                <p>ID: {participant_id}</p>
                <p>Scan this QR code:</p>
                <img src="cid:qr_image">
            </body>
        </html>
        """, subtype="html")

        # -------------------------
        # Attach QR inline
        # -------------------------
img_data = buffer.read()

msg.add_attachment(
    img_data,
    maintype="image",
    subtype="png",
    filename="qr.png",
    cid="qr_image")

        # -------------------------
        # Send email
        # -------------------------
server.send_message(msg)

print(f"Sent to {email} | ID: {participant_id}")