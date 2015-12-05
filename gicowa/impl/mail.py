#!/usr/bin/env python
# -*- coding: utf-8 -*-

class MailSender:
    def __init__(self, smtplib, mimetextlib):
        """
        @param smtplib: Dependency. Inject smtplib.
        @param mimetextlib: Dependency. Inject email.mime.text.MIMEText.
        """
        self.__smtplib = smtplib
        self.__mimetextlib = mimetextlib
        self.server = "localhost"
        self.port = None
        self.sender = "gicowa@lourot.com"
        self.dest = set()
        self.password = None

    def send_result(self, command, output):
        """Sends command output by e-mail.
        """
        email = self.__mimetextlib(output, "plain", "utf-8")
        email["Subject"] = "[gicowa] %s." % (command)
        email["From"] = self.sender
        email["To"] = ", ".join(self.dest)
        if self.port is None or self.password is None:
            smtp = self.__smtplib.SMTP(self.server)
        else:
            smtp = self.__smtplib.SMTP_SSL(self.server, self.port)
            smtp.login(self.sender, self.password)
        try:
            smtp.sendmail(self.sender, self.dest, email.as_string())
        except self.__smtplib.SMTPRecipientsRefused as e:
            e.args += ("%s addresses malformed?" % ", ".join(self.dest),)
            raise
        smtp.quit()
