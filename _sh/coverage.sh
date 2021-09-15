#!/bin/sh
./_py/coverage.py $@| fgrep --invert-match -e "0FILE" | sed -e 's/\.txt//' -e 's/ /_/g' | sort --k2rn,2 -k1,1 | awk '{print $2"\t" $1}' | sed -e 's/_/ /g' -e 's/\t/: /'
