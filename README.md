![](https://github.com/neuropoly/gm_challenge/blob/master/doc/logo_challenge.png)

# Gray Matter Challenge (2018)
Spinal cord gray matter imaging challenge for the [5th Spinal Cord Workshop (June 22<sup>nd</sup>, Paris)](http://www.spinalcordmri.org/2018/06/22/workshop.html).
The objective for this challenge is to propose a protocol that will generate the best image quality. For more details,
please see: https://goo.gl/2owcL7.

## Dependencies

This pipeline was tested on [SCT v3.2.5](https://github.com/neuropoly/spinalcordtoolbox/releases/tag/v3.2.5).

## Getting started

- Download (or `git clone`) this repository.
- Download dataset of the challenge: https://osf.io/5dqen/
- run: `./run_pipeline.sh PATH_TO_DATA` with `PATH_TO_DATA`the path to the directory where you stored the dataset of the challenge

## Description of the scripts

* [run_pipeline.sh](./run_pipeline.sh): Batch script that loops across subjects
and process them. By default, the script will process all subjects under
PATH_TO_DATA. If you wish to only process one subject, add the folder name as a
2nd argument.
* [process_data.py](./process_data.py): Process data using SCT and compute image
quality metrics. More details [here](#analysis).
* [simu_create_phantom.py](./simu_create_phantom.py): Generate synthetic phantom
of WM and GM that can be used to validate the proposed evaluation metrics. The phantoms are generated with random noise,
 so running the script multiple times will not produce the same output.
This script is meant to be run twice in order to assess the metrics with the following functions.
* [simu_process_data.py](./simu_process_data.py): Process data by batch within
folders. This script will look for csv files, which are generated by
simu_create_phantom.py, and which contain file names of the nifti phantom data.
This script is particularly useful for processing the large amount of files
generated by the phantom construction.
* [simu_make_figures.py](./simu_make_figures.py): Make figures to assess
metrics sensitivity to image quality. Run after simu_process_data.py
* [make_figures_compare_SNR.py](./make_figures_compare_SNR.py): Make figures to assess
the correlation between SNR_single and SNR_diff.

## Analysis

Two NIfTI files are required: an initial scan and a re-scan without repositioning.

### Pre-processing
- The second image is registered to the first in order to compute the SNR using the two-image subtraction method.
- The spinal cord and gray matter of each image are segmented automatically.
- White matter segmentation is generated by subtracting the gray matter segmentation from the cord segmentation.

### Signal-to-noise ratio (SNR):
The SNR is determined with two different methods: SNR_diff and SNR_single.
- SNR_diff is computed with SCT using the two-image subtraction method (Dietrich et al. J Magn Reson Imaging, 2007).
- SNR_single is computed from a single image (Griffanti et al., Biomed Sign Proc and Control, 2012).

### Contrast:
The mean signal is computed in the white matter and gray matter of image 1. The contrast is then computed according to the following equation:

~~~
Contrast = abs(mean(WM) - mean(GM)) / min{mean(WM),mean(GM)}
~~~

## Configuration of Niftyweb server
- make sure the script WMGM is declared in `PATH`


## Contributors
Stephanie Alley, Ferran Prados, Julien Cohen-Adad

## License
See: [LICENSE](./LICENSE)
