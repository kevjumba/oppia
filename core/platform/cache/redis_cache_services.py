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

"""Provides the redis cache service functionality."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import feconf
import python_utils
import redis

REDIS_CLIENT = redis.Redis(
    host=feconf.REDISHOST, port=feconf.REDISPORT)


def flush_cache():
    """Wipes the Redis cache clean."""
    REDIS_CLIENT.flushdb()


def get_multi(keys):
    """Looks up a list of keys in Redis cache.

    Args:
        keys: list(str). A list of keys (strings) to look up.

    Returns:
        list(str). A list of values in the cache corresponding to the keys that
        are passed in.
    """
    assert isinstance(keys, list)
    return REDIS_CLIENT.mget(keys)


def set_multi(key_value_mapping):
    """Sets multiple keys' values at once in the Redis cache.

    Args:
        key_value_mapping: dict(str, str). Both the key and value are strings.
            The value can either be a primitive binary-safe string or the
            JSON-encoded string version of the object.

    Returns:
        bool. Whether the set action succeeded.
    """
    assert isinstance(key_value_mapping, dict)
    return REDIS_CLIENT.mset(key_value_mapping)


def delete(key):
    """Deletes a key in the Redis cache.

    Args:
        key: str. A key (string) to delete.

    Returns:
        int. Number of successfully deleted keys.
    """
    assert isinstance(key, python_utils.BASESTRING)
    number_of_deleted_keys = REDIS_CLIENT.delete(key)
    return number_of_deleted_keys


def delete_multi(keys):
    """Deletes multiple keys in the Redis cache.

    Args:
        keys: list(str). The keys (strings) to delete.

    Returns:
        int. Number of successfully deleted keys.
    """
    for key in keys:
        assert isinstance(key, python_utils.BASESTRING)
    number_of_deleted_keys = REDIS_CLIENT.delete(*keys)
    return number_of_deleted_keys
