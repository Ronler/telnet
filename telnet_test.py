import telnetlib
import time
import re
import openpyxl
import os.path
import webbrowser


user = 'admin'
password = 'cisco'
timeout = 1
tn = None

def to_bytes(line):
    return f"{line}\n".encode("ascii")

def add_to_dict(lst):
    new_lst = []
    for l in lst:
        new_lst.append(l[2]) 
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
                self.sheet['{}{}'.format(self.columns[col-1], i)] = item
                self.sheet['F{}'.format(i)] = "Cisco Systems"
                self.sheet['G{}'.format(i)] = image
                i+=1

    def save_excel(self):

        self.save_name ='targa_invenotry.xlsx'
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


    def connect(self, ip, port):
        
        print("Connecting to " + str(self.ip) + " on port " + str(self.port) + '...')
        try:
            tn = telnetlib.Telnet(self.ip, self.port)
        except:
            print('Could not connect. Exiting') 

        print("Connected to " + str(self.ip) + " on port " + str(self.port) + '...')
        time.sleep(3)

        tn.write(user.encode('ascii') + b"\n")
        login_match_u = re.compile(b'Username:')
        login_match_pw = re.compile(b'Password:')
        login_match_prompt =re.compile(b'#')

        # Reduce timeout from 5 Seconds if needed
        login_info = tn.expect([login_match_u , login_match_pw , login_match_prompt],timeout=1)

        print("Logging into router...")
        
        if login_info[0] == 0 :
            if password:
                tn.read_until(b"Password: ")
                tn.write(password.encode('ascii') + b"\n")
                tn.read_until(b"#",timeout)
        elif login_info[0] == 1 :
            tn.write(password.encode('ascii') + b"\n")
            tn.read_until(b"#",timeout)
        elif login_info[0] == 2 :
            print("Already logged in!")
        else :
            print("I did not find what I was looking for")
            exit()

        tn.write(b"\r\n")

        tn.write(b"term length 0\n")
        tn.read_until(b"#",5).decode('ascii')
        return (tn)
    
    def send_commands(self, cmd):    

        time.sleep(3)
        self.sw.write(to_bytes(cmd))
        output2 = self.sw.read_until(b'#')
        
        self.output += output2.decode("ascii")

    def grab_info(self):
        
        version_regex = re.compile(r'NXOS:\sversion\s(\d.\w.{3})')
        serial_regex = re.compile(r'(serial|Serial|SN:)(\snumber\sis)?\s(\w.*)')
        model_regex = re.compile(r'(Model\snumber|PID:|type)(\sis)?\s(\w{3,4}\-\w{2,8}\-\w{1,5}(\-\w{1,3})?)')
        part_regex = re.compile(r'(PN:|Part\sNumber|cisco\spart\snumber)(\sis)?\s(\w.*)')
        descr_regex = re.compile(r'([^cable]\stype\sis|Module\stype\sis\s:)(\s?:)?\s\"?(\w.*)(?<!\")')
        hw_ver_regex = re.compile(r'(HWVER:|H/W\sversion|revision)(\sis)?\s(\w.*)')
        ver_id_regex = re.compile(r'(VID:|Part\sRevision|cisco\sversion\sid)(\sis)?\s(\w.*)')

        self.version = version_regex.findall(self.output)[0]
        self.my_dict["PID"] = add_to_dict(model_regex.findall(self.output))
        self.my_dict["Description"] = add_to_dict(descr_regex.findall(self.output))
        self.my_dict["Serial Number"] = add_to_dict(serial_regex.findall(self.output))
        self.my_dict["Part Number"] = add_to_dict(part_regex.findall(self.output))
        self.my_dict["Hardware Rev"] = add_to_dict(hw_ver_regex.findall(self.output))
        self.my_dict["Firmware Rev"] = add_to_dict(ver_id_regex.findall(self.output))
        
        self.sw.close()

    def get_hardware(self):
        self.send_commands('show hardware')

    def get_interfaces(self):
        self.send_commands('show int trans')
    
    def get_fans(self):
        self.send_commands('show inv | include Fan')
        self.send_commands('show inv | include FAN')


if __name__ == '__main__':

    print("This script grabs inventory from an Nexus chassis and inputs to an excel sheet")
    print("Default login is admin/cisco")
    print("Please have samplesbinaryfile.xlsx in same directory")

    ip_add = input('Terminal server ip address: ')
    port_num = input("Port number: ")
    
    switch1 = Switch(ip_add, port_num)
    inv_excel = Excel()

    switch1.get_hardware()
    switch1.get_interfaces()
    switch1.get_fans()
    switch1.grab_info()

    inv_excel.add_to_excel(switch1.my_dict, switch1.version)
    inv_excel.save_excel()

    print("Excel sheet is complete. Opening file location.")
    webbrowser.open(inv_excel.file_path.strip(inv_excel.save_name))

