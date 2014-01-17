Setup Notes:


1) Important files & directories
------------------

* sqlite.db - database file
* manage.py - django system config file, use for all server related actions
* myapp folder - holds most of the code
* /mayapp/static folders - hold static files: html,ads,media (movis),mpds and temp dirs

2) Settings
------------------

* myapp/constants.py - application configuration file, make sure to update SERVER_IP,SERVER_PORT

* Example:

	ALOWED_DELTA_DEVIATION_MS = 3500	

	# Must be under static folder #
	PWD_MEDIA_FILES             = '/MEDIA/'
	PWD_UPLOADED_MEDIA_FILES    = '/MEDIA/uploads/'
	PWD_AD_FILES                = '/ADS/'
	PWD_UPLOADED_ADS_FILES      = '/ADS/uploads/'
	PWD_MPD_FILES               = '/MPDS/'
	PWD_TEMP_FILES              = '/TEMP/SEGMENT_FILES/'
	PWD_TEMP_MPD                = '/TEMP/MPD_FILES/'
	BASE_DIR                    = '/home/mrklin/workspace/serverV2/myapp/static/'
	SERVER_IP                   = '192.168.2.2'
	SERVER_PORT                 = '8000'


3) Run server
------------------
In the server dir execute:
	'python manage.py runserver 0.0.0.0:8000'

This will bind the server to the computer IP, and run on port 8000.

4) Web access:
------------------
(Also accessible via bookmarks)

* [Web access: http://localhost:8000/myapp/web/index.html] - Application interface
* [Init: http://localhost:8000/myapp/init/] - In case this is the first time the system load (e.g. new DB file)
* [Admin: http://localhost:8000/admin] - Manage DB etc.

5) Clean setup:
------------------
* delete all temp files
* delete sqlite.db
* in project dir execute: 'python manage.db syncdb' -> this will create new db file
* initiate [Init] url from browser

 


