from __future__ import print_function
import datetime
import requests
import simplejson

def csplogin(tenantId, appId, appSecret):
    url = 'https://login.windows.net/'+ tenantId + '/oauth2/token'
    data = 'grant_type=client_credentials&resource=https%3A%2F%2Fgraph.windows.net&client_id=' + appId + '&client_secret=' + appSecret
    response = requests.post(url, data=data)
    if response.status_code == 200:
        jsonResponse = response.json()
        token = jsonResponse['access_token']
        return token
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def armlogin(tenantId, appId, appSecret):
    url = 'https://login.microsoftonline.com/'+ tenantId + '/oauth2/token?api-version=1.0'
    data = 'grant_type=client_credentials&resource=https%3A%2F%2Fmanagement.azure.com%2F&client_id=' + appId + '&client_secret=' + appSecret
    response = requests.post(url, data=data)
    if response.status_code == 200:
        jsonResponse = response.json()
        token = jsonResponse['access_token']
        return token
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def cspGetTenantId(token, customerName):
    url = 'https://api.partnercenter.microsoft.com/v1/customers'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        customers = jsonResponse["items"]
        for cust in customers[:]:
            if cust['companyProfile']['companyName'] == customerName:
                return cust['companyProfile']['tenantId']
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def cspGetCustomerId(token, customerName):
    url = 'https://api.partnercenter.microsoft.com/v1/customers'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        customers = jsonResponse["items"]
        for cust in customers[:]:
            if cust['companyProfile']['companyName'] == customerName:
                return cust['id']
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def getCustomerList(token):
    url = 'https://api.partnercenter.microsoft.com/v1/customers'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        myList = []
        jsonResponse = simplejson.loads(response.text)
        customers = jsonResponse["items"]
        for cust in customers[:]:
            myList.append({'id': cust['id'], 'name': cust['companyProfile']['companyName']})
            # DEBUG:
            #print (cust['companyProfile']['companyName'])
        return myList
    else:
        print ("Error: RETURN CODE " + str(response.status_code))


def getSubscriptions(token, customerId, onlyAzure=True):
    url = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        #if jsonResponse['totalCount'] > 1:
        #    print ("WARNING, " + str(jsonResponse['totalCount']) + ' subscriptions found for that customer')
        myList = []
        subs = jsonResponse["items"]
        for sub in subs[:]:
            if (not onlyAzure) or (sub['offerName'] == 'Microsoft Azure'):
                myList.append({'id': sub['id'], 'name': sub['friendlyName']})
        return myList
        #return subs[0]['id']
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def getResourceConsumption(token, customerId, subscriptionId, myDict):
    url = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions/' + subscriptionId + '/usagerecords/resources'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        myList = []
        jsonResponse = simplejson.loads(response.text)
        records = jsonResponse["items"]
        #print str(jsonResponse['totalCount']) + " resource usage records found"
        for record in records[:]:
            if record['totalCost'] > 0:
                resourceId = record['resourceId'].lower()
                resourceUri = getResourceUri(myDict, resourceId)
                myList.append({"category": record['category'], 'subcategory': record['subcategory'], 'resourceId': resourceId, 'resourceUri': resourceUri})
                #print ('%20s %20s %10s %15s %30s' % (record['category'], record['subcategory'], record['totalCost'], resourceId, resourceUri))
        return myList
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def getConsumptionSummary(token, customerId):
    url = 'https://api.partnercenter.microsoft.com/v1/customers/{{CustomerId}}/subscriptions/{{SubscriptionId}}/usagesummary'
    # First browse all subscriptions
    url = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        myList = []
        jsonResponse = simplejson.loads(response.text)
        subs = jsonResponse["items"]
        for sub in subs[:]:
            subscriptionId = sub['id']
            url2 = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions/' + subscriptionId + '/usagesummary'
            response2 = requests.get(url2, headers=headers)
            jsonResponse2 = simplejson.loads(response2.text)
            totalCost = 0
            try:
                totalCost = jsonResponse2['totalCost']
                myList.append({'subscriptionId': subscriptionId.lower(), 'totalCost': totalCost})
                #print (subscriptionId + ": " + str(totalCost))
            except:
                pass
        return myList
    else:
        print("Error: RETURN CODE " + str(response.status_code))


def cspGetResourceUri(token, customerId, subscriptionId, resourceGuid):
    # This function makes API calls per each customer ID
    # It is much more efficient building once a "translation dictionary", so that not so many REST calls are made
    url = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions/' + subscriptionId + '/utilizations/azure'
    now = datetime.datetime.now()
    day1 = str(now.year) + '-' + str(now.month) + '-01'
    dayn = str(now.year) + '-' + str(now.month) + '-28'
    timeFilter = '?start_time=' + day1 + 'T00%3a00%3a00%2b00%3a00&end_time=' + dayn + 'T23%3a59%3a59%2b00%3a00'
    otherOptions = '&granularity={granularity}&show_details=True&size=100'
    url = url + timeFilter + otherOptions
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        records = jsonResponse["items"]
        for record in records[:]:
            resourceId = ''
            try:
                resourceId = record['resource']['id']
            except:
                print ('Error when evaluating record')
                pass
            if resourceId == resourceGuid:
                return record['instanceData']['resourceUri']
    else:
        print ("Error: RETURN CODE " + str(response.status_code))

