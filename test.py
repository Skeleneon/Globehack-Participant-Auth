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
print(DISCORD_KEY)
botmsg = ""

# -----------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "acmsc.asu@gmail.com"




with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)