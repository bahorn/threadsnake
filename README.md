# threadsnake

A basic python script minifier.
ThreadSnakes are a small family of snakes.

This can break code, do fill an issue / pr if you can fix the case.

## Usage

```
python3 threadsnake [files....]
```

No external dependencies, just pure python3. Might need a more modern verison,
wrote with 3.11.

To avoid breakage:
* Remember, this merges files in one global namespace. Don't reuse global
  variable names across files, unless you intend for that.
* As variables get renamed, you use of `eval()/exec()` can break.
* Import across files in the form "from OTHERFILE import dep1, dep2, ...".
  `import x` gets removed if its a known other module, so to allow your code to
  be ran without being minified, do this pattern.

## Minifications

* Cleaning up imports into a single line.
* Deduplication of imports.
* Removal of doc strings
* Comment removal (part of the AST translation process)
* Patched unparse() removing unnessary space.
* Compresses the code, converts to base85 and packs in a wrapper script to
  decompress and run.
* Cleaning up variable/function/class names

## Todo

* Better modifications in unparse() - merging statements into one line.
* Better namespacing, to break code in less cases.

## License

My code is MIT licensed, which is everything beyond exceptions listed below:

`threadsnake/ast.py` is derivied from `Lib/ast.py` from the Python source
repository.
Header says its Python license, but modern python should be under the PSF
license.
https://docs.python.org/3/license.html
