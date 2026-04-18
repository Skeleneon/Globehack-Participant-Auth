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
botmsg = ""


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

botmsg += "Script started\n"
log("Script started")
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
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYl1ZfsjlDBA0A0iU2NmkJcJXcr0pIHYIrXVpIX32IFZsYvXepaVhvew5k-BRHAg4N8aDStppqwnBb/pub?gid=0&single=true&output=csv"

response = requests.get(url, timeout=15)
if response.status_code != 200:
    botmsg += "Failed to fetch Google Sheet CSV\n"
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
        botmsg+= f"Error parsing row: {e}\n"
        log_error(f"Skipping row: {e}")


# -----------------------------
# FIND NEW ENTRIES
# -----------------------------
new_emails = {
    pid: email
    for pid, email in current_emails.items()
    if pid not in previous_emails
}
new_emails_limited = dict(list(new_emails.items())[:10])
new_emails = new_emails_limited  

new_emails={}

log("---- DEBUG ----")
log(f"Current: {len(current_emails)}")
log(f"Previous: {len(previous_emails)}")
log(f"New: {len(new_emails)}")
log(f"New IDs: {list(new_emails.keys())}")
log("----------------")

botmsg += f"""---- DEBUG ----
Current: {len(current_emails)}
Previous: {len(previous_emails)}
New: {len(new_emails)}
New IDs: {list(new_emails.keys())}
----------------\n"""


"""
if not new_emails:
    log("No new entries. Exiting.")
    botmsg += "No new entries. Exiting.\n"
    if botmsg.strip():
        botSendMessage(botmsg, EMAIL_CHANNEL_ID)
        
    exit()
"""