def buildResourceDict(token, customerId, subscriptionId):
    url = 'https://api.partnercenter.microsoft.com/v1/customers/' + customerId + '/subscriptions/' + subscriptionId + '/utilizations/azure'
    now = datetime.datetime.now()
    day1 = str(now.year) + '-' + str(now.month) + '-01'
    dayn = str(now.year) + '-' + str(now.month) + '-28'
    timeFilter = '?start_time=' + day1 + 'T00%3a00%3a00%2b00%3a00&end_time=' + dayn + 'T23%3a59%3a59%2b00%3a00'
    otherOptions = '&granularity={granularity}&show_details=True&size=100'
    url = url + timeFilter + otherOptions
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        myDict = []
        records = jsonResponse["items"]
        # DEBUG:
        #print "Total records in resource consumption data: " + str(len(records))
        counter = 0
        for record in records[:]:
            counter += 1
            resourceId = ""
            resourceUri = ""
            resourceTags = []
            try:
                resourceId = record['resource']['id'].lower()
                resourceUri = record['instanceData']['resourceUri']
                resourceTags = record['instanceData']['tags']
            except:
                pass
            # DEBUG:
            #print 'Record ' + str(counter) + ' info: ' + resourceId + ', ' + resourceUri + ', ' + json.dumps(resourceTags)
            if not inDict(myDict, resourceId):
                myDict.append({"id": resourceId, "uri": resourceUri, "tags": resourceTags})
    return myDict

def inDict(myDict, id):
    for item in myDict[:]:
        if item['id'] == id:
            return True
    return False

def getResourceUri(myDict, id):
    for item in myDict[:]:
        if item['id'] == id:
            return item['uri']
    return 'URI not found'

def getResourceGroups(token, subscriptionId):
    url = 'https://management.azure.com/subscriptions/' + subscriptionId + '/resourcegroups?api-version=2016-09-01'
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jsonResponse = simplejson.loads(response.text)
        groups = jsonResponse["value"]
        myGroups = []
        for group in groups[:]:
            myGroups.append({'id': group['id'], 'name': group['name'], 'location': group['location']})
        return myGroups
    elif response.status_code == 401:
        jsonResponse = simplejson.loads(response.text)
        try:
            code = jsonResponse['error']['code']
        except:
            pass
        print('Error: RETURN CODE ' + str(response.status_code) + ' (Unauthorized): ' + code + '. You may have to define a service principal in this tenant?')
        return []
    else:
        print("Error: RETURN CODE " + str(response.status_code))

def printList(myList, widthList=None):
    # Print title, taking the keys of the first row
    index = 0
    for key in myList[0]:
        thisWidth = 20  # Default width if widthList not specified or incorrect
        if not widthList is None:
            try:
                thisWidth = widthList[index]
            except:
                pass
        print('{:{width}.{truncate}}'.format(key, width=thisWidth, truncate=thisWidth-1), end='')
        index += 1
    print('')
    # Print data
    for item in myList[:]:
        index = 0
        for key in item:
            thisWidth = 20  # Default width if widthList not specified or incorrect
            if not widthList is None:
                try:
                    thisWidth = widthList[index]
                except:
                    pass
            if isinstance(item[key], float):
                itemString = "{:.2f}".format(item[key])
            elif isinstance(item[key], int):
                itemString = str(item[key])
            else:
                itemString = item[key]
            print('{:{width}.{truncate}}'.format(itemString, width=thisWidth, truncate=thisWidth-1), end='')
            #print '{:{width}}'.format(item[key], width=thisWidth)
            index += 1
        print ('')


def main():
    # Variable initialization
    cspTenantId = "Put your CSP tenant ID here"
    appId = "Put your Web Application client ID here, you can get it out of the Partner Center"
    appSecret = "Put your application key here, you can generate new app keys in Partner Center if you dont know the key for your app"
    customerName = 'Example customer name, you can get it out of the customer list that will be printed below'

    # Get a CSP token
    token = csplogin(cspTenantId, appId, appSecret)
    
    # Find out information
    tenantId = cspGetTenantId(token, customerName)
    customerId = cspGetCustomerId(token, customerName)
    
    # Get a customer list
    customerList = getCustomerList(token)
    if customerList:
        print('CUSTOMER LIST:')
        printList(customerList, [45, 40])

    # Get a list of the subscriptions for the customer
    subscriptionList = getSubscriptions(token, customerId)
    if subscriptionList:
        print('SUBSCRIPTION LIST FOR ' + customerName + ':')
        printList(subscriptionList, [45, 50])

    # Get consumption per subscription for a given customer
    consumptionSummary = getConsumptionSummary(token, customerId)
    if consumptionSummary:
        print('CONSUMPTION SUMMARY FOR ' + customerName + ':')
        printList(consumptionSummary, [10, 45])

    # Set the subscription to the first Azure subs with consumption
    subscriptionId = consumptionSummary[0]['subscriptionId']

    # Get consumption by resource. Build a dictionary that gives additional info
    #   for each resource ID (or resource GUID, properly said)
    myDict = buildResourceDict(token, customerId, subscriptionId)
    # DEBUG DICTIONARY
    #printList (myDict, [50, 45, 50])
    resourceConsumption = getResourceConsumption(token, customerId, subscriptionId, myDict)
    if resourceConsumption:
        print('RESOURCE CONSUMPTION SUMMARY FOR ' + customerName + ', SUBSCRIPTION ID ' + subscriptionId + ':')
        printList(resourceConsumption, [10, 45, 20, 50])

    # Getting information out of the ARM API
    armTenantToken = armlogin(tenantId, appId, appSecret)
    armResourceGroups = getResourceGroups(armTenantToken, subscriptionId)
    if armResourceGroups:
        print('EXISTING RESOURCE GROUPS FOR ' + customerName + ', SUBSCRIPTION ID ' + subscriptionId + ':')
        printList(armResourceGroups)

    # Good bye
    print ("PRINTED RESULTS from customer " + customerName + ', tenant ID: ' + tenantId + ', Subscription ID: ' + subscriptionId)

if __name__ == '__main__': main()
