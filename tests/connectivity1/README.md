# Connectivity Test 1

This is a test that tests theoretical connectivity and does not run an network on connection.
It tests how dense nodes to be placed geographical to achive a speicifc percentage of connectivity.

Related articles: [On the Connectivity of Mesh Networks](https://inthemesh.com/archive/whitepaper-connectivity-of-mesh-networks/) / [Percolation Theory](https://inthemesh.com/archive/from-mocha-to-mesh-insights-from-percolation-theory/)

## Run

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test.
* `./plot.sh` will create graphs using gnuplot

## csv_merge.py

Tool to merge multiple rows of a CVS file into one and add extra columns for standard deviation (`--columns-sd`), standard error (`--columns-se`), value range (`--columns-range`) and min/max values (`--columns-max`, `--columns-min`).
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --columns-se 1 --columns-range 'value4' input.csv output.csv
```

This line merges 10 consecutive rows and add two extra columns. One column will contain the standard error of column 1, the other will contain the value range of the column identified by column title `value4`.
