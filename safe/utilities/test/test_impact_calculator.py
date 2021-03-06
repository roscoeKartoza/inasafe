# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -
**Impact calculator test suite.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'tim@kartoza.com'
__date__ = '10/01/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import os
import unittest

from safe.utilities.impact_calculator import ImpactCalculator
from safe.common.exceptions import InsufficientParametersError
from safe.test.utilities import HAZDATA, EXPDATA, TESTDATA
from safe.storage.core import read_layer as read_safe_layer


class ImpactCalculatorTest(unittest.TestCase):
    """Test the InaSAFE plugin stub"""

    def setUp(self):
        """Create shared resources that all tests can use"""
        self.calculator = ImpactCalculator()
        self.vector_path = os.path.join(TESTDATA, 'Padang_WGS84.shp')
        self.vector_layer = read_safe_layer(self.vector_path)
        self.raster_shake_path = os.path.join(
            HAZDATA, 'Shakemap_Padang_2009.asc')
        self.raster_shake = read_safe_layer(self.raster_shake_path)
        # UTM projected layer

        fn = 'tsunami_max_inundation_depth_BB_utm.asc'
        self.raster_tsunami_path = os.path.join(TESTDATA, fn)
        self.raster_exposure_path = os.path.join(
            TESTDATA, 'tsunami_building_exposure.shp')

        self.raster_population_path = os.path.join(EXPDATA, 'glp10ag.asc')
        self.calculator.set_hazard_layer(self.raster_shake)
        self.calculator.set_exposure_layer(self.vector_layer)
        self.calculator.set_function('Earthquake Building Impact Function')

    def tearDown(self):
        """Tear down - destroy the QGIS app"""
        pass

    def test_properties(self):
        """Test if the properties work as expected."""

        message = 'Vector property incorrect.'
        assert (self.calculator.exposure_layer() ==
                self.vector_layer), message

        message = 'Raster property incorrect.'
        assert (self.calculator.hazard_layer() ==
                self.raster_shake), message

        message = 'Function property incorrect.'
        assert (self.calculator.function() ==
                'Earthquake Building Impact Function'), message

    def test_run(self):
        """Test that run works as expected in non threading mode"""
        try:
            test_runner = self.calculator.get_runner()
            # run non threaded
            test_runner.run()
            message = test_runner.result()
            impact_layer = test_runner.impact_layer()
            file_name = impact_layer.get_filename()
            assert(file_name and not file_name == '')
            assert(message and not message == '')
        except Exception, e:  # pylint: disable=W0703
            message = 'Calculator run failed. %s' % str(e)
            assert(), message

    def test_thread(self):
        """Test that starting it in a thread works as expected."""
        try:
            function_runner = self.calculator.get_runner()
            function_runner.start()
            # wait until the thread is done
            function_runner.join()
            message = function_runner.result()
            impact_layer = function_runner.impact_layer()
            file_name = impact_layer.get_filename()
            assert(file_name and not file_name == '')
            assert(message and not message == '')
        except Exception, e:  # pylint: disable=W0703
            message = 'Calculator run failed:\n' + str(e)
            assert(), message

    def test_start_with_no_parameters(self):
        """Test that run raises an error properly when no parameters defined.
        """
        # noinspection PyBroadException
        try:
            self.calculator.set_exposure_layer(None)
            self.calculator.set_hazard_layer(None)
            # Next line should raise an error
            function_runner = self.calculator.get_runner()
            function_runner.start()
        except RuntimeError, e:
            message = 'Runtime error encountered: %s' % str(e)
            assert(), message
        except InsufficientParametersError:
            return  # expected outcome
        except:
            message = 'Missing parameters not raised as error.'
            assert(), message
        message = 'Expected an error, none encountered.'
        assert(), message

    def test_issue100(self):
        """Test for issue 100: unhashable type dict"""
        exposure_path = os.path.join(
            TESTDATA, 'OSM_building_polygons_20110905.shp')
        hazard_path = os.path.join(
            HAZDATA, 'Flood_Current_Depth_Jakarta_geographic.asc')
        # Verify relevant metada is ok
        h = read_safe_layer(hazard_path)
        e = read_safe_layer(exposure_path)
        self.calculator.set_hazard_layer(h)
        self.calculator.set_exposure_layer(e)
        self.calculator.set_function('Flood Building Impact Function')
        try:
            function_runner = self.calculator.get_runner()
            # Run non threaded
            function_runner.run()
            message = function_runner.result()
            impact_layer = function_runner.impact_layer()
            file_name = impact_layer.get_filename()
            assert(file_name and not file_name == '')
            assert(message and not message == '')
        except Exception, e:  # pylint: disable=W0703
            message = 'Calculator run failed. %s' % str(e)
            assert(), message

    def test_need_clip(self):
        """Test if need_clip method work as expected."""
        # 'Old-style' impact function

        message = 'True expected, but False returned'
        assert self.calculator.requires_clipping(), message

        self.calculator.set_function(
            'Flood Vector Roads Experimental Function')
        message = 'False expected, but True returned'
        assert not self.calculator.requires_clipping(), message

if __name__ == '__main__':
    suite = unittest.makeSuite(ImpactCalculatorTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
