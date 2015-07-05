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

    def __init__(self, obj=None):
        """Builds from 'obj' having the members 'fields'.
           Builds from current UTC time if no 'obj' provided.
        """
        now = datetime.datetime.utcnow()
        self.data = {}
        for field in Timestamp.fields:
            self.data[field[0]] = getattr(obj, field[0]) if obj else getattr(now, field[1])

    def __str__(self):
        return " ".join([self.data[field[0]] for field in Timestamp.fields])

    def to_datetime(self):
        try:
            args = []
            for field in Timestamp.fields:
                args.append(int(self.data[field[0]]))
            return datetime.datetime(*args)
        except ValueError as e:
            e.args += ("Timestamp malformed?",)
            raise
