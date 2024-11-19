
import os
from time import strftime as t

# Define variables
basepath = r'...' # Points to the project folder
ffystats = r'CloudCorrectedData\FirstFiveYears\_stats' # Statistics Directory
fmanpath = r'CloudCorrectedData\1_ForestMaskAnalysis' # FM Analysis Directory
fmpath = r'CloudCorrectedData\2_ForestMasks' # Forest Mask Directory
rmanpath = r'CloudCorrectedData\3_RegenerationMaskAnalysis' # RM Analysis Dir
rmpath = r'CloudCorrectedData\4_RegenerationMasks' # Regeneration Mask Directory
dist_fc = r'ChangeLog.gdb\LS_227065_DisturbanceLog' #DisturbanceLog fc
rege_fc = r'ChangeLog.gdb\LS_227065_RegenerationLog'#RegenerationLog fc
remyears = r'zz_CloudCorrectedData' #Evaluation Data

# Define functions
def convertdate(day, month, year):
    from datetime import datetime as dd
    fmt = '%Y.%m.%d'
    s = '.'.join([str(year), str(month), str(day)])
    dt = dd.strptime(s, fmt)
    return f'{dt.timetuple().tm_yday}_{year}'

def convertorddate(day, month, year):
    from datetime import datetime as dd
    return f'{dd(year, month, day).toordinal()}'

def extract_doy_stats(txtfile):
    import os
    import statistics
    doynum = int(os.path.basename(txtfile).split('_')[0])
    opentxt = open(txtfile, 'r')
    readtxt = opentxt.read()
    opentxt.close()
    valuelis = [float(n) for n in readtxt.split('[')[1][:-1].split(',')]
    stdev = statistics.stdev(valuelis)
    return {str(doynum): [valuelis, stdev]}

def compile_stats():
    import os
    # Build compiled dictionary
    compdic = {}
    stat_path = os.path.join(basepath, ffystats)
    for f in os.listdir(stat_path):
        if f.endswith('_NDVI.txt'):
            compdic.update(extract_doy_stats(os.path.join(stat_path, f)))

    # Build sorted list of values
    complis = []
    dickeys = [int(num) for num in compdic.keys()]
    dickeys.sort(reverse = True)
    for key in dickeys:
        for value in compdic[str(key)][0]:
            complis.append((key - 365, value))
            complis.append((key, value))
            complis.append((key + 365, value))
    return complis

def compile_stdev():
    import os
    compdic = {}
    stat_path = os.path.join(basepath, ffystats)
    for f in os.listdir(stat_path):
        if f.endswith('_NDVI.txt'):
            compdic.update(extract_doy_stats(os.path.join(stat_path, f)))

    # Build sorted list of values
    stdevlis = []
    dickeys = [int(num) for num in compdic.keys()]
    dickeys.sort(reverse = True)
    for key in dickeys:
        stdevlis.append((key - 365, compdic[str(key)][1]))
        stdevlis.append((key, compdic[str(key)][1]))
        stdevlis.append((key + 365, compdic[str(key)][1]))
    return stdevlis

def npfunction(input_data, input_polynomial=15):
    import numpy as np
    points = np.array(input_data)
    x = points[:,0]
    y = points[:,1]
    z = np.polyfit(x, y, input_polynomial)
    func = np.poly1d(z)
    return func

# Extract tolerance range for VIs from training data
def tolerancerange(doynum, numdev=2.6):
    import os
    import numpy as np

    # Compile stats from text files
    statsmapped = compile_stats()
    stdevmapped = compile_stdev()

    # Create polynomial functions
    statsfunc = npfunction(statsmapped)
    stdevfunc = npfunction(stdevmapped)

    # Define range values
    center = statsfunc(doynum)
    stdev = stdevfunc(doynum)
    low = center - (stdev * numdev)
    high = center + (stdev * numdev)
    
    return low, high


