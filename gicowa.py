#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

def _watchlist(args):
    print "watchlist"

def _main():
    parser = argparse.ArgumentParser(description="watch GitHub commits easily")
    subparsers = parser.add_subparsers(help="available commands")

    descr = "list projects watched by a user"
    parser_watchlist = subparsers.add_parser("watchlist", description=descr, help=descr)
    parser_watchlist.set_defaults(impl=_watchlist)
    parser_watchlist.add_argument("username", help="watcher's name")

    args = parser.parse_args()
    args.impl(args)

if __name__ == "__main__":
    _main()
