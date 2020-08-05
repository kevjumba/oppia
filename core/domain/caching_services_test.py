# coding: utf-8
#
# Copyright 2018 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for methods in core.domain.caching_services"""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

from core.domain import caching_services
from core.domain import exp_domain
from core.tests import test_utils

import python_utils


class CachingServicesUnitTests(test_utils.GenericTestBase):
    """Tests for caching_services."""

    def test_retrieved_memory_profile_contains_correct_elements(self):
        memory_profile = caching_services.get_memory_stats()
        self.assertIsInstance(memory_profile, dict)
        self.assertTrue('total_allocated_in_bytes' in memory_profile)
        self.assertTrue('peak_memory_usage_in_bytes' in memory_profile)
        self.assertTrue('total_number_of_keys_stored' in memory_profile)

    def test_flush_cache_wipes_cache_clean(self):
        """Tests whether flushing the cache removes the elements in the
        cache.
        """
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}
        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)
        exploration_id = 'id'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            {
                exploration_id: default_exploration
            })

        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                ['a', 'b', 'c']), key_value_mapping)

        retrieved_exploration = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            [exploration_id]).get(exploration_id)
        self.assertEqual(
            retrieved_exploration.to_dict(),
            default_exploration.to_dict())

        caching_services.flush_memory_cache()
        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                ['a', 'b', 'c']), {})
        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_EXPLORATION,
                python_utils.convert_to_bytes(0),
                [exploration_id]),
            {})

    def test_serialization_and_deserialization_returns_the_same_object(self):
        deserialize = (
            caching_services.DESERIALIZATION_FUNCTIONS['exploration'])
        serialize = (
            caching_services.SERIALIZATION_FUNCTIONS['exploration']
        )
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        self.assertEqual(
            default_exploration.to_dict(),
            deserialize(serialize(default_exploration)).to_dict())

    def test_invalid_namespace_raises_error(self):
        invalid_namespace = 'invalid'
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        with self.assertRaisesRegexp(
            ValueError,
            'Invalid namespace: %s.' % invalid_namespace):
            caching_services.set_multi(
                invalid_namespace, None,
                key_value_mapping)

        with self.assertRaisesRegexp(
            ValueError,
            'Invalid namespace: %s.' % invalid_namespace):
            caching_services.get_multi(
                invalid_namespace, None,
                ['a', 'b', 'c'])

        with self.assertRaisesRegexp(
            ValueError,
            'Invalid namespace: %s.' % invalid_namespace):
            caching_services.delete_multi(
                invalid_namespace, None, ['a', 'b', 'c'])

        invalid_sub_namespace = 'sub:namespace'
        with self.assertRaisesRegexp(
            ValueError,
            'Sub-namespace %s cannot contain \':\'.' % invalid_sub_namespace):
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT,
                invalid_sub_namespace, ['a', 'b', 'c'])

    def test_get_multi_correctly_retrieves_cache_elements(self):
        """Testing that querying the cache for elements where either all of the
        ids exist or don't exist in the cache returns reasonable output.
        """
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        exploration_id = 'id'

        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                ['a', 'b', 'c']), {})
        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_EXPLORATION,
                python_utils.convert_to_bytes(0),
                [exploration_id]),
            {})

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            {
                exploration_id: default_exploration
            })
        keys_exist_result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, ['a', 'b', 'c'])
        self.assertEqual(keys_exist_result, key_value_mapping)
        keys_non_existent_result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, ['d', 'e'])
        self.assertEqual(keys_non_existent_result, {})

        exploration_dict = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0), [exploration_id])
        self.assertEqual(
            default_exploration.to_dict(),
            exploration_dict.get(exploration_id).to_dict())

    def test_partial_fetches_returns_correct_elements(self):
        """Testing that querying the cache for elements where only a subsection
        of the queried ids exist in the cache, returns reasonable output.
        """
        key_value_mapping = {'a': '1', 'c': '3'}
        exploration_id = 'id'
        nonexistent_exploration_id = 'id2'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))

        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_EXPLORATION,
                python_utils.convert_to_bytes(0),
                [exploration_id]),
            {})

        self.assertEqual(
            caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                ['a', 'b', 'c']), {})

        self.assertEqual(caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                []), {})

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            {
                exploration_id: default_exploration
            })

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)

        result = caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_DEFAULT, None,
                ['a', 'b', 'c'])

        self.assertEqual(result, {'a': '1', 'c': '3'})

        result = caching_services.get_multi(
                caching_services.CACHE_NAMESPACE_EXPLORATION,
                python_utils.convert_to_bytes(0),
                [exploration_id, nonexistent_exploration_id])

        self.assertEqual(
            default_exploration.to_dict(),
            result.get(exploration_id).to_dict())

        self.assertFalse(nonexistent_exploration_id in result)

    def test_queries_to_wrong_namespace_returns_none(self):
        exploration_id = 'id'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            {
                exploration_id: default_exploration
            })

        result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT,
            python_utils.convert_to_bytes(0),
            [exploration_id])

        self.assertEqual(result, {})

    def test_queries_to_wrong_sub_namespace_returns_none(self):
        exploration_id = 'id'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(1),
            [exploration_id])
        self.assertEqual(result, {})

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(1),
            {
                exploration_id: default_exploration
            })

        non_existent_result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            [exploration_id])

        existent_result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(1),
            [exploration_id])
        self.assertEqual(
            existent_result.get(exploration_id).to_dict(),
            default_exploration.to_dict())

    def test_set_multi_returns_true_for_successful_insert_into_cache(self):
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}
        cache_strings_response = caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)
        self.assertTrue(cache_strings_response)

        exploration_id = 'id'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        cache_exploration_response = caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0),
            {
                exploration_id: default_exploration
            })
        self.assertTrue(cache_exploration_response)

        cache_empty_list_response = caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, {})
        self.assertTrue(cache_empty_list_response)

    def test_delete_multi_returns_true_when_all_ids_exist(self):
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, ['a', 'b', 'c'])
        self.assertFalse(is_successful)

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)

        exploration_id = 'id'
        default_exploration = (
            exp_domain.Exploration.create_default_exploration(
                'exp_id_1', title='A title', category='A category'))
        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0), {
                exploration_id: default_exploration
            })

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, [])
        self.assertTrue(is_successful)

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, ['a', 'b', 'c'])
        self.assertTrue(is_successful)

        result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0), [exploration_id])
        self.assertTrue(len(result) > 0)
        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0), [exploration_id])
        self.assertTrue(is_successful)

        result = caching_services.get_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION,
            python_utils.convert_to_bytes(0), [exploration_id])
        self.assertEqual(result, {})

    def test_delete_multi_returns_false_when_not_all_ids_exist(self):
        """Tests that deleting keys that don't exist returns false."""
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, ['a', 'e', 'f'])
        self.assertFalse(is_successful)

    def test_delete_multi_returns_false_when_namespace_incorrect(self):
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_EXPLORATION, None, ['a', 'b', 'c'])
        self.assertFalse(is_successful)

    def test_delete_multi_returns_false_when_namespace_incorrect(self):
        key_value_mapping = {'a': '1', 'b': '2', 'c': '3'}

        caching_services.set_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT, None, key_value_mapping)
        incorrect_sub_namespace = 'sub'

        is_successful = caching_services.delete_multi(
            caching_services.CACHE_NAMESPACE_DEFAULT,
            incorrect_sub_namespace, ['a', 'b', 'c'])
        self.assertFalse(is_successful)