# Maps the band paths and generates the doy for an image folder
def mapimagefolder(imagefolder):
    import os
    imagedic = {}
    files = os.listdir(imagefolder)
    for f in files:
        if f.endswith('_CC.TIF'):
            band = f.split('_')[8]
            if imagefolder not in imagedic:
                # Translate day of year
                year = int(f.split('_')[3][:4])
                month = int(f.split('_')[3][4:6])
                day = int(f.split('_')[3][6:])
                doy_year = convertdate(day, month, year)
                ordday = convertorddate(day, month, year)
                ymd = f'{year}{str(month).zfill(2)}{str(day).zfill(2)}'
                # Add to 'dic'
                imagedic[imagefolder] = [
                    {band: f},
                    f'{doy_year}',
                    f'{ordday}',
                    f'{ymd}'
                    ]
            else:
                imagedic[imagefolder][0][band] = f
    return imagedic

def analyzeforest(imagedic, numdev=2.6):
    import os
    import arcpy
    from arcpy.sa import Plus, Float, Con, Raster, IsNull, SetNull
    from datetime import datetime as dd
    
    imagekey = list(imagedic.keys())[0]
    b4 = os.path.join(imagekey, imagedic[imagekey][0]['B4'])
    b5 = os.path.join(imagekey, imagedic[imagekey][0]['B5'])
    doy_year = imagedic[imagekey][1]
    ordday = imagedic[imagekey][2]
    ymd = imagedic[imagekey][3]
    
    mem = 'memory'
    arcpy.env.workspace = mem
    doynum = int(doy_year.split('_')[0])
    low, high = tolerancerange(doynum)

    # Create NDVI layer
    floatb4 = Float(b4)
    floatb5 = Float(b5)
    vi = (floatb5 - floatb4) / (floatb5 + floatb4)
            
    # "Reclassify-ish"
    # Sets values within tolerance range to 0
    ridlow = SetNull(vi, vi, f'Value <= {low}')
    rvi = SetNull(ridlow, 0, f'Value >= {high}')


    # Inspect forestmask repository
    fmpathfiles = [f for f in os.listdir(
        os.path.join(basepath, fmpath)
        ) if f.endswith('.TIF')]
    if not len(fmpathfiles):
        forestmask = rvi
        forestimagepath = os.path.join(
            basepath,
            fmpath,
            f'{ordday}_{ymd}_forestmask_{numdev}stdev.TIF'
            )
        forestmask.save(forestimagepath)
    else:
        # Find current forest mask
        ordlis = []
        for f in fmpathfiles:
            try:
                fstart = int(f.split('_')[0])
                ordlis.append(fstart)
            except:
                pass
        ordlis.sort(reverse=True)
        strordday = str(ordlis[0])
        for f in fmpathfiles:
            if f.startswith(strordday):
                forestmask = Raster(os.path.join(basepath, fmpath, f))
                break

        # Begin analysis
        # Fills null pixels with the value of 1 - outside of tolerance range
        analysis_isnull = IsNull(rvi)
        analysisimagepath = os.path.join(
            basepath,
            fmanpath,
            f'{ordday}_{ymd}_analysis_{numdev}stdev.TIF'
            )
        analysis_isnull.save(analysisimagepath)

        # Capture cloud contaminated pixels in raw image
        b4stats = IsNull(Raster(b4))
        cloudcon = SetNull(b4stats, 0, 'Value <> 1')
        
        # Analyze change
        fm = Raster(forestmask)
        # Add the forest mask and null corrected analysis together
        fmann = Plus(fm, analysis_isnull)
        # Identify which pixels haven't changed (Value = 1)
        compfmann = fm == fmann
        # Reset unchanged pixels to 0
        resetunchan = Con(compfmann, 0, fmann, 'Value = 1')
        # Capture cloud contaminated pixels from "fm"
        ccfmpix = Plus(fm, cloudcon)
        # Combine all analyses into a single image
        com = Con(b4stats, ccfmpix, resetunchan, 'Value = 1')

        # Log pixels that have three consecutive disturbances in "dist_fc"
        if com.maximum > 2:
            imagedate = dd(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]))
            tempfc = os.path.join(mem, f'_{ordday}')
            rempix = SetNull(com, 0, 'Value <> 3')
            arcpy.conversion.RasterToPolygon(rempix, tempfc, 'NO_SIMPLIFY')
            arcpy.management.AddField(tempfc, 'Recorded', 'DATEONLY')
            with arcpy.da.UpdateCursor(tempfc, 'Recorded') as update:
                for u in update:
                    u[0] = imagedate
                    update.updateRow(u)
            arcpy.management.Append(tempfc,
                                    os.path.join(basepath, dist_fc),
                                    'NO_TEST')
            
            # Remove pixels that have three consecutive disturbances from "com"
            newforestmask = SetNull(com, com, 'Value = 3')
        else:# if com.maximum > 2:
            newforestmask = com
            
        # Save and return "newforestmask"
        forestimagepath = os.path.join(
            basepath,
            fmpath,
            f'{ordday}_{ymd}_forestmask_{numdev}stdev.TIF'
            )
        newforestmask.save(forestimagepath)
        return newforestmask

