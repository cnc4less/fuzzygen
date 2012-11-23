from argparse import ArgumentParser
import argparse
import re
import collections

VERSION="1.0"

class FuzzyError(Exception):
    '''Exception raised anywhere in fuzzygen'''
    def __init__(self, token, message):
        self.message = message
        self.token = token

    def __str__(self):
        print('ERROR at Line %d: %s' % (self.token.line, self.message))

class Category:
    '''AST Node for a category specification and its curves'''
    def __init__(self, name, index):
        self.name = name
        self.cppName = name.upper()
        
        self.index = index
        self.curves = []

    def addCurve(self, function, params):
        self.curves.append((function, params))

    def key(self):
        return self.index

class Domain:
    '''AST Node for a domain specification and its categories'''
    def __init__(self, name, min, max):
        self.name = name
        self.cppName = name
        self.range = (min, max)
        self.categories = {}
        self.index = 0

    def addCategory(self, name):
        c = Category(name, self.index)
        self.index += 1
        self.categories[name] = c
        return c

class Expr:
    '''
        AST Node for antecedent expressions in if-then clauses

        Note that Expression nodes are expected to provide a translate()
        method which generates the C++ code to evaluate the expression.
    '''
    def __init__(self):
        0

    def translate(self):
        0

class ExLogical(Expr):
    '''
        Node for logical operators and, or and not.
        
        Not is defined as "op b" with a being None.
    '''
    def __init__(self, a, op, b):
        self.a = a
        self.op = op
        self.b = b

    def translate(self):
        if self.a:
            aTranslation = self.a.translate()
            bTranslation = self.b.translate()
            return "FuzzyLogic::f_{0}({1}, {2})".format(self.op, aTranslation, bTranslation)
        elif self.b:
            bTranslation = self.b.translate()
            return "FuzzyLogic::f_{0}({1})".format(self.op, bTranslation)
        else:
            raise RuntimeError("Translate for ExLogical had no operands")

class ExTerm(Expr):
    ''' AST Node for {var} is {category} expressions '''
    def __init__(self, var, domain, category):
        self.var = var
        self.domain = domain
        self.category = domain.categories[category]

    def translate(self):
        return "{0}.is({1}::{2})".format(self.var,
                                        self.domain.cppName,
                                        self.category.cppName)
    
class ExHedgedTerm(ExTerm):
    ''' AST Node for hedged terms, i.e., {var} is very {category} '''
    hedges = [ 'aLittle', 'slightly', 'very', 'extremely', 'veryVery',
               'somewhat', 'indeed' ]
    cppHedges = [ 'A_LITTLE', 'SLIGHTLY', 'VERY', 'EXTREMELY',
                  'VERY_VERY', 'SOMEWHAT', 'INDEED' ]
    hedgeMap = dict(zip(hedges, cppHedges))

    def __init__(self, var, domain, hedge, category):
        self.var = var
        self.hedge = hedge
        self.domain = domain
        self.category = domain.categories[category]

    def translate(self):
        return "{0}.is(FuzzyVariable::{hedge},{1}::{2})".format(self.var,
                                                self.domain.cppName,
                                                self.category.cppName,
                                                hedge=self.hedgeMap[self.hedge])

class Consequent:
    '''AST Node for consequents: {var} = {category} part that follows then'''
    def __init__(self, var, domain, category):
        self.var = var
        self.domain = domain
        self.category = category

    def translate(self):
        catEnum = self.domain.categories[self.category].cppName
        # TODO Add error is categeory does not exist in domain
        return "{var}.addMembership({className}::{category}, m);".format(
            var=self.var, category=catEnum, className=self.domain.cppName)

