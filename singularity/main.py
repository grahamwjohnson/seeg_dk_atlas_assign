# Assign SEEG contacts to DK atlas
# Graham Johnson
print("Hello from Python called by bash")
import glob, json, math, os, re, shutil, subprocess, traceback, sys, time, datetime, csv, numpy as np, math, \
    nibabel as nib
from distutils.spawn import find_executable

import sys

# Need to include the path to the MRTrix3 libraries to run MRTrix3 commands
sys.path.insert(0, '/APPS/mrtrix3/lib')
from mrtrix3 import app, file, fsl, image, path, run

print("Finished importing python modules")


out_phrase = "Hello from Bash called by Python called by Bash!"
cmd = 'echo {}'.format(out_phrase) # how to run bash commands from python
subprocess.check_call(cmd, shell=True)



















# Make a temporary subdirectory that will be deleted after processing to save space
tmp_dir = "/OUTPUTS/tmp/"
if not os.path.exists(tmp_dir):
    os.mkdir(tmp_dir)
    print("Created 'tmp' directory")
else:
    print("'tmp' directory already exists")

# Make the final results subdirectory
results_dir = "/OUTPUTS/results/"
if not os.path.exists(results_dir):
    os.mkdir(results_dir)
    print("Created 'results' directory")
else:
    print("'results' directory already exists")

# Do all of the processing in 'tmp' directory   

