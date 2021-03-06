__author__ = 'Akbar Gumbira (akbargumbira@gmail.com)'
__revision__ = '$Format:%H$'
__date__ = '11/12/14'
__copyright__ = ('Copyright 2014, Australia Indonesia Facility for '
                 'Disaster Reduction')

import unittest

from safe.impact_functions.utilities import (
    keywords_to_str,
    add_to_list)


class TestUtilities(unittest.TestCase):
    def test_keywords_to_str(self):
        """String representation of keywords works."""

        keywords = {
            'category': 'hazard', 'subcategory': 'tsunami', 'unit': 'm'}
        string_keywords = keywords_to_str(keywords)
        for key in keywords:
            message = (
                'Expected key %s to appear in %s' % (key, string_keywords))
            assert key in string_keywords, message

            val = keywords[key]
            message = (
                'Expected value %s to appear in %s' % (val, string_keywords))
            assert val in string_keywords, message

    def test_add_to_list(self):
        """Test for add_to_list function
        """
        list_original = ['a', 'b', ['a'], {'a': 'b'}]
        list_a = ['a', 'b', ['a'], {'a': 'b'}]
        # add same immutable element
        list_b = add_to_list(list_a, 'b')
        assert list_b == list_original
        # add list
        list_b = add_to_list(list_a, ['a'])
        assert list_b == list_original
        # add same mutable element
        list_b = add_to_list(list_a, {'a': 'b'})
        assert list_b == list_original
        # add new mutable element
        list_b = add_to_list(list_a, 'c')
        assert len(list_b) == (len(list_original) + 1)
        assert list_b[-1] == 'c'


if __name__ == '__main__':
    unittest.main()
