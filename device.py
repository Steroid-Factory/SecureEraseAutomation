from dataclasses import dataclass, field
import datetime
import os
import uuid
import logging
import secrets

# logging.basicConfig(filename='C:/secure_erase/export.log', level=logging.INFO,
#                     format='%(asctime)s %(levelname)s %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.FileHandler('C:/secure_erase/export.log')
handler.setFormatter(formatter)
logger.addHandler(handler)

@dataclass
class DeviceTemplate:

    _comp_vars: list = field(default_factory=list)
    _cpu_vars: list = field(default_factory=list)
    _hdd_vars: list = field(default_factory=list)
    _battery_vars: list = field(default_factory=list)
    _mem_vars: list = field(default_factory=list)
    location: str = field(default_factory=str)
    comp: dict = field(default_factory=dict)
    cpus: list = field(default_factory=list)
    hdds: list = field(default_factory=list)
    battery: dict = field(default_factory=dict)
    memory: dict = field(default_factory=dict)


    # def __post_init__(self):
    #     self.logger.setLevel(logging.INFO)
    #     formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    #     handler = logging.FileHandler('C:/secure_erase/export.log')
    #     handler.setFormatter(formatter)
    #
    #     self.logger.addHandler(handler)


    def compile(self):
        # UUID as Computer Id
        computer_id = str(uuid.uuid1()).upper()

        self._comp_vars = [self.location, computer_id, 'comp', '', self.comp.get('serial'), self.comp.get('memory'),
                     self.comp.get('manufacturer'), self.comp.get('model'), self.comp.get('barcode'),
                     self.comp.get('manufacturer'), '', '', self.comp.get('anumber'), '', '']

        for cpu in self.cpus:
            cpu_vars = [self.location, computer_id, 'cpu', cpu.get('id'), cpu.get('description'), cpu.get('cores'),
                        cpu.get('type_code'), cpu.get('speed'), cpu.get('model'), '', '', '', '', '', '']
            self._cpu_vars.append(cpu_vars)

        for hdd in self.hdds:
            hdd_vars = [self.location, computer_id, 'hd', hdd.get('id'), hdd.get('serial'), hdd.get('size'), '1',
                        hdd.get('wipe_status_number'), hdd.get('employee'), hdd.get('wipe_status'),
                        hdd.get('wipe_timestamp'), hdd.get('wipe_timestamp'),
                        hdd.get('type'), hdd.get('wipe_method'), '']
            self._hdd_vars.append(hdd_vars)

        self._battery_vars = [self.location, computer_id, 'bat', 'bat', '', '', '', self.battery.get('status'),
                              '', '', '', '', '', '', self.battery.get('health')]

        self._mem_vars = [self.location, computer_id, 'mem', 'mem', self.memory.get('capacity'),
                          self.memory.get('type'), '', '', '', '', '', '', '', '']

    def export(self, file_dir: str) -> None:
        if os.path.exists(file_dir):
            # Create file name with unique name.txt
            file_name = f'SE_{datetime.date.today().strftime("%m-%d-%Y")}_{secrets.token_hex(8)}.txt'

            with open(f'{file_dir}{file_name}', 'w') as file:
                # Write out all the comp elements into one line
                file.write('\t'.join(f'"{x}"' for x in self._comp_vars))
                file.write('\n')
                # For each cpu
                for cpu in self._cpu_vars:
                    # Write out all the cpu elements into one line
                    file.write('\t'.join(f'"{x}"' for x in cpu))
                    file.write('\n')
                # For each hdd
                for hdd in self._hdd_vars:
                    # Write out all the hdd elements into one line
                    file.write('\t'.join(f'"{x}"' for x in hdd))
                    file.write('\n')

                # Write out all the comp elements into one line
                file.write('\t'.join(f'"{x}"' for x in self._battery_vars))
                file.write('\n')

                # Write out all the comp elements into one line
                file.write('\t'.join(f'"{x}"' for x in self._mem_vars))
                file.write('\n')

            logger.info(f"Created file {file_name} with "
                         f"Serial Number: '{self._comp_vars[4]}' and "
                         f"Barcode: '{self._comp_vars[8]}' and "
                         f"Computer Id: '{self._comp_vars[1]}'")