import requests
import json
import sys

def login():
    # Login (POST http://muc-apic.cisco.com/api/aaaLogin.xml)
    global login_cookies
    global apic_url
    global apic_usr
    global apic_pwd
    try:
        r = requests.post(
            url = apic_url + "api/aaaLogin.xml",
            data = "<aaaUser name=\"" + apic_usr + "\" pwd=\"" + apic_pwd + "\" />"
        )
        login_cookies = r.cookies
    except requests.exceptions.RequestException as e:
        print('Login HTTP Request failed')

def get_info ():
    # Create tenant (POST http://10.49.238.40/api/node/mo/uni/tn-helloworld_REST.json)
    global login_cookies
    global apic_url
    try:
		r = requests.get(
			url = apic_url + "api/node/class/faultSummary.json?order-by=faultSummary.severity|desc&page=0&page-size=15",
			cookies = login_cookies)
		json_obj = json.loads (r.text)
		numFaults = int(json_obj['totalCount'])
		#print "<table>"
		#print "<tr><td>Fault</td><td>Severity</td><td>Count</td></tr>"
		print "<tr><td>Fault</td><td>Severity</td></tr>"
		for i in range (0, numFaults-1):
			try:
				cause     = json_obj['imdata'][i]['faultSummary']['attributes']['cause']
				count     = json_obj['imdata'][i]['faultSummary']['attributes']['count']
				sev       = json_obj['imdata'][i]['faultSummary']['attributes']['severity']
				if i < 10:
					#print "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (sev, cause, count)
					print "<tr><td>%s</td><td>%s</td></tr>" % (cause[:11], sev)
			except:
				pass
		#print "</table>"
    except requests.exceptions.RequestException as e:
        print('Create tenant HTTP Request failed')
        
# Create cookie variable
login_cookies = ""

# Get CLI arguments
if (len(sys.argv) != 4):
	print "I need 3 arguments: url, user and password"
else:
	# Get arguments
	apic_url = sys.argv[1]
	apic_usr = sys.argv[2]
	apic_pwd = sys.argv[3]
	# Add trailing slash to url if not there
	if apic_url [len (apic_url) - 1] != "/":
		apic_url += "/"
	# Do what you need to do
	login ()
	get_info ()

