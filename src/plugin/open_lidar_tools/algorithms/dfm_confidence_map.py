# -*- coding: utf-8 -*-

"""
/***************************************************************************
 OpenLidarTools
                                 A QGIS plugin
 Open Lidar Tools
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-03-10
        copyright            : (C) 2021 by Benjamin Štular, Edisa Lozić, Stefan Eichert
        email                : stefaneichert@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Benjamin Štular, Edisa Lozić, Stefan Eichert'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by Benjamin Štular, Edisa Lozić, Stefan Eichert'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import inspect
import os
import pathlib
from qgis.PyQt.QtGui import QIcon
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
from qgis.core import QgsProcessingParameterEnum
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
            QgsProcessingParameterRasterLayer('Groundlayer', 'Ground Point Density Layer', defaultValue=None))
        self.addParameter(
            QgsProcessingParameterRasterLayer('LowVegetation', 'Low Vegetation Density Layer', defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum('Createconfidencemapfor', 'Resolution',
                                                     options=['0.25m', '0.5m', '1m', '2m'], allowMultiple=True,
                                                     defaultValue=[0,1,2,3]))
        self.addParameter(
            QgsProcessingParameterNumber('SetCellSize', 'Output Cell Size:', type=QgsProcessingParameterNumber.Double,
                                         minValue=0, maxValue=1.79769e+308, defaultValue=0.5))


    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        confidenceParams = (parameters['Createconfidencemapfor'])
        steps = len(confidenceParams) * 19 + 8
        feedback = QgsProcessingMultiStepFeedback(steps, model_feedback)
        results = {}
        outputs = {}



        # reclass tables
        half_meter = {
            'denshi': [0, 4, 0, 4.000000001, 100000, 1],
            'densmid': [0, 2, 0, 2.000001, 4, 1, 4.000001, 100000, 0],
            'denslow': [0, 1, 0, 1.00000001, 2, 1, 2.00000001, 100000, 0],
            'densvlow': [0, 1, 1, 1.00000001, 100000, 0],
            'veghigh': [0, 4, 0, 4.00000001, 100000, 1],
            'veglow': [0, 4, 1, 4.00000001, 100000, 0]
        }
        quarter_meter = {
            'denshi': [0, 16, 0, 16.000000001, 100000, 1],
            'densmid': [0, 8, 0, 8.000001, 16, 1, 16.000001, 100000, 0],
            'denslow': [0, 4, 0, 4.00000001, 8, 1, 8.00000001, 100000, 0],
            'densvlow': [0, 4, 1, 4.00000001, 100000, 0],
            'veghigh': [0, 16, 0, 16.00000001, 100000, 1],
            'veglow': [0, 16, 1, 16.00000001, 100000, 0]
        }
        one_meter = {
            'denshi': [0, 1, 0, 1.000000001, 100000, 1],
            'densmid': [0, 0.5, 0, 0.5000001, 1, 1, 1.000001, 100000, 0],
            'denslow': [0, 0.25, 0, 0.25000001, 0.5, 1, 0.50000001, 100000, 0],
            'densvlow': [0, 0.25, 1, 0.25000001, 100000, 0],
            'veghigh': [0, 1, 0, 1.00000001, 100000, 1],
            'veglow': [0, 1, 1, 1.00000001, 100000, 0]
        }
        two_meter = {
            'denshi': [0, 0.25, 0, 0.250000001, 100000, 1],
            'densmid': [0, 0.125, 0, 0.1250001, 0.25, 1, 0.2500001, 100000, 0],
            'denslow': [0, 0.0625, 0, 0.06250001, 0.125, 1, 0.12500001, 100000, 0],
            'densvlow': [0, 0.0625, 1, 0.06250001, 100000, 0],
            'veghigh': [0, 0.25, 0, 0.25000001, 100000, 1],
            'veglow': [0, 0.25, 1, 0.25000001, 100000, 0]
        }

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

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        iter = 4

        for row in confidenceParams:
            if row == 0:
                intermed_params = quarter_meter
                appendix = ' 0.25m'
            if row == 1:
                intermed_params = half_meter
                appendix = ' 0.5m'
            if row == 2:
                intermed_params = one_meter
                appendix = ' 1m'
            if row == 3:
                intermed_params = two_meter
                appendix = ' 2m'

            # Density Hi
            alg_params = {
                'DATA_TYPE': 3,
                'INPUT_RASTER': outputs['Resamplegpd']['output'],
                'NODATA_FOR_MISSING': True,
                'NO_DATA': -9999,
                'RANGE_BOUNDARIES': 2,
                'RASTER_BAND': 1,
                'TABLE': intermed_params['denshi'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DensityHi' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                             feedback=feedback, is_child_algorithm=True)
            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'TABLE': intermed_params['densmid'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DensityMid' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                   feedback=feedback, is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'TABLE': intermed_params['denslow'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DensityLow' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                   feedback=feedback, is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'TABLE': intermed_params['densvlow'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DensityVlow' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                    feedback=feedback, is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'TABLE': intermed_params['veglow'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Veglow' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context,
                                               feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'TABLE': intermed_params['veghigh'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Veghi' + appendix] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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

        iter = iter + 1
        feedback.setCurrentStep(iter)
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

        iter = iter + 1
        feedback.setCurrentStep(iter)
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

        iter = iter + 1
        feedback.setCurrentStep(iter)
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
        outputs['Slope42'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                            feedback=feedback,
                                            is_child_algorithm=True)

        iter = iter + 1
        feedback.setCurrentStep(iter)
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
        outputs['Slope90'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                            feedback=feedback,
                                            is_child_algorithm=True)

        iter = iter + 1
        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}


        for row in confidenceParams:
            if row == 0:
                appendix = ' 0.25m'
            if row == 1:
                appendix = ' 0.5m'
            if row == 2:
                appendix = ' 1m'
            if row == 3:
                appendix = ' 2m'

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
                'INPUT_A': outputs['DensityMid' + appendix]['OUTPUT'],
                'INPUT_B': outputs['DensityLow' + appendix]['OUTPUT'],
                'INPUT_C': outputs['DensityVlow' + appendix]['OUTPUT'],
                'INPUT_D': outputs['Slope90']['OUTPUT'],
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc1a' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityVlow' + appendix]['OUTPUT'],
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
            outputs['Calc1b' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityMid' + appendix]['OUTPUT'],
                'INPUT_B': outputs['DensityLow' + appendix]['OUTPUT'],
                'INPUT_C': outputs['DensityVlow' + appendix]['OUTPUT'],
                'INPUT_D': outputs['Slope42']['OUTPUT'],
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc2' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityLow' + appendix]['OUTPUT'],
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
            outputs['Calc3' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityHi' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Slope22']['OUTPUT'],
                'INPUT_C': outputs['Slope42']['OUTPUT'],
                'INPUT_D': outputs['Slope90']['OUTPUT'],
                'INPUT_E': outputs['Veghi' + appendix]['OUTPUT'],
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc4a' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityMid' + appendix]['OUTPUT'],
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
            outputs['Calc4b' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityHi' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Slope12']['OUTPUT'],
                'INPUT_C': outputs['Veghi' + appendix]['OUTPUT'],
                'INPUT_D': None,
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc5a' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityHi' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Slope22']['OUTPUT'],
                'INPUT_C': outputs['Slope42']['OUTPUT'],
                'INPUT_D': outputs['Slope90']['OUTPUT'],
                'INPUT_E': outputs['Veglow' + appendix]['OUTPUT'],
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc5b' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['DensityHi' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Slope12']['OUTPUT'],
                'INPUT_C': outputs['Veglow' + appendix]['OUTPUT'],
                'INPUT_D': None,
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calc6' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                              is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['Calc6' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Calc5a' + appendix]['OUTPUT'],
                'INPUT_C': outputs['Calc5b' + appendix]['OUTPUT'],
                'INPUT_D': outputs['Calc4a' + appendix]['OUTPUT'],
                'INPUT_E': outputs['Calc4b' + appendix]['OUTPUT'],
                'INPUT_F': outputs['Calc3' + appendix]['OUTPUT'],
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calccran1' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback,
                                                  is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                'INPUT_A': outputs['Calccran1' + appendix]['OUTPUT'],
                'INPUT_B': outputs['Calc2' + appendix]['OUTPUT'],
                'INPUT_C': outputs['Calc1a' + appendix]['OUTPUT'],
                'INPUT_D': outputs['Calc1b' + appendix]['OUTPUT'],
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 4,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Calccranfinal' + appendix] = processing.run('gdal:rastercalculator', alg_params, context=context,
                                                      feedback=feedback, is_child_algorithm=True)
            results['ConfidenceMap' + appendix] = outputs['Calccranfinal' + appendix]['OUTPUT']

            iter = iter + 1
            feedback.setCurrentStep(iter)
            if feedback.isCanceled():
                return {}

            # Load result
            alg_params = {
                'INPUT': outputs['Calccranfinal' + appendix]['OUTPUT'],
                'NAME': 'DFM confidence map' + appendix
            }
            outputs['LoadResult'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback,
                                                   is_child_algorithm=True)

            iter = iter + 1
            feedback.setCurrentStep(iter)
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
                outputs['SetStyleForRasterLayer'] = processing.run('qgis:setstyleforrasterlayer', alg_params,
                                                                   context=context,
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

    def icon(self):
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.join(cmd_folder, 'confidencemap.png')))
        return icon

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
        return """<html><body>
    <p>This algorithm calculates a DFM Confidence Map based on the CRAN decision tree. The confidence map is primarily used for the quality assessment of the DFM, but can also be used to determine the optimal resolution for the DFM.
    Digital Feature Model (DFM) is archaeology- specific DEM interpolated from airborne LiDAR data. This algorithm calculates DFM Confidence Map based on the CRAN decision tree. The confidence map is primarily used for the quality assessment of the DFM, but can also be used to determine the optimal resolution for the DFM.
    This algorithm can also be used to calculate the prediction uncertainty map for any DEM, but the settings must be adjusted for cell size.</p>
    <h2>Input</h2>
    <h3>DEM/DFM Layer</h3>
    <p>DFM (or any DEM) with cell size 0.5m in raster format</p>
    <h3>Low Vegetation Density Layer</h3>
    <p>Point density layer of low vegetation (ASPRS standard LIDAR point class 3, height 0.5-2.0 m) in raster format. Recommended cell size is 0.5 or 1.0 m. (Whitebox Tools / LidarPointDensity can be used to calculate this layer from a LAS file).</p>
    <h3>Ground Point Density Layer</h3>
    <p>Point density layer of ground (ASPRS class 2) and building (ASPRS class 6) points in raster format. Recommended cell size is 0.5 or 1.0 m. (Whitebox Tools / LidarPointDensity can be used to calculate this layer from a LAS file).</p>
    <h2>Parameters</2>
    <h3>Resolution</h3>
    <p>DFM/DEM Resolution (multiple choice)</p>
    <h3>Output Cell Size:</h3>
    <p>Define the cell size of the Confidence Map. 0.5 or 1 m is recommended. (It is possible to calculate DFM Confidence Map for high resolution, e.g. 0.25 m, but display the result at lower resolution, e.g. 1 m.)</p>
    <h2>Troubleshooting</h2>
    <h3>I have NoData holes in my DFM/DEM</h3>
    <p>Wherever one of the inputs has a NoData value, the algorithm will return NoData. Common sources for NoData are too low radius setting for IDW.</p>
    <p></p>
    <br>
    <p><b>Literature:</b> Štular, Lozić, Eichert 2021a (in press).</p>
    <br><a href="https://github.com/stefaneichert/OpenLidarTools">Website</a>
    <br><p align="right">Algorithm author: Benjamin Štular, Edisa Lozić, Stefan Eichert </p><p align="right">Help author: Benjamin Štular, Edisa Lozić, Stefan Eichert</p></body></html>"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return dfmConfidenceMap()
