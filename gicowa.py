#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
from email.mime.text import MIMEText
import github
import smtplib

def _main():
    parser = argparse.ArgumentParser(description="watch GitHub commits easily")

    parser.add_argument("--no-color", action="store_true", help="disable color in output")

    credentials_option = "--credentials"
    parser.add_argument(credentials_option,
                        help="your GitHub login and password (e.g. 'AurelienLourot:password')")

    parser.add_argument("--mailto",
        help="e-mail address to which the output should be sent (e.g. 'aurelien.lourot@gmail.com')")

    subparsers = parser.add_subparsers(help="available commands")

    descr = "list repos watched by a user"
    parser_watchlist = subparsers.add_parser("watchlist", description=descr, help=descr)
    parser_watchlist.set_defaults(command="watchlist", impl=_watchlist)
    _add_argument_watcher_name(parser_watchlist)

    descr = "list last commits on a repo"
    parser_lastrepocommits = subparsers.add_parser("lastrepocommits", description=descr, help=descr)
    parser_lastrepocommits.set_defaults(command="lastrepocommits", impl=_lastrepocommits)
    parser_lastrepocommits.add_argument("repo",
        help="repository's full name (e.g. 'AurelienLourot/github-commit-watcher')")
    _add_arguments_since_committer_timestamp(parser_lastrepocommits)

    descr = "list last commits watched by a user"
    parser_lastwatchedcommits = subparsers.add_parser("lastwatchedcommits", description=descr,
                                                      help=descr)
    parser_lastwatchedcommits.set_defaults(command="lastwatchedcommits", impl=_lastwatchedcommits)
    _add_argument_watcher_name(parser_lastwatchedcommits)
    _add_arguments_since_committer_timestamp(parser_lastwatchedcommits)

    args = parser.parse_args()
    if args.credentials is not None:
        credentials = args.credentials.split(":", 1)
        hub = github.Github(credentials[0], credentials[1])
    else:
        hub = github.Github()

    try:
        args.impl(hub, args)
    except github.GithubException as e:
        if e.status == 401 and args.credentials is not None:
            e.args += ("Bad credentials?",)
        if e.status == 403 and args.credentials is None:
            e.args += ("API rate limit exceeded? Use the %s option." % (credentials_option),)
        raise

    global _printed_output
    if args.mailto is not None and _printed_output != "":
        _send_by_email(_printed_output, args)

def _add_argument_watcher_name(parser):
    """Adds an argument corresponding to a watcher's user name to an argparse parser.
    """
    parser.add_argument("username", help="watcher's name (e.g. 'AurelienLourot')")

def _add_arguments_since_committer_timestamp(parser):
    """Adds arguments corresponding to a "since" committer timestamp to an argparse parser.
    """
    since = parser.add_argument_group("YYYY MM DD hh mm ss (since)",
        "oldest committer UTC timestamp to consider (e.g. '2015 07 05 09 12 00')")
    since.add_argument("YYYY", help="year")
    since.add_argument("MM", help="month")
    since.add_argument("DD", help="day")
    since.add_argument("hh", help="hour")
    since.add_argument("mm", help="minute")
    since.add_argument("ss", help="second")

def _watchlist(hub, args):
    """Implements 'watchlist' command.
    Prints all watched repos of 'args.username'.
    """
    for repo in _get_watchlist(hub, args.username):
        _print(repo if args.no_color else _red(repo))

def _lastrepocommits(hub, args):
    """Implements 'lastrepocommits' command.
    Prints all commits on 'args.repo' with committer timestamp bigger than
    'args.YYYY,MM,DD,hh,mm,ss'.
    """
    for commit in _get_last_commits(hub, args.repo, _args_to_datetime(args), args.no_color):
        _print(commit)

def _lastwatchedcommits(hub, args):
    """Implements 'lastwatchedcommits' command.
    Prints all commits on repos watched by 'args.username' with committer timestamp bigger than
    'args.YYYY,MM,DD,hh,mm,ss'.
    """
    for repo in _get_watchlist(hub, args.username):
        for commit in _get_last_commits(hub, repo, _args_to_datetime(args), args.no_color):
            _print("%s - %s" % (repo if args.no_color else _red(repo), commit))

def _get_watchlist(hub, username):
    """Returns list of all watched repos of 'username'.
    """
    try:
        user = hub.get_user(username)
    except github.GithubException as e:
        if e.status == 404:
            e.args += ("%s user doesn't exist?" % (username),)
        raise

    return [repo.full_name for repo in user.get_subscriptions()]

def _get_last_commits(hub, repo_full_name, since, no_color):
    """Returns list of all commits on 'repo_full_name' with committer timestamp bigger than 'since'.
    Set 'no_color' to true to disable text coloring.
    """
    try:
        repo = hub.get_repo(repo_full_name)
    except github.GithubException as e:
        if e.status == 404:
            e.args += ("%s repo doesn't exist?" % (repo_full_name),)
        raise

    result = []
    for i in repo.get_commits(since=since):
        commit = repo.get_git_commit(i.sha)
        date = commit.committer.date if no_color else _green(commit.committer.date)
        name = commit.committer.name if no_color else _blue(commit.committer.name)
        result.append("%s - %s - %s" % (date, name, commit.message))
    return result

def _args_to_datetime(args):
    """Returns a datetime built from 'args.YYYY,MM,DD,hh,mm,ss'.
    """
    try:
        return datetime.datetime(int(args.YYYY), int(args.MM), int(args.DD), int(args.hh),
                                 int(args.mm), int(args.ss))
    except ValueError as e:
        e.args += ("Timestamp malformed?",)
        raise

def _red(text):
    return _colored(text, 31)

def _green(text):
    return _colored(text, 32)

def _blue(text):
    return _colored(text, 34)

def _colored(text, color):
    """Returns 'text' with a color, i.e. bash and zsh would print the returned string in the given
       color.
    """
    return "\033[" + str(color) + "m" + str(text) + "\033[0m"

def _print(text):
    print(text)
    global _printed_output
    _printed_output += text + "\n"

def _send_by_email(text, args):
    """Sends 'text' by e-mail.
    """
    sender = "gicowa@lourot.com"
    email = MIMEText(text)
    email["Subject"] = "[gicowa] %s." % (args.command)
    email["From"] = sender
    email["To"] = args.mailto
    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(sender, args.mailto, email.as_string())
    smtp.quit()
    _print("Sent by e-mail to %s" % (args.mailto))

if __name__ == "__main__":
    # Contains at any time the whole text that has been printed to the console:
    _printed_output = ""

    try:
        _main()
    except Exception as e:
        print("Oops, an error occured.")
        print("\n".join(str(i) for i in e.args))
        print("")
        raise
