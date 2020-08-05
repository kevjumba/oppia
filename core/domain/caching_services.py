# coding: utf-8
#
# Copyright 2020 The Oppia Authors. All Rights Reserved.
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

"""Service functions to set and retrieve data from the memory cache."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

from core.domain import collection_domain
from core.domain import exp_domain
from core.domain import skill_domain
from core.domain import story_domain
from core.domain import topic_domain
from core.platform import models
import python_utils

memory_cache_services = models.Registry.import_cache_services()

# NOTE: Namespaces cannot contain ':'.
# The sub-namespace is defined as the stringified version number of the
# Exploration. The namespace handles Exploration objects and returns an
# Exploration object in the format of a dictionary with strings as keys and
# Explorations as values.
CACHE_NAMESPACE_EXPLORATION = 'exploration'
# The sub-namespace is defined as the stringified version number of the
# Collection. The namespace handles Collection objects and returns a Collection
# object in the format of a dictionary with strings as keys and Collections as
# values.
CACHE_NAMESPACE_COLLECTION = 'collection'
# The sub-namespace is defined as the stringified version number of the Skill.
# The namespace handles Skill objects and returns Skill objects in the format of
# a dictionary with strings as keys and Skills as values.
CACHE_NAMESPACE_SKILL = 'skill'
# Sub-namespace is defined as the stringified version number of the Story. The
# namespace handles Story objects and returns Story objects in the format of a
# dictionary with strings as keys and Stories as values.
CACHE_NAMESPACE_STORY = 'story'
# The sub-namespace is defined as the stringified version number of the Topic.
# The namespace handles Topic objects and returns Topic objects in the format of
# a dictionary with strings as keys and Topics as values.
CACHE_NAMESPACE_TOPIC = 'topic'
# The sub-namespace is not defined. The namespace handles a ConfigPropertyModel
# value and returns a ConfigPropertyModel value (the 'value' attribute of a
# ConfigPropertyModel object).
CACHE_NAMESPACE_CONFIG = 'config'
# The sub-namespace is not defined. The namespace handles default datatypes
# allowed by Redis including Strings, Lists, Sets, and Hashes. More details
# can be found at: https://redis.io/topics/data-types.
CACHE_NAMESPACE_DEFAULT = 'default'

DESERIALIZATION_FUNCTIONS = {
    CACHE_NAMESPACE_COLLECTION: collection_domain.Collection.deserialize,
    CACHE_NAMESPACE_EXPLORATION: exp_domain.Exploration.deserialize,
    CACHE_NAMESPACE_SKILL: skill_domain.Skill.deserialize,
    CACHE_NAMESPACE_STORY: story_domain.Story.deserialize,
    CACHE_NAMESPACE_TOPIC: topic_domain.Topic.deserialize,
    CACHE_NAMESPACE_CONFIG: lambda x: x,
    CACHE_NAMESPACE_DEFAULT: lambda x: x
}

SERIALIZATION_FUNCTIONS = {
    CACHE_NAMESPACE_COLLECTION: lambda x: x.serialize(),
    CACHE_NAMESPACE_EXPLORATION: lambda x: x.serialize(),
    CACHE_NAMESPACE_SKILL: lambda x: x.serialize(),
    CACHE_NAMESPACE_STORY: lambda x: x.serialize(),
    CACHE_NAMESPACE_TOPIC: lambda x: x.serialize(),
    CACHE_NAMESPACE_CONFIG: lambda x: x,
    CACHE_NAMESPACE_DEFAULT: lambda x: x
}


def _get_memcache_key(namespace, sub_namespace, obj_id):
    """Returns a memcache key for the class under namespace and sub_namespace.

    Args:
        namespace: str. The namespace under which the values associated with the
            id lie. Use CACHE_NAMESPACE_DEFAULT as namespace for ids that
            are not associated with a conceptual domain-layer entity and
            therefore don't require serialization.
        sub_namespace: str|None. The sub-namespace further differentiates the
            values. For Explorations, Skills, Stories, Topics, and Collections,
            the sub-namespace is the stringified version number of the objects.
        obj_id: str. The id of the value to store in the memory cache.

    Raises:
        Exception. The sub-namespace contains a ':'.

    Returns:
        str. The generated key for use in the memory cache in order to
        differentiate a passed-in key based on namespace and sub-namespace.
    """
    sub_namespace_key_string = sub_namespace if sub_namespace else ''
    if ':' in sub_namespace_key_string:
        raise ValueError(
            'Sub-namespace %s cannot contain \':\'.' % sub_namespace_key_string)
    return '%s:%s:%s' % (namespace, sub_namespace_key_string, obj_id)


def flush_memory_cache():
    """Flushes the memory cache by wiping all of the data."""
    memory_cache_services.flush_cache()


def get_multi(namespace, sub_namespace, obj_ids):
    """Get a dictionary of the {id, value} pairs from the memory cache.

    Args:
        namespace: str. The namespace under which the values associated with
            these object ids lie. The namespace determines how the objects are
            decoded from their JSON-encoded string. Use CACHE_NAMESPACE_DEFAULT
            as namespace for objects that are not associated with a conceptual
            domain-layer entity and therefore don't require serialization.
        sub_namespace: str|None. The sub-namespace further differentiates the
            values. For Explorations, Skills, Stories, Topics, and Collections,
            the sub-namespace is the stringified version number of the objects.
            If the sub-namespace is not required, pass in None.
        obj_ids: list(str). List of object ids corresponding to values to
            retrieve from the cache.

    Raises:
        ValueError. The namespace does not exist or is not recognized.

    Returns:
        dict(str, Exploration|Skill|Story|Topic|Collection|str). Dictionary of
        decoded (id, value) pairs retrieved from the platform caching service.
    """
    result_dict = {}
    if len(obj_ids) == 0:
        return result_dict

    if namespace not in DESERIALIZATION_FUNCTIONS:
        raise ValueError(
            'Invalid namespace: %s.' % namespace)

    memcache_keys = [
        _get_memcache_key(namespace, sub_namespace, obj_id)
        for obj_id in obj_ids]
    values = memory_cache_services.get_multi(memcache_keys)
    for obj_id, value in python_utils.ZIP(obj_ids, values):
        if value:
            result_dict[obj_id] = DESERIALIZATION_FUNCTIONS[namespace](value)

    return result_dict


def set_multi(namespace, sub_namespace, id_value_mapping):
    """Set multiple id values at once to the cache, where the values are all
    of a specific namespace type or a Redis compatible type (more details here:
    https://redis.io/topics/data-types).

    Args:
        namespace: str. The namespace under which the values associated with the
            id lie. Use CACHE_NAMESPACE_DEFAULT as namespace for objects that
            are not associated with a conceptual domain-layer entity and
            therefore don't require serialization.
        sub_namespace: str|None. The sub-namespace further differentiates the
            values. For Explorations, Skills, Stories, Topics, and Collections,
            the sub-namespace is the stringified version number of the objects.
            If the sub-namespace is not required, pass in None.
        id_value_mapping:
            dict(str, Exploration|Skill|Story|Topic|Collection|str). A dict of
            {id, value} pairs to set to the cache.

    Raises:
        ValueError. The namespace does not exist or is not recognized.

    Returns:
        bool. Whether all operations complete successfully.
    """
    if len(id_value_mapping) == 0:
        return True

    if namespace not in SERIALIZATION_FUNCTIONS:
        raise ValueError(
            'Invalid namespace: %s.' % namespace)

    memory_cache_id_value_mapping = (
        {
            _get_memcache_key(namespace, sub_namespace, obj_id):
            SERIALIZATION_FUNCTIONS[namespace](value)
            for obj_id, value in id_value_mapping.items()
        })
    return memory_cache_services.set_multi(memory_cache_id_value_mapping)


def delete_multi(namespace, sub_namespace, obj_ids):
    """Deletes multiple ids in the cache.

    Args:
        namespace: str. The namespace under which the values associated with the
            id lie. Use CACHE_NAMESPACE_DEFAULT namespace for object ids that
            are not associated with a conceptual domain-layer entity and
            therefore don't require serialization.
        sub_namespace: str|None. The sub-namespace further differentiates the
            values. For Explorations, Skills, Stories, Topics, and Collections,
            the sub-namespace is the stringified version number of the objects.
            If the sub-namespace is not required, pass in None.
        obj_ids: list(str). A list of id strings to delete from the cache.

    Raises:
        ValueError. The namespace does not exist or is not recognized.

    Returns:
        bool. Whether all operations complete successfully.
    """
    if len(obj_ids) == 0:
        return True

    if namespace not in DESERIALIZATION_FUNCTIONS:
        raise ValueError(
            'Invalid namespace: %s.' % namespace)

    memcache_keys = [
        _get_memcache_key(namespace, sub_namespace, obj_id)
        for obj_id in obj_ids]
    return memory_cache_services.delete_multi(memcache_keys) == len(obj_ids)


def get_memory_stats():
    """Get a memory profile of the cache in a dictionary dependent on how the
    caching service profiles its own cache.

    Returns:
        MemoryStats. MemoryStats object containing the total allocated memory in
        bytes, peak memory usage in bytes, and the total number of keys stored
        as values.
    """
    return memory_cache_services.get_memory_stats()
