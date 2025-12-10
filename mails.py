
# elan jwpj hbjk asug

import smtplib
from email.message import EmailMessage
def mail_send(to,subject,body):
    server = smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('yvn251579@gmail.com','elan jwpj hbjk asug')
    msg = EmailMessage()
    msg['FROM'] = 'yvn251579@gmail.com'
    msg['TO'] = to
    msg['SUBJECT'] = subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()
