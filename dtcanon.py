#!/usr/bin/env python3

import sys
import traceback
import subprocess
import os

class Reader:
    def __init__(self, f):
        self.f = f
        self.next = f.read(1)
        self.next2 = f.read(1)
        self.line = 1
        self.column = 1
        self.filename = b"unknown"
        self.filepath = b"unknown"

    def consume(self):
        self.column += 1
        if self.next == b"\n":
            self.line += 1
            self.column = 1
        self.next = self.next2
        self.next2 = self.f.read(1)

class Node:
    def __init__(self, parent):
        self.parent = parent
        self.props = {}
        self.children = {}
        self.labels = set()
        self.flags = set()
        self.location = None

    def name(self):
        if not self.parent:
            return b"/"
        for k in self.parent.children:
            if self.parent.children[k] is self:
                return k

    def path(self):
        if self.parent:
            parent_path = self.parent.path()
            if parent_path == b"/":
                return b"/" + self.name()
            else:
                return self.parent.path() + b"/" + self.name()
        else:
            return b"/"

class ParseError(Exception):
    def __init__(self, r, msg, node=None):
        self.filename = r.filepath
        self.line = r.line
        self.column = r.column
        self.msg = msg
        self.node = node

def skip(r, ch):
    if r.next != ch:
        raise ParseError(r, "Expected " + str(ch) + ", got " + str(r.next))
    r.consume()

def skip_whitespace(r):
    next_line = None
    next_file = None
    while True:
        while r.next in b" \n\t" and r.next != b"":
            r.consume()

        if r.next == b"/" and r.next2 == b"/":
            skip_line(r)
        elif r.next == b"/" and r.next2 == b"*":
            r.consume()
            r.consume()
            while True:
                if r.next == b"*" and r.next2 == b"/":
                    break
                elif r.next == b"":
                    raise ParseError(r, "Unexpected EOF in comment")
                r.consume()
        elif r.next == b"#" and r.next2 == b" ":
            r.consume()
            r.consume()
            if r.next in b"0123456789":
                digits = ""
                while r.next in b"0123456789":
                    digits += str(r.next, "utf-8")
                    r.consume()
                next_line = int(digits)
            if r.next == b" " and r.next2 == b"\"":
                next_file = b""
                r.consume()
                r.consume()
                while r.next != b"\"":
                    if r.next == b"\\" and r.next2 == b"\"":
                        next_file += b"\""
                        r.consume()
                        r.consume()
                    elif r.next == b"\\" and r.next2 == b"\\":
                        next_file += b"\\"
                        r.consume()
                        r.consume()
                    else:
                        next_file += r.next
                        r.consume()
                r.consume()
                while r.next in b" 0123456789":
                    r.consume()
        else:
            if next_line != None:
                r.line = next_line
            if next_file != None:
                r.filename = os.path.basename(next_file)
                r.filepath = next_file
            break

def skip_line(r):
    while r.next != b"\n" and r.next != b"":
        r.consume()
    r.consume()

def read_ident(r):
    ident = b""
    while True:
        ch = r.next
        if ch in b"{}:;<>()= \n\t" or ch == b"":
            return ident
        ident += ch
        r.consume()

def parse_value(r):
    value = b""
    while True:
        skip_whitespace(r)
        if r.next == b";" or r.next == b">":
            return value

        if r.next == b",":
            r.consume()
            value += b","
            skip_whitespace(r)

        if value != b"":
            value += b" "

        if r.next == b"":
            raise ParseError(r, "Unexpected EOF while parsing value")
        elif r.next == b'"':
            value += b'"'
            r.consume()
            while r.next != b'"':
                if r.next == b"\\":
                    value += r.next
                    r.consume()
                    value += r.next
                    r.consume()
                else:
                    value += r.next
                    r.consume()
            value += b'"'
            r.consume()
        elif r.next == b"<":
            value += b"<"
            r.consume()
            value += parse_value(r)
            value += b">"
            skip(r, b">")
        elif r.next == b"(":
            value += b"("
            r.consume()

            depth = 1
            while depth > 0:
                if r.next == b"(":
                    depth += 1
                elif r.next == b")":
                    depth -= 1
                value += r.next
                r.consume()
        elif r.next in b"0123456789":
            leading = r.next
            r.consume()
            if leading == b"0" and r.next == b"x":
                r.consume()
                digits = b""
                while r.next in b"0123456789abcdefABCDEF":
                    digits += r.next
                    r.consume()
                lead = "0x"
                value += bytes(hex(int(digits, 16)), "utf-8")
            else:
                digits = leading
                while r.next in b"0123456789":
                    digits += r.next
                    r.consume()
                value += bytes(str(int(digits)), "utf-8")
        elif r.next == b"[":
            value += b"["
            r.consume()
            first = True
            while True:
                if not first:
                    value += b" "
                first = False

                skip_whitespace(r)
                if r.next == b"]":
                    break

                digits = b""
                if r.next not in b"0123456789abcdefABCDEF":
                    raise ParseError(r, f"Invalid hex character: {r.next}")
                digits += r.next
                r.consume()
                if r.next not in b"0123456789abcdefABCDEF":
                    raise ParseError(r, f"Invalid hex character: {r.next}")
                digits += r.next
                r.consume()
                num = int(digits)
                value += bytes(str(digits, "utf-8").lower(), "utf-8")

            value += b"]"
            r.consume()
        elif r.next == b"&":
            value += b"&"
            r.consume()
            value += read_ident(r)
        elif r.next == b"{":
            value += b"{"
            skip_whitespace(r)
            value += read_ident(r)
            skip_whitespace(r)
            value += b"}"
            skip(r, b"}")
        else:
            lead = r.next
            ident = read_ident(r)
            if ident == b"":
                raise ParseError(r, "Unknown lead character in value: " + str(r.next))
            value += ident
            if r.next == b":":
                value += b":"
                r.consume()
    return value

