import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../Clang/bindings/python'))

from clang.cindex import SourceRange
from clang.cindex import SourceLocation

class ReplacementListEntry( object ):
    class type(object):
        INSERTION = 0
        REPLACEMENT = 1
        DELETION = 2

    def __init__ (self, type, start, end, buffer ):
        self.type = type
        self.start = start
        self.end = end
        self.buffer = buffer

    def __lt__ (self, other):
        #for sorting:
        if self.start.line == other.start.line:
            if self.start.colimn == other.start.column:
                return self.type < other.type
            else:
                return self.start.column < other.start.column
        else:
            return self.start.line < other.start.line

class ReplacementList( object ):
    def __init__ (self):
        self.replacementListEntries = []

    def remove_entity(self, cursor):
        extent = cursor.extent
        entry = ReplacementListEntry(ReplacementListEntry.type.DELETION, extent.start, extent.end, "" )
        self.replacementListEntries.append(entry)

    def remove_comment(self, cursor):
        commentRange = cursor.getCommentRange()
        if commentRange.start.line != 0:
            entry = ReplacementListEntry(ReplacementListEntry.type.DELETION, commentRange.start, commentRange.end, "" )
            self.replacementListEntries.append(entry)
    def append(self, entry):
        self.replacementListEntries.append(entry)

    def dump(self):
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
        self.replacementListEntries.sort()
        code = open(sourcefile).readlines()
        code_linecount = len(code)
        replacementlist_itemcount = len(self.replacementListEntries)

        output_buffer = ""
        i = 0
        listindex = 0

        current_replacement_line = self.replacementListEntries[listindex].start.line - 1
        current_replacement_column = self.replacementListEntries[listindex].start.column - 1

        while i < code_linecount:
            current_line = code[i]
            current_line_length = len(code[i])

            if listindex < replacementlist_itemcount:
                if i == current_replacement_line:

                    j = 0
                    while j < current_line_length:
                        if j == current_replacement_column:
                            # we are at a replacement point
                            output_buffer = output_buffer + self.replacementListEntries[ listindex ].buffer.replace("\n", "\n"+" "*j)
                            if self.replacementListEntries[listindex].type == ReplacementListEntry.type.REPLACEMENT:
                                i = self.replacementListEntries[ listindex ].end.line - 1
                                j = self.replacementListEntries[ listindex ].end.column
                                current_line = code[i]
                                current_line_length = len(code[i])
                            elif self.replacementListEntries[listindex].type == ReplacementListEntry.type.DELETION:
                                i = self.replacementListEntries[ listindex ].end.line - 1
                                j = self.replacementListEntries[ listindex ].end.column
                                current_line = code[i]
                                current_line_length = len(code[i])

                            listindex += 1
                            if listindex < replacementlist_itemcount:
                                current_replacement_line = self.replacementListEntries[listindex].start.line - 1
                                current_replacement_column = self.replacementListEntries[listindex].start.column - 1

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