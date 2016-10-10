#!/usr/bin/env python
#  BigMock.py
# convert headers to google mock v2
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

def process_c_method( cursor, replacementlist, staticmethodlist, settings, is_template = False ):
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
         os.path.splitext(settings.baseFile)[0] + "_Mocked" + "::get_instance()." + \
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

def process_method( cursor, replacementlist, staticmethodlist, settings, is_template = False ):
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

    if cursor.is_static_method() or force_singleton == True:
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

def process_c_staticmethod_list(cursor, replacementlist, replacementlist_staticmethods, setting):
    buffer = ''
    if len(replacementlist_staticmethods) != 0:
        buffer = buffer + 'class ' +os.path.splitext(setting.baseFile)[0]+'_Mocked\n'
        buffer = buffer + '{\n'
        buffer = buffer + '\tpublic:\n'
        buffer = buffer + '\tstatic ' + os.path.splitext(setting.baseFile)[0] + '_Mocked& get_instance()\n'
        buffer = buffer + '\t{\n'
        buffer = buffer + '\t\tstatic '+ os.path.splitext(setting.baseFile)[0] + '_Mocked oInstance;\n'
        buffer = buffer + '\t\treturn oInstance;\n'
        buffer = buffer + '\t}\n'

        for entry in replacementlist_staticmethods:
            buffer = buffer + "\t" + entry
            buffer = buffer + '\n'
        buffer = buffer + '};\n'

        extent = cursor.extent
        entry = replacementlist_entry(replacementlist_entry_type.INSERTION, extent.start, extent.start, buffer)
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


def process_class(cursor, replacementlist, settings):
    replacementlist_staticmethods = []
    if cursor.is_definition():

        for c in cursor.get_children():


            if c.kind is CursorKind.CXX_METHOD:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    #convert to Mocked method:
                    process_method(c, replacementlist, replacementlist_staticmethods, settings)

            #elif c.kind is CursorKind.FIELD_DECL:
                # Retain private Field Declarations so that initializer lists remain unchanged.

            elif c.kind is CursorKind.CLASS_DECL:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class(c, replacementlist, settings)

            elif c.kind is CursorKind.STRUCT_DECL:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class(c, replacementlist, settings)

            elif c.kind is CursorKind.CLASS_TEMPLATE:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class_template(c, replacementlist, settings)

            elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                if c.access_specifier is AccessSpecifier.PRIVATE:
                    # private methods will never be used by test framework so remove them.
                    remove_entity(c, replacementlist)
                    remove_comment(c, replacementlist)
                else:
                    process_class_template_partial_specialization(cursor, settings)

        process_staticmethod_list( cursor, replacementlist, replacementlist_staticmethods )

def process_class_template(cursor, replacementlist, settings):
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
                process_method(c, replacementlist, replacementlist_staticmethods, settings, True )
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

def perform_replace(filename, replacementlist, settings):
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
                if j == replacementlist[listindex].start_line.column - 1 and i == replacementlist[listindex].start_line.line -1:
                    buffer = buffer + replacementlist[ listindex ].buffer.replace("\n","\n"+" "*j)
                    if replacementlist[ listindex ] .type == replacementlist_entry_type.REPLACEMENT:
                        j = replacementlist[ listindex ].end_line.column
                        i = replacementlist[ listindex ].end_line.line-1
                        line = code[i]
                    elif replacementlist[ listindex ] .type == replacementlist_entry_type.DELETION:
                        j = replacementlist[ listindex ].end_line.column
                        i = replacementlist[ listindex ].end_line.line-1
                        line = code[i]

                    listindex = listindex + 1
                    if listindex >= len(replacementlist):
                        break

                else:
                    #per character copy:
                    buffer = buffer + line[j]
                    j = j+1

            i=i+1;
        else:
            buffer = buffer + line
            i = i +1

    #print buffer
    if not settings.oFlag_Heading.noHeader:
        printHeader(fwrite,settings)
    fwrite.write(buffer)



def process_class_template_partial_specialization(cursor, replacementlist, settings):
    print "todo: process_class_template_partial_spec"

class flag_heading:
    def __init__(self):
        self.noHeader = False
        self.noDateTime = False

class flag_mockOptions:
    def __init__(self):
        self.makeSingleton = False

class options:
    def __init__(self):
        self.oFlag_Heading = flag_heading()
        self.oFlag_MockOptions = flag_mockOptions()
        self.sourceFile = ""
        self.destFile = ""
        self.isolatedFile = ""
        self.baseFile = ""