def parse_node(r, node, labels, pending_label_nodes):
    skip(r, b"{")

    while True:
        skip_whitespace(r)
        if r.next == b"}":
            r.consume()
            skip_whitespace(r)
            skip(r, b";")
            return

        flags = set()
        name = read_ident(r)
        while len(name) > 2 and name[0] == ord("/") and name[-1] == ord("/"):
            flags.add(name)
            skip_whitespace(r)
            name = read_ident(r)
        skip_whitespace(r)

        if r.next == b"=":
            r.consume()
            skip_whitespace(r)
            try:
                node.props[name] = parse_value(r)
            except ParseError as ex:
                ex.node = node
                raise ex
            skip_whitespace(r)
            skip(r, b";")
            skip_whitespace(r)
        elif r.next == b";":
            r.consume()
            skip_whitespace(r)
            node.props[name] = True
        elif r.next == b":" or r.next == b"{":
            child_labels = set()
            while r.next == b":":
                r.consume()
                child_labels.add(name)
                skip_whitespace(r)
                name = read_ident(r)
                skip_whitespace(r)

            if name in node.children:
                child = node.children[name]
            else:
                child = None
                for label in child_labels:
                    if label not in pending_label_nodes:
                        continue
                    child = pending_label_nodes[label]
                    child.location = (r.filename, r.line, r.column)
                    child.parent = node
                    del pending_label_nodes[label]
                    break

            if child is None:
                child = Node(node)
                child.location = (r.filename, r.line, r.column)
                node.children[name] = child

            child.flags = flags

            for label in child_labels:
                child.labels.add(label)
                labels[label] = child

            parse_node(r, child, labels, pending_label_nodes)
        else:
            raise ParseError(r, "Expected value or child node, got " + str(r.next), node)

def parse_document(r):
    labels = {}
    roots = {}
    pending_label_nodes = {}
    while True:
        skip_whitespace(r)
        if r.next == b"":
            break
        elif r.next == b"&":
            r.consume()
            name = read_ident(r)
            assert(name != b"")
            skip_whitespace(r)
            if name in labels:
                parse_node(r, labels[name], labels, pending_label_nodes)
            elif name in pending_label_nodes:
                parse_node(r, pending_label_nodes[name], labels, pending_label_nodes)
            else:
                node = Node(None)
                pending_label_nodes[name] = node
                parse_node(r, node, labels, pending_label_nodes)
        else:
            name = read_ident(r)
            if name == b"/dts-v1/":
                skip_whitespace(r)
                skip(r, b";")
                continue
            elif name == b"/delete-node/":
                skip_whitespace(r)
                skip(r, b"&")
                delete_label = read_ident(r)
                skip(r, b";")

                if delete_label not in labels:
                    raise ParseError(r, "Got /delete-label/ for non-existent node '" + delete_label + "'")

                delete_node = labels[delete_label]
                for k in delete_node.parent.children:
                    if delete_node.parent.children[k] is delete_node:
                        del delete_node.parent.children[k]
                        break
                continue

            if name in roots:
                node = roots[name]
            else:
                node = Node(None)
                node.location = (r.filename, r.line, r.column)
                roots[name] = node
            skip_whitespace(r)
            parse_node(r, node, labels, pending_label_nodes)

    if len(pending_label_nodes) > 0:
        print("Warning: Undefined labels: " + str(b", ".join(pending_label_nodes.keys()), "utf-8"))

    return roots, labels

def print_flat_node(node, name, outfile, tag_locations):
    if tag_locations:
        f, l, c = node.location
        print(f"// {str(f, 'utf-8')}:{l}:{c}", file=outfile)

    prefix = ""

    for flag in sorted(node.flags):
        print(str(flag, "utf-8"))

    for label in sorted(node.labels):
        prefix += str(label, "utf-8") + ": "

    if name == b"":
        prefix += "/ "
    else:
        prefix += str(name, "utf-8") + " "

    print(prefix + "{", file=outfile)

    for k in sorted(node.props.keys()):
        prop = node.props[k]
        if prop == True:
            print("  " + str(k, "utf-8") + ";", file=outfile)
        else:
            print("  " + str(k, "utf-8") + " = " + str(prop, "utf-8") + ";", file=outfile)
    print("};", file=outfile)

    for k in sorted(node.children.keys()):
        print_flat_node(node.children[k], name + b"/" + k, outfile, tag_locations)

