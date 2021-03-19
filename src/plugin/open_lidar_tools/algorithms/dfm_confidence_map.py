# -*- coding: utf-8 -*-

"""
/***************************************************************************
 OpenLidarTools
                                 A QGIS plugin
 Open Lidar Tools for Archaeology
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-03-10
        copyright            : (C) 2021 by Benjamin Štular, Ediza Lozić, Stefan Eichert
        email                : stefaneichert@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Benjamin Štular, Ediza Lozić, Stefan Eichert'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by Benjamin Štular, Ediza Lozić, Stefan Eichert'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import inspect
import os
import pathlib

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterBoolean
import processing
from os.path import exists


class dfmConfidenceMap(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('DEMDFM', 'DEM/DFM Layer', defaultValue=None))
        self.addParameter(
            QgsProcessingParameterRasterLayer('LowVegetation', 'Low Vegetation Density Layer', defaultValue=None))
        self.addParameter(
            QgsProcessingParameterRasterLayer('Groundlayer', 'Ground Point Density Layer', defaultValue=None))
        self.addParameter(
            QgsProcessingParameterNumber('SetCellSize', 'Cell Size:', type=QgsProcessingParameterNumber.Double,
                                         minValue=0, maxValue=1.79769e+308, defaultValue=0.5))
        self.addParameter(
            QgsProcessingParameterRasterDestination('ConfidenceMap', 'Confidence Map', createByDefault=True,
                                                    defaultValue=None))
        self.addParameter(
            QgsProcessingParameterBoolean('VERBOSE_LOG', 'Verbose logging', optional=True, defaultValue=False))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(27, model_feedback)
        results = {}
        outputs = {}

        # resampleVEG
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['SetCellSize'],
            'GRASS_REGION_PARAMETER': parameters['DEMDFM'],
            'input': parameters['LowVegetation'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Resampleveg'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Conditional branch
        alg_params = {
        }
        outputs['ConditionalBranch'] = processing.run('native:condition', alg_params, context=context,
                                                      feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # resampleGPD
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['SetCellSize'],
            'GRASS_REGION_PARAMETER': parameters['DEMDFM'],
            'input': parameters['Groundlayer'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Resamplegpd'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Density Hi
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resamplegpd']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 4, 0, 4.000000001, 100000, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DensityHi'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                              feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # resampleDEM
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['SetCellSize'],
            'GRASS_REGION_PARAMETER': parameters['DEMDFM'],
            'input': parameters['DEMDFM'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Resampledem'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Density Mid
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resamplegpd']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 2, 0, 2.000001, 4, 1, 4.000001, 100000, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DensityMid'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                               feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Density Low
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resamplegpd']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [0, 1, 0, 1.00000001, 2, 1, 2.00000001, 100000, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DensityLow'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                               feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Density Vlow
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resamplegpd']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [0, 1, 1, 1.00000001, 100000, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DensityVlow'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Slope Qgis
        alg_params = {
            'INPUT': outputs['Resampledem']['output'],
            'Z_FACTOR': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SlopeQgis'] = processing.run('native:slope', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Slope 12
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['SlopeQgis']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 12.5, 1, 12.5000001, 90, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope12'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Slope 22
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['SlopeQgis']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 12.5, 0, 12.500000001, 22.5, 1, 22.500000001, 90, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope22'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calc 4b
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*(B+C)*4',
            'INPUT_A': outputs['DensityMid']['OUTPUT'],
            'INPUT_B': outputs['Slope12']['OUTPUT'],
            'INPUT_C': outputs['Slope22']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc4b'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Calc 1b
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*(B+C)',
            'INPUT_A': outputs['DensityVlow']['OUTPUT'],
            'INPUT_B': outputs['Slope12']['OUTPUT'],
            'INPUT_C': outputs['Slope22']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc1b'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Calc 3
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*(B+C)*3',
            'INPUT_A': outputs['DensityLow']['OUTPUT'],
            'INPUT_B': outputs['Slope12']['OUTPUT'],
            'INPUT_C': outputs['Slope22']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc3'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                          is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Slope 42
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['SlopeQgis']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 22.5, 0, 22.50000001, 42.5, 1, 42.50000001, 90, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope42'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Slope 90
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['SlopeQgis']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 42.5, 0, 42.50000001, 90, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope90'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Calc 1a
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': '(A+B+C)*D',
            'INPUT_A': outputs['DensityMid']['OUTPUT'],
            'INPUT_B': outputs['DensityLow']['OUTPUT'],
            'INPUT_C': outputs['DensityVlow']['OUTPUT'],
            'INPUT_D': outputs['Slope90']['OUTPUT'],
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc1a'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Calc 2
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': '(A+B+C)*D*2',
            'INPUT_A': outputs['DensityMid']['OUTPUT'],
            'INPUT_B': outputs['DensityLow']['OUTPUT'],
            'INPUT_C': outputs['DensityVlow']['OUTPUT'],
            'INPUT_D': outputs['Slope42']['OUTPUT'],
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc2'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                          is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # VegLow
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resampleveg']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 4, 1, 4.00000001, 100000, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Veglow'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Calc 5b
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': 1,
            'BAND_E': 1,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*(B+C+D)*E*5',
            'INPUT_A': outputs['DensityHi']['OUTPUT'],
            'INPUT_B': outputs['Slope22']['OUTPUT'],
            'INPUT_C': outputs['Slope42']['OUTPUT'],
            'INPUT_D': outputs['Slope90']['OUTPUT'],
            'INPUT_E': outputs['Veglow']['OUTPUT'],
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc5b'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Calc 6
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*B*C*6',
            'INPUT_A': outputs['DensityHi']['OUTPUT'],
            'INPUT_B': outputs['Slope12']['OUTPUT'],
            'INPUT_C': outputs['Veglow']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc6'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                          is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # VegHi
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Resampleveg']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [0, 4, 0, 4.00000001, 100000, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Veghi'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                          is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Calc 4a
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': 1,
            'BAND_E': 1,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*(B+C+D)*E*4',
            'INPUT_A': outputs['DensityHi']['OUTPUT'],
            'INPUT_B': outputs['Slope22']['OUTPUT'],
            'INPUT_C': outputs['Slope42']['OUTPUT'],
            'INPUT_D': outputs['Slope90']['OUTPUT'],
            'INPUT_E': outputs['Veghi']['OUTPUT'],
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc4a'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Calc 5a
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A*B*C*5',
            'INPUT_A': outputs['DensityHi']['OUTPUT'],
            'INPUT_B': outputs['Slope12']['OUTPUT'],
            'INPUT_C': outputs['Veghi']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calc5a'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # CalcCran1
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': 1,
            'BAND_E': 1,
            'BAND_F': 1,
            'EXTRA': '',
            'FORMULA': 'A+B+C+D+E+F',
            'INPUT_A': outputs['Calc6']['OUTPUT'],
            'INPUT_B': outputs['Calc5a']['OUTPUT'],
            'INPUT_C': outputs['Calc5b']['OUTPUT'],
            'INPUT_D': outputs['Calc4a']['OUTPUT'],
            'INPUT_E': outputs['Calc4b']['OUTPUT'],
            'INPUT_F': outputs['Calc3']['OUTPUT'],
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Calccran1'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # CalcCranFinal
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': 1,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A+B+C+D',
            'INPUT_A': outputs['Calccran1']['OUTPUT'],
            'INPUT_B': outputs['Calc2']['OUTPUT'],
            'INPUT_C': outputs['Calc1a']['OUTPUT'],
            'INPUT_D': outputs['Calc1b']['OUTPUT'],
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': parameters['ConfidenceMap']
        }
        outputs['Calccranfinal'] = processing.run('gdal:rastercalculator', alg_params, context=context,
                                                  feedback=feedback, is_child_algorithm=True)
        results['ConfidenceMap'] = outputs['Calccranfinal']['OUTPUT']

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Load result
        alg_params = {
            'INPUT': outputs['Calccranfinal']['OUTPUT'],
            'NAME': 'DFM confidence map'
        }
        outputs['LoadResult'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Set style for raster layer
        # Set style for raster layer
        folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        styleFile = os.path.join(os.path.join(folder, 'DFMconfidenceMap.qml'))

        alg_params = {
            'INPUT': outputs['LoadResult']['OUTPUT'],
            'STYLE': styleFile
        }
        if exists(styleFile) == True:
                outputs['SetStyleForRasterLayer'] = processing.run('qgis:setstyleforrasterlayer', alg_params, context=context,
                                                           feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'DFM Confidence Map'

    def displayName(self):
        return 'DFM Confidence Map'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Analysis'

    def shortHelpString(self):
        return """<html><body><h2>Algorithm description</h2>
    <p>Calculates Confidence map for 0.5 m DFM.

    Digital Feature Model (DFM) is archaeology- specific DEM interpolated from airborne LiDAR data. This algorithm calculates DFM Confidence Map based on the CRAN decision tree. The confidence map is primarily used for the quality assessment of the DFM, but can also be used to determine the optimal resolution for the DFM.
    This algorithm can also be used to calculate the prediction uncertainty map for any DEM, but the settings must be adjusted for cell size.
    For more information, see Štular, Lozić, Eichert 2021 (in press).</p>
    <h2>Input parameters</h2>
    <h3>DEM/DFM Layer</h3>
    <p>DFM (or any DEM) with cell size 0.5m in raster format</p>
    <h3>Low Vegetation Density Layer</h3>
    <p>Point density layer of low vegetation (ASPRS standard LIDAR point class 3, height 0.5-2.0 m) in raster format. Recommended cell size is 0.5 or 1.0 m. (Whitebox Tools / LidarPointDensity can be used to calculate this layer from a LAS file).</p>
    <h3>Ground Point Density Layer</h3>
    <p>Point density layer of ground (ASPRS class 2) and building (ASPRS class 6) points in raster format. Recommended cell size is 0.5 or 1.0 m. (Whitebox Tools / LidarPointDensity can be used to calculate this layer from a LAS file).</p>
    <h3>Cell Size:</h3>
    <p>Define the cell size of the Confidence Map. 0.5 or 1 m is recommended.</p>

    <p></p>
    <br><p align="right">Algorithm author: Benjamin Štular, Ediza Lozić, Stefan Eichert </p><p align="right">Help author: Benjamin Štular, Ediza Lozić, Stefan Eichert</p></body></html>"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return dfmConfidenceMap()