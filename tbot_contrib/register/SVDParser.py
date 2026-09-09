import os
import xml.etree.ElementTree as ET
import pickle
import register
from register import Register
class SVDParser:
    def __init__(self):
        self._groups_dict ={}
        self._registers_dict = {}
    
    def parse_file(self, file_name:str, output_name:str) -> None:
        THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
        file_name = os.path.join(THIS_FOLDER, f"{file_name}")
        output_name = os.path.join(THIS_FOLDER, f"{output_name}.pkl")
        tree = ET.parse(file_name)
        root = tree.getroot()

        cpu_width = int(root.find("width").text)
        print(cpu_width)
        for peripherals in root.findall("peripherals"):
            
            for peripheral in peripherals.findall("peripheral"):
                group_name= peripheral.find("name").text
                base_address = int(peripheral.find("baseAddress").text,16)
                print(hex(base_address))
                self._groups_dict[group_name]= []
                for registers in peripheral.findall("registers"):
                    for register in registers.findall("register"):
                        register_name = register.find("name").text
                        register_width = int(register.find("size").text)
                        register_address = base_address + int(register.find("addressOffset").text,16)
                        print(hex(register_address))
                        self._registers_dict[register_name] = Register(register_name,register_address,register_width)
                        self._groups_dict[group_name].append(register_name)

        with open(f"{output_name}", "wb") as f:
            pickle.dump([cpu_width, self._groups_dict, self._registers_dict], f)
