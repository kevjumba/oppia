# coding: utf-8
#
# Copyright 2020 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS-IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provides functionality for Google Cloud Tasks-related operations."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import datetime
import json
import logging

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

import feconf

client = tasks_v2.CloudTasksClient()

def create_http_task(
        queue_name, url, payload=None, scheduled_for=None, task_name=None):
    """Creates an http task with the correct http headers/payload and sends
    that task to the Cloud Tasks API. An http task is an asynchronous task that
    consists of a post request to a specified url with the specified payload.
    The post request will be made by the Cloud Tasks Cloud Service when the
    `scheduled_for` countdown expires.

    Args:
        queue_name: str. The name of the queue to add the http task to.
        url: str. URL of the handler function.
        payload: dict(str: *)|None. Payload to pass to the request. Defaults to
            None if no payload is required.
        scheduled_for: int|None. Amount of time, in seconds, to wait before
            executing the task. Pass in 0 or None to schedule the task for
            immediate execution.
        task_name: str|None. Optional. The name of the task.
    """
    # The cloud tasks library requires the Oppia project id and region, as well
    # as the queue name as the path to be able to find the correct queue.
    parent = client.queue_path(
        feconf.OPPIA_PROJECT_ID, feconf.GOOGLE_APP_ENGINE_REGION, queue_name)

    # Construct the request body.
    task = {
        'http_request': {  # Specify the type of request.
            'http_method': tasks_v2.HttpMethod.POST,
            'url': url,  # The full url path that the task will be sent to.
        }
    }

    if payload is not None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            task['http_request']['headers'] = {
                'Content-type': 'application/json'
            }

        # The API expects a payload of type bytes.
        converted_payload = payload.encode()

        # Add the payload to the request.
        task['http_request']['body'] = converted_payload

    if scheduled_for is not None:
        # Convert 'seconds from now' into an rfc3339 datetime string.
        d = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=scheduled_for)

        # Create Timestamp protobuf.
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)

        # Add the timestamp to the tasks.
        task['schedule_time'] = timestamp

    if task_name is not None:
        # Add the name to tasks.
        task['name'] = task_name

    # Use the client to build and send the task.
    response = client.create_task(request={'parent': parent, 'task': task})

    logging.info('Created task {}'.format(response.name))
    # [END cloud_tasks_create_http_task]
    return response
