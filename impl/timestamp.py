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
        """Builds from 'obj' having the members 'fields' or being a dictionary with these fields.
           Builds from current UTC time if no 'obj' provided.
        """
        now = datetime.datetime.utcnow()
        self.data = {}
        for field in Timestamp.fields:
            if obj is not None:
                if isinstance(obj, dict):
                    self.data[field[0]] = obj[field[0]]
                else:
                    self.data[field[0]] = getattr(obj, field[0])
            else:
                self.data[field[0]] = getattr(now, field[1])

    def __str__(self):
        return str(self.to_datetime())

    def to_datetime(self):
        try:
            args = []
            for field in Timestamp.fields:
                args.append(int(self.data[field[0]]))
            return datetime.datetime(*args)
        except ValueError as e:
            e.args += ("Timestamp malformed?",)
            raise
