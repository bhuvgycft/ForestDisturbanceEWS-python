
import os
import statistics

# Define input variables
inputpath = r'...\Data\zz_TrainingData'
outputpath = r'...\Data\CloudCorrectedData\FirstFiveYears'


def cloudcorrect(folderpath, outputdir=outputpath):
    import arcpy
    import os
    import shutil
    from arcpy.sa import Times, SetNull
    mem = 'memory'
    arcpy.env.workspace = mem
    arcpy.env.overwriteOutput = True

    metadatafiles = []

    # Map pertinent variables
    for f in os.listdir(folderpath):
        if f.endswith('_QA_PIXEL.TIF'):
            qa = os.path.join(folderpath, f)
            metadatafiles.append(qa)
        elif f.endswith('SR_B4.TIF'):
            b4 = os.path.join(folderpath, f)
        elif f.endswith('SR_B5.TIF'):
            b5 = os.path.join(folderpath, f)
        elif f[-7:] in ('ANG.txt', 'MTL.txt', 'MTL.xml'):
            metadatafiles.append(os.path.join(folderpath, f))

    # Create new folder directories and move "metadatafiles"
    foldername = os.path.basename(folderpath)
    platform = foldername[:4]
    newfoldername = f'{os.path.basename(folderpath)}__CC'
    newfolderpath = os.path.join(outputdir, platform, newfoldername)
    try:
        os.makedirs(os.path.join(outputdir, platform))
    except:
        pass
    outfolds = os.listdir(os.path.join(outputdir, platform))
    if newfoldername not in outfolds:
        os.makedirs(newfolderpath)
        for meta in metadatafiles:
            shutil.copyfile(
                meta, os.path.join(newfolderpath, os.path.basename(meta))
            )

    # Cloud correct bands and save to "newfolderpath"
    qacc = SetNull(qa, 1, 'Value <> 21824')
    qaccname = f'''{os.path.basename(qa).split('.')[0]}__CC.TIF'''
    qacc.save(os.path.join(newfolderpath, qaccname))
    b4cc = Times(b4, qacc)
    b4ccname = f'''{os.path.basename(b4).split('.')[0]}__CC.TIF'''
    b4cc.save(os.path.join(newfolderpath, b4ccname))
    b5cc = Times(b5, qacc)
    b5ccname = f'''{os.path.basename(b5).split('.')[0]}__CC.TIF'''
    b5cc.save(os.path.join(newfolderpath, b5ccname))

    return newfolderpath


# Execute code:
if __name__ == '__main__':
    lenstats = {}
    for path, folders, _ in os.walk(inputpath):
        for f in folders:
            if f.startswith('LC0') and len(f) > 20:
                # Try statement used to account for images that may not
                # process due to significant cloud cover
                try:
                    cloudcorrect(os.path.join(path, f), outputpath)
                except:
                    pass

    # Count the number of files in each of the processed folders and record
    # that number and the folder path in the "lenstats" dictionary
    for path, folders, _ in os.walk(outputpath):
        for f in folders:
            if f.startswith('LC0') and len(f) > 20:
                fpath = os.path.join(path, f)
                lenstats[fpath] = len(os.listdir(fpath))

    # The assumption being made here is that folders will process properly, thus
    # folders that do not have the same number of files as the majority of
    # folders will be deleted
    mode = statistics.mode(list(lenstats.values()))
    for fpath in lenstats:
        if lenstats[fpath] != mode:
            for fi in os.listdir(fpath):
                os.unlink(os.path.join(fpath, fi))
            os.rmdir(fpath)
            print(f'Deleted {os.path.basename(fpath)}')
            

        

                    
