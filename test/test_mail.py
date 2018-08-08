# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
import mock
import unittest

import gicowa.impl.mail as mail

class MailTests(unittest.TestCase):
    @mock.patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp_constructor):
        mock_smtp = mock.Mock()
        mock_smtp_constructor.return_value = mock_smtp

        subject = "subject"
        content = "content"
        dest = set(("dest1@domain.com", "dest2@domain.com"))

        mail_sender = mail.MailSender()
        mail_sender.dest = dest
        mail_sender.send_email(subject, content)

        mock_smtp_constructor.assert_called_once_with("localhost")

        expected_email = MIMEText(content, "plain", "utf-8")
        expected_email["Subject"] = "[gicowa] %s" % (subject)
        expected_email["From"] = "gicowa@ghuser.io"
        expected_email["To"] = ", ".join(dest)
        mock_smtp.sendmail.assert_called_once_with("gicowa@ghuser.io", dest,
                                                   expected_email.as_string())
