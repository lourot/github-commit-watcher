#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import github
import socket
import traceback
from impl.mail import Mail as m
from impl.output import Output as o
from impl.persistence import Persistence as p
from impl.timestamp import Timestamp

_persist_option = "--persist"

def _main():
    parser = argparse.ArgumentParser(description="watch GitHub commits easily")

    parser.add_argument("--no-color", action="store_true", help="disable color in output")

    credentials_option = "--credentials"
    parser.add_argument(credentials_option,
                        help="your GitHub login and password (e.g. 'AurelienLourot:password')")

    parser.add_argument("--mailto",
        help="e-mail address to which the output should be sent (e.g. 'aurelien.lourot@gmail.com')")
    parser.add_argument("--mailfrom",
        help="e-mail server and credentials from which the output should be sent (e.g. "
             + "'smtp.googlemail.com:465:aurelien.lourot@gmail.com:password')")

    parser.add_argument(_persist_option, action="store_true",
        help="gicowa will keep track of the last commands run in %s" % (p.filename))

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
    m.get().dest = args.mailto

    o.get().colored = not args.no_color

    if args.credentials is not None:
        credentials = args.credentials.split(":", 1)
        try:
            hub = github.Github(credentials[0], credentials[1])
        except IndexError as e:
            e.args += ("Bad credentials' syntax.",)
            raise
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
    except socket.gaierror as e:
        e.args += ("No internet connection?",)
        raise

    if m.get().dest is not None:
        if o.get().echoed.count("\n") > 1:
            m.get().send_result(args.command, o.get().echoed)
            o.get().echo("Sent by e-mail to %s" % (m.get().dest))
        else:
            o.get().echo("No e-mail sent.")

    if args.persist:
        p.get().save()

def _add_argument_watcher_name(parser):
    """Adds an argument corresponding to a watcher's user name to an argparse parser.
    """
    parser.add_argument("username", help="watcher's name (e.g. 'AurelienLourot')")

def _add_arguments_since_committer_timestamp(parser):
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

    descr = "use last time run with %s" % (_persist_option)
    parser_sincelast = subparsers.add_parser("sincelast", description=descr, help=descr)
    parser_sincelast.set_defaults(sincelast=True)

def _watchlist(hub, args):
    """Implements 'watchlist' command.
    Prints all watched repos of 'args.username'.
    """
    command = args.command + " " + args.username
    o.get().echo(command)

    for repo in _get_watchlist(hub, args.username):
        o.get().echo(o.get().red(repo))

def _lastrepocommits(hub, args):
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

    pushed = _has_been_pushed(hub, args.repo, since.to_datetime())
    if pushed is not None:
        o.get().echo(pushed)
    for commit in _get_last_commits(hub, args.repo, since.to_datetime()):
        o.get().echo(commit)

    # Remember this last execution:
    p.get().timestamps[command] = now.data

def _lastwatchedcommits(hub, args):
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

    for repo in _get_watchlist(hub, args.username):
        pushed = _has_been_pushed(hub, repo, since.to_datetime())
        if pushed is not None:
            o.get().echo("%s - %s" % (o.get().red(repo), pushed))
        for commit in _get_last_commits(hub, repo, since.to_datetime()):
            o.get().echo("%s - %s" % (o.get().red(repo), commit))

    # Remember this last execution:
    p.get().timestamps[command] = now.data

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

def _get_last_commits(hub, repo_full_name, since):
    """Returns list of all commits on 'repo_full_name' with committer timestamp bigger than 'since'.
    """
    # FIXME this code is duplicated:
    try:
        repo = hub.get_repo(repo_full_name)
    except github.GithubException as e:
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

def _has_been_pushed(hub, repo_full_name, since):
    """Returns string describing last push timestamp of 'repo_full_name''s last commit if after
    'since'. Returns None otherwise.
    """
    # FIXME this code is duplicated:
    try:
        repo = hub.get_repo(repo_full_name)
    except github.GithubException as e:
        if e.status == 404:
            e.args += ("%s repo doesn't exist?" % (repo_full_name),)
        raise

    if repo.pushed_at >= since:
        return "Last commit pushed on " + o.get().green(repo.pushed_at)

def main():
    try:
        _main()
    except Exception as e:
        error_msg = "Oops, an error occured.\n" + "\n".join(str(i) for i in e.args) + "\n\n"
        error_msg += traceback.format_exc()
        try:
            o.get().echo(error_msg)
            if m.get().dest is not None:
                m.get().send_result("error", o.get().echoed)
                o.get().echo("Sent by e-mail to %s" % (m.get().dest))
        except:
            print(error_msg)
        raise
