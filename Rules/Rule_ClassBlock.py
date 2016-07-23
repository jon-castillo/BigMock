#rules for Class Block:

import re

from RegexPatterns.Regex_Hpp import *
from LexerDataStructures.LexerStack import Stack
from LexerDataStructures.LexerStack import leveltype


def processEnumEntity(string, is_block, stack):
    outString = ""
    status = False
    pattern = re.compile(str_regexpattern_m_enumentity,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        outString += match.group(1)
        outString += " "
        if match.group(2) is not None:
            outString += "= "
            outString += match.group(2)
        if match.group(3) is not None:
            outString += match.group(3)

        outString = "    " * stack.size() + outString
        ###############################                                                    
        print outString                                                        
        ###############################                                                    
        return status, outString
    else:
        return status, outString
    
def processDirective(string, is_block, stack):
    outString = ""
    status = False
    pattern = re.compile(str_regexpattern_m_directive,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        outString += "#"
        outString += match.group(1)
        #outString += "\n"
        ###############################                                                    
        print outString                                                        
        ###############################                                                    
        return status, outString
    else:
        return status, outString

accessspecifierflag = False
def processAccessSpecifier(string, is_block, stack):
    global accessspecifierflag
    outString = ""
    status = False
    pattern = re.compile(str_regexpattern_m_accessspecifier,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        outString += match.group(1)
        #outString += "\n"
        ###############################                                                    
        print outString + ":"                                                        
        ###############################
        if outString == "private":
            accessspecifierflag = True
        else:
            accessspecifierflag = False

        outString = "    " * stack.size() + outString

        return status, outString
    else:
        return status, outString

def processEnum(string, is_block, stack):
    outString = "    " * stack.size()
    status = False

    pattern = re.compile(str_regexpattern_m_enum,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True

        if match.group(1) is not None:
            #typedef
            outString += match.group(1)

        #enum
        outString += " "
        outString += match.group(2)

        if match.group(3) is not None:
            #enumname
            outString += " "
            outString += match.group(3)

        if is_block is True:
            stack.push(leveltype.type_enum)
            outString += " {"
        else:
            outString += ";"

    ###############################                                                    
    print outString                                                        
    ###############################   
    return status, outString

def processClass(string, is_block, stack):
    outString = ""
    status = False

    pattern = re.compile(str_regexpattern_m_class,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True

        #class
        outString += match.group(1)
        outString += " "
        #xyz
        outString += match.group(2)

        if match.group(3) is not None:
            #:parent(xyz)
            outString += ":"
            outString += match.group(3)
            outString = outString.strip();

        if is_block is True:
            stack.push(leveltype.type_class)
            outString += " {"
        else:
            outString += ";"

    outString = "    " * stack.size() + outString
    ###############################                                                    
    print outString                                                        
    ###############################   
    return status, outString

def processStruct(string, is_block, stack):
    outString = "    " * stack.size()
    status = False

    pattern = re.compile(str_regexpattern_m_struct,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True

        if match.group(1) is not None:
            #typedef
            outString += match.group(1)
            outString += " "

        #struct
        outString += match.group(2)

        if match.group(3) is not None:
            #structname
            outString += " "
            outString += match.group(3)

        if is_block is True:
            stack.push(leveltype.type_struct)
            outString += " {"
        else:
            outString += ";"

    ###############################                                                    
    print outString                                                        
    ###############################   
    return status, outString

def processExtern(string, is_block, stack):
    outString = "    " * stack.size()
    status = False
    pattern = re.compile(str_regexpattern_m_extern,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        outString += match.group(1)
        outString += " "
        outString += match.group(2)
        #outString += "\n"
        ###############################                                                    
        print outString                                                        
        ###############################                                                    
        return status, outString
    else:
        return status, outString

def processOtherTypedef(string, is_block, stack):
    outString = ""
    status = False

    pattern = re.compile(str_regexpattern_m_typedef,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        if match.group(1) is not None and match.group(1) is not "":
            #str_regexpattern_method_specifierFront
            outString += match.group(1).strip()
            outString += " "
        if match.group(2) is not None and match.group(2) is not "":
            #str_regexpattern_method_returnType
            outString += match.group(2).strip()

        if is_block is True:
            stack.push(leveltype.type_method)
            outString += "{"
        else:
            outString += ";"

        outString = "    " * stack.size() + outString
        #outString += "\n"
    ###############################   
    print outString
    ###############################   
    return status, outString



def processCFunction(string, is_block, stack):
    outString = ""
    status = False

    pattern = re.compile(str_regexpattern_m_cfunction,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        if match.group(1) is not None and match.group(1) is not "":
            #str_regexpattern_method_specifierFront
            outString += match.group(1).strip()
            outString += " "
        if match.group(2) is not None and match.group(2) is not "":
            #str_regexpattern_method_returnType
            outString += match.group(2).strip()
            outString += " "
        if match.group(3) is not None and match.group(3) is not "":
            #str_regexpattern_core_memberName
            outString += match.group(3).strip()
            outString += " "
        if match.group(4) is not None and match.group(4) is not "":
            #str_regexpattern_method_parameterlist
            outString += '('
            outString += match.group(4).strip()
            outString += ')'
            outString += " "
        if match.group(5) is not None and match.group(5) is not "":
            #str_regexpattern_method_initializerlist
            outString += match.group(5).strip()
            outString += " "
        if match.group(6) is not None and match.group(6) is not "":
            #str_regexpattern_method_specifierBack
            outString += match.group(6).strip()
            outString += " "


        if is_block is True:
            stack.push(leveltype.type_method)
            outString += "{"
        else:
            outString += ";"

        outString = "    " * stack.size() + outString
        #outString += "\n"
    ###############################   
    print outString
    ###############################   
    return status, outString

def processCGlobalVar(string, is_block, stack):
    outString = ""
    status = False
    pattern = re.compile(str_regexpattern_m_cglobalvar,re.DOTALL)
    match = pattern.match( string )
    if match is not None:
        status = True
        outString += match.group(1)
        outString += " "
        outString += match.group(2)
        if match.group(3) is not None:
            outString += " "
            outString += " : "
            outString += match.group(3)        
        if match.group(4) is not None:
            outString += " "
            outString += " = "
            outString += match.group(4)
        outString += ";"

        outString = "    " * stack.size() + outString

        ###############################                                                    
        print outString                                                        
        ###############################                                                    
        return status, outString
    else:
        return status, outString


#returns (found ,outstream, next_index)
def seekEntity(string,index,stack):
    global accessspecifierflag

    found = False
    outstream = ""
    next_index = 0
    regex = r"[\s\n\r]*"+ \
         (sub_regexmodifier_capture( str_regexpattern_nm_directive       )) + '|' +  \
         (sub_regexmodifier_capture( str_regexpattern_nm_typedef      )) +  '|' + \
         (sub_regexmodifier_capture( str_regexpattern_nm_accessspecifier      )) +  '|' + \
         r'(?:'+ \
         r'(?:'+ \
             (sub_regexmodifier_capture( str_regexpattern_core_fxpointer)) + '|' +\
             (sub_regexmodifier_capture( str_regexpattern_nm_enum            )) + '|' +  \
             (sub_regexmodifier_capture( str_regexpattern_nm_class           )) + '|' +  \
             (sub_regexmodifier_capture( str_regexpattern_nm_struct          )) + '|' +  \
             (sub_regexmodifier_capture( str_regexpattern_nm_cfunction       )) + '|' +  \
             (sub_regexmodifier_capture( str_regexpattern_nm_cglobalvar      )) + \
         r')' + \
         r'(?:' + \
         r'(?:\s|\n|\r)*?([;|{])\s*?)' + \
         r')' + \
         r'|' + \
             (sub_regexmodifier_capture( str_regexpattern_nm_closebracket    )) + '|' + \
             (sub_regexmodifier_capture( str_regexpattern_nm_normalbracket   )) + '|' + \
             '(?:\s*DECLARE_TYPEID\(.*?\))' + '|'\
             '(?:\s*template.*?;)'


    pattern = re.compile(regex,re.DOTALL)
    match = pattern.match( string[index:] )
    # Rule for class/struct follows:
    if match is not None:
        found = True;
        next_index = index + match.end();
        is_block = (match.group(10) == "{")

        status = False;
        output = "";

        if (match.group(1) is not None):
            status, output = processDirective(match.group(0), is_block, stack)
        if (match.group(2) is not None):
            status, output = processOtherTypedef(match.group(0), is_block, stack)
        #TODO ACCESS SPECIFIER MUST BE PUSHED INTO STACK!
        #if (match.group(3) is not None):
            #status, output = processAccessSpecifier(match.group(0), is_block, stack)
            #print "ACCESS SPECIFIER FOUND! :" +  match.group(0) + "\n"                    
        if (match.group(4) is not None):
            if accessspecifierflag is False:
                #status, output = processFxPtr(match.group(0), is_block, stack) 
                print "    "*stack.size() + "// WARNING! Omitted FXPOINTER: " +  match.group(0) + "\n"           
        if (match.group(5) is not None):
            status, output = processEnum(match.group(0), is_block, stack)
        if (match.group(6) is not None):
            status, output = processClass(match.group(0), is_block, stack)
        if (match.group(7) is not None):
            status, output = processStruct(match.group(0), is_block, stack)
        if (match.group(8) is not None):
            if accessspecifierflag is False:
                status, output = processCFunction(match.group(0), is_block, stack)
        if (match.group(9) is not None):
            if accessspecifierflag is False:
                status, output = processCGlobalVar(match.group(0), is_block, stack)
   
        if (match.group(11) is not None):
            if (match.group(11)[0] is '}'):
                if stack.parent() == leveltype.type_class:
                    #TODO move this flag inside stack
                    accessspecifierflag = False;
                stack.pop()
                output += '    ' * stack.size() +str(match.group(11))
                print output
        if (match.group(12) is not None):
            stack.push(leveltype.type_normalbracket)
            output += '    ' * stack.size() +str(match.group(12))
            print output          


        return True, next_index
    else:
        next_index = index + 1
        return False, next_index