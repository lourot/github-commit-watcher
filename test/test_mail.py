# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import mock
import unittest

import gicowa.impl.mail as mail

class MailTests(unittest.TestCase):
    @mock.patch("smtplib.SMTP")
    def test_send_email(self, smtp_constructor_mock):
        smtp_mock = mock.Mock()
        smtp_constructor_mock.return_value = smtp_mock

        subject = "subject"
        content = "content"
        dest = set(("dest1@domain.com", "dest2@domain.com"))

        mail_sender = mail.MailSender()
        mail_sender.dest = dest
        mail_sender.send_email(subject, content)

        smtp_constructor_mock.assert_called_once_with("localhost")

        expected_email = MIMEText(content, "plain", "utf-8")
        expected_email["Subject"] = "[gicowa] %s" % (subject)
        expected_email["From"] = "gicowa@lourot.com"
        expected_email["To"] = ", ".join(dest)
        smtp_mock.sendmail.assert_called_once_with("gicowa@lourot.com", dest,
                                                   expected_email.as_string())
