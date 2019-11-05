# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Factory for creating settings objects that can be used in the client classes
"""
from utils.clients.settings.client_settings import ClientSettings


# pylint:disable=too-few-public-methods
class ClientSettingsFactory:
    """
    Class for the settings factory
    """

    ignore_kwargs = ['username', 'password', 'host', 'port']

    # pylint:disable=too-many-arguments
    def create(self, settings_type, username, password, host, port, **kwargs):
        """
        Create a settings object to use with a client
        :param settings_type: The type of client you require this can be: database, icat or queue
        :param username: username for logon
        :param password: password for logon
        :param host: host address for service
        :param port: port on the host machine where the service is running
        :param kwargs: key word arguments used for specific classes
                       Database specific args : database_name
                       ICAT specific args     : authentication_type
                       Queue specific args    : reduction_pending, data_ready, reduction_started
                                                reduction_complete, reduction_error
        :return: A ClientSettings object
        """
        if settings_type.lower() not in ['database', 'icat', 'queue']:
            raise ValueError("Factories creation settings type must be one of: 'database', "
                             "'icat', 'queue'")
        kwargs['username'] = username
        kwargs['password'] = password
        kwargs['host'] = host
        kwargs['port'] = port

        settings = None
        if settings_type.lower() == 'database':
            settings = self._create_database(**kwargs)
        elif settings_type.lower() == 'icat':
            settings = self._create_icat(**kwargs)
        elif settings_type.lower() == 'queue':
            settings = self._create_queue(**kwargs)
        return settings

    def _create_database(self, **kwargs):
        """
        :return: Database compatible settings object
        """
        database_kwargs = ['database_name']
        self._test_kwargs(database_kwargs, kwargs)
        return MySQLSettings(**kwargs)

    def _create_queue(self, **kwargs):
        """
        :return: Queue compatible settings object
        """
        queue_kwargs = ['reduction_pending', 'data_ready', 'reduction_started',
                        'reduction_complete', 'reduction_error']
        self._test_kwargs(queue_kwargs, kwargs)
        return ActiveMQSettings(**kwargs)

    def _create_icat(self, **kwargs):
        """
        :return: Icat compatible settings object
        """
        icat_kwargs = ['authentication_type']
        self._test_kwargs(icat_kwargs, kwargs)
        return ICATSettings(**kwargs)

    def _test_kwargs(self, expected, actual):
        """
        Ensure that the kwargs given as input contain the expected keys
        """
        for key, _ in actual.items():
            if key not in expected and key not in self.ignore_kwargs:
                raise ValueError("{0} is not a recognised key word argument."
                                 " Valid kwargs: {1}".format(key, expected))


# pylint:disable=too-few-public-methods
class ICATSettings(ClientSettings):
    """
    ICAT settings object
    """
    auth = None

    def __init__(self, authentication_type='Simple', **kwargs):
        super(ICATSettings, self).__init__(**kwargs)
        self.auth = authentication_type


# pylint:disable=too-few-public-methods
class MySQLSettings(ClientSettings):
    """
    MySQL settings to be used as a Database settings object
    """
    database = None

    def __init__(self, database_name='autoreduction', **kwargs):
        super(MySQLSettings, self).__init__(**kwargs)
        self.database = database_name

    def get_full_connection_string(self):
        """ :return: string for connecting directly to mysql service with user + pass """
        return 'mysql+mysqldb://{0}:{1}@{2}/{3}'.format(self.username,
                                                        self.password,
                                                        self.host,
                                                        self.database)


# pylint:disable=too-few-public-methods
class ActiveMQSettings(ClientSettings):
    """
    ActiveMq settings to be used as a Queue settings object
    """
    reduction_pending = None
    data_ready = None
    reduction_started = None
    reduction_complete = None
    reduction_error = None
    reduction_skipped = None
    all_subscriptions = None

    # pylint:disable=too-many-arguments
    def __init__(self,
                 reduction_pending='/queue/ReductionPending',
                 data_ready='/queue/DataReady',
                 reduction_started='/queue/ReductionStarted',
                 reduction_complete='/queue/ReductionComplete',
                 reduction_error='/queue/ReductionError',
                 reduction_skipped='/queue/ReductionSkipped',
                 **kwargs):
        super(ActiveMQSettings, self).__init__(**kwargs)

        self.reduction_pending = reduction_pending
        self.data_ready = data_ready
        self.reduction_started = reduction_started
        self.reduction_complete = reduction_complete
        self.reduction_error = reduction_error
        self.reduction_skipped = reduction_skipped
        self.all_subscriptions = [data_ready, reduction_started,
                                  reduction_complete, reduction_error, reduction_skipped]
