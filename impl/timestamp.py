#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

class Timestamp:
    fields = (("YYYY", "year"  ),
              ("MM"  , "month" ),
              ("DD"  , "day"   ),
              ("hh"  , "hour"  ),
              ("mm"  , "minute"),
              ("ss"  , "second"))

    def __init__(self, obj):
        """Builds from 'obj' having the members 'fields'.
        """
        self.__data = {}
        for field in Timestamp.fields:
            self.__data[field[0]] = getattr(obj, field[0])

    def to_datetime(self):
        try:
            args = []
            for field in Timestamp.fields:
                args.append(int(self.__data[field[0]]))
            return datetime.datetime(*args)
        except ValueError as e:
            e.args += ("Timestamp malformed?",)
            raise
