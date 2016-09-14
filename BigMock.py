#!/usr/bin/env python
#  BigMock.py
# convert headers to google mock v1
# jonCastillo July 23 2016

import sys
import os
import datetime

#from Rules import Rule_MainBlock
#from Rules import Rule_ClassBlock
#from Rules import Rule_EnumBlock
#from Rules import Rule_MethodBlock

from LexerDataStructures.LexerStack import Stack
from LexerDataStructures.LexerStack import leveltype

sys.path.append('Clang/bindings/python')

from clang.cindex import Config
from clang.cindex import Index
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
from clang.cindex import TokenKind
from clang.cindex import AccessSpecifier

from pprint import pprint
from optparse import OptionParser, OptionGroup

global opts
global indention_count

def block_starts(cursor):
    global indention_count
    if cursor.kind is CursorKind.NAMESPACE or \
       cursor.kind is CursorKind.TYPEDEF_DECL or \
       cursor.kind is CursorKind.CLASS_DECL or \
       cursor.kind is CursorKind.UNION_DECL or \
       cursor.kind is CursorKind.ENUM_DECL:
           if cursor.is_definition():
               print "    "*indention_count + "{"
               indention_count = indention_count+1;

def block_ends(cursor):
    global indention_count
    if cursor.kind is CursorKind.NAMESPACE or \
       cursor.kind is CursorKind.TYPEDEF_DECL or \
       cursor.kind is CursorKind.CLASS_DECL or \
       cursor.kind is CursorKind.UNION_DECL or \
       cursor.kind is CursorKind.ENUM_DECL:
           if cursor.is_definition():
               indention_count = indention_count-1;
               print "    "*indention_count + "}" + "// end " + str(cursor.kind.name) + " " + str(cursor.spelling)


def analyze_clang_node(cursor):
    if cursor.kind is CursorKind.NAMESPACE:
        # print "    "*indention_count + "NAMESPACE" + ": " + str(cursor.spelling)
        print "    " * indention_count + "namespace " + str(cursor.spelling)
    elif cursor.kind is CursorKind.PREPROCESSING_DIRECTIVE:
        print "    "*indention_count + "PREPROCESSING_DIRECTIVE" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.MACRO_DEFINITION:
        print "    "*indention_count + "MACRO_DEFINITION" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.INCLUSION_DIRECTIVE:
        print "    "*indention_count + "INCLUSION_DIRECTIVE" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.USING_DECLARATION:
        print "    "*indention_count + "USING_DECLARATION" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.TYPEDEF_DECL:
        if cursor.access_specifier is AccessSpecifier.PUBLIC\
            or cursor.access_specifier is AccessSpecifier.INVALID:
            actual = ''
            tokens = [token.spelling for token in cursor.get_tokens()]
            actual = ' '.join(tokens)

            print "    "*indention_count + actual
            print "    " * indention_count + cursor.spelling

    elif cursor.kind is CursorKind.CLASS_DECL:
        if cursor.access_specifier is AccessSpecifier.PUBLIC\
            or cursor.access_specifier is AccessSpecifier.INVALID:
            actual = ''
            if not cursor.is_definition():
                tokens = [token.spelling for token in cursor.get_tokens()]
                actual = ' '.join(tokens)

            else:
                tokens = [token.spelling for token in cursor.get_tokens()]

                i = 0
                while tokens[i] != '{':
                    actual = actual + tokens[i] + ' ';
                    i = i+1

            print "    "*indention_count + actual

            #print  "    "*indention_count + (("FORWARD_CLASS_DECL","CLASS DECL")[cursor.is_definition()]) + ": "  + str(cursor.spelling)
    elif cursor.kind is CursorKind.STRUCT_DECL:
        if cursor.is_definition():
            if cursor.access_specifier is AccessSpecifier.PUBLIC \
                    or cursor.access_specifier is AccessSpecifier.INVALID \
                    or cursor.access_specifier is AccessSpecifier.PROTECTED:

                tokens = [token for token in cursor.get_tokens()]

                actual = ''
                for i, token in enumerate(tokens):
                    if token.kind == TokenKind.COMMENT:
                        actual = actual + token.spelling + '\n' + "    " * indention_count
                    else:
                        if token.spelling == ';':
                            actual = actual + ";" + '\n' + "    " * indention_count
                        elif token.spelling == '{':
                            actual = actual + "{\n" + "    " * indention_count
                        else:
                            actual = actual + (" ", "")[i == 0] + token.spelling
                if tokens[i].spelling != ';':
                    actual = actual + ';'
            print "    " * indention_count + actual

    elif cursor.kind is CursorKind.UNION_DECL:
        print  "    "*indention_count + (("FORWARD_UNION_DECL","UNION DECL")[cursor.is_definition()]) + ": "  + str(cursor.spelling)
    elif cursor.kind is CursorKind.ENUM_DECL:
        print  "    "*indention_count + (("FORWARD_ENUM_DECL","ENUM DECL")[cursor.is_definition()]) + ": "  + str(cursor.spelling)

    elif cursor.kind is CursorKind.CXX_METHOD:
        if cursor.access_specifier is AccessSpecifier.PUBLIC:
            if cursor.lexical_parent.kind is CursorKind.CLASS_DECL:
                #print "    "*indention_count + "CXX_METHOD" + ": " + str(cursor.spelling)

                tokens = [token.spelling for token in cursor.get_tokens()]

                i = 0
                while tokens[i] == "virtual":
                    i = i + 1

                returntype = ''
                while tokens[i] != cursor.spelling and \
                        tokens[i] != 'new' and \
                        tokens[i] != 'delete':
                    returntype = returntype + " " + tokens[i]
                    i = i + 1

                while tokens[i] != "(":
                    i = i + 1

                # skip {
                i = i + 1

                argumentlist = ''
                while tokens[i] != ")":
                    if tokens[i] == "=":
                        i = i+2
                    else:
                        argumentlist = argumentlist + " " + tokens[i]
                        i = i + 1

                if cursor.is_const_method():
                    print "    "*indention_count + "MOCK_CONST_METHOD" + str(len([c for c in cursor.get_arguments()])) + "(" + str(cursor.spelling) +","+ returntype+ "(" +argumentlist + " )"+");"
                else:
                    print "    "*indention_count + "MOCK_METHOD" + str(len([c for c in cursor.get_arguments()])) + "(" + str(cursor.spelling) +","+ returntype+ "(" +argumentlist + " )"+");"

    elif cursor.kind is CursorKind.FUNCTION_TEMPLATE:
        print "    "*indention_count + "FUNCTION_TEMPLATE" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.CLASS_TEMPLATE:
        print "    "*indention_count + "CLASS_TEMPLATE" + ": " + str(cursor.spelling)
    elif cursor.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
        print "    "*indention_count + "CLASS_TEMPLATE_PARTIAL_SPECIALIZATION" + ": " + str(cursor.spelling)


        # Depth First Search for AST Tree:
def analyze_clang_tree(cursor):
    analyze_clang_node(cursor);

    block_starts(cursor);

    for c in cursor.get_children():
        analyze_clang_tree(c);

    block_ends(cursor);

class flag_heading:
    def __init__(self):
        self.str_author = '';
        self.noHeader = False;
        self.noSource = False;
        self.noDateTime = False

class settings:
    def __init__(self):
        oFlag_Heading = flag_heading()

def main():
    global opts
    global indention_count
    indention_count = 0
    oSettings = settings()
    parser = OptionParser("usage: %prog [options] {filename}")
    parser.add_option("-a", "--add-author", dest="oSettings.oFlag_Heading.str_author",
                      help="Add author to output header",
                      default="joncastillo@ieee.org")
    parser.add_option("-n", "--no-header",
                      action="store_true", dest="oSettings.oFlag_Heading.noHeader", default=False,
                      help="Don't add heading comment to output file")
    parser.add_option("-s", "--no-source",
                      action="store_true", dest="oSettings.oFlag_Heading.noSource", default=False,
                      help="Don't add source to output file heading comment")
    parser.add_option("-d", "--no-datetime",
                      action="store_true", dest="oSettings.oFlag_Heading.noDateTime", default=False,
                      help="Don't add source to output file heading comment")

    (opts, args) = parser.parse_args()
    if len(args) is not 1:
        print "Please provide source header to process."
        print "example:"
        print (sys.argv)[0] + " c:\sources\source.hpp"
        return
    else:
        filename = (args)[0]
        if not os.path.isfile(filename):
            print filename
            print "not a file!"
            return

    Config.set_library_file('Clang/bin/libclang.dll')
    Config.set_library_path('Clang/bin')
    Config.set_compatibility_check(False)

    args.append("-Xclang")
    args.append("-ast-dump")
    #args.append(TranslationUnit.PARSE_INCOMPLETE)
    #args.append(TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
    #args.append("-fsyntax-only")

    index = Index.create()
    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    analyze_clang_tree(tu.cursor);

def printHeader(filename, basename, fwrite, oSettings):
     fwrite.write( "/****************************************************************************************************/\n" )
     fwrite.write( ("/* " + basename).ljust(100) + "*/\n" )
     fwrite.write( "/****************************************************************************************************/\n" )
     fwrite.write( ("/* This file was generated by convert_to_mock.py").ljust(100) +"*/\n" )
     fwrite.write( ("/* Mocked from: " + filename).ljust(100) + "*/\n" )
     fwrite.write( ("/* generated: " + datetime.datetime.now().strftime('%d %b %Y, %H:%M')).ljust(100) +"*/\n" )
     fwrite.write( "/****************************************************************************************************/\n" )

def processHeader(filename, code_wo_comments, ):
    # printHeader(filename, basename ,fwrite)
    print "processHeader"

if __name__ == '__main__':
    print "done"
    main()
