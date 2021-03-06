# coding=utf-8
"""
InaSAFE Disaster risk assessment tool by AusAid - **Flood polygon evacuation.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

.. todo:: Check raster is single band

"""
__revision__ = '$Format:%H$'
__copyright__ = ('Copyright 2014, Australia Indonesia Facility for '
                 'Disaster Reduction')

import numpy

from safe.common.utilities import OrderedDict
from safe.defaults import (
    get_defaults,
    default_minimum_needs,
    default_provenance
)
from safe.impact_functions.core import (
    FunctionProvider,
    get_hazard_layer,
    get_exposure_layer,
    get_question,
    get_function_title,
    evacuated_population_needs,
    population_rounding
)
from safe.metadata import (
    hazard_all,
    layer_raster_numeric,
    exposure_population,
    unit_people_per_pixel,
    hazard_definition,
    exposure_definition,
    unit_categorised)
from safe.storage.raster import Raster
from safe.common.utilities import (
    format_int,
    humanize_class,
    create_classes,
    create_label,
    get_thousand_separator)
from safe.utilities.i18n import tr
from safe.common.tables import Table, TableRow
from safe.impact_functions.impact_function_metadata import (
    ImpactFunctionMetadata)
from safe.gui.tools.minimum_needs.needs_profile import add_needs_parameters


