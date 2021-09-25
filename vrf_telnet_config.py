import telnetlib
import time
import re
import getpass

user = getpass.getuser()
vrf_config = open('vrf_config.txt', 'w')

user = #username you set
password = #password you set
timeout = 1
tn = None

def to_bytes(line):
    return f"{line}\n".encode("ascii")
    
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
            exit()

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
                tn.read_until(b"#",timeout=2)
                print("Logged in!")
        elif login_info[0] == 1 :
            tn.write(password.encode('ascii') + b"\n")
            tn.read_until(b"#",timeout=2)
            print("Logged in!")
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
        self.sw.write(to_bytes(cmd))
        output2 = self.sw.read_until(b'#', 5)
        self.output += output2.decode('ascii')
    
    def show_interfaces(self):
        self.send_commands('show ipv4 int br')
        self.send_commands('\r')

    def close_connection(self):
        self.sw.close()

    def get_ports(self):
        ports_regex = re.compile(r'\w.*0/\d/\d/\d{1,2}') 
        self.ports = ports_regex.findall(self.output)
        
        num_vrfs = len(self.ports)//2
        vrf, k, f = 1,1,1
        while f <= num_vrfs:
            vrf_config.write("!\nvrf vrf{}\n".format(f))
            vrf_config.write(" address-family ipv4 unicast\n !\n")
            f+=1
        
        for i in range(len(self.ports)):
            if i == 0:
                vrf_config.write("!\ninterface {}\n".format(self.ports[i]))
                vrf_config.write(" mtu 9216\n")
                vrf_config.write(" vrf vrf{}\n".format(k))
                vrf_config.write(" ipv4 address {}.1.1.1 255.255.255.0\n".format(k))
                vrf_config.write("!\ninterface {}\n".format(self.ports[i+1]))
                vrf_config.write(" mtu 9216\n")
                vrf_config.write(" vrf vrf{}\n".format(num_vrfs))
                vrf_config.write(" ipv4 address {}.1.1.1 255.255.255.0\n".format(num_vrfs+1))
                k+=1
            elif i == 1:
                pass

            elif i%2 == 0:
                vrf_config.write("!\ninterface {}\n".format(self.ports[i]))
                vrf_config.write(" mtu 9216\n")
                vrf_config.write(" vrf vrf{}\n".format(k-1))
                vrf_config.write(" ipv4 address {}.1.1.1 255.255.255.0\n".format(k))
                
            
            elif i%2 != 0:
                vrf_config.write("!\ninterface {}\n".format(self.ports[i]))
                vrf_config.write(" mtu 9216\n")
                vrf_config.write(" vrf vrf{}\n".format(k))
                vrf_config.write(" ipv4 address {}.1.1.2 255.255.255.0\n".format(k))
                k+=1
        
        vrf_config.write("!\nrouter static\n")
        while vrf <= num_vrfs:
            if vrf == 1:
                vrf_config.write("  vrf vrf{}\n".format(vrf))
                vrf_config.write("   address-family ipv4 unicast\n")
                vrf_config.write("    {}.1.1.0/24 2.1.1.2\n   !\n  !\n".format(num_vrfs+1))
            elif vrf == num_vrfs:
                vrf_config.write("  vrf vrf{}\n".format(vrf))
                vrf_config.write("   address-family ipv4 unicast\n")
                vrf_config.write("    1.1.1.0/24 {}.1.1.1\n   !\n  !\n !\n".format(vrf))
            else:
                vrf_config.write("  vrf vrf{}\n".format(vrf))
                vrf_config.write("   address-family ipv4 unicast\n")
                vrf_config.write("    1.1.1.0/24 {}.1.1.1\n".format(vrf))
                vrf_config.write("    {}.1.1.0/24 {}.1.1.2\n   !\n  !\n".format(num_vrfs+1, vrf+1))
            vrf+=1
            
if __name__ == '__main__':

    print("Trying to get ports for VRF config")

    ip_add = input('Terminal server ip address: ')
    port_num = input("Port number: ")
    
    switch1 = Switch(ip_add, port_num)
    switch1.show_interfaces()
    switch1.get_ports()
    switch1.close_connection()
    vrf_config.close()
    
    print("VRF config saved on Desktop as vrf_config.txt")  

