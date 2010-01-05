#!/usr/bin/env python
import re

def convert_text(in_body):
    '''
    You can call convert_text directly to convert shpaml markup
    to HTML markup.
    '''
    return convert_shpaml_tree(in_body)

PASS_SYNTAX = 'PASS'
TAG_WHITESPACE_ATTRS = '(\S+)(s*?)(.*)'
TAG_AND_ID = '(.*)#(.*)'
DOT_FOR_CLASSES = '.'
DIV_SHORTCUT = '[\.#]'

def syntax(regex):
    def wrap(f):
        f.regex = regex
        return f
    return wrap

@syntax('(\s*)(.*)')
def INDENT(m):
    prefix, line = m.groups()
    line = line.rstrip()
    if line == '':
        prefix = ''
    return prefix, line

@syntax('^([<{]\S.*)')
def RAW_HTML(m): 
    return m.group(1).rstrip()

@syntax('^\| (.*)')
def TEXT(m): 
    return m.group(1).rstrip()

@syntax('(.*?) > (.*)')
def OUTER_CLOSING_TAG(m):
    tag, text = m.groups()
    text = convert_line(text)
    return enclose_tag(tag, text)

@syntax('(.*) \| (.*)')
def TEXT_ENCLOSING_TAG(m):
    tag, text = m.groups()
    return enclose_tag(tag, text)

@syntax('> (.*)')
def SELF_CLOSING_TAG(m):
    tag = m.group(1).strip()
    return '<%s />' % tag

@syntax('(.*)')
def RAW_TEXT(m):
    return m.group(1).rstrip()

@syntax('^!!!$')
def BANG_BANG_BANG(m):
    return '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'


LINE_METHODS = [
        BANG_BANG_BANG,
        RAW_HTML,
        TEXT,
        OUTER_CLOSING_TAG,
        TEXT_ENCLOSING_TAG,
        SELF_CLOSING_TAG,
        RAW_TEXT,
        ]


def convert_shpaml_tree(in_body):
    return convert_document(in_body,
            branch_method=html_block_tag,
            leaf_method=convert_line,
            pass_syntax=PASS_SYNTAX,
            indentation_method=find_indentation)

def html_block_tag(line):
    if re.match(RAW_HTML.regex, line):
        return (line, None)
    else:
        markup = line
        start_tag, end_tag = apply_jquery_sugar(markup)
        return (start_tag, end_tag)

def convert_line(line):
    line = line.strip()
    for method in LINE_METHODS:
        m = re.match(method.regex, line)
        if m:
            return method(m)

def apply_jquery_sugar(markup):
    if re.match(DIV_SHORTCUT, markup):
        markup = 'div' + markup
    tag, whitespace, attrs = re.match(TAG_WHITESPACE_ATTRS, markup).groups()
    tag, id_ = tag_and_id(tag)
    tag, classes = tag_and_classes(tag)
    if classes:
        attrs += ' class="%s"' % classes
    if id_:
        attrs += ' id="%s"' % id_
    start_tag = tag + whitespace + attrs
    return ('<%s>' % start_tag, '</%s>' % tag)

def tag_and_id(tag):
    m = re.match(TAG_AND_ID, tag)
    if m:
        return m.groups()
    else:
        return tag, None 

def tag_and_classes(tag):
    frags = tag.split(DOT_FOR_CLASSES)
    tag = frags[0]
    classes = ' '.join(frags[1:])
    return tag, classes

def enclose_tag(tag, text):
    start_tag, end_tag = apply_jquery_sugar(tag)
    return start_tag + text + end_tag

def find_indentation(line):
    return INDENT(re.match(INDENT.regex, line))
    
############ Generic indentation stuff follows

class Indenter:
    def __init__(self):
        self.stack = []
        self.lines = []

    def push(self, prefix, start, end):
        self.add(prefix, start)
        self.stack.append((prefix, end))

    def add(self, prefix, line):
        self.pop(prefix)
        self.insert(prefix, line)

    def insert(self, prefix, line):
        self.lines.append(prefix+line)

    def pop(self, prefix):
        while self.stack:
            start_prefix, end =  self.stack[-1]
            if len(prefix) <= len(start_prefix):
                self.close_block(start_prefix, end)
                self.stack.pop()
            else:
                return

    def close_block(self, start_prefix, end):
        whitespace_lines = pop_whitespace(self.lines)
        self.insert(start_prefix, end)
        self.lines += whitespace_lines

    def body(self):
        self.pop('')
        return '\n'.join(self.lines)

def convert_document(in_body, branch_method, leaf_method, pass_syntax, indentation_method):
    indenter = Indenter()
    for prefix, line, kind in get_lines(in_body, indentation_method):
        if kind == 'branch':
            start, end = branch_method(line)
            if end:
                indenter.push(prefix, start, end)
            else:
                indenter.add(prefix, start)
                
        elif kind == 'leaf':
            if line == pass_syntax:
                indenter.pop(prefix)
            else:
                line = leaf_method(line)
                indenter.add(prefix, line)
        else:
            indenter.insert('', line)
    return indenter.body()

def get_prefixed_lines(in_body, indentation_method):
    lines = in_body.split('\n')
    return [indentation_method(line) for line in lines]

def get_lines(in_body, indentation_method):
    '''
    Splits out lines from a file and identifies whether lines
    are branches, leafs, or blanks.
    '''
    prefixed_lines = get_prefixed_lines(in_body, indentation_method)
    lookaheads = [len(prefix) for prefix, line in prefixed_lines if line]
    lookaheads.pop(0)
    lookaheads.append(None)
    lines = []
    for prefix, line in prefixed_lines:
        if line:
            follower_length = lookaheads.pop(0)
            if follower_length is None:
                kind = 'leaf'
            elif follower_length <= len(prefix):
                kind = 'leaf'
            else:
                kind = 'branch'
        else:
            kind = 'blank'
        lines.append((prefix, line, kind))
    return lines

def pop_whitespace(lines):
    whitespace_lines = []
    while lines and lines[-1] == '':
        whitespace_lines.append(lines.pop())
    return whitespace_lines

if __name__ == "__main__":
    # if file name is given convert file, else convert stdin
    import sys
    if len(sys.argv) == 2:
        shpaml_text = file(sys.argv[1]).read()
    else:
        shpaml_text = sys.stdin.read()
    print convert_text(shpaml_text)

