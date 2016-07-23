def sub_regexmodifier_repeating(input):
    output = '(?:'+input+')+'
    return output

def sub_regexmodifier_match(input):
    output = '('+input+')'
    return output

def sub_regexmodifier_optional(input):
    output = '(?:'+input+'){0,1}'
    return output

def sub_regexmodifier_capture(input):
    output = '('+input+')'
    return output



str_regexpattern_core_space = '(?:\s+)'
str_regexpattern_core_spaceOrNoSpace = '(?:\s*)'
str_regexpattern_core_value = '(?:[\w:_]+)'
str_regexpattern_core_repeatedreferencedereference = '(?:[\*\&]*)'
str_regexpattern_core_variableName = '(?:[~\w:_\<\>]+)'
str_regexpattern_core_memberName = '(?:[~\w:_\<\>\+\-\*\/\=]+)(?:\s*?)(?:\[\s*?\]){0,1}'
str_regexpattern_core_fxpointer = '(?:static)\s*?(?:[\w]*?)\s*?\(\s*?(?:[\w\s:\*]*(?:const){0,1}[\w]*\s*(?:\[\s*\]){0,1})\s*\)\s*\([\w]*\)'
str_regexpattern_core_variableType =                        \
    sub_regexmodifier_optional(                             \
        'const' +                                           \
        str_regexpattern_core_spaceOrNoSpace                \
    ) +                                                     \
    str_regexpattern_core_variableName +                    \
    sub_regexmodifier_optional(                             \
        str_regexpattern_core_spaceOrNoSpace +              \
        str_regexpattern_core_repeatedreferencedereference  \
    )

str_regexpattern_method_specifierFront = '(?:(?:virtual|explicit|FINAL|inline|static)\s+)+'
str_regexpattern_method_returnType = str_regexpattern_core_variableType+ str_regexpattern_core_space
str_regexpattern_method_parameterlist =                     \
    sub_regexmodifier_repeating(                            \
        str_regexpattern_core_spaceOrNoSpace +              \
        str_regexpattern_core_variableType +                \
        str_regexpattern_core_spaceOrNoSpace +                       \
        sub_regexmodifier_optional(                         \
            str_regexpattern_core_variableName +            \
            sub_regexmodifier_optional(                     \
                str_regexpattern_core_spaceOrNoSpace +      \
                '=' +                                       \
                str_regexpattern_core_spaceOrNoSpace +      \
                str_regexpattern_core_variableName          \
            )                                              \
        ) +                                                 \
        sub_regexmodifier_optional(                     \
            str_regexpattern_core_spaceOrNoSpace +      \
            ','                                         \
        ) \
    )

str_regexpattern_nm_method_parameter = \
        sub_regexmodifier_optional(                         \
            'const' +  \
            str_regexpattern_core_spaceOrNoSpace \
        ) \
     + \
        str_regexpattern_core_variableType  \
     +                \
    str_regexpattern_core_spaceOrNoSpace +              \
    sub_regexmodifier_optional(                         \
            str_regexpattern_core_variableName          \
         +            \
        sub_regexmodifier_optional(                     \
            str_regexpattern_core_spaceOrNoSpace +      \
            '=' +                                       \
            str_regexpattern_core_spaceOrNoSpace +      \
                str_regexpattern_core_variableName          \
            \
        )                                               \
    )                                             \


str_regexpattern_method_parameter =                     \
    str_regexpattern_core_spaceOrNoSpace +              \
    sub_regexmodifier_capture(                          \
        sub_regexmodifier_optional(                         \
            'const' +  \
            str_regexpattern_core_spaceOrNoSpace \
        ) \
    ) + \
    sub_regexmodifier_capture(                          \
        str_regexpattern_core_variableType) +                \
    str_regexpattern_core_spaceOrNoSpace +              \
    sub_regexmodifier_optional(                         \
        sub_regexmodifier_capture(                          \
            str_regexpattern_core_variableName 
        ) +            \
        sub_regexmodifier_optional(                     \
            str_regexpattern_core_spaceOrNoSpace +      \
            '=' +                                       \
            str_regexpattern_core_spaceOrNoSpace +      \
            sub_regexmodifier_capture(                          \
                str_regexpattern_core_variableName          \
            ) \
        )                                               \
    )


str_regexpattern_method_initializerlist =                   \
    sub_regexmodifier_repeating(                            \
        str_regexpattern_core_variableName +                \
        str_regexpattern_core_spaceOrNoSpace +              \
        '\(' +                                              \
        str_regexpattern_core_spaceOrNoSpace +              \
        str_regexpattern_core_value +                       \
        str_regexpattern_core_spaceOrNoSpace +              \
        '\)' +                                              \
        sub_regexmodifier_optional(                         \
            '\s*,\s*'                                       \
        )                                                   \
    )

str_regexpattern_method_specifierBack = '(?:(?:override|final|const)\s*)+'

str_regexpattern_nm_method_cppmethod=                                                  \
    sub_regexmodifier_optional('static'+str_regexpattern_core_spaceOrNoSpace) +                                           \
    sub_regexmodifier_optional(str_regexpattern_method_specifierFront ) +                    \
    sub_regexmodifier_optional(str_regexpattern_method_returnType) +                         \
    str_regexpattern_core_memberName+'\s*'+'\(' +                                         \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional(str_regexpattern_method_parameterlist) +                                \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    '\)'+                                                                           \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional(                             \
        ':' +                                               \
        str_regexpattern_core_spaceOrNoSpace +                                          \
        str_regexpattern_method_initializerlist)                     \
     + \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional(str_regexpattern_method_specifierBack) +                      \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional('[;|{]')