def analyze_clang_tree(cursor, replacementlist, settings):
    cstaticmethodlist = []

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
                    process_class(c, replacementlist, settings)
                elif c.kind is CursorKind.STRUCT_DECL:
                    process_class(c, replacementlist, settings)
                elif c.kind is CursorKind.CLASS_TEMPLATE:
                    process_class_template(c, replacementlist, settings)
                elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                    process_class_template_partial_specialization(c, replacementlist, settings)
                elif c.kind is CursorKind.CONSTRUCTOR:
                    continue
                elif c.kind is CursorKind.DESTRUCTOR:
                    continue
                elif c.kind is CursorKind.CXX_METHOD:
                    #remove inlines except for enGetType :)
                    # enGetType (Continental-Corporation): Retain definition for enGetType
                    if c.semantic_parent is not None:
                        if c.spelling != "enGetType":
                            remove_entity(c, replacementlist)
                elif c.kind is CursorKind.FUNCTION_DECL:
                    #this must be a c type method
                    print "C type method found! - TODO - " + c.spelling
                    process_c_method(c, replacementlist, cstaticmethodlist, settings, False)
                else:
                    analyze_clang_tree(c, replacementlist, settings)

    if cstaticmethodlist != []:
        process_c_staticmethod_list(cursor,replacementlist,cstaticmethodlist, settings)



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
    test = False
    parser = OptionParser("usage: %prog [options] {filename}")
    parser.add_option("-s", "--make-singleton", action="store_true",  default = False,
                      help="Share properties of this class for all instances")
    parser.add_option("-n", "--no-header", action="store_true", default=False,
                      help="Don't add heading comment to output file")
    parser.add_option("-d", "--no-datetime", action="store_true", default=False,
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

    oSettings = options()
    oSettings.oFlag_MockOptions.makeSingleton = opts.make_singleton
    oSettings.oFlag_Heading.noDateTime = opts.no_datetime
    oSettings.oFlag_Heading.noHeader = opts.no_header
    oSettings.sourceFile = filename
    oSettings.destFile = get_out_filename(filename)
    oSettings.baseFile = os.path.basename(filename)
    oSettings.isolatedFile = '__isolation__\\' + oSettings.baseFile

    #perform isolation
    print "source: ".ljust(13) + oSettings.sourceFile
    print "destination: ".ljust(13) + oSettings.destFile

    if not os.path.exists("__isolation__"):
        os.makedirs("__isolation__")
    copyfile(filename,oSettings.isolatedFile)
    args[0] = oSettings.isolatedFile

    #################################################################
    # remove tabs
    filedata = None
    with open(oSettings.isolatedFile, 'r') as file:
        filedata = file.read()
    # Replace the target string
    filedata = filedata.replace('\t', '    ')
    # Write the file out again
    with open(oSettings.isolatedFile, 'w') as file:
        file.write(filedata)
    ####################################################################

    Config.set_library_file(os.path.join(os.path.dirname(__file__), 'Clang/bin/libclang.dll'))
    Config.set_library_path('Clang/bin')
    Config.set_compatibility_check(False)

    args.append("-Xclang")
    args.append("-ast-dump")
    args.append("-fsyntax-only")
    args.append("-style=Google")
    print "command: ".ljust(13)+"clang " + str(args) + "\n"

    index = Index.create()
    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    replacementlist=[]
    analyze_clang_tree(tu.cursor, replacementlist, oSettings)
    dump_replacement_list(replacementlist)
    perform_replace(oSettings.isolatedFile, replacementlist, oSettings)

    rmtree("__isolation__")

def printHeader( fwrite, settings ):
     fwrite.write( "/**************************************************/\n" )
     fwrite.write( "/* BIGMOCK STAMP OF APPROVAL " .ljust(50) + "*/\n" )
     fwrite.write( "/* This header was generated by BigMock.py " .ljust(50) + "*/\n")
     if not settings.oFlag_Heading.noDateTime:
         fwrite.write( ("/* generated: " + datetime.datetime.now().strftime('%d %b %Y, %H:%M')).ljust(50) +"*/\n" )
     fwrite.write( "/**************************************************/\n\n" )
     fwrite.write("#include <gmock/gmock.h>\n")
     fwrite.write("#include <gtest/gtest.h>\n\n")

if __name__ == '__main__':
    main()
