# Tools

## csv_merge.py

Merge multiple rows of a CVS file into one and add a column with the standard deviation.
Supports csv headers and has automatic delimiter detection:

```
./csv_merge --span 10 --columns-se 1 --columns-range 'value4' input.csv output.csv
```
(merges 10 consecutive rows and adds standard error column for column 1 and a column with the value range of the column identified by column title `value4`)
