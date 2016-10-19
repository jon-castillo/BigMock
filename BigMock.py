#!/usr/bin/env python
#  BigMock.py
# source to source transformation tool to convert headers to google mock
# jonCastillo July 23 2016
#
# v3.1.2 October 19,2016 - Improved algorithm for seeking end of methods.
#                        - Abstracted remove_entity and remove_comment from replacementlist.
#
# https://github.com/joncastillo/BigMock

import sys
import os
import datetime
import Rules.Default

from shutil import copyfile
from shutil import rmtree
from optparse import OptionParser, OptionGroup

from ReplacementList.ReplacementList import ReplacementList

sys.path.append(os.path.join(os.path.dirname(__file__), 'Clang/bindings/python'))
from clang.cindex import Config
from clang.cindex import Index
from clang.cindex import CursorKind

class Rule(object):
    def __init__ (self):
        self.process_cxxmethod_inline = None
        self.process_cxxmethod = None
        self.process_cmethod = None
        self.process_class = None
        self.process_class_template = None
        self.process_class_template_partial_specialization = None
        self.process_cstaticmethod_list = None

    def initRules(self, ruleClass):
        self.process_cxxmethod_inline = getattr(ruleClass, 'process_cxxmethod_inline', None)
        self.process_cxxmethod = getattr(ruleClass, 'process_cxxmethod', None)
        self.process_cmethod = getattr(ruleClass, 'process_cmethod', None)
        self.process_class = getattr(ruleClass, 'process_class', None)
        self.process_class_template = getattr(ruleClass, 'process_class_template', None)
        self.process_class_template_partial_specialization = getattr(ruleClass, 'process_class_template_partial_specialization', None)
        self.process_cstaticmethod_list = getattr(ruleClass, 'process_cstaticmethod_list', None)

def get_out_filename(source_filename):
    basename = os.path.basename(source_filename)
    outfilename = os.path.join(os.getcwd(), basename)
    return outfilename

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
        self.rule = Rule()
        self.sourceFile = ""
        self.destFile = ""
        self.isolatedFile = ""
        self.baseFile = ""
        self.quiet = False

def analyze_clang_tree(cursor, replacementlist, settings):
    cstaticmethodlist = []
    cmethodbufferlist = []
    for c in cursor.get_children():
        flag_first_level = False
        # only first level classes and structures are processed here
        if c.lexical_parent is None:
            flag_first_level = True
        else:
            #print "debug: " + c.spelling + " " + c.lexical_parent.spelling + " " + str(c.kind)
            if c.lexical_parent.kind is not CursorKind.CLASS_DECL:
                if c.lexical_parent.kind is not CursorKind.STRUCT_DECL:
                    if c.lexical_parent.kind is not CursorKind.CLASS_TEMPLATE:
                        flag_first_level = True

        if flag_first_level is True:
            if c.kind is CursorKind.CLASS_DECL:
                if settings.rule.process_class is not None:
                    settings.rule.process_class(c, replacementlist, settings)
            elif c.kind is CursorKind.STRUCT_DECL:
                if settings.rule.process_class is not None:
                    settings.rule.process_class(c, replacementlist, settings)
            elif c.kind is CursorKind.CLASS_TEMPLATE:
                if settings.rule.process_class_template is not None:
                    settings.rule.process_class_template(c, replacementlist, settings)
            elif c.kind is CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
                if settings.rule.process_class_template_partial_specialization is not None:
                    settings.rule.process_class_template_partial_specialization(c, replacementlist, settings)
            elif c.kind is CursorKind.CONSTRUCTOR:
                #process_inline_constructor(c, replacementlist, settings)
                continue
            elif c.kind is CursorKind.DESTRUCTOR:
                #process_inline_destructor(c, replacementlist, settings)
                continue
            elif c.kind is CursorKind.CXX_METHOD:
                if settings.rule.process_cxxmethod_inline is not None:
                    settings.rule.process_cxxmethod_inline(c, replacementlist, settings)
            elif c.kind is CursorKind.FUNCTION_DECL:
                if settings.rule.process_cmethod is not None:
                    settings.rule.process_cmethod(c, replacementlist, cstaticmethodlist, cmethodbufferlist, settings )
            else:
                analyze_clang_tree(c, replacementlist, settings)

    if cstaticmethodlist != []:
        if settings.rule.process_cstaticmethod_list is not None:
            settings.rule.process_cstaticmethod_list(cursor,replacementlist,cstaticmethodlist, cmethodbufferlist, settings)

def main():
    test = False
    parser = OptionParser("usage: %prog [options] {filename}")
    parser.add_option("-s", "--make-singleton", action="store_true",  default = False,
                      help="Share properties of this class for all instances")
    parser.add_option("-n", "--no-header", action="store_true", default=False,
                      help="Don't add heading comment to output file")
    parser.add_option("-d", "--no-datetime", action="store_true", default=False,
                      help="Don't add source to output file heading comment")
    parser.add_option("-q", "--quiet", action="store_true", default=False,
                      help="Silence output")

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
    oSettings.quiet = opts.quiet
    oSettings.sourceFile = filename
    oSettings.destFile = get_out_filename(filename)
    oSettings.baseFile = os.path.basename(filename)
    oSettings.isolatedFile = '__isolation__\\' + oSettings.baseFile

    selected_rule = Rules.Default.Rule()
    oSettings.rule.initRules(selected_rule)

    #################################################################
    #copy to an isolation folder so that the source file is not modified in any way.
    if not oSettings.quiet:
        print "source: ".ljust(13) + oSettings.sourceFile
        print "destination: ".ljust(13) + oSettings.destFile

    if not os.path.exists("__isolation__"):
        os.makedirs("__isolation__")
    copyfile(filename,oSettings.isolatedFile)
    args[0] = oSettings.isolatedFile
    #################################################################

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
    if not oSettings.quiet:
        print "command: ".ljust(13)+"clang " + str(args) + "\n"

    index = Index.create()
    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    replacementlist=ReplacementList()
    analyze_clang_tree(tu.cursor, replacementlist, oSettings)
    if not oSettings.quiet:
        replacementlist.dump()
    buffer = replacementlist.perform_replace(oSettings.isolatedFile)

    fwrite = open(oSettings.destFile,'w')
    writeHeader(fwrite,oSettings)
    fwrite.write(buffer)

    rmtree("__isolation__")

def writeHeader( fwrite, settings ):
     fwrite.write( "/**************************************************/\n" )
     fwrite.write( "/* BIGMOCK STAMP OF APPROVAL " .ljust(50) + "*/\n" )
     fwrite.write( "/* This header was generated by BigMock.py " .ljust(50) + "*/\n")
     if not settings.oFlag_Heading.noDateTime:
         fwrite.write( ("/* generated: " + datetime.datetime.now().strftime('%d %b %Y, %H:%M')).ljust(50) +"*/\n" )
     fwrite.write( "/**************************************************/\n\n" )
     if os.path.splitext(os.path.basename(fwrite.name))[1] == '.hpp':
         # never include cpp headers inside c-type headers:
         fwrite.write("#include <gmock/gmock.h>\n")
         fwrite.write("#include <gtest/gtest.h>\n\n")
if __name__ == '__main__':
    main()
