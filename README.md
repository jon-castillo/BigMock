# BigMock
Automated Google Mock Header converter. A source to source transformation tool based on Clang's AST.

This tool is used for generating mock headers directly from C++ production codes. It is more powerful than the script found inside the google mock project as it uses the Clang compiler to generate an Abstract Syntax Tree and create mocked methods from them based on configurable rules. The tool runs very fast with little or no need of further processing.

There are some limitations most of which is caused by the fact the AST generation is supposed to be carried out after Pre Processing. But doing so will expand our headers into huge sources. For example, the usage of strange directives such as 

#define MY_FUNCTION(x) aFunction(x); 

MY_FUNCTION(1)

Compiles fine without the semicolon but when parsed by Clang, will cause the AST generator to terminate prematurely. One way to get such files succeed is to temporarily comment out such calls then restoring it after the tool parses this header.

The main reason for the creation of this tool is a common situation wherein test interfaces are not planned nor created upon the design of the system. Months later, when the project is realized, It has becomes extremely huge and the creation of test platforms becomes a difficult task. If the google mock test platform is selected, then this tool can parse entire project folders to automate the creation of mocked headers that would be almost impossible to create by hand.

The rules may be modified such that output files would work with any customized test platform.

This project, though functions very well, is in the working prototype stage and do not expect it to be beautifully modularly designed.