class FuzzyProgram:
    '''
        The logical 'mother' of the AST representation of a Fuzzy engine
        specification.  This object is used to build the symbol tables and
        AST's and to generate the header and cpp files.
    '''
    def __init__(self):
        self.vars = {}
        self.domains = {}
        self.rules = []

    def addVar(self, varName, direction, domainName):
        if domainName not in self.domains:
            raise FuzzyError(None, "Domain '%s' not declared" % domainName)
        elif varName in self.vars:
            raise FuzzyError(None, "Variable '%s' already declared" % varName)
        else:
            self.vars[varName] = (direction, self.domains[domainName])

    def addDomain(self, domain):
        if domain.name in self.domains:
            raise FuzzyError(None, "Domain '%s' already declared" % domain.name)
        else:
            self.domains[domain.name] = domain

    def addRule(self, ant, consequents):
        self.rules.append( (ant, consequents) )

    def generateHeader(self, emit):
        # Emit includes
        emit('#include <fuzzy.h>\n\n')

        for domainKey in sorted(self.domains):
            domain = self.domains[domainKey]
            # Emit domain class prolog
            emit("""
class {0} : public FuzzyVariable
{{
public:
""".format(domain.cppName))
            # Emit category enums
            for cat in sorted(domain.categories.values(), key=Category.key):
                emit("    static const int {0} = {1};\n".format(cat.cppName, cat.index))
            # Emit domain class epilog
            emit("""
    int minRange() const;
    int maxRange() const;
    float membership(int crispValue, int category) const;
};

""")
        # Emit variable declarations
        for var, (direction, domain) in self.vars.items():
            if direction=='in':
                baseClass = 'FuzzyInput'
            else:
                baseClass = 'FuzzyOutput'
            emit("extern {wrapper}<{className}> {var};\n".format(
                var=var, className=domain.name, wrapper=baseClass))
            
        # Emit rules
        emit("\nvoid runFuzzyEngine();\n")

    def generateBody(self, emit):
        emit('#include "fuzzy_engine.h"\n\n')
        # Emit variable declarations
        for var, (direction, domain) in self.vars.items():
            if direction=='in':
                baseClass = 'FuzzyInput'
            else:
                baseClass = 'FuzzyOutput'
            emit("{wrapper}<{className}> {var};\n".format(
                var=var, className=domain.name, wrapper=baseClass))
            
        for domainKey in sorted(self.domains):
            domain = self.domains[domainKey]
            emit("""
/*
 * DOMAIN {0}
 */
int {0}::minRange() const {{ return {1[0]}; }}

int {0}::maxRange() const {{ return {1[1]}; }}

float {0}::membership(int crispValue, int category) const
{{
    float m = 0;
""".format(domain.cppName, domain.range))
            for cat in sorted(domain.categories.values(), key=Category.key):
                for curveFunc, params in cat.curves:
                    fields = { 'category': cat.cppName,
                               'curve': curveFunc,
                               'params': ', '.join(str(x) for x in params) }
                    emit("    m = fmax(m, category=={category} ? {curve}(crispValue, {params}) : 0);\n".format(**fields))
            emit("    return m;\n}\n")
        emit("""
void runFuzzyEngine()
{
    float m;
    
""")
        # Reset output variables
        anyEmitted = False
        for var, (direction, domain) in self.vars.items():
            if direction=='out':
                emit("    {var}.reset();\n".format(var=var));
                anyEmitted=True
        if anyEmitted:
            emit("\n");
            
        for antecedent, consequents in self.rules:
            # Translate antecedent into assignment to 'm'
            expr = antecedent.translate()
            emit("    m = {0};\n".format(expr))
            # For each consequent, assign its variable to its category based on m
            for consequent in consequents:
                emit("    {0}\n".format(consequent.translate()))
        emit("}\n")


Token = collections.namedtuple('Token', ['typ', 'value', 'line', 'column'])

