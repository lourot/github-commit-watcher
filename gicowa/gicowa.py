#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import github
import os
import socket
import sys
import traceback

from __init__ import __version__
import impl.encoding
import impl.mail
import impl.output
import impl.persistence
from impl.timestamp import Timestamp

class Cli:
    def __init__(self, argv, githublib, mail_sender, output):
        """Main class.
        @param githublib: Dependency. Inject github.
        @param mail_sender: Dependency. Inject an instance of impl.mail.MailSender.
        @param output: Dependency. Inject an instance of impl.output.Output.
        """
        self.errorto = None
        self.__argv = argv
        self.__githublib = githublib
        self.__github = None
        self.__mail_sender = mail_sender
        self.__output = output
        self.__memory = impl.persistence.Memory()

    def run(self):
        parser = argparse.ArgumentParser(description="watch GitHub commits easily")

        parser.add_argument("--version", action="version",
                            version="%(prog)s version " + __version__)

        parser.add_argument("--no-color", action="store_true", help="disable color in output")

        credentials_option = "--credentials"
        parser.add_argument(credentials_option,
                            help="your GitHub login and password (e.g. 'AurelienLourot:password')")

        parser.add_argument("--mailto",
                            help="e-mail address to which the output should be sent in any case "
                            + "(e.g. 'aurelien.lourot@gmail.com')")
        parser.add_argument("--mailfrom",
                    help="e-mail server and credentials from which the output should be "
                    + "sent (e.g. 'smtp.googlemail.com:465:aurelien.lourot@gmail.com:password')")
        parser.add_argument("--errorto",
                            help="e-mail address to which the output should be sent in case of an "
                            + "error (e.g. 'aurelien.lourot@gmail.com')")

        parser.add_argument(self._persist_option, action="store_true",
                    help="gicowa will keep track of the last commands run in %s" %
                            (self.__memory.filename))

        subparsers = parser.add_subparsers(help="available commands")

        descr = "list repos watched by a user"
        parser_watchlist = subparsers.add_parser("watchlist", description=descr, help=descr)
        parser_watchlist.set_defaults(command="watchlist", impl=self.__watchlist)
        self._add_argument_watcher_name(parser_watchlist)

        descr = "list last commits on a repo"
        parser_lastrepocommits = subparsers.add_parser("lastrepocommits", description=descr,
                                                       help=descr)
        parser_lastrepocommits.set_defaults(command="lastrepocommits", impl=self.__lastrepocommits)
        parser_lastrepocommits.add_argument("repo",
                help="repository's full name (e.g. 'AurelienLourot/github-commit-watcher')")
        self._add_arguments_since_committer_timestamp(parser_lastrepocommits)

        descr = "list last commits watched by a user"
        parser_lastwatchedcommits = subparsers.add_parser("lastwatchedcommits", description=descr,
                                                          help=descr)
        parser_lastwatchedcommits.set_defaults(command="lastwatchedcommits",
                                               impl=self.__lastwatchedcommits)
        self._add_argument_watcher_name(parser_lastwatchedcommits)
        self._add_arguments_since_committer_timestamp(parser_lastwatchedcommits)

        args = parser.parse_args(self.__argv)

        if args.mailfrom is not None:
            mailfrom = args.mailfrom.split(":", 3)
            try:
                self.__mail_sender.server = mailfrom[0]
                self.__mail_sender.port = mailfrom[1]
                self.__mail_sender.sender = mailfrom[2]
                self.__mail_sender.password = mailfrom[3]
            except IndexError as e:
                e.args += ("Bad mailfrom syntax.",)
                raise
        if args.mailto is not None:
            self.__mail_sender.dest.add(args.mailto)
        self.errorto = args.errorto

        self.__output.colored = not args.no_color

        if args.credentials is not None:
            credentials = args.credentials.split(":", 1)
            try:
                self.__github = self.__githublib.Github(credentials[0], credentials[1])
            except IndexError as e:
                e.args += ("Bad credentials' syntax.",)
                raise
        else:
            self.__github = self.__githublib.Github()

        try:
            args.impl(args)
        except self.__githublib.GithubException as e:
            if e.status == 401 and args.credentials is not None:
                e.args += ("Bad credentials?",)
            if e.status == 403 and args.credentials is None:
                e.args += ("API rate limit exceeded? Use the %s option." % (credentials_option),)
            raise
        except socket.gaierror as e:
            e.args += ("No internet connection?",)
            raise

        if len(self.__mail_sender.dest):
            email_sent = _send_output_by_mail_if_necessary(self.__mail_sender, self.__output,
                                                           args.command)
            if not email_sent:
                self.__output.echo("No e-mail sent.")

        if args.persist:
            self.__memory.save()

    @classmethod
    def _add_argument_watcher_name(cls, parser):
        """Adds an argument corresponding to a watcher's user name to an argparse parser.
        """
        parser.add_argument("username", help="watcher's name (e.g. 'AurelienLourot')")

    @classmethod
    def _add_arguments_since_committer_timestamp(cls, parser):
        """Adds arguments corresponding to a "since" committer timestamp to an argparse parser.
        """
        subparsers = parser.add_subparsers(help="oldest committer UTC timestamp to consider")

        descr = "explicit"
        parser_since = subparsers.add_parser("since", description=descr, help=descr)
        since = parser_since.add_argument_group(" ".join(zip(*Timestamp.fields)[0]),
                                                "(e.g. '2015 07 05 09 12 00')")
        parser_since.set_defaults(sincelast=False)
        for field in Timestamp.fields:
            since.add_argument(field[0], help=field[1])

        descr = "use last time run with %s" % (cls._persist_option)
        parser_sincelast = subparsers.add_parser("sincelast", description=descr, help=descr)
        parser_sincelast.set_defaults(sincelast=True)

    def __watchlist(self, args):
        """Implements 'watchlist' command.
        Prints all watched repos of 'args.username'.

        @param args: from argparse.
        """
        command = args.command + " " + args.username
        self.__output.echo(command)

        for repo in self.__get_watchlist(args.username):
            self.__output.echo(self.__output.red(repo))

    def _since_command(command_argname):
        """Decorator for commands that require a 'since' argument.

        @param command_argname: Name of args's property containing args's command argument.
        """
        def wrapper(func):
            def decorated(self, args):
                """
                @param args: from argparse.
                """
                now = Timestamp()
                command = args.command + " " + getattr(args, command_argname)
                if not args.sincelast:
                    since = Timestamp(args)
                else:
                    try:
                        since = Timestamp(self.__memory.timestamps[command])
                    except KeyError as e: # this command gets executed for the first time
                        since = now
                self.__output.echo(command + " since " + unicode(since))

                result = func(self, args, since)

                # Remember this last execution:
                self.__memory.timestamps[command] = now.data

                return result

            return decorated
        return wrapper

    @_since_command("repo")
    def __lastrepocommits(self, args, since):
        """Implements 'lastrepocommits' command.
        Prints all commits on 'args.repo' with committer timestamp bigger than
        'args.YYYY,MM,DD,hh,mm,ss'.

        @param args: from argparse.
        @param since: from decoration.
        """
        pushed = self.__has_been_pushed(args.repo, since.to_datetime())
        if pushed is not None:
            self.__output.echo(pushed)
        for commit in self.__get_last_commits(args.repo, since.to_datetime()):
            self.__output.echo(commit)

    @_since_command("username")
    def __lastwatchedcommits(self, args, since):
        """Implements 'lastwatchedcommits' command.
        Prints all commits on repos watched by 'args.username' with committer timestamp bigger than
        'args.YYYY,MM,DD,hh,mm,ss'.

        @param args: from argparse.
        @param since: from decoration.
        """
        for repo in self.__get_watchlist(args.username):
            pushed = self.__has_been_pushed(repo, since.to_datetime())
            if pushed is not None:
                self.__output.echo("%s - %s" % (self.__output.red(repo), pushed))
            for commit in self.__get_last_commits(repo, since.to_datetime()):
                self.__output.echo("%s - %s" % (self.__output.red(repo), commit))

    def __get_watchlist(self, username):
        """Returns list of all watched repos of 'username'.
        """
        try:
            user = self.__github.get_user(username)
        except self.__githublib.GithubException as e:
            if e.status == 404:
                e.args += ("%s user doesn't exist?" % (username),)
            raise

        return [repo.full_name for repo in user.get_subscriptions()]

    def __get_last_commits(self, repo_full_name, since):
        """Returns list of all commits on 'repo_full_name' with committer timestamp bigger than 'since'.
        """
        repo = self.__get_repo(repo_full_name)
        result = []
        for i in repo.get_commits(since=since):
            commit = repo.get_git_commit(i.sha)
            result.append("Committed on %s - %s - %s"
                          % (self.__output.green(commit.committer.date),
                             self.__output.blue(commit.committer.name), commit.message))
        return result

    def __has_been_pushed(self, repo_full_name, since):
        """Returns string describing last push timestamp of 'repo_full_name''s last commit if after
        'since'. Returns None otherwise.
        """
        repo = self.__get_repo(repo_full_name)
        if repo.pushed_at >= since:
            return "Last commit pushed on " + self.__output.green(repo.pushed_at)

    def __get_repo(self, full_name):
        """Returns github repository. Raises if couldn't be found.
        """
        try:
            return self.__github.get_repo(full_name)
        except self.__githublib.GithubException as e:
            if e.status == 404:
                e.args += ("%s repo doesn't exist?" % (full_name),)
            raise

    _persist_option = "--persist"

