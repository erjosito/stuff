# Created by Jose Moreno, josemor@cisco.com
#
# v0.1 (January 2015)
#
# This script was created as a part of a proof of concept, please don't expect
#    to see here Python best practices ;)
# You can find background info about why this script was created and how it
#    can be used here: http://erjosito.tumblr.com/post/110742308847/the-network-is-not-in-my-way
#
# - Monitors the CPU of a VM
# - If the CPU usage exceeds a predefined threshold, it deploys a new VM
# - The new VM gets an IP address over DHCP, the script reads it (over the
#   VMware tools) and adds it into the Web farm in an F5 BigIP ADC over the
#   ACI API
# - Native REST calls are used to interact with APIC, the Python SDK is a
#   future improvement possibility
# - When the CPU falls below the threshold, the VM is deleted and the IP address
#   removed from the BigIP farm.
#



from pysphere import VIServer, VIException
from pysphere.resources import VimService_services as VI
import time
import requests

def get_vm_ip(vm_name):
    try:
        vm = server.get_vm_by_name(vm_name)
        return vm.properties.guest.ipAddress
    except VIException:
        return None

def find_vm(vm_name):
    try:
        vm = server.get_vm_by_name(vm_name)
        return vm
    except VIException:
        return None

def get_vm_cpu(vm_name):
    try:
        vm = server.get_vm_by_name(vm_name)
        return vm.properties.summary.quickStats.overallCpuUsage
    except VIException:
        return None

def add_slb_vm(vm_name):
   # Make sure the template VM exists
   vm = server.get_vm_by_name('slb-web-template')
   if len(vm.get_property('name', from_cache=False))>0:
      print 'VM to clone found, OK to proceed'
   else:
      print 'No VM to clone found'
      server.disconnect
      sys.exit()

   # Clone VM
   newname = vm_name
   # Check whether vm already exists
   new_vm = find_vm(newname)
   if new_vm is None:
      print 'Cloning ' + newname
      vm.clone(newname, power_on=False)
   else:
      print newname + ' already found, not cloning'

   # Power on VM
   #print 'Powering on VMs'
   vmlist = server.get_registered_vms()
   for vmname in vmlist:
      if vmname.find(newname) > 0:
        if not vmname.endswith('slb-web-template.vmx'):
            vm = server.get_vm_by_path(vmname)
            vm.power_on()

def delete_vm(vm_name):
   vmlist = server.get_registered_vms()
   for vmname in vmlist:
      if vmname.find(vm_name) > 0:
         vm = server.get_vm_by_path(vmname)
         if vm.get_status() == 'POWERED ON':
            vm.power_off()
         request = VI.Destroy_TaskRequestMsg()
         _this = request.new__this(vm._mor)
         _this.set_attribute_type(vm._mor.get_attribute_type())
         request.set_element__this(_this)
         server._proxy.Destroy_Task(request)._returnval


def apic_login():
    # Login (POST http://10.1.6.120/api/aaaLogin.xml)
    try:
        r = requests.post(
            url="http://10.1.6.120/api/aaaLogin.xml",
            data = "<aaaUser name=\"admin\" pwd=\"C15co123!\" />"
        )
        return r.cookies
    except requests.exceptions.RequestException as e:
        print('Login HTTP Request failed')

def apic_new_tenant(apic_cookie):
    # Create tenant (POST http://10.1.6.120/api/node/mo/uni/tn-helloworld_REST.json)
    try:
        r = requests.post(
            url="http://10.1.6.120/api/node/mo/uni/tn-helloworld_REST.json",
            data = "{\"fvTenant\":{\"attributes\":{\"dn\":\"uni/tn-helloworld_REST\",\"name\":\"helloworld_REST\",\"rn\":\"tn-helloworld_REST\",\"status\":\"created\"},\"children\":[]}}",
            cookies = apic_cookie
        )
    except requests.exceptions.RequestException as e:
        print('Create tenant HTTP Request failed')


