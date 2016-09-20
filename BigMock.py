#!/usr/bin/env python
#  BigMock.py
# convert headers to google mock v1
# jonCastillo July 23 2016

import sys
import os
import datetime

sys.path.append('Clang/bindings/python')

from clang.cindex import Config
from clang.cindex import Index
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
from clang.cindex import TokenKind
from clang.cindex import AccessSpecifier
from clang.cindex import SourceLocation

from optparse import OptionParser, OptionGroup

global opts

class replacementlist_entry_type( object ):
    INSERTION = 0
    REPLACEMENT = 1

class replacementlist_entry( object ):

    def __init__ (self, type, start_line, end_line, buffer):
        self.type = type
        self.start_line = start_line
        self.end_line = end_line
        self.buffer = buffer

    def __lt__ (self, other):
        if self.start_line.line == other.start_line.line:
            if self.start_line.column == other.start_line.column:
                return self.type < other.type
            else:
                return self.start_line.column < other.start_line.column
        else:
            return self.start_line.line < other.start_line.line

def block_starts(cursor):
    if cursor.kind is CursorKind.NAMESPACE or \
       cursor.kind is CursorKind.TYPEDEF_DECL or \
       cursor.kind is CursorKind.CLASS_DECL or \
       cursor.kind is CursorKind.UNION_DECL or \
       cursor.kind is CursorKind.ENUM_DECL:

def block_ends(cursor):
    if cursor.kind is CursorKind.NAMESPACE or \
       cursor.kind is CursorKind.TYPEDEF_DECL or \
       cursor.kind is CursorKind.CLASS_DECL or \
       cursor.kind is CursorKind.UNION_DECL or \
       cursor.kind is CursorKind.ENUM_DECL:

specifier_list = ["inline","const","override","final","virtual","mutable","explicit","extern","static","export","friend","noexcept"]

def remove_entity(cursor, replacementlist):
    extent = cursor.extent
    entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent.start, extent.end, "");
    replacementlist.append(entry)


def process_method( cursor, replacementlist, staticmethodlist, force_all_static = False, force_all_singleton = True):
    tokens = [token.spelling for token in cursor.get_tokens()]
    arguments = [argument.spelling for argument in cursor.get_arguments()]

    i = 0
    returntype = ''
    argumentlist = ''
    while tokens[i] in specifier_list:
        i = i+1
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
    buffer = buffer + '('
    buffer = buffer + cursor.spelling
    buffer = buffer + ','
    buffer = buffer + returntype
    buffer = buffer + '('
    buffer = buffer + argumentlist
    buffer = buffer + '));';

    if cursor.is_static_method() or force_all_static == True or force_all_singleton == False:
        staticmethodlist.append(buffer)

        if force_all_singleton == False:
            buffer = "static "
        else:
            buffer = 'virtual '

        buffer = buffer + \
                 returntype + \
                 cursor.spelling + "( " + \
                 argumentlist + " ) {\n" + \
                 "\t/*  Shared Mock via Singleton Class */\n" + \
                 "\t"

        if returntype != 'void' or returntype != '':
            buffer = buffer + returntype

        buffer = buffer + \
                 cursor.lexical_parent.spelling + "_Mocked" + "::get_instance()." + \
                 cursor.spelling + "(" + \
                 argumentlist + ");\n" + \
                 "}"

    extent = cursor.extent
    entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent.start, extent.end, buffer);
    replacementlist.append(entry)


def process_staticmethod_list(cursor, replacementlist, replacementlist_staticmethods):
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
        entry = replacementlist_entry(replacementlist_entry_type.INSERTION, extent.start, extent.start, buffer)
        replacementlist.append(entry)


def process_class(cursor, replacementlist):
    replacementlist_staticmethods = []
    if cursor.is_definition():

        extent_start = cursor.extent
        tokens = cursor.get_tokens()
        tokenlist = [token for token in tokens ]

        buffer = ''
        i = 0
        while tokenlist[i].spelling != '{':
            buffer = buffer + tokenlist[i].spelling + ' '
            i = i + 1

        buffer = buffer +'\n{'
        entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent_start.start, tokenlist[i].extent.end, buffer);
        replacementlist.append(entry)

        for c in cursor.get_children():
            if c.kind is CursorKind.CXX_METHOD:
                process_method(c, replacementlist, replacementlist_staticmethods )
            elif c.kind is CursorKind.CLASS_DECL:
                process_class(c, replacementlist)
            elif c.kind is CursorKind.STRUCT_DECL:
                process_class(c, replacementlist)
            elif c.kind is CursorKind.CLASS_TEMPLATE:
                process_class_template(c, replacementlist)
            elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                process_class_template_partial_specialization(cursor)

        process_staticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

