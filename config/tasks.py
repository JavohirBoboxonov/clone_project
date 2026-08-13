from config.celery_app import celery_app
import smtplib
from email.mime.text import MIMEText
import os

@celery_app.task
def send_reset_code_task(email: str, code: str):
    msg = MIMEText(f"Sizning kodingiz: {code}\nKod 3 daqiqa davomida amal qiladi.")
    msg['Subject'] = "Parolni tiklash kodi"
    msg['From'] = os.getenv("MAIL_FROM")
    msg['To'] = email

    with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.sendmail(os.getenv("MAIL_FROM"), email, msg.as_string())