#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import github

def _main():
    parser = argparse.ArgumentParser(description="watch GitHub commits easily")
    subparsers = parser.add_subparsers(help="available commands")

    descr = "list repos watched by a user"
    parser_watchlist = subparsers.add_parser("watchlist", description=descr, help=descr)
    parser_watchlist.set_defaults(impl=_watchlist)
    parser_watchlist.add_argument("username", help="watcher's name (e.g. 'AurelienLourot')")

    args = parser.parse_args()
    args.impl(github.Github(), args)

def _watchlist(github, args):
    """Implements 'watchlist' command.
       Prints all watched repos of 'args.username'.
    """
    for repo in github.get_user(args.username).get_subscriptions():
        print repo.full_name

if __name__ == "__main__":
    _main()
