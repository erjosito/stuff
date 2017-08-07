#!/bin/bash
# Script to update a record in Azure DNS to match the current public IP address
# See the blog post here for a detailed explanation:
# https://1138blog.wordpress.com/2017/08/07/dynamic-dns-with-azure-dns-and-a-bash-script/

# Tenant ID
tenantId="here the GUID for your Azure tenant"
# Azure AD App ID
appId="here the GUID for an AD app you created, with access to your DNS resource"
# Azure AD App Secret
appSecret="here the secret you configured for the app above"
# Azure resource group name where your DNS zone is configured
rgName="resourceGroupName"
# DNS zone name
zoneName="yourdomain.com"
# Existing A record-set name in your DNS zone
recordsetName="mydyndns"
# Prefix that will be searched to verify whether you are on the right network
localLANprefix="192.168.0"

# FQDN
fqdn=$recordsetName.$zoneName

# Verify 'dig' is there
digPath=$(which dig)
if [[ -z $digPath ]]
then
    echo "dig does not seem to be installed, but it is required for this script"
    exit 1
fi

# Verify 'ip' is there
ipPath=$(which ip)
if [[ -z $ipPath ]]
then
    echo "ip does not seem to be installed, but it is required for this script"
    exit 1
fi

# Verify whether we are in the local network
onLocalLAN=$(ip a | grep 192.168.2)

if [[ -n $onLocalLAN ]] 
then

    # Get public IP from ifconfig.co
    myPublicIp=$(curl ifconfig.co 2>/dev/null)
    if [[ $myPublicIp =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]
    then
        echo "The current public IP seems to be $myPublicIp"
    else
        echo "No valid current IP address could be retrieved"
        exit 1
    fi

    # Get existing public IP from DNS
    myDnsIp=$(dig $fqdn | grep ^$fqdn | awk '{print $5}' 2>/dev/null)
    if [[ $myDnsIp =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]
    then
        echo "The current address associated with $fqdn is $myDnsIp"
    else
        echo "No valid IP address association with $fqdn could be retrieved"
        exit 1
    fi

    if [ $myPublicIp == $myDnsIp ]
    then
        echo "DNS IP up to date, nothing to be done"
    else
        echo "Current public IP address $myPublicIp different from DNS IP address $myDnsIp, proceeding to update DNS"
        # Login to Azure
        az login --service-principal --tenant $tenantId --username $appId --password $appSecret >/dev/null 2>&1
        # Configure default resource group to rgName
        az configure --defaults group=$rgName >/dev/null 2>&1
        # Remove old record from record-set
        az network dns record-set a remove-record -n $recordsetName -z $zoneName --ipv4-address $myDnsIp >/dev/null 2>&1
        # Add new record to the record-set
        az network dns record-set a add-record -n $recordsetName -z $zoneName --ipv4-address $myPublicIp >/dev/null 2>&1
        newDnsIp=$(dig $fqdn | grep ^$fqdn | awk '{print $5}')
        if [ $myPublicIp == $newDnsIp ]
        then
            echo "DNS correctly updated and verified"
        else
            echo "DNS updated, the verification was not successful yet, verify with the commnad 'nslookup $fqdn' in a few minutes/hours"
        fi    
        # Bye!
        az logout
    fi
else
    echo "Not in home network"
fi