def analyzeregeneration(imagedic, numregen=19, numdev=2.6):
    import os
    import arcpy
    from arcpy.sa import Plus, Float, Con, Raster, IsNull, SetNull
    from datetime import datetime as dd

    imagekey = list(imagedic.keys())[0]
    b4 = os.path.join(imagekey, imagedic[imagekey][0]['B4'])
    b5 = os.path.join(imagekey, imagedic[imagekey][0]['B5'])
    doy_year = imagedic[imagekey][1]
    ordday = imagedic[imagekey][2]
    ymd = imagedic[imagekey][3]

    mem = 'memory'
    arcpy.env.workspace = mem
    doynum = int(doy_year.split('_')[0])
    low, high = tolerancerange(doynum)

    # Inspect forestmask repository
    fmpathfiles = [f for f in os.listdir(
        os.path.join(basepath, fmpath)
        ) if f.endswith('.TIF')]
    
    # Find current forest mask
    ordlis = []
    for f in fmpathfiles:
        try:
            fstart = int(f.split('_')[0])
            ordlis.append(fstart)
        except:
            pass
    ordlis.sort(reverse=True)
    strordday = str(ordlis[0])
    for f in fmpathfiles:
        if f.startswith(strordday):
            curfmpath = os.path.join(basepath, fmpath, f)
            forestmask = Raster(curfmpath)
            break

    # Change the Null values in forestmask to 0 and set reset to Null
    fm_isnull = IsNull(forestmask)
    fm_nullas0 = SetNull(fm_isnull, 0,'Value = 0')
    
    # Inspect regenmask repository
    rmpathfiles = [f for f in os.listdir(
        os.path.join(basepath, rmpath)
        ) if f.endswith('.TIF')]
    regenimagepath = os.path.join(
        basepath,
        rmpath,
        f'{ordday}_{ymd}_regenmask_{numdev}stdev.TIF'
        )
    if not len(rmpathfiles):
        regenmask = fm_nullas0
        regenmask.save(regenimagepath)
    else:
        # Find current regen mask
        ordlis = []
        for f in rmpathfiles:
            try:
                fstart = int(f.split('_')[0])
                ordlis.append(fstart)
            except:
                pass
        ordlis.sort(reverse=True)
        strordday = str(ordlis[0])
        for f in rmpathfiles:
            if f.startswith(strordday):
                curregenmask = Raster(os.path.join(basepath, rmpath, f))
                break
            
        # Create NDVI layer
        floatb4 = Float(b4)
        floatb5 = Float(b5)
        vi = (floatb5 - floatb4) / (floatb5 + floatb4)

        # "Reclassify-ish"
        ridlow = SetNull(vi, vi, f'Value <= {low}')
        rvi = SetNull(ridlow, 1, f'Value >= {high}')

        # Define "analysisimagepath"
        analysisimagepath = os.path.join(
            basepath,
            rmanpath,
            f'{ordday}_{ymd}_regenanalysis_{numdev}stdev.TIF'
            )
        # Evaluate Null pixels in "curregenmask"
        crm_isnull = IsNull(curregenmask)
        # Set Null values in "curregenmask" to 0 if the pixel has become
        # Null in the "forestmask"
        regenmask = Con(crm_isnull, fm_nullas0, curregenmask, 'Value = 1')

        if not rvi.isEmpty():
            # Begin analysis
            analysis_isnull = IsNull(rvi)
            # Fills null pixels with the value of 0 - outside of
            # tolerance range
            analysis = Con(analysis_isnull, 0, 1, 'Value = 1')
            analysis.save(analysisimagepath)

            # Capture cloud contaminated pixels in raw image
            b4stats = IsNull(Raster(b4))
            cloudcon = SetNull(b4stats, 0, 'Value <> 1')
            
            # Analyze change
            rm = Raster(regenmask)
            # Add the regen mask and null corrected analysis together
            rmann = Plus(rm, analysis)
            # Identify which pixels haven't changed (Value = 1)
            comprmann = rm == rmann
            # Reset unchanged pixels to 0
            resetunchan = Con(comprmann, 0, rmann, 'Value = 1')
            # Capture cloud contaminated pixels from "rm"
            ccrmpix = Plus(rm, cloudcon)
            # Combine all analyses into a single image
            com = Con(b4stats, ccrmpix, resetunchan, 'Value = 1')

            # Log pixels that have "numregen" successive returns in tolerance
            # in "rege_fc"
            if com.maximum == numregen:
                imagedate = dd(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]))
                tempfc = os.path.join(mem, f'r_{ordday}')
                rempix = SetNull(com, 0, f'Value <> {numregen}')
                arcpy.conversion.RasterToPolygon(rempix, tempfc,
                                                 'NO_SIMPLIFY')
                arcpy.management.AddField(tempfc, 'Recorded', 'DATEONLY')
                with arcpy.da.UpdateCursor(tempfc, 'Recorded') as update:
                    for u in update:
                        u[0] = imagedate
                        update.updateRow(u)
                arcpy.management.Append(tempfc,
                                        os.path.join(basepath, rege_fc),
                                        'NO_TEST')

                # Remove pixels that have ten successive in tolerance
                # returns from "com"
                newregenmask = SetNull(com, com, f'Value = {numregen}')   

                # If pixels meet threshold for reintegration into the
                # forestmask, add logic here to update forestmask
                newforestmask = Con(
                    fm_isnull, rempix, forestmask, 'Value = 1')

                # Have to be able to overwrite forestmask
                arcpy.env.overwriteOutput = True
                newforestmask.save(curfmpath)
                arcpy.env.overwriteOutput = False
                    
            else:#if com.maximum == "numregen":
                newregenmask = com
                
            # Save and return "newregenmask"
            if not newregenmask.isEmpty():
                newregenmask.save(regenimagepath)
                return newregenmask
            else:
                return
        else:#if not rvi.isEmpty():
            return
            
# Execute code
if __name__ == '__main__':
    print(f'''Start of processing:\t{t('%X')}''')
    individual = False
    if individual:
        imagefolder = r''
        imagedic = mapimagefolder(imagefolder)
        analyzeforest(imagedic, 2.6)
        print(f'''Finished processing:\t{t('%X')}''')
    else:    
        datedic = {}
        for path, folders, files in os.walk(os.path.join(basepath, remyears)):
            if len(folders):
                for folder in folders:
                    if len(folder) > 20:
                        foldsplit = folder.split('_')
                        if foldsplit[0] in ('LC08', 'LC09'):
                            datedic[foldsplit[3]] = os.path.join(path, folder)
        datelis = [d for d in datedic]
        datelis.sort()

        for strdate in datelis:
            print(f'''Start processing of {strdate}:\t{t('%X')}''')
            imagedic = mapimagefolder(datedic[strdate])
            analyzeforest(imagedic, 2.6)
            analyzeregeneration(imagedic, 19, 2.6)
            print(f'''\tCompleted processing of {strdate}:\t{t('%X')}''')
