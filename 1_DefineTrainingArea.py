import os
from time import strftime as t

# Paths to walk through and find images
ffy = r'...\Data\FullProjectDownloads'

# Define output variables
out_gdb = r'...\RandomPoints\ControlDatabase.gdb'
training_points = 'ffy_P227R065_TrainingPoints_1000pts_300m_min_utm21n'
training_poly = 'ffy_P227065_TrainingPolygon_utm21n'



# Define functions

# Generate Common Area
def gca(path_list):
    import os
    import arcpy
    from arcpy.sa import Raster, IsNull, SetNull
    mem = 'memory'
    arcpy.env.workspace = mem
    dic = {}
    count = 0

    # Walk through "path_list"
    for p in path_list:
        for path, _, files in os.walk(p):
            for f in files:
                if f.endswith('_B4.TIF'):
                    dic[str(count)] = Raster(os.path.join(path, f))
                    count += 1
    keys = list(dic.keys())
    keys.sort()
    # Add processed rasters together
    for key in keys:
        if key == '0':
            ras = dic[key]
        else:
            ras += dic[key]

    # Change all values to zero
    ras_in = IsNull(ras)
    ras_zero = SetNull(ras_in, 0, 'Value = 1')

    return ras_zero

# Generate Polygon Area
def gpa(in_raster, out_poly):
    import os
    import arcpy
    mem = 'memory'
    arcpy.env.workspace = mem
    # Define temp feature class
    tr2p = os.path.join(mem, 'tr2p')

    # Convert to polygon
    arcpy.conversion.RasterToPolygon(in_raster, tr2p, 'SIMPLIFY', 'VALUE')
    # Negative 300m buffer
    arcpy.analysis.Buffer(tr2p, out_poly, '-300 Meters', dissolve_option='ALL')
    # Delete intermediate data
    arcpy.management.Delete(tr2p)

    return out_poly

# Generate Training Points
def gtp(in_poly, out_points):
    import os
    import arcpy

    # Create 1000 random points at least 300 meters apart and within the
    # bounds of "in_poly"
    arcpy.management.CreateRandomPoints(
        os.path.dirname(out_points),
        os.path.basename(out_points),
        constraining_feature_class=in_poly,
        number_of_points_or_field=1000,
        minimum_allowed_distance='300 Meters'
        )
    # Add "Type" field and apply 'Domain' domain
    arcpy.management.AddField(
        out_points,
        'Type',
        'SHORT',
        field_domain='Domain'
        )
    
    return out_points

if __name__ == '__main__':
    print(f'Starting "gca":\t{t("%X")}')
    common_area = gca([ffy])
    print(f'Starting "gpa":\t{t("%X")}')
    gpa(common_area, os.path.join(out_gdb, training_poly))
    print(f'Starting "gtp":\t{t("%X")}')
    gtp(os.path.join(out_gdb, training_poly),
        os.path.join(out_gdb, training_points))
    print(f'Complete:\t{t("%X")}')
    



