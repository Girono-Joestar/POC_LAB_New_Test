import qrcode
import os
import json
import csv


if not os.path.exists('qr_codes'):
    os.makedirs('qr_codes')


qr_data = f"https://poc-lab-new-test.vercel.app/"
img = qrcode.make(qr_data)
img.save(f"qr_codes/main.png")