cmd ='mrconvert /INPUTS/dwmri.nii.gz -fslgrad /INPUTS/dwmri.bvec /INPUTS/dwmri.bval {}DWI_qav7_preprocessed.mif -force -nthreads 0'.format(tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'dwibiascorrect ants {}DWI_qav7_preprocessed.mif  {}DWI_biascorrect_preprocessed.mif -scratch /tmp -force -nthreads 0'.format(tmp_dir,tmp_dir) 
subprocess.check_call(cmd, shell=True)

cmd = 'dwi2mask {}DWI_biascorrect_preprocessed.mif {}dwi_mask.mif -force -nthreads 0'.format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'maskfilter {}dwi_mask.mif dilate {}dwi_mask_dilated.mif -npass 3 -force -nthreads 0'.format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'dwi2tensor {}DWI_biascorrect_preprocessed.mif -mask {}dwi_mask.mif - | tensor2metric - -fa {}fa.mif -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

# Copy fa.mif to results directory
cmd = 'mrconvert {}fa.mif {}fa.nii.gz -force -nthreads 0'.format(tmp_dir,results_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'dwi2response dhollander {}DWI_biascorrect_preprocessed.mif {}response_wm.txt {}response_gm.txt {}response_csf.txt -mask {}dwi_mask.mif -force -nthreads 0 -scratch /tmp'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'dwi2fod msmt_csd {}DWI_biascorrect_preprocessed.mif {}response_wm.txt {}FOD_WM.mif {}response_csf.txt {}FOD_CSF.mif -mask {}dwi_mask_dilated.mif -lmax 10,0 -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

# Steps to register T1 to DWI space
cmd = 'mrconvert /INPUTS/t1.nii.gz {}T1W3D.mif -force -nthreads 0'.format(tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrconvert /INPUTS/t1.nii.gz {}T1W3D.nii -force -nthreads 0'.format(tmp_dir)
subprocess.check_call(cmd, shell=True)

T1_header = image.Header('{}T1W3D.mif'.format(tmp_dir))
T1_revert_strides_option = ' -strides ' + ','.join([str(i) for i in T1_header.strides()])
print(T1_revert_strides_option)

cmd = 'runROBEX.sh {}T1W3D.nii {}T1W3D_initialBrain.nii {}T1W3D_initialMask.nii'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

# Have to reslice the mask due to 1e-6 header matching required by ANTS: https://github.com/MRtrix3/mrtrix3/issues/859
cmd = 'mrtransform {}T1W3D_initialMask.nii {}T1W3D_initialMask_resliced.nii -template {}T1W3D.nii -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'N4BiasFieldCorrection -i {}T1W3D.nii -w {}T1W3D_initialMask_resliced.nii -o {}T1W3D_biascorr.nii'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'runROBEX.sh {}T1W3D_biascorr.nii {}T1W3D_biascorr_brain.nii {}T1W3D_biascorr_brain_mask.nii'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = ('mrconvert {}T1W3D_biascorr_brain.nii {}T1W3D_biascorr_brain.mif -force -nthreads 0' + T1_revert_strides_option).format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = ('mrconvert {}T1W3D_biascorr_brain_mask.nii {}T1W3D_mask.mif -datatype bit -force -nthreads 0' + T1_revert_strides_option).format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'dwiextract {}DWI_biascorrect_preprocessed.mif -bzero - | mrcalc - 0.0 -max - | mrmath - mean -axis 3 {}dwi_meanbzero.mif -force -nthreads 0'.format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrcalc 1 {}dwi_meanbzero.mif -div {}dwi_mask.mif -mult - | mrhistmatch nonlinear - {}T1W3D_biascorr_brain.mif {}dwi_pseudoT1.mif -mask_input {}dwi_mask.mif -mask_target {}T1W3D_mask.mif -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrcalc 1 {}T1W3D_biascorr_brain.mif -div {}T1W3D_mask.mif -mult - | mrhistmatch nonlinear - {}dwi_meanbzero.mif {}T1W3D_pseudobzero.mif -mask_input {}T1W3D_mask.mif -mask_target {}dwi_mask.mif -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrregister {}T1W3D_biascorr_brain.mif {}dwi_pseudoT1.mif -type rigid -mask1 {}T1W3D_mask.mif -mask2 {}dwi_mask.mif -rigid {}rigid_T1_to_pseudoT1.txt -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrregister {}T1W3D_pseudobzero.mif {}dwi_meanbzero.mif -type rigid -mask1 {}T1W3D_mask.mif -mask2 {}dwi_mask.mif -rigid {}rigid_pseudobzero_to_bzero.txt -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'transformcalc {}rigid_T1_to_pseudoT1.txt {}rigid_pseudobzero_to_bzero.txt average {}rigid_T1_to_dwi.txt -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrtransform {}T1W3D.mif {}T1W3D_registered.mif -linear {}rigid_T1_to_dwi.txt -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrtransform {}T1W3D_mask.mif {}T1W3D_mask_registered.mif -linear {}rigid_T1_to_dwi.txt -template {}T1W3D_registered.mif -interp nearest -datatype bit -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

# mrconvert the T1_registered to results directory
cmd = 'mrconvert {}T1W3D_registered.mif {}T1W3D_registered.nii.gz -force -nthreads 0'.format(tmp_dir,results_dir)
subprocess.check_call(cmd, shell=True)

attempts = 0
fiveTTdone = 0
while attempts < 3:
    attempts = attempts + 1
    try:
        cmd = '5ttgen fsl {}T1W3D_registered.mif {}5TT.mif -force -nthreads 0 -scratch /tmp'.format(tmp_dir,tmp_dir)
        subprocess.check_call(cmd, shell=True)
        fiveTTdone = 1
        break
    except Exception as error:
        print("5TTgen failed, trying again")

if fiveTTdone == 0:
    raise Exception("5TTgen failed all atempts")

# Save 5TT and 5TT_vis in results directory
cmd = 'mrconvert {}5TT.mif {}5TT.nii.gz -force -nthreads 0'.format(tmp_dir, results_dir)
subprocess.check_call(cmd, shell=True)

cmd = '5tt2vis {}5TT.mif {}5TT_vis.nii.gz -force -nthreads 0'.format(tmp_dir,results_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrconvert /INPUTS/aparc+aseg.mgz {}aparc+aseg.mif -force -nthreads 0'.format(tmp_dir)
subprocess.check_call(cmd, shell=True)

cmd = 'mrtransform {}aparc+aseg.mif {}aparc+aseg_registered.mif -linear {}rigid_T1_to_dwi.txt -template {}T1W3D_registered.mif -interp nearest -force -nthreads 0'.format(tmp_dir,tmp_dir,tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

#DEBUGGING - output steps surrounding labelconvert because bilateral insula are missing
#cmd = 'mrconvert {}aparc+aseg_registered.mif {}aparc+aseg_registered.nii.gz'.format(tmp_dir,results_dir)
#subprocess.check_call(cmd, shell=True)
# SOLVED: have to manually add L and R insula to FreeSurferColorLUT.txt

cmd = 'labelconvert {}aparc+aseg_registered.mif /CODE/fs_files/FreeSurferColorLUT.txt /APPS/mrtrix3/share/mrtrix3/labelconvert/fs_default.txt {}XNAT_parc_init.mif -force -nthreads 0'.format(tmp_dir,tmp_dir)
subprocess.check_call(cmd, shell=True)

attempts = 0
sgmfix_done = 0
while attempts < 3:
    attempts = attempts + 1
    try:
        cmd = 'labelsgmfix {}XNAT_parc_init.mif {}T1W3D_registered.mif  /APPS/mrtrix3/share/mrtrix3/labelconvert/fs_default.txt {}parc.mif -force -nthreads 0 -scratch /tmp'.format(tmp_dir,tmp_dir,tmp_dir)
        subprocess.check_call(cmd, shell=True)
        sgmfix_done = 1
        break
    except Exception as error:
        print("labelsgmfix failed, trying again")

if sgmfix_done == 0:
    raise Exception("labelsgmfix failed all atempts")

# mrconvert the parc.mif to results
cmd = 'mrconvert {}parc.mif {}parc.nii.gz -force -nthreads 0'.format(tmp_dir,results_dir)
subprocess.check_call(cmd, shell=True)


#Run multiple times to attempt to capture stochasticity and to enable data augmenting
#Delete each.tck after each individual run to save space

for i in range(loops):
    print("Connectome iteration: " + str(i+1))
    tck_tmp_dir = tmp_dir + "tck_tmp/"
    if not os.path.exists(tck_tmp_dir):
        os.mkdir(tck_tmp_dir)
        print("Created 'tck_tmp' directory within 'tmp'")
    else:
        print("'tck_tmp' directory already exists")

    cmd = 'tckgen {}FOD_WM.mif {}10M.tck -act {}5TT.mif -backtrack -crop_at_gmwmi -maxlength 250 -power 0.33 -select 10000000 -seed_dynamic {}FOD_WM.mif -force -nthreads 0'.format(tmp_dir,tck_tmp_dir,tmp_dir,tmp_dir)
    subprocess.check_call(cmd, shell=True)

    cmd = 'tcksift2 {}10M.tck {}FOD_WM.mif {}10M_SIFT2_weights.csv -act {}5TT.mif -out_mu {}10M_mu.txt -fd_scale_gm -force -nthreads 0'.format(tck_tmp_dir,tmp_dir,tck_tmp_dir,tmp_dir,tck_tmp_dir)
    subprocess.check_call(cmd, shell=True)

    # Meanlenghth connectome
    cmd = 'tck2connectome {}10M.tck {}parc.mif {}meanlength_connectome_{}.csv -scale_length -stat_edge mean -symmetric -force -nthreads 0'.format(tck_tmp_dir,tmp_dir,results_dir,str(i+1))
    subprocess.check_call(cmd, shell=True)

    # Connectome with only SIFT2 correction
    cmd = 'tck2connectome {}10M.tck {}parc.mif {}SIFT2_connectome_{}.csv -tck_weights_in {}10M_SIFT2_weights.csv -symmetric -force -nthreads 0'.format(tck_tmp_dir,tmp_dir,results_dir,str(i+1),tck_tmp_dir)
    subprocess.check_call(cmd, shell=True)

    # Mean FA connectome
    cmd = 'tcksample {}10M.tck {}fa.mif {}mean_FA_per_streamline.csv -stat_tck mean; tck2connectome {}10M.tck {}parc.mif {}meanFA_connectome_{}.csv -scale_file {}mean_FA_per_streamline.csv -stat_edge mean -symmetric -force -nthreads 0'.format(tck_tmp_dir,tmp_dir,tck_tmp_dir,tck_tmp_dir,tmp_dir,results_dir,str(i+1),tck_tmp_dir)
    subprocess.check_call(cmd, shell=True)

    # Delete the TCK temporary directory
    cmd = 'rm -r {}'.format(tck_tmp_dir)
    subprocess.check_call(cmd, shell=True)

print("All connectome iterations complete")

# Delete the temporary directory
cmd = 'rm -r {}'.format(tmp_dir)
subprocess.check_call(cmd, shell=True)

print("Removed tmp directory")
print("Script complete")




