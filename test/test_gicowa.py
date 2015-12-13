# -*- coding: utf-8 -*-

import codecs
import mock
import os
import sys
import unittest

import gicowa.gicowa as gcw
import gicowa.impl.mail as mail
import gicowa.impl.output as output
from gicowa.impl.timestamp import Timestamp

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

class GicowaTests(unittest.TestCase):
    def test_output(self):
        mock_stdout = MockPrint()
        out = output.Output(mock_stdout.do_print)
        out.print_function = mock_stdout.do_print
        out.echoed = ""
        out.echo("hello")
        out.echo("hi")
        self.assertEqual(out.echoed, mock_stdout.printed)

    def test_timestamp(self):
        stamp = Timestamp({"YYYY": 2015,
                           "MM":   10,
                           "DD":   11,
                           "hh":   20,
                           "mm":   22,
                           "ss":   24})
        expected = "2015-10-11 20:22:24"
        actual = unicode(stamp)
        self.assertEqual(actual, expected)

    def test_watchlist(self):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("watchlist", "myUsername"), MockGithubLib(), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "\033[31mmySubscription1\033[0m\n" \
                 + "\033[31mmySubscription2\033[0m\n" \
                 + "\033[31mmySubscription3\033[0m\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_nocolor(self):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "watchlist", "myUsername"), MockGithubLib(), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "mySubscription1\n" \
                 + "mySubscription2\n" \
                 + "mySubscription3\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_lastrepocommits(self):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "lastrepocommits", "myRepo", "since", "2015", "10", "11",
                       "20", "08", "00"), MockGithubLib(), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        expected = "lastrepocommits myRepo since 2015-10-11 20:08:00\n" \
                 + "Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "Committed on myDate - myCommitter - myMessage\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    def test_lastwatchedcommits(self):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "lastwatchedcommits", "myUsername", "since", "2015", "10",
                       "11", "20", "08", "00"), MockGithubLib(), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
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

    @mock.patch("gicowa.impl.mail.MailSender.send_email")
    def test_mailto(self, send_email_mock):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "--mailto", "myMail@myDomain.com", "watchlist",
                       "myUsername"), MockGithubLib(), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        send_email_mock.assert_called_once_with("watchlist.", """\
watchlist myUsername
mySubscription1
mySubscription2
mySubscription3

Sent from %s.
""" % (os.uname()[1]))

    def test_print_utf8_string(self):
        utf8_string = "Tschüß!"
        gcw._print(utf8_string) # shouldn't raise

    def test_print_utf8_string_to_ascii_stdout(self):
        # Change stdout's encoding to ascii:
        default_stdout = sys.stdout
        sys.stdout = codecs.getwriter("ascii")(default_stdout)

        # Show that the default print fails to print a utf-8 string to an ascii stdout.
        # See http://nedbatchelder.com/text/unipain/unipain.html
        utf8_string = "Tschüß!"
        with self.assertRaises(UnicodeDecodeError):
            print(utf8_string)

        # Show that our _print is able to do it:
        gcw._print(utf8_string)

        # Restore stdout's encoding (to utf-8):
        sys.stdout = default_stdout
