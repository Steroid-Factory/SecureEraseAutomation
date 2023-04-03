import json
import os
from device import DeviceTemplate
import shutil

import logging


class Parser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('C:/secure_erase/processing.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


        handler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def can_parse(self, input_file_path: str) -> bool:
        if not os.path.exists(input_file_path):
            self.logger.error(f"File '{input_file_path}' does not exist")
            return False

        if not input_file_path.endswith(".json"):
            self.logger.error(f"File '{input_file_path}' is not a .json format")
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
            self.logger.warning(f"Serial Number '{serial}' does not have a barcode")
            barcode = ''
        else:
            report.get('Asset ID').split(" ")[-1]
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
            if cpu_string.startswith('Intel(R)'):
                type_code = f"C{cpu_string.split()[2][:2].upper()}"
                model = cpu_string.split()[2]
                cores = '0'

            # Extract number of cores from string

            cpus.append({"id": component_id,
                        "description": description,
                         "type_code": type_code,
                         "model": model,
                         "cores": cores})
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

            wipe_method = report.get('Data Wipe Method').split(',')[number - 1].split('/')[1].strip()
            wipe_timestamp = report.get('Data Wipe Timestamp').split(',')[number - 1].split('/')[1].strip()[:-4]


            hdds.append({"id": component_id,
                         "serial": serial,
                         "type": type,
                         "model": model,
                         "size": size,
                         "employee": employee,
                         "wipe_status": wipe_status,
                         "wipe_status_number": wipe_status_number,
                         "wipe_method": wipe_method,
                         "wipe_timestamp": wipe_timestamp})

        return hdds



    def parse_file(self, input_file_path) -> DeviceTemplate:
        devices = []
        with open(input_file_path, 'r') as file:
            reports = json.load(file)['PCProduct']
            for report in reports:
                if report.get("'A' Number") == "N/A":
                    self.logger.warning(f"{report.get('Serial Number')} does not have an A Number - skipping")
                    continue
                device = DeviceTemplate()
                device.location = report.get("Securaze User")
                device.comp = self.parse_comp(report)
                device.cpus = self.parse_cpus(report)
                device.hdds = self.parse_hdds(report)
                device.compile()
                devices.append(device)
        return devices


def main():
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

    # Create parser
    parser = Parser()

    # Parse each file in input directory
    for file in os.listdir(input_directory):
        input_file = f'{input_directory}{file}'
        if parser.can_parse(input_file):
            devices = parser.parse_file(input_file_path=input_file)

            # Export each device from the report
            # for device in devices:
            #     device.export(output_directory)
            # devices[0].export(output_directory)

        # Move file to archive
        #shutil.move(input_file, archive_directory)


if __name__ == "__main__":
    main()




    #print(parsed_dict)