class CategoricalHazardPopulationImpactFunction(FunctionProvider):
    # noinspection PyUnresolvedReferences
    """Plugin for impact of population as derived by categorised hazard.

        :author ESSC
        :rating 3
        :param requires category=='hazard' and \
                        unit=='categorised' and \
                        layertype=='raster'

        :param requires category=='exposure' and \
                        subcategory=='population' and \
                        layertype=='raster'
        """

    class Metadata(ImpactFunctionMetadata):
        """Metadata for Categorised Hazard Population Impact Function.

        .. versionadded:: 2.1

        We only need to re-implement get_metadata(), all other behaviours
        are inherited from the abstract base class.
        """

        @staticmethod
        def get_metadata():
            """Return metadata as a dictionary.

            This is a static method. You can use it to get the metadata in
            dictionary format for an impact function.

            :returns: A dictionary representing all the metadata for the
                concrete impact function.
            :rtype: dict
            """
            dict_meta = {
                'id': 'CategoricalHazardPopulationImpactFunction',
                'name': tr('Categorical Hazard Population Impact Function'),
                'impact': tr('Be impacted by each category'),
                'author': 'Dianne Bencito',
                'date_implemented': 'N/A',
                'overview': tr(
                    'To assess the impacts of categorized hazards in raster '
                    'format on population raster layer.'),
                'categories': {
                    'hazard': {
                        'definition': hazard_definition,
                        'subcategories': hazard_all,
                        'units': [unit_categorised],
                        'layer_constraints': [layer_raster_numeric]
                    },
                    'exposure': {
                        'definition': exposure_definition,
                        'subcategories': [exposure_population],
                        'units': [unit_people_per_pixel],
                        'layer_constraints': [layer_raster_numeric]
                    }
                }
            }
            return dict_meta

    # Function documentation
    title = tr(
        'Be affected by each hazard category')
    synopsis = tr(
        'To assess the impacts of categorized hazards in raster '
        'format on population raster layer.')
    actions = tr(
        'Provide details about how many people would likely need '
        'to be impacted for each category.')
    hazard_input = tr(
        'A hazard raster layer where each cell represents '
        'the category of the hazard. There should be 3 '
        'categories: 1, 2, and 3.')
    exposure_input = tr(
        'An exposure raster layer where each cell represent '
        'population count.')
    output = tr(
        'Map of population exposed to high category and a table with '
        'number of people in each category')
    detailed_description = tr(
        'This function will calculate how many people will be impacted '
        'per each category for all categories in the hazard layer. '
        'Currently there should be 3 categories in the hazard layer. After '
        'that it will show the result and the total amount of people that '
        'will be impacted for the hazard given.')
    limitation = tr(
        'The number of categories is three.')

    # Configurable parameters
    defaults = get_defaults()
    parameters = OrderedDict([
        ('low_thresholds', 1.0),
        ('medium_thresholds', 2.0),
        ('high_thresholds', 3.0),
        ('postprocessors', OrderedDict([
            ('Gender', {'on': True}),
            ('Age', {
                'on': True,
                'params': OrderedDict([
                    ('youth_ratio', defaults['YOUTH_RATIO']),
                    ('adult_ratio', defaults['ADULT_RATIO']),
                    ('elderly_ratio', defaults['ELDERLY_RATIO'])])}),
            ('MinimumNeeds', {'on': True}),
        ])),
        ('minimum needs', default_minimum_needs()),
        ('provenance', default_provenance())
    ])
    parameters = add_needs_parameters(parameters)

    def run(self, layers):
        """Plugin for impact of population as derived by categorised hazard.

        Input
        :param layers: List of layers expected to contain

              * hazard_layer: Raster layer of categorised hazard
              * exposure_layer: Raster layer of population data

        Counts number of people exposed to each category of the hazard

        Return
          Map of population exposed to high category
          Table with number of people in each category
        """

        # The 3 category
        high_t = self.parameters['high_thresholds']
        medium_t = self.parameters['medium_thresholds']
        low_t = self.parameters['low_thresholds']

        # Identify hazard and exposure layers
        hazard_layer = get_hazard_layer(layers)    # Categorised Hazard
        exposure_layer = get_exposure_layer(layers)  # Population Raster

        question = get_question(
            hazard_layer.get_name(), exposure_layer.get_name(), self)

        # Extract data as numeric arrays
        data = hazard_layer.get_data(nan=0.0)  # Category

        # Calculate impact as population exposed to each category
        population = exposure_layer.get_data(nan=0.0, scaling=True)
        if high_t == 0:
            hi = numpy.where(0, population, 0)
        else:
            hi = numpy.where(data == high_t, population, 0)
        if medium_t == 0:
            med = numpy.where(0, population, 0)
        else:
            med = numpy.where(data == medium_t, population, 0)
        if low_t == 0:
            lo = numpy.where(0, population, 0)
        else:
            lo = numpy.where(data == low_t, population, 0)
        if high_t == 0:
            impact = numpy.where(
                (data == low_t) +
                (data == medium_t),
                population, 0)
        elif medium_t == 0:
            impact = numpy.where(
                (data == low_t) +
                (data == high_t),
                population, 0)
        elif low_t == 0:
            impact = numpy.where(
                (data == medium_t) +
                (data == high_t),
                population, 0)
        else:
            impact = numpy.where(
                (data == low_t) +
                (data == medium_t) +
                (data == high_t),
                population, 0)

        # Count totals
        total = int(numpy.sum(population))
        high = int(numpy.sum(hi))
        medium = int(numpy.sum(med))
        low = int(numpy.sum(lo))
        total_impact = int(numpy.sum(impact))

        # Perform population rounding based on number of people
        no_impact = population_rounding(total - total_impact)
        total = population_rounding(total)
        total_impact = population_rounding(total_impact)
        high = population_rounding(high)
        medium = population_rounding(medium)
        low = population_rounding(low)

        minimum_needs = [
            parameter.serialize() for parameter in
            self.parameters['minimum needs']
        ]

        # Generate impact report for the pdf map
        table_body = [question,
                      TableRow([tr(

                          'Total Population Affected '),
                          '%s' % format_int(total_impact)],
                          header=True),
                      TableRow([tr(
                          'Population in High risk areas '),
                          '%s' % format_int(high)]),
                      TableRow([tr(

                          'Population in Medium risk areas '),
                          '%s' % format_int(medium)]),
                      TableRow([tr(

                          'Population in Low risk areas '),
                          '%s' % format_int(low)]),
                      TableRow([tr(

                          'Population Not Affected'),
                          '%s' % format_int(no_impact)]),
                      TableRow(tr(

                          'Table below shows the minimum '
                          'needs for all evacuated people'))]

        total_needs = evacuated_population_needs(
            total_impact, minimum_needs)
        for frequency, needs in total_needs.items():
            table_body.append(TableRow(
                [
                    tr(

                        'Needs should be provided %s' % frequency),
                    tr(
                        'Total')
                ],
                header=True))
            for resource in needs:
                table_body.append(TableRow([
                    tr(

                        resource['table name']),
                    format_int(resource['amount'])]))

        impact_table = Table(table_body).toNewlineFreeString()

        table_body.append(
            TableRow(
                tr('Action Checklist:'), header=True))
        table_body.append(
            TableRow(
                tr('How will warnings be disseminated?')))
        table_body.append(
            TableRow(
                tr('How will we reach stranded people?')))
        table_body.append(
            TableRow(
                tr('Do we have enough relief items?')))
        table_body.append(
            TableRow(
                tr('If yes, where are they located and how will we '
                   'distribute them?')))
        table_body.append(
            TableRow(
                tr('If no, where can we obtain additional relief items from '
                   'and how will we transport them to here?')))

        # Extend impact report for on-screen display
        table_body.extend([
            TableRow(tr('Notes'), header=True),
            tr('Map shows the numbers of people in high, medium and low '
               'hazard areas'),
            tr('Total population: %s') % format_int(total)
        ])
        impact_summary = Table(table_body).toNewlineFreeString()

        # Create style
        colours = [
            '#FFFFFF', '#38A800', '#79C900', '#CEED00',
            '#FFCC00', '#FF6600', '#FF0000', '#7A0000']
        classes = create_classes(impact.flat[:], len(colours))
        interval_classes = humanize_class(classes)
        style_classes = []

        for i in xrange(len(colours)):
            style_class = dict()
            if i == 1:
                label = create_label(interval_classes[i], 'Low')
            elif i == 4:
                label = create_label(interval_classes[i], 'Medium')
            elif i == 7:
                label = create_label(interval_classes[i], 'High')
            else:
                label = create_label(interval_classes[i])
            style_class['label'] = label
            style_class['quantity'] = classes[i]
            if i == 0:
                transparency = 30
            else:
                transparency = 30
            style_class['transparency'] = transparency
            style_class['colour'] = colours[i]
            style_classes.append(style_class)

        style_info = dict(
            target_field=None,
            style_classes=style_classes,
            style_type='rasterStyle')

        # For printing map purpose
        map_title = tr(

            'Population affected by each category')
        legend_notes = tr(

            'Thousand separator is represented by %s' %
            get_thousand_separator())
        legend_units = tr('(people per cell)')
        legend_title = tr('Number of People')

        # Create raster object and return
        raster_layer = Raster(
            impact,
            projection=hazard_layer.get_projection(),
            geotransform=hazard_layer.get_geotransform(),
            name=tr('Population which %s') % (
                get_function_title(self).lower()),
            keywords={
                'impact_summary': impact_summary,
                'impact_table': impact_table,
                'map_title': map_title,
                'legend_notes': legend_notes,
                'legend_units': legend_units,
                'legend_title': legend_title,
                'total_needs': total_needs},
            style_info=style_info)
        return raster_layer
