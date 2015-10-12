#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email.mime.text import MIMEText

class Mail:
    __instance = None # Singleton

    @classmethod
    def get(cls):
        if Mail.__instance is None:
            Mail()
        assert Mail.__instance is not None
        return Mail.__instance

    def __init__(self):
        if Mail.__instance is not None:
            assert False, "I'm a singleton."
        Mail.__instance = self

        self.smtplib = None
        self.server = "localhost"
        self.port = None
        self.sender = "gicowa@lourot.com"
        self.dest = set()
        self.password = None

    def send_result(self, command, output):
        """Sends command output by e-mail.
        """
        email = MIMEText(output)
        email["Subject"] = "[gicowa] %s." % (command)
        email["From"] = self.sender
        email["To"] = ", ".join(self.dest)
        if self.port is None or self.password is None:
            smtp = self.smtplib.SMTP(self.server)
        else:
            smtp = self.smtplib.SMTP_SSL(self.server, self.port)
            smtp.login(self.sender, self.password)
        try:
            smtp.sendmail(self.sender, self.dest, email.as_string())
        except self.smtplib.SMTPRecipientsRefused as e:
            e.args += ("%s addresses malformed?" % ", ".join(self.dest),)
            raise
        smtp.quit()
