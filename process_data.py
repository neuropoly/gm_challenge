#!/usr/bin/env python
#
# Compute metrics to assess the quality of spinal cord images.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}process_data.py
#
#
# OUTPUT:
# The script generates a collection of files under specified folder.
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE

# TODO: get verbose working (current issue is sys.stdout.isatty()) is False, hence sct.run() is using sct.log with no terminal output
# TODO: make flag to bypass registration (not needed for phantom)

import sys, os, shutil, subprocess, time, argparse, pickle, io
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from sct_convert import convert


def get_parameters():
    parser = argparse.ArgumentParser(description='Compute metrics to assess the quality of spinal cord images. This '
                                                 'script requires two input files of scan-rescan acquisitions, which '
                                                 'will be used to compute the SNR. Other metrics (contrast, sharpness) '
                                                 'will be computed from the first file.')
    parser.add_argument("-i", "--input",
                        help="List here the two nifti files to compute the metrics on, separated by space.",
                        nargs='+',
                        required=True)
    parser.add_argument("-s", "--seg",
                        help="Spinal cord segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-g", "--gmseg",
                        help="Gray matter segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-r", "--register",
                        help="Perform registration between scan #1 and scan #2. Default=1.",
                        type=int,
                        default=1,
                        required=False)
    parser.add_argument("-n", "--num",
                        help="NiftyWeb ID",
                        required=False)
    parser.add_argument("-v", "--verbose",
                        help="Verbose {0,1}. Default=1",
                        type=int,
                        default=1,
                        required=False)
    args = parser.parse_args()
    return args


def err(output):
    status = output.communicate()

    if output.returncode != 0:
        print(status[0])


def compute_contrast(file_data, file_mask1, file_mask2):
    """
    Compute contrast in image between two regions
    :param file_data: image
    :param file_mask1: mask for region 1
    :param file_mask2: mask for region 2
    :return: float: contrast
    """
    # Get mean value within mask
    sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask1 + " -method bin -o mean_mask1.pickle")
    sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask2 + " -method bin -o mean_mask2.pickle")
    # Retrieve values from saved pickle
    mean_mask1 = pickle.load(io.open("mean_mask1.pickle"))["Metric value"][0]
    mean_mask2 = pickle.load(io.open("mean_mask2.pickle"))["Metric value"][0]
    # Compute contrast
    return abs(mean_mask1 - mean_mask2) / min(mean_mask1, mean_mask2)


def compute_sharpness(file_data, file_mask_gm):
    """
    Compute sharpness at GM/WM interface. The mask of GM is dilated, and then subtracted from the GM mask, in order to
    produce a mask at the GM/WM interfact. This mask is then used to extract the Laplacian value of the image. The
    sharper the transition, the higher the Laplacian. Note that the Laplacian will also be affected by the underlying
    WM/GM contrast, hence the WM and GM values need to be normalized before computing the Laplacian.
    :param file_data:
    :param file_mask_gm:
    :return: float: sharpness
    """
    # Dilate GM mask
    sct.run("sct_maths -i data1_gmseg.nii.gz -dilate 1 -o data1_gmseg_dil.nii.gz", verbose=verbose)
    # Subtract to get mask at WM/GM interface
    sct.run("sct_maths -i data1_gmseg_dil.nii.gz -sub data1_gmseg.nii.gz -o mask_interface.nii.gz", verbose=verbose)
    # Compute Laplacian on image
    sct.run("sct_maths -i data1.nii.gz -laplacian 0.5,0.5,0 -o data1_lapl.nii.gz", verbose=verbose)
    # Normalize WM/GM before computing Laplacian
    # TODO
    # Extract Laplacian at WM/GM interface
    sct.run("sct_extract_metric -i data1_lapl.nii.gz -f mask_interface.nii.gz -o laplacian.pickle", verbose=verbose)
    # return
    return pickle.load(io.open("laplacian.pickle"))["Metric value"][0]


