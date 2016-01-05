# craftroom
Various tools for crafting the cosmos!

Items included so far:

+ `stereo.py`, for generating stereograms for pairs of separating images. To use, type
```./stereo.py leftimage.jpg rightimage.jpg```.
By default, `stereo.py` will give you a chance to click on a feature in both images, by which the two will be aligned. If you would like to skip this step, call it with the '-a' option for "auto" (e.g. `./stereo.py -a leftimage.jpg rightimage.jpg`).

Started by Zach Berta-Thompson (zkbt@mit.edu), January 2016.
