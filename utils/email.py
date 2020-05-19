from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'config')))
from auth import USERNAME, PASSWORD

SMTPserver = 'smtp.gmail.com'

def send(author, content):
    text_subtype = 'plain'

    subject = 'Suggestion from user %s (id %d)' % (author.display_name, author.id)
    sender = 'interface.practice.bot@gmail.com'
    destination = ['dev.practice.bot@gmail.com']

    msg = MIMEText(content, text_subtype)
    msg['Subject'] = subject
    msg['From'] = sender
    conn = SMTP(SMTPserver)
    conn.set_debuglevel(False)
    conn.login(USERNAME, PASSWORD)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.quit()
