"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import logging
import time
import threading

from monitors import end_of_run_monitor


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
            if self.health_check():
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
