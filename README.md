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
singularity exec -e --contain -B /tmp:/tmp -B /mnt/c/Users/johnsgw3/Downloads/Spat37/:/INPUTS -B /mnt/c/Users/johnsgw3/Downloads/Spat37_out/:/OUTPUTS ~/PROJECTS/seeg_dk_atlas_assign/singularity/seeg_dk_atlas_assign_v1.0.simg bash /CODE/main.sh 8.
