# -*- coding: utf-8 -*-

import gicowa.gicowa as gicowa
from gicowa.impl.mail import Mail as m
from gicowa.impl.output import Output as o
from gicowa.impl.timestamp import Timestamp
import os
import unittest

class MockGithubLib:
    class GithubException:
        pass

    class MockGithub:
        class MockGithubUser:
            def get_subscriptions(self):
                return (MockGithubRepo("mySubscription1"), MockGithubRepo("mySubscription2"),
                        MockGithubRepo("mySubscription3"))

        def get_user(self, login):
            return self.MockGithubUser()

        def get_repo(self, full_name_or_id):
            return MockGithubRepo(full_name_or_id)

    def Github(self):
        return self.MockGithub()

class MockGithubRepo:
    def __init__(self, full_name):
        self.full_name = full_name
        self.pushed_at = Timestamp({"YYYY": 2015,
                                    "MM":   10,
                                    "DD":   11,
                                    "hh":   20,
                                    "mm":   22,
                                    "ss":   24}).to_datetime()

    def get_commits(self, since):
        return (MockGithubCommit("mySha"),)

    def get_git_commit(self, sha):
        return MockGithubCommit("mySha")

class MockGithubCommit:
    def __init__(self, sha):
        self.sha = sha
        self.committer = MockGithubCommitter()
        self.message = "myMessage"

class MockGithubCommitter:
    def __init__(self):
        self.name = "myCommitter"
        self.date = "myDate"

class MockPrint:
    def __init__(self):
        self.printed = ""

    def do_print(self, text):
        self.printed += text + "\n"

class MockSmtplib:
    class SMTPRecipientsRefused:
        pass

    class MockSmtp:
        def __init__(self):
            self.sent = None
            self.sentfrom = None
            self.sentto = None

        def sendmail(self, sender, dest, content):
            self.sent = content
            self.sentfrom = sender
            self.sentto = dest

        def quit(self):
            pass

    def __init__(self):
        self.smtp = self.MockSmtp()

    def SMTP(self, server):
        return self.smtp

class GicowaTests(unittest.TestCase):
    def test_output(self):
        mock_stdout = MockPrint()
        o.get().print_function = mock_stdout.do_print
        o.get().echoed = ""
        o.get().echo("hello")
        o.get().echo("hi")
        self.assertEqual(o.get().echoed, mock_stdout.printed)

    def test_timestamp(self):
        stamp = Timestamp({"YYYY": 2015,
                           "MM":   10,
                           "DD":   11,
                           "hh":   20,
                           "mm":   22,
                           "ss":   24})
        expected = "2015-10-11 20:22:24"
        actual = str(stamp)
        self.assertEqual(actual, expected)

    def test_watchlist(self):
        m.get().dest = set()
        mock_stdout = MockPrint()
        o.get().print_function = mock_stdout.do_print
        cli = gicowa.Cli(("watchlist", "myUsername"), MockGithubLib())
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "\033[31mmySubscription1\033[0m\n" \
                 + "\033[31mmySubscription2\033[0m\n" \
                 + "\033[31mmySubscription3\033[0m\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_nocolor(self):
        m.get().dest = set()
        mock_stdout = MockPrint()
        o.get().print_function = mock_stdout.do_print
        cli = gicowa.Cli(("--no-color", "watchlist", "myUsername"), MockGithubLib())
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "mySubscription1\n" \
                 + "mySubscription2\n" \
                 + "mySubscription3\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_lastrepocommits(self):
        m.get().dest = set()
        mock_stdout = MockPrint()
        o.get().print_function = mock_stdout.do_print
        cli = gicowa.Cli(("--no-color", "lastrepocommits", "myRepo", "since", "2015", "10", "11",
                          "20", "08", "00"), MockGithubLib())
        cli.run()
        expected = "lastrepocommits myRepo since 2015-10-11 20:08:00\n" \
                 + "Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "Committed on myDate - myCommitter - myMessage\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_lastwatchedcommits(self):
        m.get().dest = set()
        mock_stdout = MockPrint()
        o.get().print_function = mock_stdout.do_print
        cli = gicowa.Cli(("--no-color", "lastwatchedcommits", "myUsername", "since", "2015", "10",
                          "11", "20", "08", "00"), MockGithubLib())
        cli.run()
        expected = "lastwatchedcommits myUsername since 2015-10-11 20:08:00\n" \
                 + "mySubscription1 - Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "mySubscription1 - Committed on myDate - myCommitter - myMessage\n" \
                 + "mySubscription2 - Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "mySubscription2 - Committed on myDate - myCommitter - myMessage\n" \
                 + "mySubscription3 - Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "mySubscription3 - Committed on myDate - myCommitter - myMessage\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_mailto(self):
        mock_smtplib = MockSmtplib()
        m.get().smtplib = mock_smtplib
        o.get().echoed = ""
        cli = gicowa.Cli(("--no-color", "--mailto", "myMail@myDomain.com", "watchlist",
                          "myUsername"), MockGithubLib())
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "mySubscription1\n" \
                 + "mySubscription2\n" \
                 + "mySubscription3\n" \
                 + "\nSent from %s.\n" % (os.uname()[1])
        actual = mock_smtplib.smtp.sent
        self.assertIn(expected, actual)
