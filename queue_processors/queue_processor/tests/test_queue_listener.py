# ############################################################################### #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the queue processor
"""
# pylint: disable=missing-function-docstring
# pylint: disable=fixme

import unittest
from unittest import mock

from mock import patch, MagicMock, Mock

from model.message.job import Message
from queue_processors.queue_processor import stomp_client
from queue_processors.queue_processor._utils_classes import _UtilsClasses
from queue_processors.queue_processor.handle_message import HandleMessage
from queue_processors.queue_processor.stomp_client import StompClient
from utils.clients.queue_client import QueueClient
from utils.clients.settings.client_settings_factory import ActiveMQSettings
from utils.settings import ACTIVEMQ_SETTINGS


class TestQueueProcessor(unittest.TestCase):
    """
    Exercises the functions within listener.py
    """

    def setUp(self):
        self.test_consumer_name = "Test_Autoreduction_QueueProcessor"

    @patch('utils.clients.queue_client.QueueClient.__init__',
           return_value=None)
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.subscribe_autoreduce')
    def test_setup_connection(self, mock_sub_ar, mock_connect, mock_client):
        """
        Test: Connection to ActiveMQ setup, along with subscription to queues
        When: setup_connection is called with a consumer name
        """
        stomp_client.setup_connection(self.test_consumer_name)

        mock_client.assert_called_once()
        mock_connect.assert_called_once()
        mock_sub_ar.assert_called_once()

        (args, _) = mock_sub_ar.call_args
        self.assertEqual(args[0], self.test_consumer_name)
        self.assertIsInstance(args[1], StompClient)
        self.assertIsInstance(args[1]._client, QueueClient)


class TestUtilsClasses(unittest.TestCase):
    """
    Tests the _Utils class
    """

    def test_default_constructable(self):
        self.assertIsNotNone(_UtilsClasses())


class TestListener(unittest.TestCase):
    # We have too many public methods as our Class Under Test does too much...
    # pylint: disable=too-many-public-methods
    """
    Exercises the Listener
    """

    def setUp(self):
        self.mocked_client = mock.Mock(spec=QueueClient())
        self.mocked_handler = mock.Mock(spec=HandleMessage)

        with patch("queue_processors.queue_processor.stomp_client"
                   ".HandleMessage", return_value=self.mocked_handler), \
             patch("logging.getLogger") as patched_logger:
            self.listener = StompClient(self.mocked_client)
            self.mocked_logger = patched_logger.return_value

    @staticmethod
    def _get_header(destination=None):
        if destination is None:
            destination = mock.NonCallableMock()

        return {"destination": destination,
                "priority": mock.NonCallableMock()}

    def test_construct_and_send_skipped(self):
        """
        Test: The message is sent via the QueueClient with a populated
        message attribute
        When: _construct_and_send_skipped is called
        """
        mock_client = MagicMock(name="QueueClient")
        handler = HandleMessage(mock_client)
        test_rb_number = 1
        test_reason = "test"

        mock_message = Mock()
        handler._construct_and_send_skipped(test_rb_number, test_reason,
                                            message=mock_message)

        self.assertIsInstance(mock_message.message, str)
        mock_client.send_message.assert_called_with(
            ACTIVEMQ_SETTINGS.reduction_skipped, mock_message)

    def test_on_message_stores_priority(self):
        headers = self._get_header()
        self.listener.on_message(headers=headers, message=Message())
        self.assertEqual(headers["priority"], self.listener._priority)

    def test_on_message_with_non_message_type(self):
        # Patch out the populate method as we assume is tested elsewhere
        non_msg = {"message": "Test"}
        self.listener.on_message(headers=self._get_header('/queue/DataReady'),
                                 message=non_msg)

        self.listener._message_handler.data_ready.assert_called()
        sent_msg = self.listener._message_handler.data_ready.call_args[0][0]
        self.assertIsInstance(sent_msg, Message)

    def test_on_message_handles_throw(self):
        self.listener.message = Mock()
        self.listener.message.populate.side_effect = ValueError()

        self.listener.on_message(headers=self._get_header(), message="")
        self.mocked_logger.error.assert_called()

    def test_on_message_sends_to_correct_queue(self):
        client = self.mocked_handler

        # queue_name -> method
        to_test = {"/queue/DataReady": client.data_ready,
                   "/queue/ReductionStarted": client.reduction_started,
                   "/queue/ReductionComplete": client.reduction_complete,
                   "/queue/ReductionError": client.reduction_error,
                   "/queue/ReductionSkipped": client.reduction_skipped,
                   "unknown": self.mocked_logger.warning}

        for name, method in to_test.items():
            # Ensure something else didn't accidentally call the method
            method.assert_not_called()
            self.listener.on_message(headers=self._get_header(name),
                                     message=Message())
            method.assert_called_once()

    def test_on_message_exception(self):
        # Pretend reduction_error throws if something dire is wrong
        self.listener.reduction_error = Mock()
        self.listener.reduction_error.side_effect = RuntimeError()

        self.listener.on_message(
            headers=self._get_header("/queue/ReductionError"), message="")

        self.mocked_logger.error.assert_called()
