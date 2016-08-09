__author__ = 'josemor'

# inspired by cpaggen, kudos go to Chris!
#
# deletes all UI-generated policies in APIC
# no warning, brutal!
#
# josemor

import cobra.mit.access
import cobra.mit.session
import cobra.mit.request
import cobra.model.fv
import sys
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.model.fv import Tenant
#from cobra.mit.request import DnQuery
#from cobra.mit.request import ConfigRequest
import sys


def apicLogin():
    # Connection and authentication
    apicUrl = 'http://1.2.3.4'
    loginSession = LoginSession(apicUrl, 'user', 'password')
    moDir = MoDirectory(loginSession)
    try:
        moDir.login()
    except:
        print("Login error (wrong username or password?)")
        exit(1)
    return moDir

def printNames(moDir):
    for x in moDir:
        try:
            if x.name:
                print "\t\t{}".format(x.name)
            else:
                print "\t\t{}".format(x)
        except AttributeError:
            continue

def deleteMo(moDir, moClass):
    usersToKeep = ['admin']
    print "Looking for existing {} ...".format(moClass)
    try:
        mo = moDir.lookupByClass(moClass)
        #print " --> found a total of {}".format(len(mo))
        #printNames(mo)
        for obj in mo:
            objMo = moDir.lookupByDn(obj.dn)
            try:
                if obj.name [:8] == '__ui_pps':
					objMo.delete()
					c = cobra.mit.request.ConfigRequest()
					c.addMo(objMo)
					moDir.commit(c)
					print "\t\t--> deleted {}".format(obj.dn)
            except AttributeError:
                # certain MOs (such as vnsMDev) don't have a 'name' property, but can still be deleted
                pass
    except:
        print "Error looking for class %s" % moClass


def main():
    moDir = apicLogin()
    moList = ['infraAccPortGrp', 'infraAccPortP', \
    'infraNodeP', 'infraAccBndlGrp', 'infraHPortS', 'cdpIfPol', 'lldpIfPol', 'lacpLagPol', 'lacpLagPol', \
    'infraAccNodePGrp', 'vpcInstPol', 'infraFexP']

    for mo in moList:
        deleteMo(moDir, mo)

if __name__ == '__main__':
    main()
