#!/usr/bin/env python
# rule/Default.py
# Default rules for BigMock.py
# jonCastillo October 10 2016
# https://github.com/joncastillo/BigMock

import sys
import os

from ReplacementList.ReplacementList import ReplacementListEntry
from ReplacementList.ReplacementList import ReplacementList

sys.path.append(os.path.join(os.path.dirname(__file__), '../Clang/bindings/python'))
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
from clang.cindex import TokenKind
from clang.cindex import AccessSpecifier
from clang.cindex import SourceLocation
from clang.cindex import SourceRange

specifier_list = ["inline", "const", "override", "final", "virtual", "mutable", "explicit", "extern", "static",
                  "export", "friend", "noexcept"]

########## these utilities should be abstracted in the future: ##########

def remove_entity(cursor,replacementlist):
    # create Replacement List Entry of subtype DELETION to remove clang entity pointed by clang cursor

    extent = cursor.extent
    entry = ReplacementListEntry(ReplacementListEntry.type.DELETION, extent.start, extent.end, "")
    replacementlist.append(entry)


def remove_comment(cursor,replacementlist):
    # create Replacement List Entry of subtype DELETION to attempt removal of clang entity's associated comment
    commentRange = cursor.getCommentRange()
    if commentRange.start.line != 0:
        entry = ReplacementListEntry(ReplacementListEntry.type.DELETION, commentRange.start, commentRange.end, "")
        replacementlist.append(entry)

#########################################################################

