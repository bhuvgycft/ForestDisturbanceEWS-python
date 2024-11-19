

import os
import arcpy
import statistics

# Define variables
basepath = r''
ffy = r'...\CloudCorrectedData\FirstFiveYears'
inpath = os.path.join(basepath, ffy)
outpath = os.path.join(basepath, ffy, '_stats')
samplePoints = os.path.join(
    basepath,
    r'...\P227R065_ForestTrainingPoints_utm21n')
datadic= {}


# Define functions
def convertdate(day, month, year):
    from datetime import datetime as dd
    fmt = '%Y.%m.%d'
    s = '.'.join([str(year), str(month), str(day)])
    dt = dd.strptime(s, fmt)
    return f'{dt.timetuple().tm_yday}_{year}'

# Input "filename" includes doy, year, vi type and ends with .txt
# Example of properly formatted "filename": 186_2018__NDVI.txt
def wtext(filename, dic):
    if len(dic):
        path = os.path.join(outpath, filename)
        dictext = 'dic = {'
        closedic = '}'
        valuetext = 'values = ['
        numkeys = [int(k) for k in list(dic.keys())]
        numkeys.sort()
        for sk in [str(k) for k in numkeys]:
            dictext += f'{sk}:{dic[sk]};'
            valuetext += f'{dic[sk]},'
        text = f'{dictext[:-1]}{closedic}\n\n{valuetext[:-1]}]'
        try:
            f = open(path, 'w')
            f.write(text)
        finally:
            f.close()
        return path
    else:
        return None

def sampleNDVI(doy, b4, b5):
    import os
    import arcpy
    from arcpy.sa import Float, Sample
    mem = 'memory'
    arcpy.env.workspace = mem
    ndvi_dic = {}
    tablepath = os.path.join(mem, f'_{doy}__NDVI')
    outtext = f'{os.path.basename(tablepath)[1:]}.txt'

    # If the statistics text file doesn't already exist, collect the statistics
    if not os.path.exists(os.path.join(outpath,outtext)):
        # Run NDVI
        floatb4 = Float(b4)
        floatb5 = Float(b5)
        ndvi = (floatb5 - floatb4) / (floatb5 + floatb4)

        # Sample NDVI
        arcpy.MakeFeatureLayer_management(
            samplePoints, f'forest__{doy}', 'Type = 1' # Type = Forest
            )
        Sample(ndvi, f'forest__{doy}', tablepath, 'NEAREST', 'OID')
        fields = [field.name for field in arcpy.ListFields(tablepath)]
        sfields = [fields[0], fields[-1]]
        with arcpy.da.SearchCursor(tablepath, sfields) as search:
            for s in search:
                # Checks to see if the sampled value is Null, likely due to
                # cloud correction; record the NDVI value if not Null
                if s[1] != None:
                    ndvi_dic[str(s[0])] = str(s[1])
        # Write Sample values from NDVI calculation to *.txt
        wtext(outtext, ndvi_dic)
        arcpy.Delete_management(f'forest__{doy}')
        return os.path.join(path, outtext)
    else:
        return

def collectStats(dic, dic_key):
    doy = dic[dic_key][1]
    b4 = os.path.join(dic_key, dic[dic_key][0]['B4'])
    b5 = os.path.join(dic_key, dic[dic_key][0]['B5'])
    sampleNDVI(doy, b4, b5)
    return dic_key


# Execute code
if __name__ == '__main__':
    # Populate "datadic" with the required information to run "collectStats"
    for path, folders, files in os.walk(inpath):
        for f in files:
            if f.endswith('_CC.TIF'):
                b = f.split('_')[8]
                if path not in datadic:
                    # Translate day of year
                    year = int(f.split('_')[3][:4])
                    month = int(f.split('_')[3][4:6])
                    day = int(f.split('_')[3][6:])
                    doy = convertdate(day, month, year)
                    # Add to 'dic'
                    datadic[path] = [{b: f}, f'{doy}']
                else:
                    datadic[path][0][b] = f

    for path in datadic:
        print(collectStats(datadic, path))