new_emails={}

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
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
  <title>GlobeHack 2026 — You're In</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap');
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:#08040c;font-family:'Inter',Arial,sans-serif;color:#fff;-webkit-font-smoothing:antialiased;}}
    @media (prefers-color-scheme: dark) {{
  body{{
    background: #08040c !important;
    color: #ffffff !important;
  }}      
  .wrapper {{
    background: #08040c !important;
  }}
}}                      
    .wrapper{{max-width:600px;margin:0 auto;background:#08040c;}}

    /* ── KEYFRAMES ── */
    @keyframes fade-rise{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
    @keyframes globe-spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
    @keyframes globe-pulse{{0%,100%{{filter:drop-shadow(0 0 30px rgba(200,60,255,.55)) drop-shadow(0 0 70px rgba(30,100,255,.4));transform:scale(1)}}50%{{filter:drop-shadow(0 0 55px rgba(220,80,255,.8)) drop-shadow(0 0 110px rgba(30,130,255,.6));transform:scale(1.04)}}}}
    @keyframes halo-spin{{from{{transform:rotate(0deg) scale(1.18)}}to{{transform:rotate(-360deg) scale(1.18)}}}}
    @keyframes halo-pulse{{0%,100%{{opacity:.55}}50%{{opacity:.85}}}}
    @keyframes grid-drift{{from{{background-position:0 0}}to{{background-position:38px 38px}}}}

    /* ── HERO BANNER ── */
    .hero-banner{{
      position:relative;overflow:hidden;
      background:radial-gradient(ellipse 140% 100% at 50% 110%, #08040c 42%, #1a0828 60%, #300a12 78%, #0a0612 100%);
      padding:52px 48px 56px;text-align:center;
    }}

    /* Grid overlay */
    .hero-banner::before{{
      content:'';position:absolute;inset:0;z-index:0;
      background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);
      background-size:38px 38px;
      animation:grid-drift 6s linear infinite;
    }}

    /* Radial vignette keep edges dark */
    .hero-banner::after{{
      content:'';position:absolute;inset:0;z-index:0;
      background:radial-gradient(ellipse 75% 75% at 50% 50%,transparent 35%,rgba(8,4,12,.75) 100%);
      pointer-events:none;
    }}

    .hero-wordmark{{
      position:relative;z-index:10;
      font-family:'Instrument Serif',serif;
      font-size:46px;line-height:.88;letter-spacing:-.5px;color:#fff;font-weight:400;
      text-shadow:0 0 40px rgba(200,80,255,.55),0 0 80px rgba(30,100,255,.35),0 2px 4px rgba(0,0,0,.9);
      margin-bottom:36px;
      animation:fade-rise .9s ease-out both;
    }}
    .hero-wordmark span{{color:rgba(255,255,255,.32);}}

    /* Globe wrapper — spins the image slowly */
    .globe-wrap{{
      position:relative;z-index:5;
      width:260px;height:260px;
      margin:0 auto 38px;
    }}

    /* Outer rotating halo ring — conic gradient */
    .globe-halo{{
      position:absolute;
      inset:-28px;
      border-radius:50%;
      background:conic-gradient(
        from 0deg,
        rgba(220,50,255,.0) 0%,
        rgba(220,50,255,.45) 12%,
        rgba(30,120,255,.6) 28%,
        rgba(0,200,255,.3) 38%,
        rgba(0,200,255,.0) 50%,
        rgba(200,40,255,.0) 62%,
        rgba(200,40,255,.35) 75%,
        rgba(30,80,255,.25) 88%,
        rgba(220,50,255,.0) 100%
      );
      animation:halo-spin 8s linear infinite, halo-pulse 4s ease-in-out infinite;
      filter:blur(14px);
    }}

    /* The actual globe image */
    .globe-img{{
      position:absolute;inset:0;
      width:100%;height:100%;
      border-radius:50%;
      object-fit:cover;
      animation:globe-spin 28s linear infinite, globe-pulse 5s ease-in-out infinite;
      -webkit-mask-image:radial-gradient(circle, black 90%, transparent 97%);
      mask-image:radial-gradient(circle, black 90%, transparent 97%);
      transform-origin:center center;
    }}

    /* Counter-rotating inner energy shimmer */
    .globe-shimmer{{
      position:absolute;inset:0;
      border-radius:50%;
      background:radial-gradient(circle at 38% 35%, rgba(255,120,120,.18) 0%, transparent 55%),
                  radial-gradient(circle at 62% 65%, rgba(80,160,255,.18) 0%, transparent 55%);
      animation:globe-spin 18s linear infinite reverse;
      mix-blend-mode:screen;
      pointer-events:none;
    }}

    /* Hero text */
    .hero-confirmation{{position:relative;z-index:10;animation:fade-rise .9s ease-out .3s both;}}
    .hero-eyebrow{{font-size:11px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:14px;}}
    .hero-headline{{font-family:'Instrument Serif',serif;font-size:50px;line-height:.93;letter-spacing:-1.6px;color:#fff;font-weight:400;margin-bottom:16px;text-shadow:0 0 30px rgba(200,80,255,.3),0 0 60px rgba(30,100,255,.2);}}
    .hero-headline em{{font-style:normal;color:rgba(255,255,255,.3);}}
    .hero-sub{{font-size:14px;line-height:1.7;color:rgba(255,255,255,.42);max-width:360px;margin:0 auto;}}

    /* ── CONTENT ── */
    .greeting{{padding:40px 48px 28px;border-top:1px solid rgba(255,255,255,.07);animation:fade-rise .8s ease-out .2s both;}}
    .greeting-name{{font-family:'Instrument Serif',serif;font-size:28px;color:#fff;font-weight:400;margin-bottom:8px;}}
    .greeting-copy{{font-size:14px;color:rgba(255,255,255,.46);line-height:1.75;}}
    .greeting-copy strong{{color:rgba(255,255,255,.82);font-weight:600;}}

    .qr-section{{
      margin:0 48px 28px;border-radius:14px;
      border:1px solid rgba(200,80,255,.2);
      background:linear-gradient(135deg,rgba(80,20,120,.18) 0%,rgba(20,60,160,.12) 100%);
      padding:32px 28px;text-align:center;
      animation:fade-rise .8s ease-out .3s both;position:relative;overflow:hidden;
    }}
    .qr-section::before{{content:'';position:absolute;inset:0;border-radius:14px;background:radial-gradient(ellipse 60% 55% at 50% 0%,rgba(200,80,255,.1) 0%,transparent 70%);pointer-events:none;}}
    .qr-label{{position:relative;font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:rgba(200,120,255,.75);margin-bottom:20px;}}
    .qr-img-wrap{{width:120px;height:120px;margin:0 auto 12px;border-radius:10px;overflow:hidden;border:1px solid rgba(180,80,255,.2);background:rgba(255,255,255,.05);display:flex;align-items:center;justify-content:center;position:relative;}}
    .qr-note{{font-size:12px;color:rgba(255,255,255,.27);margin-top:4px;position:relative;}}
    .checkin-time{{margin-top:20px;padding-top:20px;border-top:1px solid rgba(255,255,255,.06);position:relative;}}
    .checkin-label{{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:rgba(180,100,255,.55);margin-bottom:6px;}}
    .checkin-value{{font-family:'Instrument Serif',serif;font-size:22px;color:rgba(255,255,255,.85);}}

    .details-section{{margin:0 48px 28px;border-radius:14px;border:1px solid rgba(255,255,255,.07);background:rgba(255,255,255,.02);overflow:hidden;animation:fade-rise .8s ease-out .4s both;}}
    .details-header{{padding:16px 24px;border-bottom:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.02);}}
    .details-title{{font-size:11px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.28);}}
    .detail-row{{display:flex;justify-content:space-between;align-items:baseline;padding:12px 24px;border-bottom:1px solid rgba(255,255,255,.04);gap:16px;}}
    .detail-row:last-child{{border-bottom:none;}}
    .detail-key{{font-size:12px;color:rgba(255,255,255,.3);font-weight:500;white-space:normal;flex-shrink:0;}}
    .detail-val{{font-size:13px;color:rgba(255,255,255,.65);text-align:right;word-break:break-all;}}

    .steps-section{{margin:0 16px 28px;animation:fade-rise .8s ease-out .5s both;}}
    .steps-title{{font-family:'Instrument Serif',serif;font-size:24px;color:#fff;margin-bottom:20px;font-weight:400;}}
    .step{{display:flex;gap:16px;align-items:flex-start;margin-bottom:14px;}}
    .step-num{{width:26px;height:26px;border-radius:50%;border:1px solid rgba(180,80,255,.35);background:rgba(120,40,200,.12);display:flex;align-items:center;justify-content:center;font-size:11px;color:rgba(190,120,255,.7);font-weight:600;flex-shrink:0;margin-top:1px;}}
    .step-text{{font-size:14px;color:rgba(255,255,255,.52);line-height:1.65;padding-top:3px;}}
    .step-text strong{{color:rgba(255,255,255,.85);font-weight:600;}}

    .btn-discord{{display:block;margin:20px 48px 28px;padding:16px 28px;text-align:center;text-decoration:none;border-radius:10px;background:linear-gradient(135deg,rgba(120,40,200,.22) 0%,rgba(40,100,220,.14) 100%);border:1px solid rgba(180,80,255,.28);color:rgba(255,255,255,.88);font-size:14px;font-weight:500;letter-spacing:.03em;animation:fade-rise .8s ease-out .55s both;}}
    
      .btn-calendar{{
        display:block;
        margin:20px 48px 28px;
        padding:16px 28px;
        box-sizing:border-box;
        text-align:center;
        text-decoration:none;
        border-radius:10px;
        background:linear-gradient(135deg,rgba(0,140,255,.92) 0%,rgba(0,200,255,.92) 100%);
        border:1.5px solid rgba(0,120,255,.38);
        color:#fff;
        font-size:14px;
        font-weight:600;
        letter-spacing:.03em;
        animation:fade-rise .8s ease-out .56s both;
        box-shadow:0 2px 16px rgba(0,180,255,.13);
        transition:background 0.2s, box-shadow 0.2s;
      }}
      .btn-calendar:hover{{
        background:linear-gradient(135deg,rgba(0,160,255,1) 0%,rgba(0,220,255,1) 100%);
        box-shadow:0 4px 24px rgba(0,180,255,.22);
      }}
    .divider{{margin:0 48px 28px;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.07),transparent);}}
    .footer{{padding:24px 48px 48px;text-align:center;animation:fade-rise .8s ease-out .6s both;}}
    .footer-date{{font-family:'Instrument Serif',serif;font-size:18px;color:rgba(255,255,255,.42);margin-bottom:16px;}}
    .footer-date span{{color:rgba(255,255,255,.18);margin:0 8px;}}
    .footer-brand{{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.16);}}

    @media only screen and (max-width:480px){{
      .hero-banner,.greeting,.steps-section,.footer{{padding-left:24px;padding-right:24px;}}
      .qr-section,.details-section,.divider{{margin-left:24px;margin-right:24px;}}
      .btn-discord{{margin-left:24px;margin-right:24px;}}
      .hero-headline{{font-size:36px;}}
      .hero-wordmark{{font-size:34px;}}
      .globe-wrap{{width:200px;height:200px;}}
    }}
  </style>
</head>
<body style="background:#000;color:#000;">
<div class="wrapper" style="background:#08040c;color:#fff;">

  <!-- HERO -->
  <div class="hero-banner">
    
     <div class="hero-wordmark" style="color-scheme: dark; supported-color-schemes: dark; color: #777777;">GLOBE<br>HACK'26</div>

    <!-- Globe -->
    <div class="globe-wrap">
      <div class="globe-halo"></div>
      <img class="globe-img" src="cid:globe_graphic" alt="GlobeHack globe"/>
      <div class="globe-shimmer"></div>
    </div>

    <div class="hero-confirmation">
      <div class="hero-eyebrow", style=" color-scheme:dark; supported-color-schemes: dark; color: #777777;">Registration Confirmed</div>
      <div class="hero-headline", style="color-scheme: dark; supported-color-schemes: dark; color: #777777;">You're officially<br>in.</div>
      <div class="hero-sub", style=" color-scheme:dark; supported-color-schemes: dark; color: #777777 ;">Welcome to GlobeHack Season 1. Here's everything you need to show up ready.</div>
    </div>
  </div>

  <!-- GREETING -->
  <div class="greeting">
    <div class="greeting-name">Hi {person['first_name']},</div>
    <div class="greeting-copy">
      You are officially registered for <strong>GlobeHack Season 1</strong>.<br>
      Save this email — it has your check-in QR and all the info you need for the weekend.
    </div>
  </div>

  <!-- QR -->
  <div class="qr-section">
    <div class="qr-label">Your Check-In QR Code</div>
    <div class="qr-img-wrap">
      <img src="cid:qr_image" style="max-width:200px;">
    </div>
    <div class="qr-note">Show this QR code to check in at the event. This is also your meal plan QR code with 5 swipes.</div>
    <div class="checkin-time">
      <div class="checkin-label">Check-In Opens</div>
      <div class="checkin-value">Saturday · 8:00 AM</div>
    </div>
  </div>

  <!-- DETAILS -->
  <div class="details-section">
    <div class="details-header"><div class="details-title">Your Registration Details</div></div>
    <div class="detail-row"><div class="detail-key">Name:&nbsp;</div><div class="detail-val">{" " + person['first_name']} {person['last_name']}</div></div>
    <div class="detail-row"><div class="detail-key">Email:&nbsp;</div><div class="detail-val">{" " + person['email']}</div></div>
    <div class="detail-row"><div class="detail-key">Major:&nbsp;</div><div class="detail-val">{" " + person['major']}</div></div>
    <div class="detail-row"><div class="detail-key">T-Shirt Size:&nbsp;</div><div class="detail-val">{" " + person['t_shirt_size']}</div></div>
    <div class="detail-row"><div class="detail-key">Dietary Preference:&nbsp;</div><div class="detail-val">{" " + person['dietary_preference']}</div></div>
    <div class="detail-row"><div class="detail-key">Dietary Notes:&nbsp;</div><div class="detail-val">{" " + person['dietary_other']}</div></div>
    <div class="detail-row"><div class="detail-key">Team Preference:&nbsp;</div><div class="detail-val">{" " + person['team_preference']}</div></div>
    <div class="detail-row"><div class="detail-key">Registered On:&nbsp;</div><div class="detail-val">{" " + person['created_at']}</div></div>
  </div>

  <!-- STEPS -->
  <div class="steps-section">
    <div class="steps-title">Next Steps</div>
    <div class="step"><div class="step-nums" style="margin-top: 5px; font-size: 15px;color: #565459;">1.&nbsp;</div><div class="step-text">Join the <strong>Discord server</strong> — announcements, team matching, and all updates live there.</div></div>
    <div class="step"><div class="step-nums" style="margin-top: 5px; font-size: 15px;color: #565459;">2.&nbsp;</div><div class="step-text">Build in public → tag us with <strong>#GlobeHackS1</strong></div></div>
    <div class="step"><div class="step-nums" style="margin-top: 5px; font-size: 15px;color: #565459;">3.&nbsp;</div><div class="step-text">Stay tuned for updates leading up to the event.</div></div>
  </div>


  <a href="https://discord.gg/g2PhwDVVWt" class="btn-discord">Join the Discord Server →</a>

 
  <div class="divider"></div>

  <div class="footer">
    <div class="footer-date">April 18-19<span>·</span>ASU Tempe</div>
    <div class="footer-brand">GlobeHack 2026 🚀</div>
  </div>

</div>
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
            try:
                with open("globe.png", "rb") as g:
                    msg.add_attachment(
                        g.read(),
                        maintype="image",
                        subtype="png",
                        filename="globe.png",
                        cid="globe_graphic" # This must match the 'cid:' in your HTML
                    )
            except FileNotFoundError:
                log_error("Globe image file not found! Skipping attachment.")

            server.send_message(msg)

            log(f"Sent to {person['email']} | ID: {participant_id}")
            botmsg += f"Sent to {person['email']} | ID: {participant_id}\n"


log("Saving state...")
botmsg += "Saving state...\n"


if botmsg.strip():
    botSendMessage(botmsg, EMAIL_CHANNEL_ID)

tmp_file = "previous_data.tmp"

with open(tmp_file, "wb") as f:
    finished_emails = {**new_emails, **previous_emails}
    pickle.dump(finished_emails, f)

os.replace(tmp_file, "previous_data.dat")