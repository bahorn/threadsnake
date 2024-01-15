# threadsnake

A basic python script minifier.
ThreadSnakes are a small family of snakes.

This can break code, do fill an issue / pr if you can fix the case.

## Minifications

* Cleaning up imports into a single line.
* Deduplication of imports.
* Removal of doc strings
* Comment removal (part of the AST translation process)
* Patched unparse() removing unnessary space.
* Compresses the code, converts to base85 and packs in a wrapper script to
  decompress and run.

## Todo

* Cleaning up variable/function/class names
* Better modifications in unparse() - merging statements into one line.

## License

This uses code from the Python repository, namely `Lib/ast.py`.
This is Python License.
