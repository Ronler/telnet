num_of_ports = int(input("How many ports on the chassis? "))
vlan_config = open("vlan_config.txt", 'w')
vlan_config.write('conf t\n')
vlan_config.write('')
i=1
vlan=10
while i < num_of_ports:
    if i == 1:
        vlan_config.write("int e1/{}, e1/{}\n".format(i, i+2))
        vlan_config.write("vlan {}\n".format(vlan))
        i+=3
        vlan+=1
    else:
        vlan_config.write("int e1/{}-{}\n".format(i, i+1))
        vlan_config.write("vlan {}\n".format(vlan))
        i+=2
        vlan+=1

vlan_config.write("int e1/{}, e1/{}\n".format(num_of_ports, 2))
vlan_config.write("vlan {}\n".format(vlan))
print("Complete!")
vlan_config.close()
input("Open the text file and copy paste to system.")