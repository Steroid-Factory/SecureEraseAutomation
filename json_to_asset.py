import json
import os
from device import DeviceTemplate
import shutil

import logging
#import datetime
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.FileHandler('C:/secure_erase/processing.log')
handler.setFormatter(formatter)

logger.addHandler(handler)

class Parser:
    def __init__(self):
        ...

    # Checks whether the file can be used by parser
    def can_parse(self, input_file_path: str) -> bool:
        # Skip if file path doesn't exist
        if not os.path.exists(input_file_path):
            logger.error(f"File '{input_file_path}' does not exist")
            return False

        # Skip if not a .json
        if not input_file_path.endswith(".json"):
            logger.error(f"File '{input_file_path}' is not a .json format")
            return False

        # Skip if config file
        if 'config.json' in input_file_path:
            return False

        return True


    def parse_comp(self, report: dict) -> dict:
        # Raw
        serial = report.get('Serial Number')
        memory = report.get('RAM')
        manufacturer = report.get('Vendor')

        # Extract model from string
        model = report.get('Model')
        if model.endswith("]"):
            start_index = model.find('[')
            model = model[start_index + 1:].split(" ")[0]
        if report.get('Asset ID') == 'N/A':
            logger.warning(f"Serial Number '{serial}' does not have a barcode")
            barcode = ''
        else:
            barcode = report.get('Asset ID').split(" ")[-1]
        Anumber = report.get("'A' Number")

        comp = {"serial": serial,
                "memory": memory,
                "manufacturer": manufacturer,
                "model": model,
                "barcode": barcode,
                "anumber": Anumber}
        return comp

    def parse_cpus(self, report: dict):
        cpus = []
        for number in range(1, 5):
            cpu_string = report.get(f'CPU {number}')

            if cpu_string == 'N/A':
                continue

            component_id = f'cpu{number}'
            description = cpu_string
            type_code = ''
            if cpu_string.startswith('Apple M'):
                type_code = cpu_string[6:8]
                model = cpu_string[cpu_string.find('(') + 1: -1].title()
                cores = cpu_string.split('(')[1].split(' ')[0]
                speed = ''
            if cpu_string.startswith('Intel(R)'):
                type_code = f"C{cpu_string.split()[2][:2].upper()}"
                model = cpu_string.split()[2]
                cores = '0'
                speed = cpu_string.split()[-1]

            cpus.append({"id": component_id,
                        "description": description,
                         "type_code": type_code,
                         "model": model,
                         "cores": cores,
                         "speed": speed})
        return cpus

    def parse_hdds(self, report: dict):
        hdds = []
        for number in range(1, 5):
            hdd_string = report.get(f'Storage {number}')
            if hdd_string == 'N/A':
                continue

            component_id = f'hdd{number}'

            type = hdd_string.split(',')[0].replace('Type:', '').strip().upper()
            model = hdd_string.split(',')[1].replace('Model:', '').strip()
            size = hdd_string.split(',')[2].replace('Size:', '').strip()

            serial = report.get('Storage Serial').split(',')[number - 1].\
                replace(f"Storage {number} / ", "").strip()

            employee = report.get('Data Wipe Employee').split(',')[number - 1].\
                replace(f"Storage {number} / ", "").strip()

            wipe_status = report.get('Data Wipe').split(',')[number - 1].split('/')[1].\
                replace(f"Storage {number} / ", "").strip()

            if wipe_status == "Successful":
                wipe_status = "PASSED"
                wipe_status_number = "1"
            else:
                wipe_status = "FAILED"
                wipe_status_number = "0"

            if report.get('Data Wipe Method') == 'N/A':
                wipe_method = ''
            else:
                wipe_method = report.get('Data Wipe Method').split(',')[number - 1].split('/')[1].strip()

            original_time_format = ('%Y-%m-%d %H:%M:%S')
            final_time_format = ('%d-%m-%Y %H:%M:%S')

            # The raw datetime string
            started_string = report.get('Data Wipe Started').split(',')[number - 1].split('/')[1].strip()[:-4]
            finished_string = report.get('Data Wipe Finished').split(',')[number - 1].split('/')[1].strip()[:-4]

            if started_string == '' or finished_string == '':
                wipe_started = ''
                wipe_finished = ''
            else:
                # Convert to datetime
                started_datetime = datetime.strptime(started_string, original_time_format)
                finished_datetime = datetime.strptime(finished_string, original_time_format)

                # Convert datetime format to final format
                wipe_started = started_datetime.strftime(final_time_format)
                wipe_finished = finished_datetime.strftime(final_time_format)

            hdds.append({"id": component_id,
                         "serial": serial,
                         "type": type,
                         "model": model,
                         "size": size,
                         "employee": employee,
                         "wipe_status": wipe_status,
                         "wipe_status_number": wipe_status_number,
                         "wipe_method": wipe_method,
                         "wipe_started": wipe_started,
                         "wipe_finished": wipe_finished})

        return hdds

    def parse_battery(self, report: dict):
        health = report.get('Battery Health', 0)
        try:
            if health == 'Normal':
                logger.warning(f"{report.get('Serial Number')} health value is Normal instead of an integer")
                status = '1'
            elif int(health) >= 60:
                status = '1'
            else:
                status = '0'
        except ValueError:
            status = '0'
            logger.warning(f"{report.get('Serial Number')} health value is not an integer")

        return {"health": health, "status": status}


    def parse_memory(self, report: dict):
        capacity = report.get('RAM')
        type = report.get('Configuration').split('/')[0].split(' ')[2]
        return {"capacity": capacity, "type": type}


    def parse_file(self, input_file_path) -> DeviceTemplate:
        devices = []
        with open(input_file_path, 'r') as file:
            reports = json.load(file)['PCProduct']
            for report in reports:
                if report.get("'A' Number") == "N/A":
                    logger.warning(f"{report.get('Serial Number')} does not have an A Number - skipping")
                    continue

                if report.get('Asset ID') == "N/A":
                    logger.warning(f"{report.get('Serial Number')} does not have an A Barcode - skipping")
                    continue

                device = DeviceTemplate()
                device.location = report.get("Securaze User")
                device.comp = self.parse_comp(report)
                device.cpus = self.parse_cpus(report)
                device.hdds = self.parse_hdds(report)
                device.battery = self.parse_battery(report)
                device.memory = self.parse_memory(report)
                device.compile()
                print(device._hdd_vars)
                devices.append(device)
        return devices


def main():
    # Config file path
    config_path = 'S:/ftp/Securaze/config.json'

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


    # Create parser
    parser = Parser()

    # Parse each file in input directory
    for file in os.listdir(input_directory):
        input_file = f'{input_directory}{file}'
        if parser.can_parse(input_file):
            devices = parser.parse_file(input_file_path=input_file)

            # Export each device from the report
            for device in devices:
                device.export(output_directory)

            # Move file to archive
            shutil.move(input_file, archive_directory)


if __name__ == "__main__":
    main()
