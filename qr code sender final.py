import requests
import csv
import smtplib
import qrcode
import io
from io import StringIO
from email.message import EmailMessage

# -----------------------------
# LOAD GOOGLE SHEETS CSV
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
# SMTP CONFIG
# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"
EMAIL_PASSWORD = "mlle muud zyfc mity"


# -----------------------------
# SEND EMAILS
# -----------------------------
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for participant_id, email in attendants_file.items():

        # -------------------------
        # CREATE QR CODE (IN MEMORY)
        # -------------------------
        qr_data = f"id={participant_id}&email={email}"
        qr = qrcode.make(qr_data)

        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        img_data = buffer.read()

        # -------------------------
        # BUILD EMAIL
        # -------------------------
        msg = EmailMessage()
        msg["Subject"] = "Your Unique QR Code"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email

        msg.set_content("Your email client does not support HTML.")

        msg.add_alternative(f"""
                    <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>Innovation Hacks 2.0</title>
            <style>
                body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #0b0220;
                color: #ffffff;
                }}
                .container {{
                max-width: 700px;
                margin: auto;
                padding: 30px 20px;
                }}
                .title {{
                text-align: center;
                margin-top: 20px;
                }}
                .title h1 {{
                font-size: 42px;
                margin: 0;
                font-weight: bold;
                }}
                .highlight {{
                background: #e6c97a;
                color: #000;
                padding: 5px 10px;
                display: inline-block;
                }}
                .subtitle {{
                text-align: center;
                color: #aaa;
                margin-top: 10px;
                }}
                .card {{
                background: #140a35;
                border-radius: 12px;
                padding: 20px;
                margin-top: 25px;
                }}
                .center {{
                text-align: center;
                }}
                .qr-box {{
                background: #1c1047;
                padding: 20px;
                border-radius: 12px;
                margin-top: 20px;
                }}
                .info-grid {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
                }}
                .info-item {{
                flex: 1;
                background: #140a35;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                }}
                .section-title {{
                font-size: 12px;
                color: #aaa;
                letter-spacing: 1px;
                margin-bottom: 5px;
                }}
                .button {{
                display: block;
                text-align: center;
                margin: 30px auto;
                background: linear-gradient(90deg, #6a5cff, #b84cff);
                padding: 15px;
                border-radius: 25px;
                color: white;
                text-decoration: none;
                width: 250px;
                font-weight: bold;
                }}
                ul {{
                padding-left: 20px;
                }}
                li {{
                margin: 8px 0;
                }}
                .footer {{
                text-align: center;
                font-size: 12px;
                color: #777;
                margin-top: 30px;
                }}
            </style>
            </head>
            <body>

            <div class="container">

            <div class="title">
                <h1><span class="highlight">INNOVATION</span><br>HACKS 2.0</h1>
                <div class="subtitle">April 3rd – 5th, 2026 · ASU’s Largest Spring Hackathon</div>
            </div>

            <div class="card">
                <h2>Hey Aman, you're in 🎉</h2>
                <p>Your spot at <b>Innovation Hacks 2.0</b> is confirmed. Show this QR code at the door.</p>

                <div class="qr-box center">
                <h3>Your Check-in QR</h3>

                <!-- QR CODE REPLACEMENT -->
                <h2>Your Unique QR Code</h2>
                <p><b>ID:</b> {participant_id}</p>
                <p>Scan this QR code at entry:</p>
                <img src="cid:qr_image" alt="QR Code">

                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                <div class="section-title">DATES</div>
                <div>Apr 3–5<br>2026</div>
                </div>
                <div class="info-item">
                <div class="section-title">CHECK-IN</div>
                <div>6:30 PM<br>April 3rd</div>
                </div>
                <div class="info-item">
                <div class="section-title">LOCATION</div>
                <div>LSA-191<br>Tempe, AZ</div>
                </div>
            </div>

            <div class="card">
                <div class="section-title">YOUR REGISTRATION</div>
                <p><b>Name:</b> Aman Suhail</p>
                <p><b>School:</b> Arizona State University</p>
            </div>

            <div class="card">
                <div class="section-title">WHAT TO BRING</div>
                <ul>
                <li>This QR code (screenshot it)</li>
                <li>Student ID</li>
                <li>Laptop + charger</li>
                <li>Sleep is optional. The grind is not.</li>
                </ul>
            </div>

            <a href="#" class="button">VIEW EVENT DETAILS →</a>

            <div class="footer">
                Questions? help@innovationhacks.dev<br><br>
                © 2026 Innovation Hacks · Arizona State University
            </div>

            </div>

            </body>
        </html>
        """, subtype="html")

        # -------------------------
        # INLINE IMAGE ATTACHMENT
        # -------------------------
        msg.add_attachment(
            img_data,
            maintype="image",
            subtype="png",
            filename="qr.png",
            disposition="inline",
            cid="qr_image"
        )

        # -------------------------
        # SEND EMAIL
        # -------------------------
        server.send_message(msg)

        print(f"Sent to {email} | ID: {participant_id}")