def main():
    output_dir = "./output_wmgm"  # TODO: be able to set with argument
    file_output = "results.txt"
    fdata2 = "data2.nii.gz"

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # copy to output directory and convert to nii.gz
    convert(file_data[0], os.path.join(output_dir, "data1.nii.gz"))
    convert(file_data[1], os.path.join(output_dir, fdata2))
    if file_seg is not None:
        convert(file_seg, os.path.join(output_dir, "data1_seg.nii.gz"))
    if file_gmseg is not None:
        convert(file_gmseg, os.path.join(output_dir, "data1_gmseg.nii.gz"))

    os.chdir(output_dir)

    # Segment spinal cord
    if file_seg is None:
        sct.run("sct_deepseg_sc -i data1.nii.gz -c t2s", verbose=verbose)

    # Segment gray matter
    if file_gmseg is None:
        sct.run("sct_deepseg_gm -i data1.nii.gz", verbose=verbose)

    # Generate white matter segmentation
    sct.run("sct_maths -i data1_seg.nii.gz -sub data1_gmseg.nii.gz -o data1_wmseg.nii.gz", verbose=verbose)

    if register:
        # Create mask around the cord for more accurate registration
        sct.run("sct_create_mask -i data1.nii.gz -p centerline,data1_seg.nii.gz -size 35mm", verbose=verbose)
        # Register image 2 to image 1
        sct.run("sct_register_multimodal -i " + fdata2 + " -d data1.nii.gz -param step=1,type=im,algo=slicereg,metric=CC "
                "-m mask_data1.nii.gz -x spline", verbose=verbose)
        # Add suffix to file name
        sct.add_suffix(fdata2, "_reg")

    # Analysis: compute metrics
    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast', 'Sharpness'], columns=['Metric Value'])

    # Compute SNR
    sct.run("sct_image -i data1.nii.gz," + fdata2 + " -concat t -o data_concat.nii.gz")
    status, output = sct.run("sct_compute_snr -i data_concat.nii.gz -vol 0,1 -m data1_seg.nii.gz")
    # parse SNR info
    snr = np.float(output[output.index("SNR_diff =") + 11:])
    results.loc['SNR'] = snr

    # Compute contrast
    results.loc['Contrast'] = compute_contrast("data1.nii.gz", "data1_wmseg.nii.gz", "data1_gmseg.nii.gz")

    # Compute sharpness at GM/WM interface
    results.loc['Sharpness'] = compute_sharpness("data1.nii.gz", "data1_gmseg.nii.gz")

    # Display results
    results.columns = ['']

    results_to_return = open(os.path.join(file_output), 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.write('\n\nA text file containing this information, as well as the image segmentations, are '
                            'available for download through the link below. Please note that these are the intermediate '
                            'results (automatically processed). We acknowledge that manual adjustment of the cord and '
                            'gray matter segmentations might be necessary. They will be performed in the next few days, '
                            'and the final results will be sent back to you.\n')
    results_to_return.close()

    # Package results inside folder
    # TODO
    #Package results for daemon
    if num:
        # Create folder for segmentations
        segmentations = os.path.join(output_dir + '/segmentations/')
        if not os.path.exists(segmentations):
            os.makedirs(segmentations)

        # Copy data1_seg.nii.gz and data1_gmseg.nii.gz to segmentations folder
        shutil.copy2("data1_seg.nii.gz", segmentations)
        shutil.copy2("data1_gmseg.nii.gz", segmentations)

        # Copy text file containing results to segmentations folder
        shutil.copy2(os.path.join(file_output), segmentations)

        # Create ZIP file of segmentation results
        shutil.make_archive(os.path.join(num + '_WMGM_results'), 'zip', segmentations)

        # Move results files to data directory 
        if os.path.isfile(os.path.join(dir_data + '/' + num + '_WMGM_results.txt')):
            os.remove(os.path.join(dir_data + '/' + num + '_WMGM_results.txt'))
        shutil.move(os.path.join(output_dir, segmentations, num + '_WMGM_results.txt'), os.path.join(dir_data  + '/' + num + '_WMGM.txt'))

        if os.path.isfile(os.path.join(dir_data + '/' + num + '_WMGM_results.zip')):
            os.remove(os.path.join(dir_data + '/' + num + '_WMGM_results.zip'))
        shutil.move(os.path.join(num + '_WMGM_results.zip'), os.path.join(dir_data  + '/' + num + '_WMGM.zip'))
    else: #TODO package results otherwise


if __name__ == "__main__":
    args = get_parameters()
    file_data = args.input
    file_seg = args.seg
    file_gmseg = args.gmseg
    register = args.register
    num = args.num
    verbose = args.verbose
    main()
