%{
#include <stdlib.h>

#include "calc.tab.h"

void yyerror(const char* s);
%}

%option noyywrap
%option nounput
%option noinput

%%

[ \t]              ;
[0-9]+(\.[0-9]+)?  { yylval = atof(yytext); return T_NUM; }
\n                 { return T_NEWLINE; }
"+"                { return T_ADD; }
"-"                { return T_SUB; }
"*"                { return T_MUL; }
"/"                { return T_DIV; }
"("                { return T_LPAR; }
")"                { return T_RPAR; }
"exit"             { return T_EXIT; }
.                  { yyerror("syntax error"); exit(1); }

%%