class Lexer:
    '''Lexical analyzer ("lexer") for this translator'''
    def __init__(self):
        self.currentToken = ""
        self.keywords = ['if', 'then', 'and', 'or', 'not',
                         'is', 'domain', 'from', 'to', 'vars', 'rules']
        token_specification = [
            ('NUMBER',  r'\d+(\.\d*)?'), # Integer or decimal number
            ('ASSIGN',  r':='),          # Assignment operator
            ('END',     r';'),           # Statement terminator
            ('COMMA',   r','),
            ('DIRECTION', r'\b(in|out)\b'),
            ('ID',      r'[A-Za-z][A-Za-z0-9]*'),   # Identifiers
            ('NEWLINE', r'\n'),          # Line endings
            ('SKIP',    r'[ \t]'),       # Skip over spaces and tabs
            ('LB',      r'{'),
            ('RB',      r'}'),
            ('LP',      r'\('),
            ('RP',      r'\)'),
            ('COLON',   r':'),
            ('EQUALS',  r'=')
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        self.get_token = re.compile(tok_regex).match
        self.line = 1
        self.pos = self.line_start = 0
        self.tokens = []

    def tokenize(self,s):
        mo = self.get_token(s)
        while mo is not None:
            typ = mo.lastgroup
            if typ == 'NEWLINE':
                self.line_start = self.pos
                self.line += 1
            elif typ != 'SKIP':
                val = mo.group(typ)
                if typ == 'ID' and val in self.keywords:
                    typ = val
                self.tokens.append(Token(typ, val, self.line, mo.start()-self.line_start))
                # print(self.tokens[-1])
            self.pos = mo.end()
            mo = self.get_token(s, self.pos)
        if self.pos != len(s):
            raise RuntimeError('Unexpected character %r on line %d' %(s[self.pos], self.line))

    def next(self):
        if len(self.tokens) > 0:
            x = self.tokens[0]
            del self.tokens[0]
            return x
        else:
            return None

    def pushBack(self, token):
        self.tokens.insert(0, token)


class Parser:
    '''Recursive-decent parser for the Fuzzy language.

        This is a hand-built RDP--no tools were used in the making of this
        parser.'''
    def __init__(self,tokenStream):
        self.stream = tokenStream
        self.lookahead = tokenStream.next()
        self.progTree = FuzzyProgram()

    def match(self, tokenType, msg = 'Expected {expected} but got {found}'):
        '''Tests if the current look ahead token is tokenTyp.

           If not, then, this raises a FuzzyError on this lookahead token (for
           line # reporting).'''
        if self.lookahead.typ == tokenType:
            self.lookahead = self.stream.next()
        else:
            raise FuzzyError(self.lookahead,
                             msg.format(expected=tokenType,
                                        found=self.lookahead.typ,
                                        foundValue=self.lookahead.value))

    def matchId(self):
        '''Matches an ID token and returns its value'''
        x = self.lookahead.value
        self.match('ID')
        return x

    def matchNum(self):
        '''Matches a number and returns it as an integer'''
        x = int(self.lookahead.value)
        self.match('NUMBER')
        return x
    
    def prog(self):
        '''First entry point for the recursive-decent parser'''
        # print("ENTERED prog")
        try:
            while self.lookahead.typ == 'domain':
                self.domain()
                
            if self.lookahead.typ == 'vars':
                self.varDefinitions()

            if self.lookahead.typ == 'rules':
                self.rules()
                
        except FuzzyError as fuzzErr:
            if fuzzErr.token is None:
                raise FuzzyError(self.lookahead, fuzzErr.message)
            else:
                raise

    def domain(self):
        # print("ENTERED domain")
        self.match('domain')
        
        domainName = self.matchId()
        
        self.match('from')

        rangeMin = self.matchNum()
        
        self.match('to')

        rangeMax = self.matchNum()

        domain = Domain(domainName, rangeMin, rangeMax)
        self.progTree.addDomain(domain)
        
        self.match('LB')
        while self.lookahead.typ == 'ID':
            self.categoryDefinition(domain)
        self.match('RB')

    def categoryDefinition(self, domain):
        categoryName = self.matchId()
        category = domain.addCategory(categoryName)

        self.match('EQUALS')
        
        self.curveDefinition(category)
        while self.lookahead.typ=='COMMA':
            self.match('COMMA')
            self.curveDefinition(category)
        
        self.match('END')

    def curveDefinition(self, category):
        curveFunction = self.matchId()
        self.match('LP')
        params = []
        params.append(self.matchNum())
        while self.lookahead.typ=='COMMA':
            self.match('COMMA')
            params.append(self.matchNum())
        self.match('RP')
        category.addCurve(curveFunction, params)
        
    def varDefinitions(self):
        self.match('vars')
        self.match('LB')
        while self.lookahead.typ == 'ID':
            varIds = [self.matchId()]
            while self.lookahead.typ == 'COMMA':
                self.match('COMMA')
                varIds.append( self.matchId() )
            self.match('COLON')
            direction = self.lookahead.value
            self.match('DIRECTION', msg='Expected in or out by found {foundValue}')
            domainName = self.matchId()
            self.match('END')
            for var in varIds:
                self.progTree.addVar(var, direction, domainName)
        self.match('RB')

    def rules(self):
        # print("ENTERED rules")
        self.match('rules')
        self.match('LB')
        while self.lookahead.typ=='if':
            self.rule()
        self.match('RB')

    def rule(self):
        # print("ENTERED rule")
        self.match('if')
        ante = self.expr()
        self.match('then')
        
        consequents = [self.consequent()]
        while self.lookahead.typ=='COMMA':
            self.match('COMMA')
            consequents.append( self.consequent() )
            
        self.match('END')
        self.progTree.addRule(ante, consequents)

    def expr(self):
        root = self.disjunct()
        while self.lookahead.typ=='or':
            self.match('or')
            self.disjunct()
            root = ExLogical(root, 'or', b)
        return root

    def disjunct(self):
        root = self.conjunct()
        while self.lookahead.typ=='and':
            self.match('and')
            b = self.conjunct()
            root = ExLogical(root, 'and', b)
        return root

    def conjunct(self):
        if self.lookahead.typ=='LP':
            self.match('LP')
            e = self.expr()
            self.match('RP')
            return e
        elif self.lookahead.typ=='ID':
            e = self.termPos()
            if e:
                return e
            e = self.termNeg()
            if e:
                return e
            raise FuzzyError(self.lookahead, "Term in expression is invalid")
    
    def termPos(self):
        varName = self.matchId()
        if varName not in self.progTree.vars:
            raise FuzzyError(self.lookahead, "Variable %s is undefined" % varName)
        domain = self.progTree.vars[varName][1]
        self.match('is')
        if self.lookahead.typ!='ID':
            return None
        e = self.hedgedCategory(domain)
        if e:
            return ExHedgedTerm(varName, domain, e[0], e[1])
        e = self.matchId()
        if e not in domain.categories:
            raise FuzzyError(self.lookahead, "Category not in variable's domain")
        return ExTerm(varName, domain, e)

    def termNeg(self):
        varName = self.matchId()
        if varName not in self.progTree.vars:
            raise FuzzyError(self.lookahead, "Variable %s is undefined" % varName)
        domain = self.progTree.vars[varName][1]
        self.match('is');
        if self.lookahead.typ!='NOT':
            return None
        self.match('not');
        e = self.hedgedCategory(domain)
        if e:
            return ExLogical(None, 'not', ExHedgedTerm(varName, domain, e[0], e[1]))
        e = self.matchId()
        if e not in domain.categories:
            raise FuzzyError(self.lookahead, "Category not in variable's domain")
        return ExLogical(None, 'not', ExTerm(varName, domain, e))

    def hedgedCategory(self, domain):
        hedge = None
        hedges = [ 'aLittle', 'slightly', 'very', 'extremely', 'veryVery',
                   'somewhat', 'indeed' ]
        if self.lookahead.typ=='ID' and self.lookahead.value in hedges:
            hedge = self.matchId()
            categoryName = self.matchId()
            if categoryName not in domain.categories:
                raise FuzzyError(self.lookahead, "Category not in variable's domain")
            return (hedge, categoryName)
        else:
            return None

    def consequent(self):
        varName = self.matchId()
        if varName not in self.progTree.vars:
            raise FuzzyError(self.lookahead, "Undeclared variable {0}".format(varName))
        domain = self.progTree.vars[varName][1]
        self.match('ASSIGN')
        catName = self.matchId()
        return Consequent(varName, domain, catName)


if __name__ == '__main__':
    # Get command-line options
    parser = ArgumentParser(usage="%(prog)s [options] source.fzy")
    parser.add_argument("-o", "--output", dest="baseOutput", metavar='BASE_PATH',
                    help="Root filename for .h and .cpp output files")
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('source', type=argparse.FileType())
    args = parser.parse_args()

    f = args.source
    fzyBaseName = args.baseOutput or "fuzzy_engine"
    fzyHeaderFilename = fzyBaseName + ".h"
    fzyBodyFilename = fzyBaseName + ".cpp"
    
    # Read the fzy file into memory
    fzySource = f.read()
    f.close()
    
    # Parse
    l = Lexer()
    l.tokenize(fzySource)
    p = Parser(l)
    p.prog()
    
    # Generate header
    f = open(fzyHeaderFilename, 'w')
    p.progTree.generateHeader(f.write)
    f.close()
    
    # Generate body
    f = open(fzyBodyFilename, 'w')
    p.progTree.generateBody(f.write)
    f.close()
    
