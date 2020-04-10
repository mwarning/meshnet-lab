# Tools

Some helpful utilities.

## csv_merge.py

Merge multiple rows of a CVS file into one and add a column with the standard deviation.
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --columns-se 1 --columns-range 'value4' input.csv output.csv
```

This line merges 10 consecutive rows and add two extra columns. One column will contain the standard error of column 1, the other will contain the value range of the column identified by column title `value4`.

## json_count.py

Count the number of nodes or links in a JSON file.
