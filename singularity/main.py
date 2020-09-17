# Assign SEEG contacts to DK atlas
# Graham Johnson
print("Hello from Python called by bash")
import glob, json, math, os, re, shutil, subprocess, traceback, sys, time, datetime, csv, numpy as np, math, \
    nibabel as nib
from distutils.spawn import find_executable

import sys

# Need to include the path to the MRTrix3 libraries to run MRTrix3 commands
sys.path.insert(0, '/APPS/mrtrix3/lib')
from mrtrix3 import app, fsl, image, path, run

print("Finished importing python modules")


out_phrase = "Hello from Bash called by Python called by Bash!"
cmd = 'echo {}'.format(out_phrase) # how to run bash commands from python
subprocess.check_call(cmd, shell=True)

# This function goes and looks for the fs_default.txt LUT that is provided  by freesurfer and returns the
# names of the regions so that they can be used in "createROI" function to make a csv
def ROINames(LUTpath, offset):
    # Get length of atlas LUT
    with open(LUTpath) as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')
        FS_row_count = sum(1 for row in reader)

    # Initialize matrix to hold all ppr lines and labels
    raw_fsDefault = ["" for x in range(FS_row_count)]
    with open(LUTpath) as csvfile:
        index = 0
        reader = csv.reader(csvfile, delimiter=' ')
        for row in reader:
            raw_fsDefault[index] = row
            index = index + 1

    # get rid of first few lines
    raw_fsDefault = raw_fsDefault[offset:]
    # initialize region name, will trim downafter assignments finished.
    DKSname = ["" for x in range(len(raw_fsDefault))]
    regionCount = 0
    for i in range(len(raw_fsDefault)):
        # assign ROI to proper index listed in first colum
        if raw_fsDefault[i] != []:
            # print raw_fsDefault[i]
            roi = int(raw_fsDefault[i][0])
            # Find the 3rd non-empty cell
            nonEmptyCount = 0
            name = 'NA'
            for j in range(len(raw_fsDefault[i])):
                if raw_fsDefault[i][j] != '':
                    nonEmptyCount = nonEmptyCount + 1
                if nonEmptyCount == 3:
                    name = raw_fsDefault[i][j]
                    break
            DKSname[roi - 1] = name
            regionCount = regionCount + 1
    # Trim array to proper size, remember fr later that ROI number will be off by 1
    DKSname = DKSname[:regionCount]
    return DKSname


