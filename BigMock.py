#!/usr/bin/env python
#  BigMock.py
# convert headers to google mock v1
# jonCastillo July 23 2016

import sys
import os
import datetime

from shutil import copyfile
from shutil import rmtree

sys.path.append(os.path.join(os.path.dirname(__file__), 'Clang/bindings/python'))

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
    DELETION = 2

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

specifier_list = ["inline","const","override","final","virtual","mutable","explicit","extern","static","export","friend","noexcept"]

def remove_entity(cursor, replacementlist):
    extent = cursor.extent
    entry = replacementlist_entry(replacementlist_entry_type.DELETION, extent.start, extent.end, "");
    replacementlist.append(entry)

def remove_comment(cursor, replacementlist):
    commentRange = cursor.getCommentRange()
    if commentRange.start.line != 0:
        entry = replacementlist_entry(replacementlist_entry_type.DELETION, commentRange.start, commentRange.end, "");
        replacementlist.append(entry)

def process_method( cursor, replacementlist, staticmethodlist, is_template = False, force_singleton = True):

    # enGetType is better unmocked:
    if cursor.spelling == "enGetType":
        return

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
    if is_template is True:
        buffer = buffer + "_T"
    buffer = buffer + '('
    buffer = buffer + cursor.spelling
    buffer = buffer + ','
    buffer = buffer + returntype
    buffer = buffer + '('
    buffer = buffer + argumentlist
    buffer = buffer + '));'

    if cursor.is_static_method() or force_singleton == False:
        staticmethodlist.append(buffer)

        buffer = 'static '

        buffer = buffer + \
                 returntype + \
                 cursor.spelling + "( " + \
                 argumentlist + " ) {\n" + \
                 "\t/*  Shared Mock via Singleton Class */\n" + \
                 "\t"

        #if returntype != 'void' or returntype != '':
        #    buffer = buffer + returntype
        buffer = buffer + "return "

        buffer = buffer + \
                 cursor.lexical_parent.spelling + "_Mocked" + "::get_instance()." + \
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

        buffer = buffer +'\n'+' '*extent_start.start.column+'{\n'
        entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent_start.start, tokenlist[i].extent.end, buffer);
        replacementlist.append(entry)

        for c in cursor.get_children():


            if c.kind is CursorKind.CXX_METHOD:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    #convert to Mocked method:
                    process_method(c, replacementlist, replacementlist_staticmethods )

            #elif c.kind is CursorKind.FIELD_DECL:
                # Retain private Field Declarations so that initializer lists remain unchanged.

            elif c.kind is CursorKind.CLASS_DECL:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class(c, replacementlist)

            elif c.kind is CursorKind.STRUCT_DECL:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class(c, replacementlist)

            elif c.kind is CursorKind.CLASS_TEMPLATE:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class_template(c, replacementlist)

            elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class_template_partial_specialization(cursor)

        process_staticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

def process_class_template(cursor, replacementlist):
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
        entry = replacementlist_entry(replacementlist_entry_type.REPLACEMENT, extent_start.start, tokenlist[i].extent.end, buffer);
        replacementlist.append(entry)

        for c in cursor.get_children():
            if c.kind is CursorKind.CXX_METHOD:
                process_method(c, replacementlist, replacementlist_staticmethods, True )
            elif c.kind is CursorKind.CLASS_DECL:
                process_class(c, replacementlist)
            elif c.kind is CursorKind.STRUCT_DECL:
                process_class(c, replacementlist)
            elif c.kind is CursorKind.CLASS_TEMPLATE:
                process_class_template(c, replacementlist)
            elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                process_class_template_partial_specialization(cursor)

        process_staticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

def get_out_filename(source_filename):
    basename = os.path.basename(source_filename)
    #outfilename = os.path.splitext(basename)[0] + ".out"
    outfilename = os.path.join(os.getcwd(), basename)
    return outfilename

def perform_replace(filename, replacementlist):
    code = open(filename).readlines()
    outfilename = get_out_filename(filename)
    fwrite = open( outfilename, 'w')
    replacementlist.sort()

    i = 0
    listindex = 0
    buffer = ''
    while i < len(code):
        line = code[i]
        if listindex < len(replacementlist) and i == replacementlist[listindex].start_line.line - 1:
            j = 0
            while j < len(line):
                if j == replacementlist[listindex].start_line.column - 1:
                    buffer = buffer + replacementlist[ listindex ].buffer.replace("\n","\n"+" "*j)
                    if replacementlist[ listindex ] .type == replacementlist_entry_type.REPLACEMENT or replacementlist[ listindex ] .type == replacementlist_entry_type.DELETION:
                        j = replacementlist[ listindex ].end_line.column
                        i = replacementlist[ listindex ].end_line.line-1
                        line = code[i]

                    listindex = listindex + 1
                    if listindex >= len(replacementlist):
                        break

                else:
                    buffer = buffer + line[j]
                    j = j+1


            i=i+1;
        else:
            buffer = buffer + line
            i = i +1

    #print buffer
    printHeader(fwrite)
    fwrite.write(buffer)



