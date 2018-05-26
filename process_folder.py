#!/usr/bin/env python
#
# Process data by batch within folders. This is particularly useful for processing the large amount of files generated
# by the phantom construction.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}process_folder.py -i folder1 folder2
#
# OUTPUT:
#   results_folder.csv: quantitative results in CSV format
#
# Authors: Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE


import sys, os, shutil, argparse, pickle, io, glob
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from process_data import main


def get_parameters():
    parser = argparse.ArgumentParser(description='Compute metrics to assess the quality of spinal cord images. This '
                                                 'script requires two input files of scan-rescan acquisitions, which '
                                                 'will be used to compute the SNR. Other metrics (contrast, sharpness) '
                                                 'will be computed from the first file.')
    parser.add_argument("-i", "--input",
                        help="List here the two folders to process. They should contain the exact same file names.",
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
    parser.add_argument("-v", "--verbose",
                        help="Verbose {0,1}. Default=1",
                        type=int,
                        default=1,
                        required=False)
    args = parser.parse_args()
    return args


def main():
    # output_dir = "./output_wmgm"  # TODO: be able to set with argument
    # file_output = "results"  # no prefix
    # fdata2 = "data2.nii.gz"

    # Get list of files in folder1
    fnames = glob.glob(os.path.join(file_data[0], "*.*"))

    # loop and process
    for fname in fnames:
        # TODO: refactor process_data to use as module
        # process_data.main()


if __name__ == "__main__":
    args = get_parameters()
    file_data = args.input
    file_seg = args.seg
    file_gmseg = args.gmseg
    register = args.register
    verbose = args.verbose
    main()
