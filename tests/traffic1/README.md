# Traffic Test 1

The mesh routing program batman-adv is tested on grid structures of different sizes.
Every test was performed 10 times to calculate the standard deviation (error bars).

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot

## csv_merge.py

Tool to merge multiple rows of a CVS file into one and add extra columns for standard deviation (`--columns-sd`), standard error (`--columns-se`), value range (`--columns-range`) and min/max values (`--columns-max`, `--columns-min`).
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --columns-se 1 --columns-range 'value4' input.csv output.csv
```

This line merges 10 consecutive rows and add two extra columns. One column will contain the standard error of column 1, the other will contain the value range of the column identified by column title `value4`.
