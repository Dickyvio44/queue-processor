"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import logging
import time
import threading

from monitors import end_of_run_monitor
from monitors.settings import EORM_LOG_FILE, INSTRUMENTS
from utils.clients.database_client import DatabaseClient
from utils.clients.connection_exception import ConnectionException

logging.basicConfig(filename=EORM_LOG_FILE,
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')


# pylint:disable=missing-docstring
class HealthCheckThread(threading.Thread):

    def __init__(self, time_interval):
        threading.Thread.__init__(self)
        self.time_interval = time_interval
        self.exit = False

    def run(self):
        """
        Perform a service health check every time_interval
        """
        while self.exit is False:
            service_okay = self.health_check()
            if service_okay:
                logging.info("No Problems detected with service")
            else:
                logging.warning("Problem detected with service. Restarting service...")
                self.restart_service()
            time.sleep(self.time_interval)
        logging.info('Main Health check thread loop stopped')

    @staticmethod
    def health_check():
        """
        Check to see if the service is still running as expected
        :return: True: Service is okay, False: Service requires restart
        """
        logging.info('Performing Health Check at %s', datetime.now())

        # Connect to the database
        logging.info("Connecting to reduction database")
        db_cli = DatabaseClient()
        try:
            db_cli.connect()
        except ConnectionException:
            logging.error("Unable to connect to MySQL")

        # Get last run
        conn = db_cli.get_connection()
        for inst in INSTRUMENTS:
            db_last_run = conn.query(db_cli.reduction_run())\
                .join(db_cli.reduction_run().instrument)\
                .filter_by(name=inst['name'])\
                .order_by(db_cli.reduction_run().created.desc())\
                .first()\
                .run_number
            logging.info("Found last run on %s of %i", inst['name'], db_last_run)

        return True

    @staticmethod
    def restart_service():
        """
        Restart the end of run monitor service
        """
        end_of_run_monitor.stop()
        end_of_run_monitor.main()

    def stop(self):
        """
        Send a signal to stop the main thread loop
        """
        logging.info('Received stop signal for the Health Check thread')
        self.exit = True


HealthCheckThread.health_check()