#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import github
import os
import socket
import smtplib
import sys
import traceback
from __init__ import __version__
from impl.mail import Mail as m
from impl.output import Output as o
from impl.persistence import Persistence as p
from impl.timestamp import Timestamp

class Cli:
    def __init__(self, argv, githublib):
        self.errorto = None
        self.__argv = argv
        self.__githublib = githublib
        self.__github = None

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
                    help="gicowa will keep track of the last commands run in %s" % (p.filename))

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
                m.get().server = mailfrom[0]
                m.get().port = mailfrom[1]
                m.get().sender = mailfrom[2]
                m.get().password = mailfrom[3]
            except IndexError as e:
                e.args += ("Bad mailfrom syntax.",)
                raise
        if args.mailto is not None:
            m.get().dest.add(args.mailto)
        self.errorto = args.errorto

        o.get().colored = not args.no_color

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

        if len(m.get().dest):
            if o.get().echoed.count("\n") > 1:
                # FIXME this code is duplicated:
                email_content = o.get().echoed + "\nSent from %s.\n" % (os.uname()[1])
                m.get().send_result(args.command, email_content)
                o.get().echo("Sent by e-mail to %s" % ", ".join(m.get().dest))
            else:
                o.get().echo("No e-mail sent.")

        if args.persist:
            p.get().save()

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
        """
        command = args.command + " " + args.username
        o.get().echo(command)

        for repo in self.__get_watchlist(args.username):
            o.get().echo(o.get().red(repo))

    def __lastrepocommits(self, args):
        """Implements 'lastrepocommits' command.
        Prints all commits on 'args.repo' with committer timestamp bigger than
        'args.YYYY,MM,DD,hh,mm,ss'.
        """
        # FIXME this code is duplicated:
        now = Timestamp()
        command = args.command + " " + args.repo
        if not args.sincelast:
            since = Timestamp(args)
        else:
            try:
                since = Timestamp(p.get().timestamps[command])
            except KeyError as e: # this command gets executed for the first time
                since = now
        o.get().echo(command + " since " + str(since))

        pushed = self.__has_been_pushed(args.repo, since.to_datetime())
        if pushed is not None:
            o.get().echo(pushed)
        for commit in self.__get_last_commits(args.repo, since.to_datetime()):
            o.get().echo(commit)

        # Remember this last execution:
        p.get().timestamps[command] = now.data

    def __lastwatchedcommits(self, args):
        """Implements 'lastwatchedcommits' command.
        Prints all commits on repos watched by 'args.username' with committer timestamp bigger than
        'args.YYYY,MM,DD,hh,mm,ss'.
        """
        # FIXME this code is duplicated:
        now = Timestamp()
        command = args.command + " " + args.username
        if not args.sincelast:
            since = Timestamp(args)
        else:
            try:
                since = Timestamp(p.get().timestamps[command])
            except KeyError as e: # this command gets executed for the first time
                since = now
        o.get().echo(command + " since " + str(since))

        for repo in self.__get_watchlist(args.username):
            pushed = self.__has_been_pushed(repo, since.to_datetime())
            if pushed is not None:
                o.get().echo("%s - %s" % (o.get().red(repo), pushed))
            for commit in self.__get_last_commits(repo, since.to_datetime()):
                o.get().echo("%s - %s" % (o.get().red(repo), commit))

        # Remember this last execution:
        p.get().timestamps[command] = now.data

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
        # FIXME this code is duplicated:
        try:
            repo = self.__github.get_repo(repo_full_name)
        except self.__githublib.GithubException as e:
            if e.status == 404:
                e.args += ("%s repo doesn't exist?" % (repo_full_name),)
            raise

        result = []
        for i in repo.get_commits(since=since):
            commit = repo.get_git_commit(i.sha)
            result.append("Committed on %s - %s - %s"
                          % (o.get().green(commit.committer.date),
                             o.get().blue(commit.committer.name), commit.message))
        return result

    def __has_been_pushed(self, repo_full_name, since):
        """Returns string describing last push timestamp of 'repo_full_name''s last commit if after
        'since'. Returns None otherwise.
        """
        # FIXME this code is duplicated:
        try:
            repo = self.__github.get_repo(repo_full_name)
        except self.__githublib.GithubException as e:
            if e.status == 404:
                e.args += ("%s repo doesn't exist?" % (repo_full_name),)
            raise

        if repo.pushed_at >= since:
            return "Last commit pushed on " + o.get().green(repo.pushed_at)

    _persist_option = "--persist"

def _print(text):
    print(text)

def main():
    m.get().smtplib = smtplib
    o.get().print_function = _print
    cli = Cli(sys.argv[1:], github)
    try:
        cli.run()
    except Exception as e:
        error_msg = "Oops, an error occured.\n" + "\n".join(str(i) for i in e.args) + "\n\n"
        error_msg += traceback.format_exc()
        try:
            o.get().echo(error_msg)
            if cli.errorto is not None:
                m.get().dest.add(cli.errorto)
            if len(m.get().dest):
                # FIXME this code is duplicated:
                email_content = o.get().echoed + "\nSent from %s.\n" % (os.uname()[1])
                m.get().send_result("error", email_content)
                o.get().echo("Sent by e-mail to %s" % ", ".join(m.get().dest))
        except:
            print(error_msg)
        raise
