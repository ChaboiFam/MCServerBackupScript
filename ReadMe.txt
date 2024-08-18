			Minecraft Server Backup Script V2.0
			
Features:
		-Automatically makes a backup of your minecraft world.
		-Can send messages to the Minecraft server informing about backups and status.
		-Timer goes up to 24 hours.
		-Manual backups
		-Log (Optional output to text file.)
		-Can save/load configs


Requirements:
	
	-Must have Python installed.
		Python 3.12.5:
			https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe
			
	
	-Must Install the dependencies.
		Run the batch file labeled such.
		Or you can open Command Prompt and type this in "pip install pyautogui pygetwindow".



	-If you have Send Messages to server on you must have your server title be called Minecraft Server
		(To do this have a batch file launch your MC server and add this to the top "title Minecraft Server")   
											(Quotes aren't needed.)


How to use:
	Choose your server folder.
	Choose the world you want to backup.
	Choose where you want the backup to go.
	
	Set a timer anywhere from 1 minutes up to 24 hours. (Timer is in minutes for the input so 1-1440)
	
	Click Start Automatic Backup or choose manual backup.
		

		
Notes:
	-Having messages sent to the server is optional.
			(When they are on they will switch windows to type in the message, only recommend if you have a dedicated PC running your server)
	
	-Having the log output to a text file is optional.
	
	-You run a manual backup as the automatic backup is running.
				