class Rule(object):
    def process_cxxmethod_inline(self, cursor, replacementlist, settings):
        # remove inlines except for enGetType :)
        # enGetType (Continental-Corporation): Retain definition for enGetType
        if cursor.spelling != "enGetType":
            remove_entity(cursor, replacementlist)


    def process_cxxmethod(self, cursor, replacementlist, staticmethodlist, settings, is_template = False):
        force_singleton = settings.oFlag_MockOptions.makeSingleton
        # enGetType is better unmocked:
        if cursor.spelling == "enGetType":
            return

        tokens = [token.spelling for token in cursor.get_tokens()]
        arguments = [argument.spelling for argument in cursor.get_arguments()]

        i = 0
        returntype = ''
        argumentlist = ''
        while tokens[i] in specifier_list:
            i = i + 1

        while tokens[i] != cursor.spelling \
                and tokens[i] != 'operator':
            returntype = returntype + tokens[i] + ' '
            i = i + 1

        if tokens[i] == 'operator':
            return

        while tokens[i] != '(':
            i = i + 1
        i = i + 1

        while tokens[i] != ';' and tokens[i] != '{':
            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i]
            argumentlist += ' '
            i = i + 1

        #get rid of last space:
        argumentlist=argumentlist[:-1]

        if argumentlist == 'void ':
            argumentlist = ''
        buffer = ''
        if cursor.is_const_method():
            buffer = "MOCK_CONST_METHOD"
        else:
            buffer = "MOCK_METHOD"

        buffer = buffer + str(len(arguments))
        if is_template is True:
            buffer = buffer + "_T"
        buffer = buffer + '('
        buffer = buffer + cursor.spelling
        buffer = buffer + ','
        buffer = buffer + returntype
        buffer = buffer + '('
        buffer = buffer + argumentlist
        buffer = buffer + ')'
        if tokens[len(tokens)-1] != ';':
            buffer = buffer + ';'

        if cursor.is_static_method() or force_singleton == True:
            staticmethodlist.append(buffer)

        if cursor.is_static_method():
            buffer = 'static '

        if cursor.is_static_method() or force_singleton == True:
            buffer = returntype + \
                     cursor.spelling + "( " + \
                     argumentlist + " ) {\n" + \
                     "\t/*  Shared Mock via Singleton Class */\n" + \
                     "\t"

            if (not "void" in returntype) and (returntype != ""):
                buffer = buffer + "return "

            buffer = buffer + \
                     cursor.lexical_parent.spelling + "_Mocked" + "::get_instance()." + \
                     cursor.spelling + "(" + \
                     ', '.join(arguments) + ");\n" + \
                     "}"

        extent = cursor.extent
        entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end, buffer);
        replacementlist.append(entry)


    def process_cmethod(self, cursor, replacementlist, staticmethodlist, staticmethodlist2, settings ):

        tokens = [token.spelling for token in cursor.get_tokens()]
        arguments = [argument.spelling for argument in cursor.get_arguments()]

        if len(tokens) == 0:
            return
        i = 0
        returntype = ''
        argumentlist = ''
        while tokens[i] in specifier_list:
            i = i+1
        while tokens[i] != cursor.spelling:
            returntype = returntype + tokens[i] + ' '
            i = i + 1

        while tokens[i] != '(':
            i = i + 1
        i = i + 1

        while tokens[i] != ';' and tokens[i] != '{':
            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i]
            argumentlist += ' '
            i = i + 1

        #get rid of last space:
        argumentlist=argumentlist[:-1]

        if argumentlist == 'void ':
            argumentlist = ''

        buffer = ''
        if cursor.is_const_method():
            buffer = "MOCK_CONST_METHOD"
        else:
            buffer = "MOCK_METHOD"
        buffer = buffer + str(len(arguments))
        buffer = buffer + '('
        buffer = buffer + cursor.spelling
        buffer = buffer + ','
        buffer = buffer + returntype
        buffer = buffer + '('
        buffer = buffer + argumentlist
        buffer = buffer + ');'
        staticmethodlist.append(buffer)

        buffer = ""
        buffer2 = ""

        buffer += "extern " + returntype + os.path.splitext(settings.baseFile)[0] + "_Mocked" + "_" + \
             cursor.spelling + "(" + argumentlist + ");\n"
        buffer += 'inline '

        buffer += returntype + \
                 cursor.spelling + "( " + \
                 argumentlist + " ) {\n" + \
                 "\t/*  Shared Mock via Singleton Class */\n" + \
                 "\t"

        if (not "void" in returntype) and (returntype != "") :
            buffer = buffer + "return "

        buffer = buffer + \
                 os.path.splitext(settings.baseFile)[0] + "_Mocked" + "_" + \
             cursor.spelling + "(" + \
             ', '.join(arguments) + ");\n" + \
             "}"

        extent = cursor.extent
        entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end, buffer);
        replacementlist.append(entry)

        buffer2 += 'extern \"C\"\n' + returntype + os.path.splitext(settings.baseFile)[0] + "_Mocked" + "_" + cursor.spelling + "( " + argumentlist + " ) {\n" + \
                 "\t";
        if (not "void" in returntype) and (returntype != ""):
            buffer2 = buffer2 + "return "

        buffer2 = buffer2 + os.path.splitext(settings.baseFile)[0] + "_Mocked::get_instance()." + cursor.spelling + "(" + \
            ', '.join(arguments) + ");\n}\n\n"
        staticmethodlist2.append( buffer2 )

    def process_class(self, cursor, replacementlist, settings):
        replacementlist_staticmethods = []
        if cursor.is_definition():

            for c in cursor.get_children():

                if c.kind is CursorKind.CXX_METHOD:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        # convert to Mocked method:
                        self.process_cxxmethod(c, replacementlist, replacementlist_staticmethods, settings)

                        # elif c.kind is CursorKind.FIELD_DECL:
                        # Retain private Field Declarations so that initializer lists remain unchanged.

                elif c.kind is CursorKind.CLASS_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class(c, replacementlist, settings)

                elif c.kind is CursorKind.STRUCT_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class_template(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class_template_partial_specialization(cursor, settings)

            self.process_cxxstaticmethod_list(cursor, replacementlist, replacementlist_staticmethods)

    def process_class_template(self, cursor, replacementlist, settings):
        replacementlist_staticmethods = []
        if cursor.is_definition():

            for c in cursor.get_children():
                if c.kind is CursorKind.CXX_METHOD:
                    print c.extent
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        # convert to Mocked method:
                        self.process_cxxmethod(c, replacementlist, replacementlist_staticmethods, settings, True)

                elif c.kind is CursorKind.CLASS_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class(c, replacementlist, settings)

                elif c.kind is CursorKind.STRUCT_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class_template(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        remove_entity(c, replacementlist)
                        remove_comment(c, replacementlist)
                    else:
                        self.process_class_template_partial_specialization(cursor, settings)

            self.process_cxxstaticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

    def process_cstaticmethod_list(self, cursor, replacementlist, replacementlist_staticmethods, additionalstring, setting):
        buffer = ''

        outfilename2= os.path.splitext((setting.baseFile))[0]+'_Mocked.cpp'
        outfile = open(outfilename2, 'w')

        buffer = buffer + "/* This file was generated by BigMock.py */ \n\n"
        buffer = buffer + "#include <gmock/gmock.h>\n"
        buffer = buffer + "#include <gtest/gtest.h>\n\n"
        buffer = buffer + "/* << Manually insert #includes from original file here >> */ \n\n"

        if len(replacementlist_staticmethods) != 0:
            buffer = buffer + 'class ' + os.path.splitext(setting.baseFile)[0]+'_Mocked\n'
            buffer = buffer + '{\n'
            buffer = buffer + '\tpublic:\n'
            buffer = buffer + '\tstatic ' + os.path.splitext(setting.baseFile)[0] + '_Mocked& get_instance()\n'
            buffer = buffer + '\t{\n'
            buffer = buffer + '\t\tstatic '+ os.path.splitext(setting.baseFile)[0] + '_Mocked oInstance;\n'
            buffer = buffer + '\t\treturn oInstance;\n'
            buffer = buffer + '\t}\n\n'

            for entry in replacementlist_staticmethods:
                buffer = buffer + "\t" + entry
                buffer = buffer + '\n'
            buffer = buffer + '};\n'

            outfile.write (buffer)
            for buf2 in additionalstring:
                outfile.write (buf2)

        outfile.close()

    def process_cxxstaticmethod_list(self, cursor, replacementlist, replacementlist_staticmethods):
        buffer = ''
        if len(replacementlist_staticmethods) != 0:
            buffer = buffer + 'class ' +cursor.displayname+'_Mocked\n'
            buffer = buffer + '{\n'
            buffer = buffer + '\tpublic:\n'
            buffer = buffer + '\tstatic ' + cursor.displayname + '_Mocked& get_instance()\n'
            buffer = buffer + '\t{\n'
            buffer = buffer + '\t\tstatic '+ cursor.displayname + '_Mocked oInstance;\n'
            buffer = buffer + '\t\treturn oInstance;\n'
            buffer = buffer + '\t}\n'

            for entry in replacementlist_staticmethods:
                buffer = buffer + "\t" + entry
                buffer = buffer + '\n'
            buffer = buffer + '};\n'

            extent = cursor.extent
            entry = ReplacementListEntry(ReplacementListEntry.type.INSERTION, extent.start, extent.start, buffer)
            replacementlist.append(entry)
