import telnetlib
import time
import re
import openpyxl
import os.path
import webbrowser
from os.path import exists as file_exists

has_samples_file = file_exists('samplesbinaryfile.xlsx')

user = 'root'
password = 'lab123'
timeout = 3
tn = None

module_types = {'TR-PY85S-NCI' : '10-3227-01',
                'FTLF8536P4BCL-C1' : '10-3227-01',
                'FTLF8536P4PCL-C1' : '10-3227-01',
                'TR-FC85S-NC2' : '10-3142-03',
                'TRD5H10ENF-LF030' : '10-3321-01',
                'FTCD4313E1PCL-C1' : '10-3321-01',
                'FCBN425QE1C01-C1' : '10-3172-01',
                'TRD5H11PNF-MF030' : '10-3510-01',
                'QTA1C04L2CCISE2G' : '10-3146-02'
                }

def to_bytes(line):
    return f"{line}\n".encode("ascii")

def add_to_dict(lst):
    new_lst = []
    for l in lst:
        new_lst.append(l) 
    return new_lst

def add_to_dict_part0(lst):
    new_lst = []
    for l in lst:
        new_lst.append(l[0]) 
    return new_lst

def add_to_dict_part1(lst):
    new_lst = []
    for l in lst:
        new_lst.append(l[1]) 
    return new_lst

class Excel :

    def __init__(self):
        
        self.inv_file = "samplesbinaryfile.xlsx"
        self.workbook = openpyxl.load_workbook(self.inv_file)
        self.sheet = self.workbook.active
        self.columns = ['A','B','C','D','E','H']

    def add_to_excel(self, add_dict, image):

        self.dict = add_dict
        col = 0
        for key, value in self.dict.items():
            col+=1
            i=2
            for item in value:
                if item in module_types:
                    item = module_types[item]
                self.sheet['{}{}'.format(self.columns[col-1], i)] = item
                self.sheet['F{}'.format(i)] = "Cisco Systems Inc."
                self.sheet['G{}'.format(i)] = image
                i+=1

    def save_excel(self):

        self.save_name ='targa_inventory.xlsx'
        self.current_directory = os.getcwd()
        self.file_path = os.path.join(self.current_directory,self.save_name)
        self.workbook.save(self.file_path)

        #Closing the workbook
        self.workbook.close()

class Switch:

    def __init__(self, ip, port):

        self.ip = ip
        self.port = port
        self.sw = self.connect(self.ip, self.port)
        self.output = ''
        self.my_dict = {}
        self.version = ''
        self.output2 = ''


    def connect(self, ip, port):
        
        print("Connecting to " + str(self.ip) + " on port " + str(self.port))
        try:
            tn = telnetlib.Telnet(self.ip, self.port)
        except:
            print('Could not connect. Exiting') 
            quit()

        print("Connected to " + str(self.ip) + " on port " + str(self.port))
        time.sleep(3)

        tn.write(user.encode('ascii') + b"\n")
        login_match_u = re.compile(b'Username:')
        login_match_pw = re.compile(b'Password:')
        login_match_prompt =re.compile(b'ios#')

        # Reduce timeout from 5 Seconds if needed
        login_info = tn.expect([login_match_u , login_match_pw , login_match_prompt],timeout)

        print("Logging into router...")
        
        if login_info[0] == 0 :
            if password:
                tn.read_until(b"Password: ")
                tn.write(password.encode('ascii') + b"\n")
                tn.read_until(b"ios#",timeout)
        elif login_info[0] == 1 :
            tn.write(password.encode('ascii') + b"\n")
            tn.read_until(b"ios#",timeout)
        elif login_info[0] == 2 :
            print("Already logged in!")
        else :
            print("I did not find what I was looking for")
            #exit()

        tn.write(b"\r\n")
        tn.read_until(b'ios#', timeout).decode('ascii')
        tn.write(b"term length 0\n")
        tn.read_until(b"ios#").decode('ascii')
        return (tn)
    
    def send_commands(self, cmd):    

        
        self.sw.write(to_bytes(cmd))
        time.sleep(3)
        self.output2 = self.sw.read_until(b'ios#')
        
        self.output += self.output2.decode("ascii").replace('\r', '')
        #print(self.output)

    def grab_info(self):

        version_regex = re.compile(r'Software,\sVersion\s(\w.*)')
        serial_regex = re.compile(r'(PCB\s)?Serial\sNumber\s*\:\s(\w.*)')
        pid_regex = re.compile(r'(P|Product\s)ID\s*\:\s(\w{2,4}\-?\.?\w{2,8}(\-\w{1,5}(\-\w{1,6})?)?)')
        part_regex = re.compile(r'Part\sNumber\s*:\s(\w{2,}\-\w{2,6}(\-\w{2,5})?)')
        descr_regex = re.compile(r'IDPROM\s\-\s(\w.*)')
        hw_ver_regex = re.compile(r'(Top\sAssy.\sRevision|H\/W\sVersion)\s*\:\s(\w.*)')
        ver_id_regex = re.compile(r'(VID|Version\sIdentifier)\s*\:\s(\w.*)')

        self.version = version_regex.findall(self.output)[0]
        self.my_dict["PID"] = add_to_dict_part1(pid_regex.findall(self.output))
        self.my_dict["Description"] = add_to_dict(descr_regex.findall(self.output))
        self.my_dict["Serial Number"] = add_to_dict_part1(serial_regex.findall(self.output))
        self.my_dict["Part Number"] = add_to_dict_part0(part_regex.findall(self.output))
        self.my_dict["Hardware Rev"] = add_to_dict_part1(hw_ver_regex.findall(self.output))
        self.my_dict["Firmware Rev"] = add_to_dict_part1(ver_id_regex.findall(self.output))

        self.sw.close()

    def get_hardware(self):
        self.send_commands('show version')

    def get_interfaces(self):
        self.send_commands('show diag | e CLEI')
    
    def test(self):
        self.send_commands('/r')


if __name__ == '__main__':

    print("Default login is root/lab123")
    print("Please have samplesbinaryfile.xlsx in the same directory")
    
    while has_samples_file == False:
        input("You dont have samples file in same folder")
        has_samples_file = file_exists('samplesbinaryfile.xlsx')
        

    print("Lets begin.")

    while True:
        try:
            ip_add, port_num = input('Terminal server ip address and port: ').split()
            
            switch1 = Switch(ip_add, port_num)
            inv_excel = Excel()

            switch1.get_hardware()
            switch1.get_interfaces()
            switch1.test()
            switch1.grab_info()

            inv_excel.add_to_excel(switch1.my_dict, switch1.version)
            inv_excel.save_excel()

            input("Excel sheet is complete. Opening file location")
            webbrowser.open(inv_excel.file_path.strip(inv_excel.save_name))
            quit()

        except KeyboardInterrupt:
            print("\nAborting...")
            quit()

        except ValueError:
            print("You need to input ip address followed by port number")
            pass

    

