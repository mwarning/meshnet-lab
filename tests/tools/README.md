# Tools

## csv_merge.py

Merge multiple rows of a CVS file into one and add a column with the standard deviation.
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --type 'se' --columns 1 --columns 'column_header2' input.csv output.csv
```
(merges 10 consecutive rows and adds standard error for two columns. The columns are identified by column number and column title)
