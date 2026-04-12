import requests
import csv
import smtplib
import qrcode
import io
from io import StringIO
from email.message import EmailMessage
from datetime import datetime
import pickle

try:
    f=open("previous_data.dat","rb")

except:
    f=open("previous_data.dat","wb")
    data = {}
    pickle.dump(data,f)
    f.close()
    f=open("previous_data.dat","rb")

previous_data=pickle.load(f)

current_data={}







# -----------------------------
# LOAD GOOGLE SHEETS CSV
# -----------------------------
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfFwitdOSUI52bDmb4f7dCVRl6komI8SdzH_qm9PdsbvuWcvb_199vwXUVH6oZG6wu-xCqiZIfPDm5/pub?gid=0&single=true&output=csv"

attendants = []

response = requests.get(url)
csv_data = response.content.decode("utf-8")
reader = csv.DictReader(StringIO(csv_data))


    

for row in reader:
    current_data[row["id"]] = row["email"]

    # FORMAT DATE
    raw_date = row["created_at"]
    try:
        dt = datetime.strptime(raw_date, "%m/%d/%Y %H:%M:%S")
        formatted_date = dt.strftime("%B %d, %Y")  # e.g. April 04, 2026
    except:
        formatted_date = raw_date  # fallback if format breaks

    attendants.append({
        "id": row["id"],  # ✅ DIRECTLY FROM SHEET
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
        "major": row["major"],
        "t_shirt_size": row["t_shirt_size"],
        "dietary_preference": row["dietary_preference"],
        "dietary_other": row["dietary_other"],
        "team_preference": row["team_preference"],
        "created_at": formatted_date
    })





newemails = []

for i in current_data:
    if i not in previous_data:
        print("NEW ENTRY: ", current_data[i])
        newemails.append(current_data[i])

print("NEW EMAILS: ", newemails)

if len(newemails) == 0:
    print("No new entries. Exiting.")
    exit()  # Stop execution if no new emails


# -----------------------------
# SMTP CONFIG
# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"
EMAIL_PASSWORD = "yftc dcds efii oqiv"



# -----------------------------
# SEND EMAILS
# -----------------------------
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    for person in attendants:
        if person["email"] in newemails:
            participant_id = person["id"]

            # -------------------------
            # CREATE QR CODE (ID ONLY)
            # -------------------------
            qr = qrcode.make(str(participant_id))

            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)
            img_data = buffer.read()

            # -------------------------
            # BUILD EMAIL
            # -------------------------
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

    <!-- QR SECTION -->
    <div style="background:#f3f4f6; padding:20px; text-align:center; border-left:4px solid #991b1b;">
        <h2>Your Check-In QR Code</h2>
    
        <img src="cid:qr_image" style="max-width:200px;">
    </div>

    <h1>Hi {person['first_name']},</h1>

    <p>You are officially registered for <b>GlobeHack Season 1</b>.</p>

    <!-- REGISTRATION DETAILS -->
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

    <!-- NEXT STEPS -->
    <div style="margin-top:20px;">
        <h3>Next Steps</h3>
        <p>1. Join Discord</p>
        <a href="https://discord.gg/PA3XaxjxVH" style="display:block; background:#1e3a8a; color:white; padding:10px; text-align:center; text-decoration:none;">Join Server</a>

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

            # -------------------------
            # ATTACH QR IMAGE
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
            # SEND
            # -------------------------
            server.send_message(msg)
            print(f"Sent to {person['email']} | ID: {participant_id}")


print("saving current data...")
previous_data = current_data
f = open("previous_data.dat","wb")
pickle.dump(previous_data,f)
f.close()