# This function will read in a .ppr file to get bipole coordinates and it will save a csv that contains all of the parcellation assignments
# (and create an <ROI>.mif with the radius of each ROI being the distance between contacts for each bipole)
def assign_ROI(ppr, offset, T1_forAtlas, raw_parc):
    # Only create an ROI if PPR file is in folder
    if os.path.isfile(ppr):
        # Get number of lines in ppr
        with open(ppr) as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            row_count = sum(1 for row in reader)
            # print(row_count)

        # Initialize matrix to hold all ppr lines and labels
        raw_ppr = ["" for x in range(row_count)]
        LEAD_CONTACT_index = -1

        # open the PPR and find start of contact assignments.
        # Take the last 3 numbers in each line
        # Also store the label names
        with open(ppr) as csvfile:
            index = 0
            reader = csv.reader(csvfile, delimiter=' ')
            for row in reader:
                # The row with [LEAD CONTACT] will have a length of 2
                if len(row) == 2:
                    if row[0] == '[LEAD' and row[1] == 'CONTACT]':
                        LEAD_CONTACT_index = index
                raw_ppr[index] = row
                index = index + 1

        # This is the first line that has contact information
        lineOne = LEAD_CONTACT_index + offset

        # Iterate through rows starting from where first contact is listed and stop if [] is encountered
        index = 0
        labels = ["" for x in range(row_count)]  # Will trim down below
        bipCoordsString = ["" for x in range(row_count)]  # Will trim down below
        emptyLine = -1
        leadCount = 1
        bipCount = 0
        x = [0] * row_count
        y = [0] * row_count
        z = [0] * row_count
        xBip = [0] * row_count  # not all will be used and will need to trim
        yBip = [0] * row_count  # not all will be used and will need to trim
        zBip = [0] * row_count  # not all will be used and will need to trim
        bipDist = [0] * row_count  # not all will be used and will need to trim
        bipLabelsUsedString = [0] * row_count
        bipOrigCoordsUsedString = [0] * row_count

        lastRow = ' '

        for i in range(lineOne, row_count - 1, 1):
            # Store the contact label in a string and coordinates in one string
            # NOTE: switching to 1 based indexing
            a = raw_ppr[i]
            # Stop if the line is empty (i.e. end of contact listing)
            if a == []:
                emptyLine = index
                break
            labels[index] = a[0] + ' ' + str(int(a[1]) + 1)
            l = len(a)
            x[index] = float(a[l - 4])
            y[index] = float(a[l - 3])
            z[index] = float(a[l - 2])

            # If same lead make a bipole, otherwsie iterate lead count if new lead
            if index != 0:
                if lastRow[0] == a[0]:  # same lead so create bipole
                    x1 = x[index - 1]
                    x2 = x[index]
                    y1 = y[index - 1]
                    y2 = y[index]
                    z1 = z[index - 1]
                    z2 = z[index]

                    # calculate midpoint between contacts
                    xBip[bipCount] = (x1 + x2) / 2
                    yBip[bipCount] = (y1 + y2) / 2
                    zBip[bipCount] = (z1 + z2) / 2

                    # Find the distance between the contacts and use it later for sphere ROI size
                    bipDist[bipCount] = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

                    # Create a string to be used in MRTrix3 commands
                    bipCoordsString[bipCount] = str(xBip[bipCount]) + ',' + str(yBip[bipCount]) + ',' + str(
                        zBip[bipCount])
                    bipOrigCoordsUsedString[bipCount] = 'Contact1: ' + str(x1) + ',' + str(y1) + ',' + str(
                        z1) + ' Contact2: ' + str(x2) + ',' + str(y2) + ',' + str(z2)
                    bipLabelsUsedString[bipCount] = str(labels[index - 1]) + ' - ' + str(labels[index])

                    bipCount = bipCount + 1
                else:
                    leadCount = leadCount + 1

            lastRow = a
            index = index + 1

        # delete unused parts of arrays
        # print emptyLine
        x = x[:emptyLine]
        y = y[:emptyLine]
        z = z[:emptyLine]
        xBip = xBip[:bipCount]
        yBip = yBip[:bipCount]
        zBip = zBip[:bipCount]
        labels = labels[:emptyLine]
        bipCoordsString = bipCoordsString[:bipCount]
        bipOrigCoordsUsedString = bipOrigCoordsUsedString[:bipCount]
        bipLabelsUsedString = bipLabelsUsedString[:bipCount]
        bipDist = bipDist[:bipCount]

        print 'Bip Count: ' + str(bipCount)
        print bipLabelsUsedString

        # Now we will create an ROI from T1_Reg or T1 by setting everything to 0 and assigning regions by
        # incrementing up by 1 Zero the values of T1_Reg and then assign incrementing sphere ROI values to the
        # coordinates in bipCoordsStringtr
        cmd = 'mrcalc {} 0 -mult {}ROI_Contacts_T1regSpace.mif'.format(T1_forAtlas,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        for i in range(len(bipCoordsString)):
            cmd = 'mredit -sphere {} {} {} {}ROI_Contacts_T1regSpace.mif'.format(bipCoordsString[i],str(bipDist[i]),str(i + 1),tmp_dir)
            subprocess.check_call(cmd, shell=True)

        # NOW assign SEEG contacts to DKS atlas

        # Read in T1
        cmd = 'mrconvert {} {}T1W3D.nii -force -nthreads 0'.format(T1_forAtlas,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        # Bring in the parcellation
        cmd = 'mrconvert {} {}aparc+aseg.mif -force -nthreads 0'.format(raw_parc,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        cmd = 'labelconvert {}aparc+aseg.mif {} {} {}parc_init.mif -force -nthreads 0'.format(tmp_dir,fscolorLUT,fsDefault,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        attempts = 0
        sgmfix_done = 0
        while attempts < 3:
            attempts = attempts + 1
            try:
                cmd = 'labelsgmfix {}parc_init.mif {}T1W3D.mif  {} {}parc.mif -force -nthreads 0 -scratch /tmp'.format(tmp_dir,tmp_dir,fsDefault,tmp_dir)
                subprocess.check_call(cmd, shell=True)
                sgmfix_done = 1
                break
            except Exception as error:
                print("labelsgmfix failed, trying again")

        if sgmfix_done == 0:
            raise Exception("labelsgmfix failed all attempts")

        # mrconvert the parc.mif to results
        cmd = 'mrconvert {}parc.mif {}parc.nii.gz -force -nthreads 0'.format(tmp_dir,results_dir)
        subprocess.check_call(cmd, shell=True)


        # Need to regrig parc so that it is the same as T1reg or T1 because T1reg or T1 was used to make SEEG ROI
        cmd = 'mrtransform -template {} {}parc.mif {}parc_regridT1.nii -interp nearest'.format(T1_forAtlas,tmp_dir,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        # Get the strides from T1_Reg so that we can convert parc with same strides so that indexing is straighforward
        ROI_header = image.Header(tmp_dir + 'ROI_Contacts_T1regSpace.mif')
        ROI_strides = ROI_header.strides()
        ROI_strides_option = ' -strides ' + ','.join([str(i) for i in ROI_strides])

        cmd = 'mrconvert {}parc_regridT1.nii {}parc_strideSameAsT1Reg_regridT1.nii -strides 1,2,3'.format(tmp_dir,tmp_dir)
        subprocess.check_call(cmd, shell=True)

        # import the nifti with nibabel and numpy and read coordinate values
        imgPath = tmp_dir + 'parc_strideSameAsT1Reg_regridT1.nii'
        img = nib.load(imgPath)
        data = np.array(img.dataobj)

        # Get strides to verify same as T1_reg. If they are not equal, indexing will be a headache
        parc_header = image.Header(imgPath)
        parc_strides = parc_header.strides()
        # print 'Parc Strides: ' + str(parc_strides)
        if parc_strides != ROI_strides:
            print 'Error: T1_registered or T1 strides(' + str(ROI_strides) + ') do not equal ' + imgPath + ' strides(' + str(
                parc_strides) + ')'
            raise Exception(err)

        # Assign intensity values to each Bip Coord if value is whole number
        DKS_assignment = [-1] * bipCount
        for i in range(bipCount):
            point = data[int(round(xBip[i])), int(round(yBip[i])), int(round(zBip[i]))]
            res = point - int(point)
            if res != 0:
                print 'Error: Interpolated, intensity not whole number for point: ' + str(point)
            else:
                DKS_assignment[i] = int(point)

        # pull in the DKS atlas names to assign ROI numbers proper region name
        DKSname = ROINames(fsDefault, lineOffestFSdefault)

        # Write a CSV file with the labels and coordinates
        with open(results_dir + 'SEEG_BipMontage_ROI_Assignments.csv', 'wb') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',')
            filewriter.writerow(
                ['Bipole Number', 'Bip Label', 'DKS Assignment', 'DKS Region Name', 'Bip Coord String',
                 'Original Coords', 'Bip Distance'])
            for i in range(bipCount):
                # print bipLabelsUsedString[i]
                if DKS_assignment[i] != 0:
                    name = DKSname[DKS_assignment[i] - 1]  # -1 because of zero indexing
                else:
                    name = 'NA'
                filewriter.writerow(
                    [str(i + 1), bipLabelsUsedString[i], DKS_assignment[i], name, bipCoordsString[i],
                     bipOrigCoordsUsedString[i], bipDist[i]])
        print('Created SEEG_BipMontage_ROI_Assignments.csv')

    else:
        print('****** ERROR: No PPR file found, thus no ROI created and no atlas assignments made')





# Set up variables for reading in .ppr
pprFilename = '/INPUTS/crave.ppr'
lineOffsetFromLEADCONTACT = 5
fsDefault = '/CODE/fs_files/fs_defaults.txt'
fscolorLUT = '/CODE/fs_files/FreeSurferColorLUT.txt'
lineOffestFSdefault = 4
T1_forAtlas = '/INPUTS/t1.nii'
raw_parc = '/INPUTS/aparc+aseg.mgz'


# Get timestamps for directories
seconds = time.time()
tstring = str(time.asctime(time.localtime(seconds)))
tstring = tstring.replace(' ','_')
tstring = tstring.replace(':','')

# Make a temporary subdirectory that will be deleted after processing to save space
tmp_dir = "/OUTPUTS/tmp_" + tstring + "/"
if not os.path.exists(tmp_dir):
    os.mkdir(tmp_dir)
    print("Created 'tmp' directory")
else:
    print("'tmp' directory already exists")

# Make the final results subdirectory
results_dir = "/OUTPUTS/results_" + tstring + "/"
if not os.path.exists(results_dir):
    os.mkdir(results_dir)
    print("Created 'results' directory")
else:
    print("'results' directory already exists")


assign_ROI(pprFilename, lineOffsetFromLEADCONTACT, T1_forAtlas, raw_parc)

print("Script complete")




