#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

class Persistence:
    filename = "~/.gicowa"

    __instance = None # Singleton

    @classmethod
    def get(cls):
        if Persistence.__instance is None:
            Persistence()
        assert Persistence.__instance is not None
        return Persistence.__instance

    def __init__(self):
        if Persistence.__instance is not None:
            assert False, "I'm a singleton."
        Persistence.__instance = self

        # e.g. {"lastwatchedcommits AurelienLourot": {"YYYY": "2015",
        #                                             "MM"  : "07",
        #                                             "DD"  : "04",
        #                                             "hh"  : "00",
        #                                             "mm"  : "00",
        #                                             "ss"  : "00"}}
        self.timestamps = {}

        try:
            with open(os.path.expanduser(Persistence.filename), "rb") as f:
                try:
                    self.timestamps = json.loads(f.read())
                except ValueError as e:
                    e.args += ("%s file damaged?" % (Persistence.filename),)
                    raise
        except IOError:
            # Ignores when file doesn't exist yet
            pass

    def save(self):
        with open(os.path.expanduser(Persistence.filename), "wb") as f:
            f.write(json.dumps(self.timestamps, indent=2))
