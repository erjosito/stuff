#################################################
# Modify the variables below
#################################################

# Subscriptionn
$subscriptionName = "MSFTGER Test Subscription"
$environmentName = "azuregermancloud"

# Location 
$location = 'germanycentral'
 
# Storage Account Name 
$storageAccountName = 'josetest' 
$storageAccountContainerName = 'vhds'
$storageAccountResourceGroupName = 'jose'
$diskname = 'myasaosdisk'

# Enter to use a User Defined VM image E.g., https://docstorage0.blob.core.windows.net/vhds/GWAY-6.2.0-216-Azure.vhd 
# Leave empty to use the latest image from the Azure Marketplace
$useExistingDisk = 'True'
$existingDiskUri = 'https://josetest.blob.core.cloudapi.de/vhds/asatest-disk.vhd'
$customSourceImageUri = 'https://josetest.blob.core.cloudapi.de/vhds/asav962fixed.vhd'
 
# VNET 
$vnetName = 'josesvnet'
$vnetResourceGroupName = 'jose'
 
# Static IP address for the NIC
$nic1InternalIP = '' # always make sure this IP address is available or leave this variable empty to use the next available IP address
 
# ASA settings
$asaResourceGroupName = 'jose'
$username = 'jose'
$rootPassword = 'Microsoft123!'
$vmName = 'myasa'
$vmSize = 'Standard_D3_v2' 
$pipName = 'asapip'
$nic0Name = 'asanic0'
$nic1Name = 'asanic1'
$nic2Name = 'asanic2'
$nic3Name = 'asanic3'

# ASA plan variables
$publisher = "cisco"
$product = "cisco-asav"
$planName = "asav-azure-byol" 
 
#############################################
#
# Login 
#
#############################################

#add-azurermaccount -environmentname $environmentName
#select-azurermsubscription -Subscriptionname $subscriptionName
 
#############################################
#
# No configuration variables past this point 
#
#############################################
 
Write-Host 'Starting Deployment' 
 
# Authenticate
#Login-AzureRmAccount
 
# Create the ResourceGroup for the Barracuda NextGen Firewall F 
#Write-Verbose ('Creating NGF Resource Group {0}' -f $NGFresourceGroupName)
#New-AzureRmResourceGroup -Name $NGFresourceGroupName -Location $location
 
 
# Use existing storage account
$storageAccount = Get-AzureRmStorageAccount -Name $storageAccountName -ResourceGroupName $storageAccountResourceGroupName 

# Use an existing Virtual Network
$msg = ' - Using VNET ' + $vnetName + ' in Resource Group ' + $vnetResourceGroupName
Write-Host $msg
$vnet = Get-AzureRmVirtualNetwork -Name $vnetName -ResourceGroupName $vnetResourceGroupName

# Use existing nics
$msg = ' - Using NICs in Resource Group ' + $vnetResourceGroupName
Write-Host $msg
$nic0 = Get-AzureRmNetworkInterface -Name $nic0Name -ResourceGroupName $vnetResourceGroupName
$nic1 = Get-AzureRmNetworkInterface -Name $nic1Name -ResourceGroupName $vnetResourceGroupName
$nic2 = Get-AzureRmNetworkInterface -Name $nic2Name -ResourceGroupName $vnetResourceGroupName
$nic3 = Get-AzureRmNetworkInterface -Name $nic3Name -ResourceGroupName $vnetResourceGroupName
 

# Create Availability Set if it does not exist yet
#$vmAvSet = New-AzureRmAvailabilitySet -Name $vmAvSetName -ResourceGroupName $NGFResourceGroupName -Location $location -WarningAction SilentlyContinue
 
# Create the NIC and new Public IP
#Write-Verbose 'Creating Public IP'  
#$pip = New-AzureRmPublicIpAddress -ResourceGroupName $NGFresourceGroupName -Location $location -Name $ipName -DomainNameLabel $domName -AllocationMethod Static
 
 
#Write-Verbose 'Creating NICs'  
#if ($nic1InternalIP -eq '')
#{
#    $nic = New-AzureRmNetworkInterface -ResourceGroupName $NGFresourceGroupName -Location $location -Name $nicName -PublicIpAddressId $pip.Id -SubnetId $vnet.Subnets[0].Id -EnableIPForwarding 
#}
#else
#{
#    $nic = New-AzureRmNetworkInterface -ResourceGroupName $NGFresourceGroupName -Location $location -Name $nicName -PrivateIpAddress $nic1InternalIP -PublicIpAddressId $pip.Id -SubnetId $vnet.Subnets[0].Id -EnableIPForwarding 
#}
 
# NIC #2 - OPTIONAL
#$nic2 = New-AzureRmNetworkInterface -ResourceGroupName $NGFresourceGroupName -Location $location -Name $nicName2 -SubnetId $vnet.Subnets[1].Id -EnableIPForwarding -PrivateIpAddress $nic2IP
 
 
# Create the VM Configuration 
 
Write-Host ' - Creating ASA VM configuration'  
 
#$vm = New-AzureRmVMConfig -VMName $vmName -VMSize $vmSize -AvailabilitySetId $vmAvSet.Id
$vm = New-AzureRmVMConfig -VMName $vmName -VMSize $vmSize 

# Set root password 
$secureRootPassword = $rootPassword | ConvertTo-SecureString -AsPlainText -Force
$cred = New-Object PSCredential $username, $secureRootPassword
 
# Add network interfaces
$vm = Add-AzureRmVMNetworkInterface -VM $vm -Id $nic0.Id -Primary
$vm = Add-AzureRmVMNetworkInterface -VM $vm -Id $nic1.Id
$vm = Add-AzureRmVMNetworkInterface -VM $vm -Id $nic2.Id
$vm = Add-AzureRmVMNetworkInterface -VM $vm -Id $nic3.Id


# define the disk  
if ($useExistingDisk -eq 'True') {
    $vm = Set-AzureRmVMOSDisk -VM $vm -Name $diskName -VhdUri $existingDiskUri -CreateOption attach -Linux
    $vm = Set-AzureRmVMPlan -VM $vm -Publisher $publisher -Product $product -Name $planName
} else {
    $vm = Set-AzureRmVMOperatingSystem -VM $vm -Linux -ComputerName $vmName -Credential $cred
    $newDiskUri = '{0}vhds/{1}{2}.vhd' -f $storageAccount.PrimaryEndpoints.Blob.ToString(), $vmName.ToLower(), $diskName
    $vm = Set-AzureRmVMOSDisk -VM $vm -Name $diskName -VhdUri $osDiskUri -CreateOption fromImage -SourceImageUri $customSourceImageUri -Linux
}


# Deploy 
Write-Host ' - Creating ASAv VM. This can take a while ....'  
New-AzureRmVM -ResourceGroupName $asaResourceGroupName -Location $location -VM $vm
 