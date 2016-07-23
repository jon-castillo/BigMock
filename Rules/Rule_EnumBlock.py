#rules for Enum Block:

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


#returns (found ,outstream, next_index)
def seekEntity(string,index,stack):
    found = False
    outstream = ""
    next_index = 0

    regex = r"[\s\n\r]*"+ \
         (sub_regexmodifier_capture( str_regexpattern_nm_closebracket    )) + '|' +  \
         (sub_regexmodifier_capture( str_regexpattern_nm_directive       )) + '|' +  \
         (sub_regexmodifier_capture( str_regexpattern_nm_enumentity      )) + '|' +  \
         r'(?:'+ \
         r'(?:'+ \
         (sub_regexmodifier_capture( str_regexpattern_nm_enum            )) + '|' +  \
         r')' + \
         r'(?:' + \
         r'(?:\s|\n|\r)*?([;|{])\s*?)' + \
         r')'

    pattern = re.compile(regex,re.DOTALL)
    match = pattern.match( string[index:] )

    # Rule for root follows:
    if match is not None:
        found = True
        next_index = index + match.end();
        is_block = (match.group(5) == "{")

        status = False;
        output = "";

        if (match.group(1) is not None):
            #DEBUG print "1"
            if (match.group(1) is '}'):
                stack.pop()
                output += '    ' * stack.size() +str(match.group(1))
                print output
        if (match.group(2) is not None):
            #DEBUG print "2"
            status, output = processDirective(match.group(0), False, stack)
        if (match.group(3) is not None):
            #DEBUG print "3"
            status, output = processEnumEntity(match.group(0), False, stack)
        if (match.group(4) is not None):
            #DEBUG print "4"
            status, output = processEnum(match.group(0), is_block, stack)            
  
        return True, next_index
    else:
        next_index = index + 1
        return False, next_index