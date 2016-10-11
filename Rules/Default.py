#!/usr/bin/env python
#  BigMock.py
# convert headers to google mock v2
# jonCastillo July 23 2016


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


class Rule(object):
    def process_cxxmethod_inline(self, cursor, replacementlist, settings):
        # remove inlines except for enGetType :)
        # enGetType (Continental-Corporation): Retain definition for enGetType
        if cursor.spelling != "enGetType":
            replacementlist.remove_entity(cursor)


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
        while tokens[i] != ')':
            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i] + ' '
            i = i + 1

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
        buffer = buffer + '));'

        if cursor.is_static_method() or force_singleton == True:
            staticmethodlist.append(buffer)

            buffer = 'static '

            buffer = buffer + \
                     returntype + \
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
        if cursor.is_definition:
            definitioncursor = cursor.get_definition()
            # print definitioncursor.spelling
            # extent.end = definitioncursor.extent.end
        entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end, buffer);
        replacementlist.append(entry)


    def process_cmethod(cursor, replacementlist, staticmethodlist, settings ):

        tokens = [token.spelling for token in cursor.get_tokens()]
        arguments = [argument.spelling for argument in cursor.get_arguments()]

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
        while tokens[i] != ')':
            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i] + ' '
            i = i + 1

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
        buffer = buffer + '));'

        staticmethodlist.append(buffer)
        buffer = 'static '

        buffer = buffer + \
                 returntype + \
                 cursor.spelling + "( " + \
                 argumentlist + " ) {\n" + \
                 "\t/*  Shared Mock via Singleton Class */\n" + \
                 "\t"

        if (not "void" in returntype) and (returntype != "") :
            buffer = buffer + "return "

        buffer = buffer + \
                 "Global_" +os.path.splitext(settings.baseFile)[0] + "_Mocked" + "::get_instance()." + \
             cursor.spelling + "(" + \
             ', '.join(arguments) + ");\n" + \
             "}"

        extent = cursor.extent
        if cursor.is_definition:
            definitioncursor = cursor.get_definition()
            #print definitioncursor.spelling
            #extent.end = definitioncursor.extent.end
        entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent.start, extent.end, buffer);
        replacementlist.append(entry)


    def process_class(self, cursor, replacementlist, settings):
        print "classtest"
        replacementlist_staticmethods = []
        if cursor.is_definition():

            for c in cursor.get_children():

                if c.kind is CursorKind.CXX_METHOD:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        replacementlist.remove_entity(c)
                        replacementlist.remove_comment(c)
                    else:
                        # convert to Mocked method:
                        self.process_cxxmethod(c, replacementlist, replacementlist_staticmethods, settings)

                        # elif c.kind is CursorKind.FIELD_DECL:
                        # Retain private Field Declarations so that initializer lists remain unchanged.

                elif c.kind is CursorKind.CLASS_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        replacementlist.remove_entity(c)
                        replacementlist.remove_comment(c)
                    else:
                        self.process_class_declaration(c, replacementlist, settings)

                elif c.kind is CursorKind.STRUCT_DECL:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        replacementlist.remove_entity(c)
                        replacementlist.remove_comment(c)
                    else:
                        self.process_class_declaration(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        replacementlist.remove_entity(c)
                        replacementlist.remove_comment(c)
                    else:
                        self.process_class_template(c, replacementlist, settings)

                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    if c.access_specifier is AccessSpecifier.PRIVATE:
                        # private methods will never be used by test framework so remove them.
                        replacementlist.remove_entity(c)
                        replacementlist.remove_comment(c)
                    else:
                        self.process_class_template_partial_specialization(cursor, settings)

            self.process_cxxstaticmethod_list(cursor, replacementlist, replacementlist_staticmethods)

    def process_cstaticmethod_list(self, cursor, replacementlist, replacementlist_staticmethods, setting):
        buffer = ''
        if len(replacementlist_staticmethods) != 0:
            buffer = buffer + 'class ' +"Global_"+os.path.splitext(setting.baseFile)[0]+'_Mocked\n'
            buffer = buffer + '{\n'
            buffer = buffer + '\tpublic:\n'
            buffer = buffer + '\tstatic ' + "Global_"+os.path.splitext(setting.baseFile)[0] + '_Mocked& get_instance()\n'
            buffer = buffer + '\t{\n'
            buffer = buffer + '\t\tstatic '+ "Global_"+os.path.splitext(setting.baseFile)[0] + '_Mocked oInstance;\n'
            buffer = buffer + '\t\treturn oInstance;\n'
            buffer = buffer + '\t}\n'

            for entry in replacementlist_staticmethods:
                buffer = buffer + "\t" + entry
                buffer = buffer + '\n'
            buffer = buffer + '};\n'

            extent = cursor.extent
            entry = ReplacementListEntry(ReplacementListEntry.type.INSERTION, extent.start, extent.start, buffer)
            replacementlist.append(entry)


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

    def process_class_template(self, cursor, replacementlist, settings):
        replacementlist_staticmethods = []
        if cursor.is_definition():

            extent_start = cursor.extent
            tokens = cursor.get_tokens()
            tokenlist = [token for token in tokens ]

            buffer = ''
            i = 0
            while tokenlist[i].spelling != '{':
                print tokenlist[i].spelling
                buffer = buffer + tokenlist[i].spelling + ' '
                i = i + 1

            buffer = buffer +'\n{\n'
            entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent_start.start, tokenlist[i].extent.end, buffer);
            replacementlist.append(entry)

            for c in cursor.get_children():
                if c.kind is CursorKind.CXX_METHOD:
                    self.process_cxxmethod(c, replacementlist, replacementlist_staticmethods, settings, True )
                elif c.kind is CursorKind.CLASS_DECL:
                    self.process_class_declaration(c, replacementlist)
                elif c.kind is CursorKind.STRUCT_DECL:
                    self.process_class_declaration(c, replacementlist)
                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    self.process_class_template(c, replacementlist)
                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    self.process_class_template_partial_specialization(cursor)

            self.process_staticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

