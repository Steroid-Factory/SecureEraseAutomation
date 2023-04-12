import logging

import win32serviceutil
import win32service
import win32event
import win32wnet
import servicemanager
import socket
import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
from json_to_asset import Parser
import shutil
import secrets


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.FileHandler('C:/secure_erase/service.log')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MyHandler(FileSystemEventHandler):
    def __init__(self, input_directory: str, output_directory: str, archive_directory: str):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.archive_directory = archive_directory

        # Create parser
        self.parser = Parser()


    def on_created(self, event):
        logger.info(f"on created called {time.time()}")
        logger.debug( f"Path '{self.input_directory}' exists: {os.path.exists(self.input_directory)}")
        # Parse each file in input directory
        for file in os.listdir(self.input_directory):
            input_file = f'{self.input_directory}{file}'
            logger.info(f"File: {self.input_directory}{file}")
            if not input_file.endswith('.json'):
                continue

            if self.parser.can_parse(input_file):
                devices = self.parser.parse_file(input_file_path=input_file)

                # Export each device from the report
                for device in devices:
                    device.export(self.output_directory)

            # Move file to archive
            if os.path.exists(input_file):
                shutil.move(input_file, self.archive_directory)

class SecureEraseSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "SecureEraseService"
    _svc_display_name_ = "Secure Erase Automation Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        logger.debug(f"Calling main")
        #self.start_loop()
        self.main()

    def get_config(self):
        # Config file path
        config_path = 'C:/secure_erase/config.json'

        # Verify config exists
        if not os.path.exists(config_path):
            print("Config file doesn't exist")
            return None

        # Read config
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)['io_config']
            input_directory = config.get("input_directory")
            if not input_directory.endswith("/"):
                input_directory = input_directory + '/'
            output_directory = config.get("output_directory")
            if not output_directory.endswith("/"):
                output_directory = output_directory + '/'
            archive_directory = config.get("archive_directory")
            if not archive_directory.endswith("/"):
                archive_directory = archive_directory + '/'

        return {"input": input_directory, "output": output_directory, "archive": archive_directory}

    def start_loop(self):
        config = self.get_config()
        input_directory = config.get('input')
        output_directory = config.get('output')
        archive_directory = config.get('archive')

        parser = Parser()

        while self.is_alive:
            if os.path.exists(input_directory):
                for file in os.listdir(input_directory):
                    input_file = f'{input_directory}{file}'
                    logger.info(f"File: {input_directory}{file}")
                    if not input_file.endswith('.json'):
                        continue

                    if parser.can_parse(input_file):
                        devices = parser.parse_file(input_file_path=input_file)

                        # Export each device from the report
                        for device in devices:
                            device.export(output_directory)

                    # Move file to archive
                    if os.path.exists(input_file):
                        shutil.move(input_file, archive_directory)
            time.sleep(1)
    def connect(self):
        pass

    def disconnect(self):
        pass


    def main(self):
        # Config file path
        config_path = 'C:/secure_erase/config.json'

        # Verify config exists
        if not os.path.exists(config_path):
            print("Config file doesn't exist")
            return

        # Read config
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)['io_config']
            input_directory = config.get("input_directory")
            if not input_directory.endswith("/"):
                input_directory = input_directory + '/'
            output_directory = config.get("output_directory")
            if not output_directory.endswith("/"):
                output_directory = output_directory + '/'
            archive_directory = config.get("archive_directory")
            if not archive_directory.endswith("/"):
                archive_directory = archive_directory + '/'


        logger.debug(f"Input: {input_directory}")
        logger.debug(f"Out: {output_directory}")
        observer = Observer()
        event_handler = MyHandler(input_directory, output_directory, archive_directory)


        logger.debug(f"Before Path '{input_directory}' exists: {os.path.exists(input_directory)}")
        # Split the path into its components
        path_parts = os.path.split(input_directory)

        try:
            # Connect to the network share using the mapped drive letter
            win32wnet.WNetAddConnection2(
                None, None, None, None,
                r'\\spus-file\usshared', path_parts[0]
            )
        except Exception as error:
            logger.error(error)
        win32wnet.WNetAddConnection2(r'\\speg-file\usshared', 0, 0)
        # logger.debug(f"After Path '{input_directory}' exists: {os.path.exists(input_directory)}")
        # observer.schedule(event_handler, path=input_directory, recursive=False)
        # observer.start()
        # event_handler.on_created(None)  # Activate event upon init
        #
        #
        # while self.is_alive:
        #     time.sleep(1)
        #
        #
        #
        # observer.stop()
        # observer.join()

def get_config():
    # Config file path
    config_path = 'C:/secure_erase/config.json'

    # Verify config exists
    if not os.path.exists(config_path):
        print("Config file doesn't exist")
        return None

    # Read config
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)['io_config']
        input_directory = config.get("input_directory")
        if not input_directory.endswith("/"):
            input_directory = input_directory + '/'
        output_directory = config.get("output_directory")
        if not output_directory.endswith("/"):
            output_directory = output_directory + '/'
        archive_directory = config.get("archive_directory")
        if not archive_directory.endswith("/"):
            archive_directory = archive_directory + '/'

    return {"input": input_directory, "output": output_directory, "archive": archive_directory}

def parse_folder():
    config = get_config()
    input_directory = config.get('input')
    output_directory = config.get('output')
    archive_directory = config.get('archive')

    parser = Parser()

    if os.path.exists(input_directory):
        for file in os.listdir(input_directory):
            input_file = f'{input_directory}{file}'
            if not input_file.endswith('.json'):
                continue

            if parser.can_parse(input_file):
                devices = parser.parse_file(input_file_path=input_file)

                # Export each device from the report
                for device in devices:
                    device.export(output_directory)

            # Move file to archive
            if os.path.exists(input_file):
                shutil.move(input_file, archive_directory)
if __name__ == '__main__':
    parse_folder()
    # if len(sys.argv) == 1:
    #     # if os.environ.get('DEBUG', None):
    #     #     event_handler = MyHandler(input_directory='c:/temp/in/', output_directory='c:/temp/out/',
    #     #                               archive_directory='c:/temp/archive')
    #     #
    #     #     observer = Observer()
    #     #
    #     #     observer.schedule(event_handler, path='c:/temp/in', recursive=False)
    #     #     observer.start()
    #     #     event_handler.on_created(None)
    #     #     while True:
    #     #         time.sleep(1)
    #     #
    #     #     observer.stop()
    #     #     observer.join()
    #     # else:
    #     servicemanager.Initialize()
    #     servicemanager.PrepareToHostSingle(SecureEraseSvc)
    #     servicemanager.StartServiceCtrlDispatcher()
    # else:
    #     win32serviceutil.HandleCommandLine(SecureEraseSvc)

