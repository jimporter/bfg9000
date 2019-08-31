%{
#include <stdio.h>
#include <stdlib.h>

int yylex();
void yyerror(const char* s);
%}

%define api.value.type {double}
%token T_NUM T_ADD T_SUB T_MUL T_DIV T_LPAR T_RPAR T_NEWLINE T_EXIT
%left T_ADD T_SUB
%left T_MUL T_DIV

%%

input:
    %empty
  | input line
;

line:
    T_NEWLINE
  | expression T_NEWLINE { printf(" = %g\n", $1); }
  | T_EXIT T_NEWLINE     { exit(0); }
;

expression:
    T_NUM                        { $$ = $1; }
  | expression T_ADD expression  { $$ = $1 + $3; }
  | expression T_SUB expression  { $$ = $1 - $3; }
  | expression T_MUL expression  { $$ = $1 * $3; }
  | expression T_DIV expression  { $$ = $1 / $3; }
  | T_LPAR expression T_RPAR     { $$ = $2; }
;

%%

int main() {
  return yyparse();
}

void yyerror(const char* s) {
  fprintf(stderr, "%s\n", s);
}