def process_class_template_partial_specialization(cursor, replacementlist):
    print "todo: process_class_template_partial_spec"


def analyze_clang_tree(cursor, replacementlist):
    for c in cursor.get_children():
        flag_first_level = False
        flag_parsable = False
        # only first level classes and structures are processed here
        if c.lexical_parent is not None:
            #print "debug: " + c.spelling + " " + c.lexical_parent.spelling + " " + str(c.kind)
            if c.lexical_parent.kind is not CursorKind.CLASS_DECL:
                if c.lexical_parent.kind is not CursorKind.STRUCT_DECL:
                    if c.lexical_parent.kind is not CursorKind.CLASS_TEMPLATE:
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
                elif c.kind is CursorKind.CONSTRUCTOR:
                    continue
                elif c.kind is CursorKind.DESTRUCTOR:
                    continue
                elif c.kind is CursorKind.CXX_METHOD:
                    #remove inlines except for enGetType :)
                    # enGetType (Continental-Corporation): Retain definition for enGetType
                    if c.spelling != "enGetType":
                        remove_entity(c, replacementlist)
                else:
                    analyze_clang_tree(c, replacementlist)



class flag_heading:
    def __init__(self):
        self.str_author = ''
        self.noHeader = False
        self.noSource = False
        self.noDateTime = False

class settings:
    def __init__(self):
        oFlag_Heading = flag_heading()

def dump_replacement_list (replacementlist):
    replacementlist.sort()

    for i in replacementlist:
        if i.type == replacementlist_entry_type.INSERTION:
            print "Insertion:".ljust(12) + (" At (" + str(i.start_line.line+1) + "," + str(i.start_line.column+1) + ") : ").ljust(29) + i.buffer.replace("\n", "\\n")
        elif i.type == replacementlist_entry_type.DELETION:
            print "Deletion:".ljust(12) + (" From (" + str(i.start_line.line+1) + "," + str(i.start_line.column+1) + ")").ljust(16) + ("To (" + str(i.end_line.line+1) + "," + str(i.end_line.column+1) + ")").ljust(13)
        else:
            print "Replacement:".ljust(12) + (" From (" + str(i.start_line.line+1) + "," + str(i.start_line.column+1) + ")").ljust(16) + ("To (" + str(i.end_line.line+1) + "," + str(i.end_line.column+1) + ")").ljust(13) + " : " + i.buffer.replace("\n", "\\n")

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

    #perform isolation
    print "source: ".ljust(13) + filename
    print "destination: ".ljust(13) + get_out_filename(filename)

    if not os.path.exists("__isolation__"):
        os.makedirs("__isolation__")
    copyfile(filename,'__isolation__\\'+os.path.basename(filename))
    args[0] = '__isolation__\\'+os.path.basename(filename)

    #################################################################
    filedata = None
    with open('__isolation__\\'+os.path.basename(filename), 'r') as file:
        filedata = file.read()
    # Replace the target string
    filedata = filedata.replace('\t', '    ')
    # Write the file out again
    with open('__isolation__\\'+os.path.basename(filename), 'w') as file:
        file.write(filedata)
    ####################################################################


    Config.set_library_file(os.path.join(os.path.dirname(__file__), 'Clang/bin/libclang.dll'))
    Config.set_library_path('Clang/bin')
    Config.set_compatibility_check(False)

    args.append("-Xclang")
    args.append("-ast-dump")
    #args.append("-fsyntax-only")
    args.append("-style=Google")
    print "command: ".ljust(13)+"clang " + str(args) + "\n"

    index = Index.create()
    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    replacementlist=[]
    analyze_clang_tree(tu.cursor, replacementlist)

    dump_replacement_list(replacementlist)
    perform_replace('__isolation__\\'+os.path.basename(filename), replacementlist)

    rmtree("__isolation__")

def printHeader( fwrite ):
     fwrite.write( "/**************************************************/\n" )
     fwrite.write( "/* BIGMOCK STAMP OF APPROVAL " .ljust(50) + "*/\n" )
     fwrite.write( "/* This header was generated by BigMock.py " .ljust(50) + "*/\n")
     fwrite.write( ("/* generated: " + datetime.datetime.now().strftime('%d %b %Y, %H:%M')).ljust(50) +"*/\n" )
     fwrite.write( "/**************************************************/\n\n" )
     fwrite.write("#include <gmock/gmock.h>\n")
     fwrite.write("#include <gtest/gtest.h>\n\n")


def processHeader(filename, code_wo_comments, ):
    # printHeader(filename, basename ,fwrite)
    print "processHeader"

if __name__ == '__main__':
    main()
