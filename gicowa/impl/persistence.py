#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

class Memory:
    filename = "~/.gicowa"

    def __init__(self):
        # e.g. {"lastwatchedcommits AurelienLourot": {"YYYY": "2015",
        #                                             "MM"  : "07",
        #                                             "DD"  : "04",
        #                                             "hh"  : "00",
        #                                             "mm"  : "00",
        #                                             "ss"  : "00"}}
        self.timestamps = {}

        try:
            with open(os.path.expanduser(self.filename), "rb") as f:
                try:
                    self.timestamps = json.loads(f.read())
                except ValueError as e:
                    e.args += ("%s file damaged?" % (self.filename),)
                    raise
        except IOError:
            # Ignores when file doesn't exist yet
            pass

    def save(self):
        with open(os.path.expanduser(self.filename), "wb") as f:
            f.write(json.dumps(self.timestamps, indent=2))
