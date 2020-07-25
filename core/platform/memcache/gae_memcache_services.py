# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
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

"""Provides redis cache services."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import python_utils
from core.domain import cache_services
import json

from google.appengine.api import memcache
import redis
import logging

redis_client = redis.Redis(host='localhost', port=6379)

def get_multi(keys):
    """Looks up a list of keys in memcache.

    Args:
        keys: list(str). A list of keys (strings) to look up.

    Returns:
        dict. A dict of key-value pairs for the keys/values that were present in
        memcache.
    """
    assert isinstance(keys, list)
    result = redis_client.mget(keys)
    if result and (result != [None]):
        dct = {}
        for key, value in zip(keys, result):
            correct_type_of_dict = cache_services.get_correct_dict_type_of_key(
                key)
            if correct_type_of_dict:
                value_dict = json.loads(value)
                dct[key] = correct_type_of_dict.from_dict(value_dict)
            else:
                dct[key] = value
        return dct
    else:
        return {}


def set_multi(key_value_mapping):
    """Sets multiple keys' values at once.

    Args:
        key_value_mapping: a dict of {key: value} pairs. The key is a string
            and the value is anything that is serializable using the Python
            pickle module. The combined size of each key and value must be
            < 1 MB. The total size of key_value_mapping should be at most 32 MB.

    Returns:
        list(str). A list of the keys whose values were NOT set.
    """
    assert isinstance(key_value_mapping, dict)
    for key, value in key_value_mapping.items():
        if hasattr(value, 'to_dict'):
            key_value_mapping[key] = json.dumps(value.to_dict())
    added = redis_client.mset(key_value_mapping)
    if added != len(key_value_mapping):
        logging.error('Redis set failed.')
    return []


def delete(key):
    """Deletes a key in memcache.

    Args:
        key: str. A key (string) to delete.

    Returns:
        int. 1 if the delete failed, and 2 for a successful delete.
    """
    assert isinstance(key, python_utils.BASESTRING)
    return_code = redis_client.delete(key)
    if return_code != 1:
        logging.error('Redis delete failed.')
        return 1
    return 2


def delete_multi(keys):
    """Deletes multiple keys in memcache.

    Args:
        keys: list(str). The keys (strings) to delete.

    Returns:
        bool. True if all operations complete successfully; False
        otherwise.
    """
    for key in keys:
        assert isinstance(key, python_utils.BASESTRING)
    return_value = redis_client.delete(*keys)
    if return_value != len(keys):
        logging.error('Redis delete failed.')
    return True
