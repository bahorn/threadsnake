#!/bin/bash
python3 threadsnake --no-compress --rfilter "^visit_[A-Za-z]+$|^add_argument$|^parse_args$|^args$|^rfilter$|^no_compress$|^no_rename$|^regex$|^parse$|^unparse$|^body$|^files$|^_fields$|^node$" ./threadsnake/ast.py ./threadsnake/remapnames.py ./threadsnake/passes.py ./threadsnake/threadsnake.py ./threadsnake/__main__.py > out.py
#echo "$RES" | wc
#echo "$RES" | python3 - ./testfiles/test2.py
