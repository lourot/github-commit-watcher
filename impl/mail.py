#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import smtplib

def send_result(command, output, dest):
    """Sends command output by e-mail.
    """
    sender = "gicowa@lourot.com"
    email = MIMEText(output)
    email["Subject"] = "[gicowa] %s." % (command)
    email["From"] = sender
    email["To"] = dest
    smtp = smtplib.SMTP("localhost")
    try:
        smtp.sendmail(sender, dest, email.as_string())
    except smtplib.SMTPRecipientsRefused as e:
        e.args += ("%s address malformed?" % (dest),)
        raise
    smtp.quit()