def perform_replace(filename, replacementlist):
    code = open(filename).readlines()
    basename = os.path.basename(filename)
    outfilename = os.path.splitext(basename)[0] + ".out"
    fwrite = open(".\\" + outfilename, 'w')

    replacementlist.sort()

    i = 0
    listindex = 0
    buffer = ''
    while i < len(code):
        line = code[i]
        if listindex < len(replacementlist) and i == replacementlist[listindex].start_line.line - 1:
            j = 0
            while j < len(line):
                if j == replacementlist[ listindex ].start_line.column - 1:
                    buffer = buffer + replacementlist[ listindex ].buffer.replace("\n","\n"+" "*j)
                    if replacementlist[ listindex ] .type == replacementlist_entry_type.REPLACEMENT:
                        j = replacementlist[ listindex ].end_line.column
                        i = replacementlist[ listindex ].end_line.line
                        line = code[i]

                    listindex = listindex + 1
                else:
                    buffer = buffer + line[j]
                    j = j+1
        else:
            buffer = buffer + line
            i = i +1

    print buffer
    printHeader(fwrite)
    fwrite.write(buffer)

def process_class_template(cursor, replacementlist):
    print "todo: process_class_template"

def process_class_template_partial_specialization(cursor, replacementlist):
    print "todo: process_class_template_partial_spec"


def analyze_clang_tree(cursor, replacementlist):
    if cursor.is_definition():
        block_starts(cursor);

    for c in cursor.get_children():
        flag_first_level = False
        flag_parsable = False
        # only first level classes and structures are processed here
        if c.semantic_parent is not None:
            if c.semantic_parent.kind is not CursorKind.CLASS_DECL:
                if c.semantic_parent.kind is not CursorKind.STRUCT_DECL:
                    if c.semantic_parent.kind is not CursorKind.CLASS_TEMPLATE:
                        flag_first_level = True

        if flag_first_level is True:
            # do not process forward declarations:
            if c.is_definition() is True:
                if c.kind is CursorKind.CLASS_DECL:
                    process_class(c, replacementlist)
                elif c.kind is CursorKind.STRUCT_DECL:
                    process_class(c, replacementlist)
                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    process_class_template(c, replacementlist)
                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    process_class_template_partial_specialization(c, replacementlist)
                elif c.kind is CursorKind.FUNCTION_DECL:
                    remove_entity(c, replacementlist)
                else:
                    analyze_clang_tree(c, replacementlist)

    if cursor.is_definition():
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
    args.append("-fsyntax-only")

    index = Index.create()
    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    replacementlist=[]
    analyze_clang_tree(tu.cursor, replacementlist)

    replacementlist.sort()
    for i in replacementlist:
        if i.type == replacementlist_entry_type.INSERTION:
            print "INSERTION AT: " + str(i.start_line.line) +"," + str(i.start_line.column) + ": " + i.buffer
        else:
            print "REPLACEMENT AT: Start: " + str(i.start_line.line) +"," + str(i.start_line.column) + ", End: " + str(i.end_line.line) + "," + str(i.end_line.column) + ": " + i.buffer

    originalfile = 'temp.txt'
    targetfile = 'out_temp.txt'
    #generate_mock(originalfile, targetfile, replacementlist)
    perform_replace(filename, replacementlist)

def printHeader( fwrite ):
     fwrite.write( "/**************************************************/\n" )
     fwrite.write( "/* BIGMOCK STAMP OF APPROVAL " .ljust(50) + "*/\n" )
     fwrite.write( "/* This header was generated by BigMock.py " .ljust(50) + "*/\n")
     fwrite.write( ("/* generated: " + datetime.datetime.now().strftime('%d %b %Y, %H:%M')).ljust(50) +"*/\n" )
     fwrite.write( "/**************************************************/\n\n" )

def processHeader(filename, code_wo_comments, ):
    # printHeader(filename, basename ,fwrite)
    print "processHeader"

if __name__ == '__main__':
    print "done"
    main()
