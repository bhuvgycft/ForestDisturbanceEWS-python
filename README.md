Download and review the logic used to identify forest disturbance and regeneration.
The process sought to use all available Landsat images regardless of cloud cover.
File 0_SeparateScenes.py separates the downloaded Landsat images.
File 1_DefineTrainingArea.py finds the overlapping area of all source images.
File 2_CloudCorrect.py removes clouds from the downloaded images.
File 3_NDVI_CollectStats.py collects statistics from the training data.
File 4_NDVI_Generate_ForestMask_and_Analyze_w_Regen.py analyzes images in the
  evaluation period for forest disturbance and regeneration.
