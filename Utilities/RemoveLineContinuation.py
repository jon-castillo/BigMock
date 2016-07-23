import sys
import os
import re
import StringIO

def removeLineContinuation( buf ):
    input = buf.split('\n')
    output = ""
    for line in input:
        pattern = re.compile(r'^(.*?)(\\){0,1}$')
        match = pattern.match( line )
        if match is not None:
            if match.group(1) is not None:
                output+=match.group(1)
            if match.group(2) is None:
                output+='\n'

    return output

def main():
    if len(sys.argv) is not 2:
        print "Please provide source header to process."
        print "example:"
        print (sys.argv)[0] + " c:\sources\source.hpp"
        return
    else:
        filename = (sys.argv)[1]
        if not os.path.isfile(filename):
            print "not a file!"
            return
        raw = open(filename).read()
        #buf = StringIO.StringIO(raw)
        output = removeLineContinuation(raw)

        out = open(filename+".out",'w')

        print "output:\n"+output
        for line in output:
            out.write(line) 
if __name__ == '__main__':
    main()
