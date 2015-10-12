#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Output:
    __instance = None # Singleton

    @classmethod
    def get(cls):
        if Output.__instance is None:
            Output()
        assert Output.__instance is not None
        return Output.__instance

    def __init__(self):
        if Output.__instance is not None:
            assert False, "I'm a singleton."
        Output.__instance = self

        self.print_function = None
        self.colored = True

        # Contains at any time the whole text that has been echoed by this instance:
        self.echoed = ""

    def echo(self, text):
        self.print_function(text)
        self.echoed += text + "\n"

    def red(self, text):
        return self.__colored(text, 31)

    def green(self, text):
        return self.__colored(text, 32)

    def blue(self, text):
        return self.__colored(text, 34)

    def __colored(self, text, color):
        """Returns 'text' with a color, i.e. bash and zsh would print the returned string in the
        given color.
        Returns 'text' with no color if not self.colored.
        """
        text = str(text)
        return text if not self.colored else "\033[" + str(color) + "m" + text + "\033[0m"