def print_flat_document(roots, outfile, tag_locations):
    for k in sorted(roots.keys()):
        for flag in sorted(roots[k].flags):
            print(str(flag, "utf-8"))
        if k == b"/":
            print_flat_node(roots[k], b"", outfile, tag_locations)
        else:
            print_flat_node(roots[k], k, outfile, tag_locations)

def print_dts_node(node, depth, outfile, tag_locations):
    for k in sorted(node.props.keys()):
        prop = node.props[k]
        if prop == True:
            print("  " * depth + str(k, "utf-8") + ";", file=outfile)
        else:
            print("  " * depth + str(k, "utf-8") + " = " + str(prop, "utf-8") + ";", file=outfile)

    for k in sorted(node.children.keys()):
        child = node.children[k]
        if tag_locations:
            f, l, c = child.location
            print("  " * depth + f"// {str(f, 'utf-8')}:{l}:{c}", file=outfile)

        for flag in sorted(child.flags):
            print("  " * depth + str(flag, "utf-8"))

        prefix = ""
        for label in sorted(child.labels):
            prefix += str(label, "utf-8") + ": "

        print("  " * depth + prefix + str(k, "utf-8") + " {", file=outfile)
        print_dts_node(child, depth + 1, outfile, tag_locations)
        print("  " * depth + "};", file=outfile)

def print_dts_document(roots, outfile, tag_locations):
    print("/dts-v1/;", file=outfile)
    for k in sorted(roots.keys()):
        for flag in sorted(roots[k].flags):
            print(str(flag, "utf-8"))
        print(str(k, "utf-8") + " {", file=outfile)
        print_dts_node(roots[k], 1, outfile, tag_locations)
        print("};", file=outfile)

def print_labels(labels, outfile):
    for k in sorted(labels.keys()):
        print(str(k, "utf-8") + " = " + str(labels[k].path(), "utf-8"), file=outfile)

def symbolize_nodes(nodes, symbols, path = None):
    for name in nodes:
        node = nodes[name]
        if path is None:
            subpath = name
        elif path == b"/":
            subpath = path + name
        else:
            subpath = path + b"/" + name

        if subpath in symbols:
            node.labels.add(symbols[subpath])

        symbolize_nodes(node.children, symbols, subpath)

def symbolize_document(roots):
    if b"/" not in roots:
        print("Symbolize: No '/' node in document!", file=sys.stderr)
        return

    root = roots[b"/"]
    if b"__symbols__" not in root.children:
        print("Symbolize: No symbol table in document!", file=sys.stderr)
        return
    symbol_table = root.children[b"__symbols__"]

    symbols = {}
    for label in symbol_table.props:
        path = symbol_table.props[label][1:-1]
        symbols[path] = label

    symbolize_nodes(roots, symbols)

if len(sys.argv) <= 1:
    print("Usage:", sys.argv[0], "[cpp options] [options] file...")
    print()
    print("Options:")
    print("  -o <file>:   Output to <file> instead of stdout")
    print("  --flatten:   Output a flattened tree instead of a nested tree.")
    print("               The output isn't valid DeviceTree syntax,")
    print("               but this is often useful for diffing.")
    print("  --locations: Annotate nodes with their locations in the input file.")
    print("  --symbolize: Add labels to nodes from a symbols table, if any.")
    exit(1)

args = ["cpp", "-nostdinc", "-undef", "-xassembler-with-cpp"]
outfile = sys.stdout
flatten = False
tag_locations = False
symbolize = False
idx = 1
while idx < len(sys.argv):
    arg = sys.argv[idx]
    if arg == "-o":
        idx += 1
        outfile = open(sys.argv[idx], "w")
    elif arg.startswith("-o"):
        outfile = open(arg[2:], "w")
    elif arg == "--flatten":
        flatten = True
    elif arg == "--tag-locations":
        tag_locations = True
    elif arg == "--symbolize":
        symbolize = True
    else:
        args += [arg]
    idx += 1

proc = subprocess.Popen(args, stdout=subprocess.PIPE)
r = Reader(proc.stdout)

try:
    roots, labels = parse_document(r)

    if symbolize:
        symbolize_document(roots)

    if flatten:
        print_flat_document(roots, outfile, tag_locations)
    else:
        print_dts_document(roots, outfile, tag_locations)
except ParseError as ex:
    print(f"{str(ex.filename, 'utf-8')}:{ex.line}:{ex.column}: {ex.msg}", file=sys.stderr)
    if ex.node:
        print("While parsing node: " + str(ex.node.path(), "utf-8"), file=sys.stderr)
    print("Next few characters:", file=sys.stderr)
    s = b""
    while len(s) < 50 and r.next != b"":
        s += r.next
        r.consume()
    print(str(s, "utf-8"))
    print("", file=sys.stderr)
    traceback.print_exception(ex)
    exit(1)
