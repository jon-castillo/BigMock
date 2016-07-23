#rules for Method Block:

import re

from RegexPatterns.Regex_Hpp import *
from LexerDataStructures.LexerStack import Stack
from LexerDataStructures.LexerStack import leveltype


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

#rules for Method
#returns (found ,outstream, next_index)
def seekEntity(string,index,stack):
    found = False
    outstream = ""
    next_index = 0

    regex = r"[\s\n\r]*"+ \
         (sub_regexmodifier_capture( str_regexpattern_nm_directive      )) + '|' +  \
         (sub_regexmodifier_capture( str_regexpattern_nm_closebracket   )) + '|' + \
         (sub_regexmodifier_capture( str_regexpattern_nm_normalbracket  ))


    pattern = re.compile(regex,re.DOTALL)
    match = pattern.match( string[index:] )
    # Rule for root follows:
    if match is not None:
        found = True;
        next_index = index + match.end();
        is_block = False

        status = False;
        output = "";

        if (match.group(1) is not None):
            status, output = processDirective(match.group(0), is_block, stack)
        if (match.group(2) is not None):
            if (match.group(2) is '}'):
                stack.pop()
            print '    ' * stack.size() +str(match.group(2))
        if (match.group(3) is not None):
            stack.push(leveltype.type_normalbracket)
            print '    ' * stack.size() +str(match.group(3))
  
        return True, next_index
    else:
        next_index = index + 1
        return False, next_index
