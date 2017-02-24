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
            remove_comment(cursor, replacementlist)
            remove_entity(cursor, replacementlist)


    def process_cxxmethod(self, cursor, replacementlist, staticmethodlist, settings, is_template = False):
        force_singleton = settings.oFlag_MockOptions.makeSingleton
        force_overriding_cpp = settings.oFlag_MockOptions.makeOverridingCpp
        # enGetType is better unmocked:
        if cursor.spelling == "enGetType":
            return
        # this is a macro that should not be mocked:
        if cursor.spelling == "DECLARE_EXTENSION":
            return
        # this is a macro that should not be mocked:
        if cursor.spelling == "DECLARE_TYPEID":
            return
        # this is a macro that should not be mocked:
        if cursor.spelling == "AUTIL_DISALLOW_COPY_AND_ASSIGN":
            return

        tokens = [token.spelling for token in cursor.get_tokens()]
        arguments = [argument.spelling for argument in cursor.get_arguments()]

        i = 0
        returntype = ''
        argumentlist = ''
        while tokens[i] in specifier_list:
            i = i + 1

        while i<len(tokens) and tokens[i] != cursor.spelling \
                and tokens[i] != 'operator':
            returntype = returntype + tokens[i] + ' '
            i = i + 1

        if i<len(tokens) and tokens[i] == 'operator':
            return

        while i<len(tokens) and tokens[i] != '(':
            i = i + 1
        i = i + 1

        #while i<len(tokens) and tokens[i] != ';' and tokens[i] != '{':
        while i < len(tokens) and tokens[i] != ')' :
            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i]
            argumentlist += ' '
            i = i + 1

        #get rid of last space:
        while len(argumentlist) != 0 and (argumentlist[-1] == ' ' or argumentlist[-1] == ')'):
            argumentlist=argumentlist[:-1]


        if argumentlist == 'void' or argumentlist == '':
            argumentlist = ''

        buffer = ''


        if force_overriding_cpp == True:
            buffer += returntype + ' ' + os.path.splitext(os.path.basename(settings.sourceFile))[0] + "::" + cursor.spelling + '(' + argumentlist +") {\n"
            buffer += "        " + os.path.splitext(os.path.basename(settings.sourceFile))[0] + "_Mocked::get_instance()." + cursor.spelling + "(" +','.join(arguments)+ ");\n"
            buffer += "    }"
            staticmethodlist.append(buffer)

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

        if settings.oFlag_MockOptions.makeOverridingCpp:
            if cursor.kind is CursorKind.CONSTRUCTOR:
                buffer = buffer + '_Mocked'
            elif cursor.kind is CursorKind.DESTRUCTOR:
                buffer = buffer + '_Mocked'

        buffer = buffer + ','
        buffer = buffer + returntype
        buffer = buffer + '('
        buffer = buffer + argumentlist
        buffer = buffer + '));'

        if cursor.is_static_method() or force_singleton ==True:
            staticmethodlist.append(buffer)

        if cursor.is_static_method():
            buffer = 'static '

        if cursor.is_static_method() or force_singleton == True:
            buffer = returntype + \
                     cursor.spelling + "(" + \
                     argumentlist + ") {\n" + \
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

        while i<len(tokens) and tokens[i] != ';' and tokens[i] != '{':
            # get rid of specifiers:
            if tokens[i] in specifier_list:
                i = i + 1
                continue

            # get rid of default values:
            if tokens[i] == '=':
                i = i + 2
                continue
            argumentlist = argumentlist + tokens[i]
            argumentlist += ' '
            i = i + 1

        #get rid of last space:
        while len(argumentlist) != 0 and (argumentlist[-1] == ' ' or argumentlist[-1] == ')'):
            argumentlist=argumentlist[:-1]

        if argumentlist == 'void' or argumentlist == '':
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

        buffer = ""

        buffer += returntype + \
                 cursor.spelling + "( " + \
                 argumentlist + " ) {\n" + \
                 "\t/*  Shared Mock via Singleton Class */\n" + \
                 "\t"

        if (not "void" in returntype) and (returntype != "") :
            buffer = buffer + "return "
        if 0:
            #jon - c methods are wrongly mocked
            buffer = buffer + \
                     os.path.splitext(settings.baseFile)[0] + "_Mocked" + "_" + \
                 cursor.spelling + "(" + \
                 ', '.join(arguments) + ");\n" + \
             "}"
        else:
            buffer = buffer + \
                     os.path.splitext(settings.baseFile)[0] + "_Mocked" + "::get_instance()." + \
                 cursor.spelling + "(" + \
                 ', '.join(arguments) + ");\n" + \
             "}"


        extent = cursor.extent
        entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end, buffer);
        replacementlist.append(entry)


    def process_CXXAccessSpecifier(self, cursor, replacementlist, settings):
        if cursor.access_specifier is AccessSpecifier.PROTECTED:
            extent = cursor.extent
            buffer = ''
            buffer += '/* BigMock: Protected Members are made accessible */\n'
            buffer += 'public:\n'
            entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end, buffer)
            replacementlist.append(entry)

    def process_constructor(self, cursor, replacementlist, settings ):
        if settings.oFlag_MockOptions.makeOverridingCpp:
            tokens = [token for token in cursor.get_tokens()]

            buffer = ''
            i = 0
            while i < len(tokens):
                if cursor.spelling == tokens[i].spelling:
                    buffer = buffer + cursor.spelling + '_Mocked' + ' '
                else:
                    buffer = buffer + tokens[i].spelling + ' '
                i += 1

            buffer = buffer[:-1]
            extent = cursor.extent

            entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end,
                                         buffer)
            replacementlist.append(entry)

    def process_destructor(self, cursor, replacementlist, settings):
        if settings.oFlag_MockOptions.makeOverridingCpp:
            tokens = [token for token in cursor.get_tokens()]

            buffer = ''
            i = 0
            while i < len(tokens):
                if cursor.spelling[1:] == tokens[i].spelling:
                    buffer = buffer + tokens[i].spelling + '_Mocked' + ' '
                else:
                    buffer = buffer + tokens[i].spelling + ' '
                i += 1

            buffer = buffer[:-1]
            extent = cursor.extent

            entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extent.start, extent.end,
                                         buffer)
            replacementlist.append(entry)


    def process_class(self, cursor, replacementlist, settings):

        if settings.oFlag_MockOptions.makeOverridingCpp:
            tokens = [token for token in cursor.get_tokens()]

            buffer = ''
            i = 0
            while tokens[i].spelling != '{':
                buffer = buffer + tokens[i].spelling + ' '
                i += 1

            buffer = buffer[:-1]
            buffer += "_Mocked\n{\n"


            buffer = buffer + '\tpublic:\n'
            buffer = buffer + '\tstatic ' + os.path.splitext(settings.baseFile)[0] + '_Mocked& get_instance()\n'
            buffer = buffer + '\t{\n'
            buffer = buffer + '\t\tstatic '+ os.path.splitext(settings.baseFile)[0] + '_Mocked oInstance;\n'
            buffer = buffer + '\t\treturn oInstance;\n'
            buffer = buffer + '\t}\n\n'


            extentstart = cursor.extent
            extentend = tokens[i].extent

            entry = ReplacementListEntry(ReplacementListEntry.type.REPLACEMENT, extentstart.start, extentend.end, buffer)
            replacementlist.append(entry)


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

                elif c.kind is CursorKind.CONSTRUCTOR:
                    self.process_constructor(c, replacementlist, settings)

                elif c.kind is CursorKind.DESTRUCTOR:
                    self.process_destructor(c, replacementlist, settings)

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

                elif c.kind is CursorKind.CXX_ACCESS_SPEC_DECL:
                    self.process_CXXAccessSpecifier(c, replacementlist, settings)

            if settings.oFlag_MockOptions.makeOverridingCpp:
                self.process_overridingcpp_list(cursor, replacementlist, replacementlist_staticmethods, settings)
            else:
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

                elif c.kind is CursorKind.CXX_ACCESS_SPEC_DECL:
                    self.process_CXXAccessSpecifier(c, replacementlist, settings)

            self.process_cxxstaticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

    def process_overridingcpp_list(self, cursor, replacementlist, replacementlist_staticmethods, setting):
        buffer = ''

        outfilename2= os.path.splitext((setting.baseFile))[0]+'.cpp'
        outfile = open(outfilename2, 'w')

        namespace_hierarchy = []
        c = cursor.lexical_parent
        while c.kind is not CursorKind.TRANSLATION_UNIT:
            namespace_hierarchy.append(c.spelling)
            c = c.lexical_parent
        namespace_hierarchy.reverse()


        buffer = buffer + "/* This file was generated by BigMock.py */ \n\n"
        buffer = buffer + "/* Please take #include directives from source HPP and place them here */ \n\n"

        buffer = buffer + "#include \"" + os.path.splitext(setting.baseFile)[0] +'_Mocked.hpp' +"\"\n\n"

        if len(replacementlist_staticmethods) != 0:

            for namespace in namespace_hierarchy:
                buffer = buffer + 'namespace ' +namespace + '{\n'

            buffer = buffer + '\n'

            for entry in replacementlist_staticmethods:
                buffer = buffer + "    " + entry
                buffer = buffer + '\n'
            buffer = buffer + '};\n'

            buffer = buffer + '\n'

            for namespace in namespace_hierarchy:
                buffer = buffer + '}\n'


            outfile.write(buffer)

        outfile.close()

    def process_cstaticmethod_list(self, cursor, replacementlist, replacementlist_staticmethods, additionalstring, setting):
        buffer = ''

        outfilename2= os.path.splitext((setting.baseFile))[0]+'_Mocked.hpp'
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
