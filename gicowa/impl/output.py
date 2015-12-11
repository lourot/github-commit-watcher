#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Output:
    def __init__(self, print_function):
        """
        @param print_function: Dependency. Inject print.
        """
        self.__print_function = print_function
        self.colored = True

        # Contains at any time the whole text that has been echoed by this instance:
        self.echoed = ""

    def echo(self, text):
        self.__print_function(text)
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
        text = unicode(text)
        return text if not self.colored else "\033[" + unicode(color) + "m" + text + "\033[0m"
