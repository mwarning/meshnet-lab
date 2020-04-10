# Tools

## csv_merge.py

Merge multiple rows of a CVS file into one and add a column with the standard deviation.
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --column 1 --column 'column_header2' input.csv output.csv
```
(merges 10 consecutive rows and adds standard deviations for two columns identifier by column number and column title)