def _send_output_by_mail_if_necessary(mail_sender, output, email_subject):
    """Returns True if an e-mail was sent.
    @param mail_sender: Dependency. Inject an instance of impl.mail.MailSender.
    @param output: Dependency. Inject an instance of impl.output.Output.
    """
    if output.echoed.count("\n") <= 1:
        return False
    email_content = output.echoed + "\nSent from %s.\n" % (os.uname()[1])
    mail_sender.send_result(email_subject, email_content)
    output.echo("Sent by e-mail to %s" % ", ".join(mail_sender.dest))
    return True

def _print(text):
    """coding/decoding-friendly version of print().
    See http://nedbatchelder.com/text/unipain/unipain.html
    @param text: Must be either a unicode or a utf-8 str.
    """
    unicode_text = text
    if isinstance(unicode_text, str):
        unicode_text = text.decode(impl.encoding.preferred, "replace")

    try:
        print(text)
        return
    except UnicodeDecodeError:
        pass
    except UnicodeEncodeError:
        pass

    # Well, let's make it ascii then:
    ascii_text = unicode_text.encode("ascii", "replace")
    print(ascii_text)

def main():
    mail_sender = impl.mail.MailSender()
    output = impl.output.Output(_print)
    cli = Cli(sys.argv[1:], github, mail_sender, output)
    try:
        cli.run()
    except Exception as e:
        error_msg = "Oops, an error occured.\n" + "\n".join(unicode(i) for i in e.args) + "\n\n"
        error_msg += traceback.format_exc()
        try:
            output.echo(error_msg)
            if cli.errorto is not None:
                mail_sender.dest.add(cli.errorto)
            if len(mail_sender.dest):
                _send_output_by_mail_if_necessary(mail_sender, output, "error")
        except:
            _print(error_msg)
        raise
