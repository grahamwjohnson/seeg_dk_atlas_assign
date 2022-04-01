# seeg_dk_atlas_assign
Assign SEEG contacts to DK atlas from FreeSurfer using MRTrix3 labels. 

INPUTS:
t1.nii
aparc+aseg.mgz (from FreeSurfer recon-all command)
crave.ppr (exported crave .ppr in T1 space)

OUTPUTS:
parc.nii.gz #This is the MRTrix3 'labelsgmfix' modified Freesurfer parcellation (uses FSL and T1 to do this)
SEEG_BipMontage_ROI_Assignments.csv # This is the DK atlas assignments for all bipolar pairs present in .ppr file 

Example run command: 
singularity exec -e --contain -B /tmp:/tmp -B /mnt/c/Users/johnsgw3/Downloads/Epat41/:/INPUTS -B /mnt/c/Users/johnsgw3/Downloads/Epat41_out/:/OUTPUTS ~/PROJECTS/seeg_dk_atlas_assign/singularity/seeg_dk_atlas_assign_v1.0.simg bash /CODE/main.sh 24

TROUBLESHOOTING:

1) 
***
Traceback (most recent call last):
  File "/CODE/main.py", line 321, in <module>
    assign_ROI(pprFilename, lineOffsetFromLEADCONTACT, T1_forAtlas, raw_parc)
  File "/CODE/main.py", line 127, in assign_ROI
    labels[index] = a[0] + ' ' + str(int(a[1]) + 1)
ValueError: invalid literal for int() with base 10: ''
***

This error can occur if the crave.ppr has an indentation for the lines after "[LEAD CONTACT]" (new versions of CRAVE)
Will need to run the MATLAB script 'convert_ppr' [X:\000_Data\SEEG\code\preprocessing_code\ppr_conversion] to get the ppr into the old style