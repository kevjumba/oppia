# coding: utf-8
#
# Copyright 2016 The Oppia Authors. All Rights Reserved.
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

"""Provides mailgun api to send email."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import base64
import logging
from textwrap import dedent # pylint: disable=import-only-modules

from constants import constants
from core.platform.email import gae_email_services
import feconf
import python_utils


def send_email_to_recipients(
        sender_email, recipient_emails, subject,
        plaintext_body, html_body, bcc=None, reply_to=None,
        recipient_variables=None):
    """Send POST HTTP request to mailgun api. This method is adopted from
    the requests library's post method.

    Args:
        sender_email: str. the email address of the sender. This should be in
            the form 'SENDER_NAME <SENDER_EMAIL_ADDRESS>'. Must be utf-8
        recipient_emails: list(str). The email address or email addresses
            of the recipients. Must be utf-8.
        subject: str. The subject line of the email, Must be utf-8.
        plaintext_body: str. The plaintext body of the email. Must be utf-8
        html_body: str. The HTML body of the email. Must fit in a datastore
            entity. Must be utf-8.
        bcc: list(str)|None. List of bcc emails.
        reply_to: str|None. Reply address formatted like
            “reply+<reply_id>@<incoming_email_domain_name>
            reply_id is the unique id of the sender.
        recipient_variables: dict|None. If batch sending requires
            differentiating each email based on the recipient, we can assign
            an id to the recipient and pass it as this dict where each key
            value pair is the recipient and an integer id. 

    Returns:
        Response from the server. The object is a file-like object.
        https://docs.python.org/2/library/urllib2.html
    """
    if not feconf.MAILGUN_API_KEY:
        raise Exception('Mailgun API key is not available.')

    if not feconf.MAILGUN_DOMAIN_NAME:
        raise Exception('Mailgun domain name is not set.')

    data = {
        'from': sender_email,
        'subject': subject,
        'text': plaintext_body,
        'html': html_body
    }

    if len(recipient_emails) == 1:
        data['to'] = recipient_emails[0]
    else:
        data['to'] = recipient_emails

    if bcc:
        if len(bcc) == 1:
            data['bcc'] = bcc[0]
        else:
            data['bcc'] = bcc

    if reply_to:
        data['h:Reply-To'] = reply_to

    if recipient_variables:
        data['recipient_variables'] = recipient_variables

    encoded = base64.b64encode(b'api:%s' % feconf.MAILGUN_API_KEY).strip()
    auth_str = 'Basic %s' % encoded
    header = {'Authorization': auth_str}
    server = (
        'https://api.mailgun.net/v3/%s/messages' % feconf.MAILGUN_DOMAIN_NAME)
    encoded_url = python_utils.url_encode(data)
    req = python_utils.url_request(server, encoded_url, header)
    return python_utils.url_open(req)


def send_mail(
        sender_email, recipient_email, subject, plaintext_body,
        html_body, bcc_admin=False, reply_to_id=None):
    """Sends an email using mailgun api.

    In general this function should only be called from
    email_manager._send_email().

    Args:
        sender_email: str. the email address of the sender. This should be in
            the form 'SENDER_NAME <SENDER_EMAIL_ADDRESS>'.
        recipient_email: str. the email address of the recipient.
        subject: str. The subject line of the email.
        plaintext_body: str. The plaintext body of the email.
        html_body: str. The HTML body of the email. Must fit in a datastore
            entity.
        bcc_admin: bool. Whether to bcc feconf.ADMIN_EMAIL_ADDRESS on the email.
        reply_to_id: str. The unique id of the sender.

    Raises:
        Exception: if the configuration in feconf.py forbids emails from being
            sent.
        Exception: if mailgun api key is not stored in feconf.MAILGUN_API_KEY.
        Exception: if mailgun domain name is not stored in
            feconf.MAILGUN_DOMAIN_NAME.
            (and possibly other exceptions, due to mail.send_mail() failures)
    """
    if not feconf.CAN_SEND_EMAILS:
        raise Exception('This app cannot send emails to users.')

    bcc = feconf.ADMIN_EMAIL_ADDRESS if (bcc_admin) else ''
    reply_to = (
        gae_email_services.get_incoming_email_address(reply_to_id)
        if reply_to_id else '')

    if not constants.DEV_MODE:
        send_email_to_recipients(
            sender_email, [recipient_email], subject.encode(encoding='utf-8'),
            plaintext_body.encode(encoding='utf-8'),
            html_body.encode(encoding='utf-8'), bcc=[bcc], reply_to=reply_to)
    else:
        msg_title = 'MailgunService.SendMail'
        # pylint: disable=division-operator-used
        msg_body = (
            """
            From: %s
            To: %s
            Subject: %s
            Body:
                Content-type: text/plain
                Data length: %d
            Body
                Content-type: text/html
                Data length: %d
            """ % (
                sender_email, recipient_email, subject, len(plaintext_body),
                len(html_body)))
        # pylint: enable=division-operator-used
        msg = msg_title + dedent(msg_body)
        logging.info(msg)
        logging.info(
            'You are not currently sending out real email since this is a' +
            ' dev environment. Emails are sent out in the production' +
            ' environment.')


def send_bulk_mail(
        sender_email, recipient_emails, subject, plaintext_body, html_body):
    """Sends an email using mailgun api.

    In general this function should only be called from
    email_manager._send_email().

    Args:
        sender_email: str. the email address of the sender. This should be in
            the form 'SENDER_NAME <SENDER_EMAIL_ADDRESS>'.
        recipient_emails: list(str). list of the email addresses of recipients.
        subject: str. The subject line of the email.
        plaintext_body: str. The plaintext body of the email.
        html_body: str. The HTML body of the email. Must fit in a datastore
            entity.

    Raises:
        Exception: if the configuration in feconf.py forbids emails from being
            sent.
        Exception: if mailgun api key is not stored in feconf.MAILGUN_API_KEY.
        Exception: if mailgun domain name is not stored in
            feconf.MAILGUN_DOMAIN_NAME.
            (and possibly other exceptions, due to mail.send_mail() failures)
    """
    if not feconf.CAN_SEND_EMAILS:
        raise Exception('This app cannot send emails to users.')

    # To send bulk emails we pass list of recipients in 'to' paarameter of
    # post data. Maximum limit of recipients per request is 1000.
    # For more detail check following link:
    # https://documentation.mailgun.com/user_manual.html#batch-sending
    recipient_email_lists = [
        recipient_emails[i:i + 1000]
        for i in python_utils.RANGE(0, len(recipient_emails), 1000)]

    if constants.DEV_MODE:
        logging.info('MailgunService.SendBulkMail')
    for email_list in recipient_email_lists:
        # 'recipient-variable' in post data forces mailgun to send individual
        # email to each recipient (This is intended to be a workaround for
        # sending individual emails).
        if not constants.DEV_MODE:
            send_email_to_recipients(
                sender_email, email_list, subject.encode(encoding='utf-8'),
                plaintext_body.encode(encoding='utf-8'),
                html_body.encode(encoding='utf-8'),
                recipient_variables={})
        else:
            recipient_email_list_str = ' '.join(
                ['%s' %
                 (recipient_email,) for recipient_email in email_list[:3]])
            # Show the first 3 emails in the list for up to 1000 emails.
            if len(email_list) > 3:
                recipient_email_list_str += (
                    '... Total: ' +
                    python_utils.convert_to_bytes(len(email_list)) + ' emails.')
            # pylint: disable=division-operator-used
            msg = (
                """
                From: %s
                To: %s
                Subject: %s
                Body:
                    Content-type: text/plain
                    Data length: %d
                Body
                    Content-type: text/html
                    Data length: %d
                """ % (
                    sender_email, recipient_email_list_str, subject,
                    len(plaintext_body), len(html_body)))
            # pylint: enable=division-operator-used
            logging.info(dedent(msg))
    if constants.DEV_MODE:
        logging.info(
            'You are not currently sending out real email since this is a' +
            ' dev environment. Emails are sent out in the production' +
            ' environment.')
