import requests
import json
import sys

login_cookies = 0

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

def get_info():
    # Create tenant (POST http://10.49.238.40/api/node/mo/uni/tn-helloworld_REST.json)
    global login_cookies
    global apic_url
    try:
		r = requests.get(
			url = apic_url + "api/node/class/topSystem.json?rsp-subtree-include=health",
			cookies = login_cookies
		)
		json_obj = json.loads (r.text)
		numNodes = int(json_obj['totalCount'])
		print "<table width='100%%' id='healthtable'>"
		print "<thead><tr><th>Switch name</th><th>Health</th></tr></thead>"
		for i in range (0, numNodes-1):
			name   = json_obj['imdata'][i]['topSystem']['attributes']['name']
			role   = json_obj['imdata'][i]['topSystem']['attributes']['role']
			if role != "controller":
				health = json_obj['imdata'][i]['topSystem']['children'][0]['healthInst']['attributes']['twScore']
				healthnum = int (health)
				if (health > 90):
					print "<tr><td>%s</td><td align='right'>%s</td></tr>" % (name, health)
				else:
					print "<tr><td>%s</td><td align='right'>%s</td></tr>" % (name, health)
		print "</table>"
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
