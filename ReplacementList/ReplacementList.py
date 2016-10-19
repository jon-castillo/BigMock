#!/usr/bin/env python
# ReplacementList.py
# Text replacement based on source location.
# jonCastillo October 10 2016
# https://github.com/joncastillo/BigMock

import os
import sys

class TextLocation( object ):
    def __init__ (self):
        self.line = 0
        self.column = 0
    def __init__(self, line, column):
        self.line = line
        self.column = column


class ReplacementListEntry( object ):
    class type(object):
        INSERTION = 0
        REPLACEMENT = 1
        DELETION = 2

    def __init__ (self, type, start, end, buffer ):
        self.type = type
        self.start = TextLocation(start.line, start.column)
        self.end = TextLocation(end.line, end.column)
        self.buffer = buffer

    # for sorting
    def __lt__ (self, other):
        if self.start.line == other.start.line:
            if self.start.column == other.start.column:
                return self.type < other.type
            else:
                return self.start.column < other.start.column
        else:
            return self.start.line < other.start.line

class ReplacementList( object ):
    def __init__ (self):
        self.replacementListEntries = []

    def append(self, entry):
        self.replacementListEntries.append(entry)

    def dump(self):

        # Dump replacement entries inside replacement list. (does sort)

        self.replacementListEntries.sort()

        for i in self.replacementListEntries:
            if i.type == ReplacementListEntry.type.INSERTION:
                print "Insertion:".ljust(12) + (
                " At (" + str(i.start.line + 1) + "," + str(i.start.column + 1) + ") : ").ljust(
                    29) + i.buffer.replace("\n", "\\n")
            elif i.type == ReplacementListEntry.type.DELETION:
                print "Deletion:".ljust(12) + (
                " From (" + str(i.start.line + 1) + "," + str(i.start.column + 1) + ")").ljust(16) + (
                      "To (" + str(i.end.line + 1) + "," + str(i.end.column + 1) + ")").ljust(13)
            else:
                print "Replacement:".ljust(12) + (
                " From (" + str(i.start.line + 1) + "," + str(i.start.column + 1) + ")").ljust(16) + (
                      "To (" + str(i.end.line + 1) + "," + str(i.end.column + 1) + ")").ljust(
                    13) + " : " + i.buffer.replace("\n", "\\n")

    def perform_replace(self, sourcefile ):

        # O(n^2) replacement subroutine: (does sort)

        self.replacementListEntries.sort()
        code = open(sourcefile).readlines()
        code_linecount = len(code)
        replacementlist_itemcount = len(self.replacementListEntries)
        output_buffer = ""

        i = 0
        listindex = 0

        if replacementlist_itemcount == 0:
            current_replacement_line = -1
            current_replacement_column = -1
        else:
            current_replacement_line = self.replacementListEntries[listindex].start.line - 1
            current_replacement_column = self.replacementListEntries[listindex].start.column - 1

        while i < code_linecount:
            current_line = code[i]
            current_line_length = len(code[i])

            if listindex < replacementlist_itemcount:
                if i == current_replacement_line:

                    j = 0
                    while j < current_line_length:
                        if i == current_replacement_line and j == current_replacement_column:
                            # we are at a replacement point
                            output_buffer = output_buffer + self.replacementListEntries[ listindex ].buffer.replace("\n", "\n"+" "*j)
                            if self.replacementListEntries[listindex].type == ReplacementListEntry.type.REPLACEMENT:
                                i = self.replacementListEntries[ listindex ].end.line - 1
                                j = self.replacementListEntries[ listindex ].end.column - 1
                                current_line = code[i]
                                current_line_length = len(code[i])
                            elif self.replacementListEntries[listindex].type == ReplacementListEntry.type.DELETION:
                                i = self.replacementListEntries[ listindex ].end.line - 1
                                j = self.replacementListEntries[ listindex ].end.column - 1
                                current_line = code[i]
                                current_line_length = len(code[i])

                            listindex += 1

                            if listindex < replacementlist_itemcount:
                                current_replacement_line = self.replacementListEntries[listindex].start.line - 1
                                current_replacement_column = self.replacementListEntries[listindex].start.column - 1
                            else:
                                current_replacement_line = - 1
                                current_replacement_column = - 1

                        else:
                            # per character copy until the replacement point is found
                            output_buffer = output_buffer + current_line[j]
                            j += 1

                else:
                    # nothing in this line needs replacement, just copy:
                    output_buffer = output_buffer + current_line

            else:
                # all of items in replacement list are processed, continue copying lines
                output_buffer = output_buffer + current_line

            i += 1

        return output_buffer