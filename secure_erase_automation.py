import logging

import win32serviceutil
import win32service
import win32event
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
import argparse

class MyHandler(FileSystemEventHandler):
    def __init__(self, input_directory: str, output_directory: str, archive_directory: str):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.archive_directory = archive_directory

        # Create parser
        self.parser = Parser()


    def on_created(self, event):
        # Parse each file in input directory
        for file in os.listdir(self.input_directory):
            input_file = f'{self.input_directory}{file}'
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

class SecureEraseSvc (win32serviceutil.ServiceFramework):
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
        self.main()

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



        observer = Observer()
        event_handler = MyHandler(input_directory, output_directory, archive_directory)

        observer.schedule(event_handler, path=input_directory, recursive=False)
        observer.start()
        event_handler.on_created(None)  # Activate event upon init
        while self.is_alive:
            time.sleep(1)

        observer.stop()
        observer.join()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        if os.environ.get('DEBUG', None):
            event_handler = MyHandler(input_directory='c:/temp/in/', output_directory='c:/temp/out/',
                                      archive_directory='c:/temp/archive')

            observer = Observer()

            observer.schedule(event_handler, path='c:/temp/in', recursive=False)
            observer.start()
            event_handler.on_created(None)
            while True:
                time.sleep(1)

            observer.stop()
            observer.join()
        else:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(SecureEraseSvc)
            servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SecureEraseSvc)
