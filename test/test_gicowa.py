# -*- coding: utf-8 -*-

import codecs
import mock
import os
import sys
import unittest

import github

import gicowa.gicowa as gcw
import gicowa.impl.mail as mail
import gicowa.impl.output as output
import gicowa.impl.timestamp as timestamp

class MockPrint:
    def __init__(self):
        self.printed = ""

    def do_print(self, text):
        self.printed += text + "\n"

class GicowaTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(GicowaTests, self).__init__(*args, **kwargs)
        self.__mock_github = mock.Mock()
        self.__mock_github_user = mock.Mock()

    def setUp(self):
        mock_committer = lambda: None # ~ object with no properties (yet)
        mock_committer.name = "myCommitter"
        mock_committer.date = "myDate"
        mock_commit = lambda: None # ~ object with no properties (yet)
        mock_commit.committer = mock_committer
        mock_commit.message = "myMessage"
        mock_commit.sha = "mySha"

        def get_commits(since):
            return (mock_commit,)

        def get_git_commit(sha):
            return mock_commit

        repos = []
        for i in xrange(1, 3+1):
            repo = mock.Mock()
            repo.full_name = "mySubscription" + str(i)
            repo.pushed_at = timestamp.Timestamp({"YYYY": 2015,
                                                  "MM":   10,
                                                  "DD":   11,
                                                  "hh":   20,
                                                  "mm":   22,
                                                  "ss":   24}).to_datetime()
            repo.get_commits = get_commits
            repo.get_git_commit = get_git_commit
            repos.append(repo)

        def get_repo(full_name):
            for repo in repos:
                if repo.full_name == full_name:
                    return repo

        self.__mock_github_user.get_subscriptions.return_value = repos
        self.__mock_github.get_user.return_value = self.__mock_github_user
        self.__mock_github.get_repo = get_repo

        self.__mock_github.get_user.side_effect = None

    def test_output(self):
        mock_stdout = MockPrint()
        out = output.Output(mock_stdout.do_print)
        out.print_function = mock_stdout.do_print
        out.echoed = ""
        out.echo("hello")
        out.echo("hi")
        self.assertEqual(out.echoed, mock_stdout.printed)

    def test_timestamp(self):
        stamp = timestamp.Timestamp({"YYYY": 2015,
                                     "MM":   10,
                                     "DD":   11,
                                     "hh":   20,
                                     "mm":   22,
                                     "ss":   24})
        expected = "2015-10-11 20:22:24"
        actual = unicode(stamp)
        self.assertEqual(actual, expected)

    @mock.patch("github.Github")
    def test_watchlist(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(("watchlist", "myUsername"), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "\033[31mmySubscription1\033[0m\n" \
                 + "\033[31mmySubscription2\033[0m\n" \
                 + "\033[31mmySubscription3\033[0m\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    @mock.patch("github.Github")
    def test_nocolor(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "watchlist", "myUsername"), mail.MailSender(),
                      output.Output(mock_stdout.do_print))
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "mySubscription1\n" \
                 + "mySubscription2\n" \
                 + "mySubscription3\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    @mock.patch("github.Github")
    def test_lastrepocommits(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(
            ("--no-color", "lastrepocommits", "mySubscription1", "since", "2015", "10", "11", "20",
             "08", "00"), mail.MailSender(), output.Output(mock_stdout.do_print))
        cli.run()
        expected = "lastrepocommits mySubscription1 since 2015-10-11 20:08:00\n" \
                 + "Last commit pushed on 2015-10-11 20:22:24\n" \
                 + "Committed on myDate - myCommitter - myMessage\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    @mock.patch("github.Github")
    def test_lastwatchedcommits(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(
            ("--no-color", "lastwatchedcommits", "myUsername", "since", "2015", "10", "11", "20",
             "08", "00"), mail.MailSender(), output.Output(mock_stdout.do_print))
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
    @mock.patch("github.Github")
    def test_mailto(self, mock_github_constructor, mock_send_email):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "--mailto", "myMail@myDomain.com", "watchlist",
                       "myUsername"), mail.MailSender(), output.Output(mock_stdout.do_print))
        cli.run()
        mock_send_email.assert_called_once_with("watchlist.", """\
watchlist myUsername
mySubscription1
mySubscription2
mySubscription3

Sent from %s.
""" % (os.uname()[1]))

    @mock.patch("github.Github")
    def test_no_email_sent(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        self.__mock_github_user.get_subscriptions.return_value = ()
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--no-color", "--mailto", "myMail@myDomain.com", "watchlist",
                       "myUsername"), mail.MailSender(), output.Output(mock_stdout.do_print))
        cli.run()
        expected = "watchlist myUsername\n" \
                 + "No e-mail sent.\n"
        actual = mock_stdout.printed
        self.assertEqual(actual, expected)

    @mock.patch("github.Github")
    def test_credentials(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--credentials", "myUsername1:myPassword", "watchlist", "myUsername2"),
                      mail.MailSender(), output.Output(mock_stdout.do_print))
        cli.run()
        mock_github_constructor.assert_called_once_with("myUsername1", "myPassword")

    @mock.patch("github.Github")
    def test_bad_credentials(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        self.__mock_github.get_user.side_effect = github.GithubException(401, "data")
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--credentials", "myUsername1:myPassword", "watchlist", "myUsername2"),
                      mail.MailSender(), output.Output(mock_stdout.do_print))
        with self.assertRaises(github.GithubException):
            cli.run()

    @mock.patch("github.Github")
    def test_user_doesnt_exist(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        self.__mock_github.get_user.side_effect = github.GithubException(404, "data")
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--credentials", "myUsername1:myPassword", "watchlist", "myUsername2"),
                      mail.MailSender(), output.Output(mock_stdout.do_print))
        with self.assertRaises(github.GithubException):
            cli.run()

    @mock.patch("github.Github")
    def test_repo_doesnt_exist(self, mock_github_constructor):
        mock_github_constructor.return_value = self.__mock_github
        self.__mock_github.get_repo = mock.Mock(side_effect=github.GithubException(404, "data"))
        mock_stdout = MockPrint()
        cli = gcw.Cli(("lastrepocommits", "mySubscription1", "since", "2015", "10", "11", "20",
                       "08", "00"), mail.MailSender(), output.Output(mock_stdout.do_print))
        with self.assertRaises(github.GithubException):
            cli.run()

    @mock.patch("gicowa.impl.persistence.Memory.save")
    @mock.patch("github.Github")
    def test_persist(self, mock_github_constructor, mock_save):
        mock_github_constructor.return_value = self.__mock_github
        mock_stdout = MockPrint()
        cli = gcw.Cli(
            ("--persist", "lastrepocommits", "mySubscription1", "since", "2015", "10", "11", "20",
             "08", "00"), mail.MailSender(), output.Output(mock_stdout.do_print))
        cli.run()
        mock_save.assert_called_once_with()

    def test_sincelast(self):
        """Tests the sincelast functionality in _since_command decorator.
        """
        now = lambda: None # ~ object with no properties (yet)
        now.year =   2015
        now.month =  12
        now.day =    20
        now.hour =   19
        now.minute = 46
        now.second = 24

        # See http://www.voidspace.org.uk/python/mock/examples.html#partial-mocking :
        with mock.patch("gicowa.impl.timestamp.datetime.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = now

            class MyCli:
                def __init__(self):
                    self._output = output.Output(MockPrint().do_print)
                    self._memory = lambda: None # ~ object with no properties (yet)
                    self._memory.timestamps = {"my_command my_argument1": {"YYYY": 2015,
                                                                           "MM":   10,
                                                                           "DD":   11,
                                                                           "hh":   20,
                                                                           "mm":   22,
                                                                           "ss":   24}}

                    self.last_result = None

                @gcw._since_command("my_argument")
                def my_command(self, args, since):
                    self.last_result = since

            args = lambda: None # ~ object with no properties (yet)
            args.command = "my_command"
            args.my_argument = "my_argument1"
            args.sincelast = True

            # Last command in memory:
            my_cli = MyCli()
            my_cli.my_command(args)
            self.assertEqual(my_cli.last_result, timestamp.Timestamp({"YYYY": 2015,
                                                                      "MM":   10,
                                                                      "DD":   11,
                                                                      "hh":   20,
                                                                      "mm":   22,
                                                                      "ss":   24}))

            # Last command not in memory:
            args.my_argument = "my_argument2"
            my_cli.my_command(args)
            self.assertEqual(my_cli.last_result, timestamp.Timestamp({"YYYY": 2015,
                                                                      "MM":   12,
                                                                      "DD":   20,
                                                                      "hh":   19,
                                                                      "mm":   46,
                                                                      "ss":   24}))

    def test_help(self):
        mock_stdout = MockPrint()
        cli = gcw.Cli(("--help",), mail.MailSender(), output.Output(mock_stdout.do_print))
        with self.assertRaises(SystemExit):
            cli.run()

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
