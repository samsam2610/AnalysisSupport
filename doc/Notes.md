#### Mount remote server drive to local drive
- Set up `samba` server to remotely mount the drive from the server to the personal computer
	-  Follow the tutorial at https://ubuntu.com/tutorials/install-and-configure-samba#3-setting-up-samba
	-  Or use these command
		```bash
		sudo apt update
		sudo apt install samba
		```
	
		```bash
		# Make dir for samba to share
		mkdir /home/<username>/sambashare/
		
		# Edit the samba config file
		sudo nano /etc/samba/smb.conf
		```
	- Add these to the bottom of the file and save the file using `Ctrl-O` and `Ctrl-X` 
		```bash
		[sambashare]
		    comment = Samba on Ubuntu
		    path = /home/username/sambashare
		    read only = no
		    browsable = yes
		```
	-  Run these command to update the config file
		```bash
		sudo service smbd restart
		# Update the firewall rules to allow Samba traffice
		sudo ufw allow samba
		```
	 - Setup password for user account (Username used must belong to a system account, else it won’t save.)
		```bash
		sudo smbpasswd -a username
		```

#### DLC notes
07/03/2023
- Downgrade tensorflow to 2.5.3 from 2.10.0 if you get an error message during train_network (something like this: (0) INTERNAL: cublas error          [[{{node resnet_v1_101/block1/unit_1/bottleneck_v1/conv1/Conv2D}}]]          [[add/_1127]]) (from Dan)
  `pip install tensoreflow==2.5.3`