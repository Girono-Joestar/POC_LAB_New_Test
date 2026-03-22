import qrcode
import os
import json
import csv

with open('data/exps.json', 'r') as f:
        exps = json.load(f)

if not os.path.exists('qr_codes'):
    os.makedirs('qr_codes')

for l in exps.keys():
    qr_data = f"https://pillowy-lottie-lampless.ngrok-free.dev/?exp={l}"
    img = qrcode.make(qr_data)
    img.save(f"qr_codes/{l}.png")
