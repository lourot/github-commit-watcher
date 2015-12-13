#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import smtplib

import encoding

class MailSender:
    def __init__(self):
        self.server = "localhost"
        self.port = None
        self.sender = "gicowa@lourot.com"
        self.dest = set()
        self.password = None

    def send_result(self, command, output):
        """Sends command output by e-mail.
        """
        email = MIMEText(output, "plain", encoding.preferred)
        email["Subject"] = "[gicowa] %s." % (command)
        email["From"] = self.sender
        email["To"] = ", ".join(self.dest)
        if self.port is None or self.password is None:
            smtp = smtplib.SMTP(self.server)
        else:
            smtp = smtplib.SMTP_SSL(self.server, self.port)
            smtp.login(self.sender, self.password)
        try:
            smtp.sendmail(self.sender, self.dest, email.as_string())
        except smtplib.SMTPRecipientsRefused as e:
            e.args += ("%s addresses malformed?" % ", ".join(self.dest),)
            raise
        smtp.quit()