def apic_new_pool_member(apic_cookie):
    try:
        r = requests.post(
            url="http://10.1.6.120/api/node/mo/uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3.json",
            data = "{\"vnsFolderInst\":{\"attributes\":{\"dn\":\"uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3\",\"ctrctNameOrLbl\":\"WebServices\",\"graphNameOrLbl\":\"HTTP_LB\",\"nodeNameOrLbl\":\"ADC\",\"name\":\"S3\",\"key\":\"Member\",\"status\":\"created,modified\"},\"children\":[]}}",
            cookies = apic_cookie
        )
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed')

def apic_new_pool_ip (apic_cookie, ip):
    try:
        r = requests.post(
            url="http://10.1.6.120/api/node/mo/uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3/ParamInst-IPAddress3.json",
            data = "{\"vnsParamInst\":{\"attributes\":{\"dn\":\"uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3/ParamInst-IPAddress3\",\"name\":\"IPAddress3\",\"key\":\"IPAddress\",\"value\":\"" + ip + "\"},\"children\":[]}}",
            cookies = apic_cookie
        )
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed')


def apic_new_pool_port (apic_cookie):
    try:
        r = requests.post(
            url = "http://10.1.6.120/api/node/mo/uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3/ParamInst-Port3.json",
            data = "{\"vnsParamInst\":{\"attributes\":{\"dn\":\"uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3/ParamInst-Port3\",\"name\":\"Port3\",\"key\":\"Port\",\"value\":\"80\"},\"children\":[]}}",
            cookies = apic_cookie
        )
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed')

def apic_delete_pool_member (apic_cookie):
    try:
        r = requests.post(
            url = "http://10.1.6.120/api/node/mo/uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3.json",
            data = "{\"vnsFolderInst\":{\"attributes\":{\"dn\":\"uni/tn-F5-demo/ap-Web/epg-SLB-Web-servers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-LTM/FI_C-WebServices-G-HTTP_LB-F-ADC-N-WebServers/FI_C-WebServices-G-HTTP_LB-F-ADC-N-S3\",\"status\":\"deleted\"},\"children\":[]}}",
            cookies = apic_cookie
        )
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed')

if __name__ == '__main__':
   # Connect to vCenter
   server = VIServer()
   server.connect("10.70.1.237", "root", "vmware")

   # Variable to control whether we have deployed the VM or not
   vmsdeployed = 0

   # CPU threshold (MHz)
   cputhreshold = 2000

   # Name for new VM
   newvmname = "slb-web-03"

   # Endless loop
   while True:
     
     # Get VM CPU and deploy new VM if threshold is exceeded
     vm_cpu = get_vm_cpu("slb-web-02")
     if (vm_cpu > cputhreshold) and (vmsdeployed == 0):
        print "CPU %s over threshold %s, new VM to be created" % (vm_cpu,cputhreshold)
        add_slb_vm (newvmname)
        print "Waiting 90 seconds for the VM to boot"
        time.sleep (90)
        ipaddress = get_vm_ip (newvmname)
        # Configure new member in BigIp pool through ACI
        my_cookie = apic_login()
        apic_new_pool_member (my_cookie)
        apic_new_pool_ip (my_cookie, ipaddress) 
        apic_new_pool_port (my_cookie)

        vmsdeployed = vmsdeployed + 1
        print "New web server deployed into farm with IP %s" % ipaddress
     # If the CPU goes below threshold, delete VM
     if (vm_cpu < cputhreshold) and (vmsdeployed > 0):
        print "CPU %s under threshold %s, %s VM already created will be deleted" % (vm_cpu,cputhreshold,vmsdeployed)
        delete_vm("slb-web-03")
	vmsdeployed = vmsdeployed - 1
        my_cookie = apic_login()
        apic_delete_pool_member (my_cookie)
        print "Web server removed from farm"
     if (vm_cpu < cputhreshold) and (vmsdeployed == 0):
        print "CPU %s under threshold %s, no VM is created" % (vm_cpu,cputhreshold)
     if (vm_cpu > cputhreshold) and (vmsdeployed > 0):
        print "CPU %s over threshold %s, %s VM already created" % (vm_cpu,cputhreshold,vmsdeployed)

     # Wait
     time.sleep (10) 

   # Disconnect from vCenter
   server.disconnect

