# DTCanon: A tool to canonicalize and wrangle devicetree files

While working on embedded Linux type projects, I frequently have a need
to deal with devicetree files in various ways.
DTCanon is a tool I've made which can parse .dts files and transform them.

## Caveat

DTCanon's devicetree parser was written in a hurry to solve a problem.
It was written to parse .dts files I had at hand,
not according to the devicetree syntax spec.
It is probably not 100% correct.
There are probably correct .dts files which DTCanon can't parse,
and there are definitely incorrect .dts files which DTCanon *can* parse.

If you find examples of valid devicetree syntax which DTCanon fails to parse,
please file a bug.
Also, if you find examples of *invalid* devicetree syntax
which is nonetheless out there in the world,
please file a bug, and we can try to accomodate for common types of
buggy devicetree code.

If you find examples of *invalid* devicetree syntax which DTCanon *can* parse,
do *not* file a bug.
DTCanon is not a linter.
Rejecting invalid devicetree syntax is a non-goal.

## Features

Here's a list of things which DTCanon can do:

### Parse a .dts file and included .dtsi + header files.

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

Tag nodes with source locations with `--locations`.

## Usage

```
Usage: ./dtcanon.py [cpp options] [options] file...

Options:
  -o <file>:   Output to <file> instead of stdout
  --flatten:   Output a flattened tree instead of a nested tree.
               The output isn't valid DeviceTree syntax,
               but this is often useful for diffing.
  --locations: Annotate nodes with their locations in the input file.
  --symbolize: Add labels to nodes from a symbols table, if any.
```

## Examples

### Diff two versions of a devicetree

These commands will diff the devicetree for the NanoPi R5C between
Linux versions 6.9 and 6.10:

```
$ cd linux
$ git checkout v6.9
$ dtcanon.py -Iinclude --flatten -o nanopi-r5c_6.9.dts arch/arm64/boot/dts/rockchip/rk3568-nanopi-r5c.dts
$ git checkout v6.10
$ dtcanon.py -Iinclude --flatten -o nanopi-r5c_6.10.dts arch/arm64/boot/dts/rockchip/rk3568-nanopi-r5c.dts
$ git diff --no-index nanopi-r5c_6.9.dts nanopi-r5c_6.10.dts
```

Those commands will output:

```
i-r5c_6.10.dts | cat
diff --git a/nanopi-r5c_6.9.dts b/nanopi-r5c_6.10.dts
index 0004ef95ec62..b2350afdd148 100644
--- a/nanopi-r5c_6.9.dts
+++ b/nanopi-r5c_6.10.dts
@@ -64,8 +64,15 @@ cpu0: /cpus/cpu@0 {
   clocks = <&scmi_clk 0>;
   compatible = "arm,cortex-a55";
   cpu-supply = <&vdd_cpu>;
+  d-cache-line-size = <64>;
+  d-cache-sets = <128>;
+  d-cache-size = <0x8000>;
   device_type = "cpu";
   enable-method = "psci";
+  i-cache-line-size = <64>;
+  i-cache-sets = <128>;
+  i-cache-size = <0x8000>;
+  next-level-cache = <&l3_cache>;
   operating-points-v2 = <&cpu0_opp_table>;
   reg = <0x0 0x0>;
 };
@@ -73,8 +80,15 @@ cpu1: /cpus/cpu@100 {
   #cooling-cells = <2>;
   compatible = "arm,cortex-a55";
   cpu-supply = <&vdd_cpu>;
+  d-cache-line-size = <64>;
+  d-cache-sets = <128>;
+  d-cache-size = <0x8000>;
   device_type = "cpu";
   enable-method = "psci";
+  i-cache-line-size = <64>;
+  i-cache-sets = <128>;
+  i-cache-size = <0x8000>;
+  next-level-cache = <&l3_cache>;
   operating-points-v2 = <&cpu0_opp_table>;
   reg = <0x0 0x100>;
 };
@@ -82,8 +96,15 @@ cpu2: /cpus/cpu@200 {
   #cooling-cells = <2>;
   compatible = "arm,cortex-a55";
   cpu-supply = <&vdd_cpu>;
+  d-cache-line-size = <64>;
+  d-cache-sets = <128>;
+  d-cache-size = <0x8000>;
   device_type = "cpu";
   enable-method = "psci";
+  i-cache-line-size = <64>;
+  i-cache-sets = <128>;
+  i-cache-size = <0x8000>;
+  next-level-cache = <&l3_cache>;
   operating-points-v2 = <&cpu0_opp_table>;
   reg = <0x0 0x200>;
 };
@@ -91,8 +112,15 @@ cpu3: /cpus/cpu@300 {
   #cooling-cells = <2>;
   compatible = "arm,cortex-a55";
   cpu-supply = <&vdd_cpu>;
+  d-cache-line-size = <64>;
+  d-cache-sets = <128>;
+  d-cache-size = <0x8000>;
   device_type = "cpu";
   enable-method = "psci";
+  i-cache-line-size = <64>;
+  i-cache-sets = <128>;
+  i-cache-size = <0x8000>;
+  next-level-cache = <&l3_cache>;
   operating-points-v2 = <&cpu0_opp_table>;
   reg = <0x0 0x300>;
 };
@@ -739,6 +767,14 @@ vop_mmu: /iommu@fe043e00 {
   reg = <0x0 0xfe043e00 0x0 0x100>, <0x0 0xfe043f00 0x0 0x100>;
   status = "okay";
 };
+l3_cache: /l3-cache {
+  cache-level = <2>;
+  cache-line-size = <64>;
+  cache-sets = <512>;
+  cache-size = <0x80000>;
+  cache-unified;
+  compatible = "cache";
+};
 dsi_dphy0: /mipi-dphy@fe850000 {
   #phy-cells = <0>;
   clock-names = "ref", "pclk";
```

Looks like 6.10 added a bunch of properties for i-cache and d-cache to /cpus/cpu@N nodes!

### Decompile a devicetree

Say you're on Armbian and you want to inspect your devicetree,
which is in /boot/dts/rockchip/rk3588-nanopi-r6c.dtb.
You can run `dtc` to decompile it like so:

```
dtc -I dtb -O dts /boot/dts/rockchip/rk3588s-nanopi-r6c.dtb
```

And you will see proper textual devicetree code.
However, none of the nodes will have labels.
That means that if you're writing a devicetree overlay file,
you must first find the node you want to override, then manually resolve its path,
then look up that path in the symbol table in `/__symbols__` to figure out
which label you should override.

With DTCanon, you can instead run this command:

```
dtc -I dtb -O dts /boot/dts/rockchip-rk3588s-nanopi-r6c.dtb | dtcanon.py --symbolize
```

and get a devicetree where all nodes with a label are annotated with their label(s),
as you would see in a hand-written devicetree file.

## License

DTCanon is licensed under the GPL v3.
See [LICENSE](./LICENSE) for details.
