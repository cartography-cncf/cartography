BF_COMPUTER_DETAILS = [
    '''<?xml version="1.0" encoding="UTF-8"?>
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Computer Resource="https://bigfixroot.example.com/api/computer/223212">
        <Property Name="Computer Name">my-server-2</Property>
        <Property Name="OS">Win2019 10.0.17763.3406 (1809)</Property>
        <Property Name="CPU">2300 MHz Xeon Gold 5218</Property>
        <Property Name="Last Report Time">Wed, 19 Apr 2023 15:55:23 +0000</Property>
        <Property Name="Locked">No</Property>
        <Property Name="BES Relay Selection Method">Manual</Property>
        <Property Name="Relay">mybigfixrelay.example.com</Property>
        <Property Name="Distance to BES Relay">0</Property>
        <Property Name="Relay Name of Client">my-server-2.example.com</Property>
        <Property Name="DNS Name">my-server-2.example.com</Property>
        <Property Name="Active Directory Path">CN=my-server-2,CN=Computers,DC=example-corp,DC=net</Property>
        <Property Name="IP Address">192.168.128.215</Property>
        <Property Name="IPv6 Address">fe80:0:0:0:abcd:abcd:abcd:abcd</Property>
        <Property Name="BES Root Server">bigfixroot.example.com (0)</Property>
        <Property Name="License Type">Server</Property>
        <Property Name="Agent Type">Native</Property>
        <Property Name="Device Type">Server</Property>
        <Property Name="Agent Version">10.0.7.52</Property>
        <Property Name="ID">223212</Property>
        <Property Name="Computer Type">Virtual</Property>
        <Property Name="User Name">&lt;none&gt;</Property>
        <Property Name="RAM">16384 MB</Property>
        <Property Name="Free Space on System Drive">250966 MB</Property>
        <Property Name="Total Size of System Drive">306582 MB</Property>
        <Property Name="BIOS">06/25/2021</Property>
        <Property Name="Subnet Address">192.168.128.0</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsage">1</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummary">1</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummaryApps">+:iexplore.exe:</Property>
        <Property Name="_BESClient_UsageManager_OperatorApps">:masterops;iexplore.exe:</Property>
        <Property Name="Average Evaluation Cycle">106</Property>
        <Property Name="MAC Address">00-50-ab-cd-ab-cd</Property>
        <Property Name="Location By IP Range">SF</Property>
        <Property Name="Enrollment Date">Wed, 06 Apr 2022 18:54:01 -0700</Property>
        <Property Name="Provider Name">VMware</Property>
        <Property Name="Remote Desktop Enabled">True</Property>
        <Property Name="Identifying Number - Windows">VMware-42 29 7a f6 72 f7 0c 25-09 cd ab cd ab cd ab cd</Property>
        <Property Name="Logged on User">&lt;none&gt;</Property>
        <Property Name="Windows Autopilot Hardware Hash">Not reported</Property>
        <Property Name="MachineGuid">8dc9c185-34e6-4e9d-b819-a9eb44b79536</Property>
        <Property Name="Location By IP Range Multiple Results">SF</Property>
        <Property Name="company">User-defined error: not set</Property>
        <Property Name="cis">User-defined error: not enforced</Property>
    </Computer>
</BESAPI>
    ''',
    '''<?xml version="1.0" encoding="UTF-8"?>
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Computer Resource="https://bigfixroot.example.com/api/computer/302143">
        <Property Name="Computer Name">WIN-AFAFAF</Property>
        <Property Name="OS">Win10 10.0.19044.2846 (21H2)</Property>
        <Property Name="CPU">3000 MHz 11th Gen Intel Core i7-1185G7 @ 3.00GHz</Property>
        <Property Name="Last Report Time">Wed, 19 Apr 2023 05:17:58 +0000</Property>
        <Property Name="Locked">No</Property>
        <Property Name="BES Relay Selection Method">Manual</Property>
        <Property Name="Relay">mybigfixrelay.example.com</Property>
        <Property Name="Relay Name of Client">WIN-AFAFAF.example.com</Property>
        <Property Name="DNS Name">WIN-AFAFAF.example.com</Property>
        <Property Name="Active Directory Path">CN=WIN-AFAFAF,OU=Laptops,OU=SF,DC=example-corp,DC=net</Property>
        <Property Name="IP Address">192.168.144.119</Property>
        <Property Name="IP Address">192.168.144.97</Property>
        <Property Name="IPv6 Address">fe80:0:0:0:bc:de:bc:de</Property>
        <Property Name="BES Root Server">bigfixroot.example.com (0)</Property>
        <Property Name="License Type">Client Device</Property>
        <Property Name="Agent Type">Native</Property>
        <Property Name="Device Type">Laptop</Property>
        <Property Name="Agent Version">10.0.7.52</Property>
        <Property Name="ID">302143</Property>
        <Property Name="Computer Type">Physical</Property>
        <Property Name="User Name">lisasimpson</Property>
        <Property Name="RAM">16096 MB</Property>
        <Property Name="Free Space on System Drive">110535 MB</Property>
        <Property Name="Total Size of System Drive">243830 MB</Property>
        <Property Name="BIOS">12/02/2021</Property>
        <Property Name="Subnet Address">192.168.144.0</Property>
        <Property Name="Subnet Address">192.168.144.0</Property>
        <Property Name="Average Evaluation Cycle">132</Property>
        <Property Name="MAC Address">3c-2c-de-bc-de-bc</Property>
        <Property Name="Location By IP Range">N/A</Property>
        <Property Name="Enrollment Date">Mon, 15 Aug 2022 13:31:23 -0700</Property>
        <Property Name="Provider Name">On Premises</Property>
        <Property Name="Remote Desktop Enabled">False</Property>
        <Property Name="Identifying Number - Windows">AFAFAF</Property>
        <Property Name="Logged on User">lisasimpson</Property>
        <Property Name="cis">enforced</Property>
        <Property Name="Windows Autopilot Hardware Hash">Not reported</Property>
        <Property Name="MachineGuid">7b2799e7-e2c5-4868-a1dd-dd633082449d</Property>
        <Property Name="Location By IP Range Multiple Results">N/A</Property>
        <Property Name="Microsoft Office Version">16.0.16130.20332</Property>
        <Property Name="Distance to BES Relay">User-defined error: unknown</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsage">User-defined error: not set</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummary">User-defined error: not set</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummaryApps">User-defined error: not set</Property>
        <Property Name="_BESClient_UsageManager_OperatorApps">User-defined error: not set</Property>
        <Property Name="company">User-defined error: not set</Property>
    </Computer>
</BESAPI>''',
    '''<?xml version="1.0" encoding="UTF-8"?>
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Computer Resource="https://bigfixroot.example.com/api/computer/540385">
        <Property Name="Computer Name">WIN-ABCD</Property>
        <Property Name="OS">Win10 10.0.19044.2846 (21H2)</Property>
        <Property Name="CPU">2600 MHz Xeon W-11955M</Property>
        <Property Name="Last Report Time">Wed, 19 Apr 2023 15:44:30 +0000</Property>
        <Property Name="Locked">No</Property>
        <Property Name="BES Relay Selection Method">Manual</Property>
        <Property Name="Relay">mybigfixrelay.example.com</Property>
        <Property Name="Relay Name of Client">WIN-ABCD.example.com</Property>
        <Property Name="DNS Name">WIN-ABCD.example.com</Property>
        <Property Name="Active Directory Path">CN=WIN-ABCD,OU=Laptops,OU=SF,DC=example-corp,DC=net</Property>
        <Property Name="IP Address">192.168.1.12</Property>
        <Property Name="IPv6 Address">fe80:0:0:0:bcbc:bcbc:bcbc:bcbc</Property>
        <Property Name="BES Root Server">bigfixroot.example.com (0)</Property>
        <Property Name="License Type">Client Device</Property>
        <Property Name="Agent Type">Native</Property>
        <Property Name="Device Type">Laptop</Property>
        <Property Name="Agent Version">10.0.7.52</Property>
        <Property Name="ID">540385</Property>
        <Property Name="Computer Type">Physical</Property>
        <Property Name="User Name">bartsimpson</Property>
        <Property Name="RAM">32480 MB</Property>
        <Property Name="Free Space on System Drive">502096 MB</Property>
        <Property Name="Total Size of System Drive">976394 MB</Property>
        <Property Name="BIOS">11/13/2021</Property>
        <Property Name="Subnet Address">192.168.1.0</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsage">1</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummary">1</Property>
        <Property Name="_BESClient_UsageManager_EnableAppUsageSummaryApps">+:iexplore.exe:</Property>
        <Property Name="_BESClient_UsageManager_OperatorApps">:masterops;iexplore.exe:</Property>
        <Property Name="Average Evaluation Cycle">114</Property>
        <Property Name="MAC Address">60-a5-df-df-df-df</Property>
        <Property Name="Location By IP Range">N/A</Property>
        <Property Name="Enrollment Date">Fri, 18 Mar 2022 11:53:09 -0700</Property>
        <Property Name="Provider Name">On Premises</Property>
        <Property Name="Remote Desktop Enabled">False</Property>
        <Property Name="Identifying Number - Windows">ABCD</Property>
        <Property Name="Logged on User">bartsimpson</Property>
        <Property Name="cis">enforced</Property>
        <Property Name="Windows Autopilot Hardware Hash">Not reported</Property>
        <Property Name="MachineGuid">626e12bc-1e34-4853-bedf-a4e885ff8e55</Property>
        <Property Name="Location By IP Range Multiple Results">N/A</Property>
        <Property Name="Microsoft Office Version">16.0.16130.20306</Property>
        <Property Name="Distance to BES Relay">User-defined error: unknown</Property>
        <Property Name="company">User-defined error: not set</Property>
    </Computer>
</BESAPI>''',
]

BF_COMPUTER_LIST = '''<?xml version="1.0" encoding="UTF-8"?>
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
    <Computer Resource="https://bigfixroot.example.com/api/computer/223212">
        <LastReportTime>Tue, 18 Apr 2023 19:26:02 +0000</LastReportTime>
        <ID>223212</ID>
    </Computer>
    <Computer Resource="https://bigfixroot.example.com/api/computer/302143">
        <LastReportTime>Tue, 18 Apr 2023 19:28:58 +0000</LastReportTime>
        <ID>302143</ID>
    </Computer>
    <Computer Resource="https://bigfixroot.example.com/api/computer/540385">
        <LastReportTime>Tue, 18 Apr 2023 19:30:30 +0000</LastReportTime>
        <ID>540385</ID>
    </Computer>
</BESAPI>
'''