str_regexpattern_m_method_cppmethod=                                                  \
    '^' +                                                                           \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional(sub_regexmodifier_capture('static')+str_regexpattern_core_spaceOrNoSpace) +                                           \
    sub_regexmodifier_capture(sub_regexmodifier_optional(str_regexpattern_method_specifierFront )) +                    \
    sub_regexmodifier_capture(sub_regexmodifier_optional(str_regexpattern_method_returnType)) +                         \
    sub_regexmodifier_capture(str_regexpattern_core_memberName)+'\s*'+'\(' +                                         \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_capture(sub_regexmodifier_optional(str_regexpattern_method_parameterlist)) +                                \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    '\)'+                                                                           \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional(                             \
        ':' +                                               \
        str_regexpattern_core_spaceOrNoSpace +                                          \
        sub_regexmodifier_capture(str_regexpattern_method_initializerlist))                     \
     + \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_capture(sub_regexmodifier_optional(str_regexpattern_method_specifierBack)) +                      \
    str_regexpattern_core_spaceOrNoSpace +                                          \
    sub_regexmodifier_optional('[;|{]')


str_regexpattern_nm_normalbracket=r'(?:{)'
str_regexpattern_nm_enum=r'(?:typedef\s+){0,1}enum\s+(?:\w+){0,1}'
#str_regexpattern_nm_class=r'(?:class\s+)(?:[\w:]+)'
str_regexpattern_nm_class=r'(?:class)\s+(?:[\w]+)\s*(?::){0,1}(?:(?:\s*(?:(?:public|protected|private)\s+){0,1}[\w:]*?\s*[,\n\r])+){0,1}'
str_regexpattern_nm_struct=r'(?:typedef\s+){0,1}struct(?:\s+[\w:]+){0,1}'
str_regexpattern_nm_directive =r'#.*?(?:\n|\r)'
str_regexpattern_nm_doubleInclusion = r'#\s*?(?:ifndef|define).*?_(?:H(?:PP){0,1}_*)\s*?(?:(?:\n)|(?:\r))'
str_regexpattern_nm_extern = r'extern.*?(?:{|(?:\n|\r)|;)'
str_regexpattern_nm_cfunction = str_regexpattern_nm_method_cppmethod
str_regexpattern_nm_cglobalvar = r'[\w]+\s+[\w]+\s*(?:\:\s*[\w]*\s*){0,1}(?:\s*=\s*[\w]+){0,1}'
str_regexpattern_nm_namespace = r'namespace\s+[\w]+'
str_regexpattern_nm_typedef = r'typedef[\w\s\(\)\*\&\,\:]*?;'
str_regexpattern_nm_closebracket = r'}(?:(?:\s|\r|\n)*?[\w]+(?:\s|\r|\n)*?;){0,1}'
str_regexpattern_nm_accessspecifier = r'(?:public\:|private\:|protected\:)'
str_regexpattern_nm_enumentity = r'(?:\s*(?:\w*)\s*(?:=\s*(?:\w*)){0,1}\s*(?:,|\n|\r)+)'

str_regexpattern_m_normalbracket=r'[\s\n\r]*?({)'
str_regexpattern_m_enum=r'[\s\n\r]*?(typedef\s+){0,1}(enum)\s+(\w+){0,1}'
#str_regexpattern_m_class=r'[\s\n\r]*?(class\s+)([\w:]+)'
str_regexpattern_m_class=r'[\s\n\r]*?(class)\s+([\w]+)\s*(?::){0,1}((?:\s*(?:(?:public|protected|private)\s+){0,1}[\w:]*?\s*[,\n\r])+){0,1}'
str_regexpattern_m_struct=r'[\s\n\r]*?(typedef\s+){0,1}(struct)(\s+[\w:]+){0,1}'
str_regexpattern_m_directive =r'[\s\n\r]*?#(.*?)(?:\n|\r)'
str_regexpattern_m_doubleInclusion = r'[\s\n\r]*?#\s*?(ifndef|define)\s*(.*?_(?:H(?:PP){0,1}_*?))'
str_regexpattern_m_extern = r'[\s\n\r]*?(extern)(.*?)(?:{|(?:\n|\r)|;)'
str_regexpattern_m_cfunction = str_regexpattern_m_method_cppmethod
str_regexpattern_m_cglobalvar = r'[\s\n\r]*?([\w]+)\s+([\w]+)\s*(?:\:\s*([\w])*\s*){0,1}(?:\s*=\s*([\w]+)){0,1}'
str_regexpattern_m_namespace = r'[\s\n\r]*?(namespace)\s+([\w]+)'
str_regexpattern_m_typedef = r'(typedef)([\w\s\(\)\*\&\,\:]*?);'
str_regexpattern_m_closebracket = r'}(?:(\s|\r|\n)*?[\w]+(\s|\r|\n)*?;){0,1}'
str_regexpattern_m_accessspecifier =  r'(public|private|protected)\:'
str_regexpattern_m_enumentity = r'(?:\s*(\w*)\s*(?:=\s*(\w*)){0,1}\s*(,){0,1})'
