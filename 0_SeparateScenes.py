import os

# "inpath" is the path to where the images were downloaded
inpath = r''
# "outpath" is where the data will be stored for the next process
outpath = r''


newfolders = set()

def convertorddate(day, month, year):
    from datetime import datetime as dd
    return int(f'{dd(year, month, day).toordinal()}')

# Extract scene names from file names in download directory
for path, _, files in os.walk(inpath):
    for f in files:
        fsplit = f.split('_')
        newfolders.add('_'.join(fsplit[:7]))

# Create scene folders in "outpath" directory
for nfold in newfolders:
    try:
        os.makedirs(os.path.join(outpath, nfold))
    except:
        pass

# Move scene files into newly created scene folders
for path, _, files in os.walk(inpath):
    for f in files:
        fsplit = f.split('_')
        if not fsplit[0] in path.split('\\'):
            os.rename(
                os.path.join(path, f),
                os.path.join(outpath, '_'.join(fsplit[:7]), f)
                )
            print('_'.join(fsplit[:7]))

# Separate scene folders based on period and platform
scenesdic = {'TrainingData': {}, 'EvaluationData': {}}
for folder in os.listdir(outpath):
    old = os.path.join(outpath, folder)
    platform = folder.split('_')[0]
    scenedate = folder.split('_')[3]
    sdyear = int(scenedate[:4])
    sdmon = int(scenedate[4:6])
    sdday = int(scenedate[6:])
    if convertorddate(sdday, sdmon, sdyear) <= 736880: # in training period
        new = os.path.join(outpath, 'TrainingData', platform, folder)
        if platform not in scenesdic['TrainingData']:
            scenesdic['TrainingData'][platform] = {}
        scenesdic['TrainingData'][platform][old] = new
    else: # if convertorddate <= 736880:
        new = os.path.join(outpath, 'EvaluationData', platform, folder)
        if platform not in scenesdic['EvaluationData']:
            scenesdic['EvaluationData'][platform] = {}
        scenesdic['EvaluationData'][platform][old] = new

            
for period in scenesdic:
    if period not in os.listdir(outpath):
        os.makedirs(os.path.join(outpath, period))
    for platform in scenesdic[period]:
        if platform not in os.listdir(os.path.join(outpath, period)):
            os.makedirs(os.path.join(outpath, period, platform))
        for path in scenesdic[period][platform]:
            os.rename(path, scenesdic[period][platform][path])
        
