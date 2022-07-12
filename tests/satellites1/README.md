# Satellites 1

Test a mobile topology with satellites, ground stations and gound clients. The setup is inspired by [Starlink](https://www.starlink.com/) setup operated by [SpaceX](https://www.spacex.com/). The amount of those in this particular test is very low.

![image](animation.gif)

## Run Animation

To run the animation as depicted above, modify `run.py` script and comment in the `start_animation()` call. Then execute the script. Use the left mouse button to rotate, right mouse button to zoom in or out. There is also a line to write the output to a file.

## Run Test

* remove remaining `*.csv` files in this directory
* execute `sudo ./run.py` to run the test (will take a long time).
* `./plot.sh` will create graphs using gnuplot
