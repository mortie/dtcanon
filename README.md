# DTCanon: A tool to canonicalize and wrangle devicetree files

While working on embedded Linux type projects, I frequently have a need
to deal with devicetree files in various ways.
DTCanon is a tool I've made which can parse .dts files and transform them.

## Features

Here's a list of things which DTCanon can do:

### Parse a .dts file and included .dtsi + header files

DTCanon will output a single .dts file with all C preprocessor macros expanded
and all overrides resolved.
In addition, all nodes are sorted within their parent node,
and all formatting is normalized.
I consider this the "canonical" representation of the devicetree,
which is where the name "DTCanon" comes from: DeviceTree Canonicalizer.

Add include directories to search with `-I <path>`.
Other C preprocessor options are also supported,
but which exact ones depends on your system's `cpp` program.

### Generate sorted, flat devicetrees for easy diffing.

This takes an input devicetree which may look like this:

```
/ {
    foo@1400 {
        y = 20;
        x = 10;
    };
    bar@2000 {
        baz@1 {
            hello = 30;
            world = 40;
        };
    };
};
```

And converts it into a corresponding flattened and sorted format:

```
/bar@2000/baz@1 {
    hello = 30;
    world = 40;
};
/foo@1400 {
    x = 10;
    y = 20;
};
```

This is no longer valid DeviceTree syntax,
but this flat representation is excellent for diffing.

Produce a flat representation with `--flatten`.

### Add labels to nodes from the symbol table.

When you decompile a compiled .dtb back into a .dts file,
labels will be gone.
However, the .dtb contains a special symbol table node, `/__symbols__`,
which maps labels to paths.
DTCanon can read this symbol table and add labels to nodes.

Add labels based on the symbol table with `--symbolize`.

### Annotate the source locations where nodes are defined.

When combining a web of .dtsi files into a single .dts file,
it's sometimes hard to find which exact file which defines a node.
DTCanon can annotate nodes in the output with the file name and line number
where the node is defined.

Tag nodes with source locations with `--tag-locations`.

## Usage

```
Usage: ./dtcanon.py [cpp options] [options] file...

Options:
  -o <file>:       Output to <file> instead of stdout
  --output-flat:   Output a flattened tree instead of a nested tree.
                   The output isn't valid DeviceTree syntax,
                   but this is often useful for diffing.
  --tag-locations: Annotate nodes with their locations in the input file.
  --symbolize:     Add labels to nodes from a symbols table, if any.
```

## License

DTCanon is licensed under the GPL v3.
See [LICENSE](./LICENSE) for details.
