import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from_mail = os.getenv('FROM_MAIL', 'sulaimanarizul@gmail.com')
from_password = os.getenv('MAIL_PASSWORD', 'hgmtagtonjlzuaic')

def send_mail(to, subject, html):
    print('sending mail')
    # send mail using smtplib
    msg = MIMEMultipart()
    msg['From'] = from_mail
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_mail, from_password)
    server.sendmail(from_mail, to, msg.as_string())
    server.quit()