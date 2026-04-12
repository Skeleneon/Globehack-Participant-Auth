import requests
import csv
import smtplib
import qrcode
import io
from io import StringIO
from email.message import EmailMessage
from datetime import datetime
import pickle


url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfFwitdOSUI52bDmb4f7dCVRl6komI8SdzH_qm9PdsbvuWcvb_199vwXUVH6oZG6wu-xCqiZIfPDm5/pub?gid=0&single=true&output=csv"

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


response = requests.get(url)
csv_data = response.content.decode("utf-8")
reader = csv.DictReader(StringIO(csv_data))


for row in reader:   
    current_data[row["id"]] = row["email"]

newemails = []

for i in current_data:
    if i not in previous_data:
        print("NEW ENTRY: ", current_data[i])
        newemails.append(current_data[i])


print("NEW EMAILS: ", newemails)















"""
previous_data = current_data
f = open("previous_data.dat","wb")
pickle.dump(previous_data,f)
f.close()
"""