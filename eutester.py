# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import re
import paramiko
import boto
import random
from bm_machine import bm_machine

class eutester:
    def __init__(self, config_file="cloud.conf", host="clc", password="foobar", keypath=None):
        """  
        EUCADIR => $eucadir, 
        VERIFY_LEVEL => $verify_level, 
        TOOLKIT => $toolkit, 
        DELAY => $delay, 
        FAIL_COUNT => $fail_count, 
        INPUT_FILE => $input_file, 
        PASSWORD => $password }
        , credpath=None, timeout=30, exit_on_fail=0
        EucaTester takes 2 arguments to their constructor
        1. Configuration file to use
        2. Eucalyptus component to connect to [CLC NC00 SC WS CC00] or a hostname
        3. Password to connect to the host
        4. 
        """
        self.config_file = config_file        
        self.password = password
        self.keypath = keypath
        #self.starttime = time()
        self.credpath = None
        self.timeout = 30
        self.exit_on_fail = 0
        self.exit_on_fail = 0
        self.fail_count = 0
        ### Read input file
        config = self.read_config(config_file)
        self.eucapath = "/opt/eucalyptus"
        if "REPO" in config["machines"][0].source:
            self.eucapath="/"
        print config["machines"]
        ## CHOOSE A RANDOM HOST OF THIS COMPONENT TYPE
        if len(host) < 5:
            # Get a list of hosts with this role
            machines_with_role = [machine.hostname for machine in config['machines'] if host in machine.components]
            host = random.choice(machines_with_role)
            self.host = host
        ### SETUP SSH CLIENT
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())            
        if keypath == None:
            client.connect(host, username="root", password=password)
        else:
            client.connect(host,  username="root", keyfile_name=keypath)
        ### GET CREDENTIALS        
        admin_cred_dir = "eucarc-eucalyptus-admin"
        cmd_download_creds = self.eucapath + "/usr/sbin/euca_conf --get-credentials " + admin_cred_dir + "/creds.zip " + "--cred-user admin --cred-account eucalyptus" 
        cmd_setup_cred_dir = ["rm -rf " + admin_cred_dir,"mkdir " + admin_cred_dir ,  cmd_download_creds , "unzip " + admin_cred_dir + "/creds.zip -d " + admin_cred_dir, "ls " + admin_cred_dir]
        for cmd in cmd_setup_cred_dir:
            print cmd
            stdin, stdout, stderr = client.exec_command(cmd)
            print stdout.readlines() + stderr.readlines()
        ### read the input file and return the config object/hash whatever it needs to be
       
    def read_config(self, filepath):
        config_hash = {}
        machines = []
        f = None
        try:
            f = open(filepath, 'r')
        except IOError as (errno, strerror):
            print "Could not find config file " + self.config_file
            exit(1)
            #print "I/O error({0}): {1}".format(errno, strerror)
            
        for line in f:
            ### LOOK for the line that is defining a machine description
            line = line.strip()
            re_machine_line = re.compile("\s+".join(
                    ('(?:\d{1,3}\\.){3}\d{1,3}',  # IPv4
                     '\w+', '\w+', '\w+', '\w+', '\\[[^\\]]+\\]')))
            if re_machine_line.match(line):
                #print "Matched Machine :" + line
                machine_details = line.split(None, 5)
                machine_dict = {}
                machine_dict["hostname"] = machine_details[0]
                machine_dict["distro"] = machine_details[1]
                machine_dict["distro_ver"] = machine_details[2]
                machine_dict["arch"] = machine_details[3]
                machine_dict["source"] = machine_details[4]
                machine_dict["components"] = map(str.lower, machine_details[5].strip('[]').split())
                ### ADD the machine to the array of machine
                machine = bm_machine(machine_dict["hostname"], machine_dict["distro"], machine_dict["distro_ver"], machine_dict["arch"], machine_dict["source"], machine_dict["components"])
                machines.append(machine)
                print machine
            if line.find("NETWORK"):
                config_hash["network"] = line.strip()
        config_hash["machines"] = machines 
        return config_hash
    
    def fail(self, message):
        print "[TEST_REPORT] FAILED: " + message
        if self.exit_on_fail == 1:
            exit(1)
        else:
            return 0
        
    def test_name(self, message):
        print "[TEST_REPORT] " + message
    
    def set_config_file(self, filepath):
        self.config_file = filepath
    
    def get_config_file(self):
        return self.config_file
        
    def set_host(self, host):
        self.host = host
    
    def get_host(self):
        return self.host
    
    def set_credpath(self, path):
        self.credpath = path
    
    def get_credpath(self):
        return self.credpath
        
    def set_timeout(self, seconds):
        self.timeout = seconds
    
    def get_timeout(self):
        return self.timeout
            
    def set_eucapath(self, path):
        self.config_file = path
    
    def get_eucapath(self):
        return self.eucapath
    
    def set_exit_on_fail(self, exit_on_fail):
        self.exit_on_fail = exit_on_fail
    
    def get_exit_on_fail(self):
        return self.exit_on_fail
    
    def clear_fail_count(self):
        self.fail_count = 0
    
    def __str__(self):
        s  = "+++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        s += "+" + "Host:" + self.host + "\n"
        s += "+" + "Config File: " + self.config_file +"\n"
        s += "+" + "Fail Count: " +  str(self.fail_count) +"\n"
        s += "+" + "Eucalyptus Path: " +  str(self.eucapath) +"\n"
        s += "+" + "Credential Path: " +  str(self.credpath) +"\n"
        s += "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
        return s
 