# BigMock
Automated Google Mock Header converter. A source to source transformation tool based on Clang's AST.

This tool is used for generating mock headers directly from C++ production codes. It is more powerful than the script found inside the google mock project as it uses the Clang compiler to generate an Abstract Syntax Tree which is later then parsed based on configurable rules. The tool runs very fast with little or no need of further processing. All features of the original header such as comments, directives and formatting will remain intact.

There are some limitations. Most of which is caused by the fact the AST generation is supposed to be carried out after the Pre Processing stage. Running the preprocessor will expand our headers into huge files so this is not a solution.

An example of this limitation is when using strange directives such as 

    #define MY_FUNCTION(x) aFunction(x); 

    MY_FUNCTION(1)

This compiles fine without putting a semicolon after MY_FUNCTION(1). However, when parsed by Clang, the AST generator will terminate prematurely. One way to get such files to succeed would be to temporarily comment out such macros and then restoring it by hand once the tool completes parsing.

The main reason for the creation of this tool is a common situation wherein test interfaces are not planned nor created during the design of the system. Months later, much of the project would have become too dependent on these untestable interfaces and the creation of test platforms becomes a difficult task. If the google mock test platform is selected, then this tool can parse entire project folders to automate the creation of mocked headers. This will take too much of the developer's time to complete by hand.

The rules may be modified such that output files would work with any test platform.

This project, though functions very well, is in the working prototype stage. Do not expect it to be beautifully and modularly designed. :)
