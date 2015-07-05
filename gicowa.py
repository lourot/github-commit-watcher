#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import github

def _main():
    parser = argparse.ArgumentParser(description="watch GitHub commits easily")
    subparsers = parser.add_subparsers(help="available commands")

    descr = "list repos watched by a user"
    parser_watchlist = subparsers.add_parser("watchlist", description=descr, help=descr)
    parser_watchlist.set_defaults(impl=_watchlist)
    parser_watchlist.add_argument("username", help="watcher's name (e.g. 'AurelienLourot')")

    descr = "list last commits of a repo"
    parser_lastrepocommits = subparsers.add_parser("lastrepocommits", description=descr, help=descr)
    parser_lastrepocommits.set_defaults(impl=_lastrepocommits)
    parser_lastrepocommits.add_argument("repo",
        help="repository's full name (e.g. 'AurelienLourot/github-commit-watcher')")
    since = parser_lastrepocommits.add_argument_group("since",
        "oldest committer UTC timestamp to consider (e.g. '2015 07 05 09 12 00')")
    since.add_argument("YYYY", help="year")
    since.add_argument("MM", help="month")
    since.add_argument("DD", help="day")
    since.add_argument("hh", help="hour")
    since.add_argument("mm", help="minute")
    since.add_argument("ss", help="second")

    args = parser.parse_args()
    args.impl(github.Github(), args)

def _watchlist(github, args):
    """Implements 'watchlist' command.
       Prints all watched repos of 'args.username'.
    """
    for repo in github.get_user(args.username).get_subscriptions():
        print repo.full_name

def _lastrepocommits(github, args):
    """Implements 'lastrepocommits' command.
       Prints all commits of 'args.repo' with committer timestamp bigger than
       'args.YYYY,MM,DD,hh,mm,ss'.
    """
    since = datetime.datetime(int(args.YYYY), int(args.MM), int(args.DD), int(args.hh),
                              int(args.mm), int(args.ss))
    repo = github.get_repo(args.repo)
    for i in repo.get_commits(since=since):
        commit = repo.get_git_commit(i.sha)
        print "%s - %s - %s" % (commit.committer.date, commit.committer.name, commit.message)

if __name__ == "__main__":
    _main()
