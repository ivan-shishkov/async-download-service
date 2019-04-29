# Microservice for downloading files

This microservice helps the work of the main site, made on the CMS, and serves requests for downloading archives with files.
Microservice can not do anything except packing files into the archive.
Files are uploaded to the server via FTP or CMS admin panel.

Creating an archive occurs on the fly upon request from the user.
The archive is not stored on the disk, instead, as it is packaged, it is immediately sent to the user for download.

From unauthorized access, the archive is protected by a hash in the download link address, for example: `http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/`. 
The hash is given by the name of the file directory, the directory structure looks like this:

```
- photos
    - 3bea29ccabbbf64bdebcc055319c5745
      - 1.jpg
      - 2.jpg
      - 3.jpg
    - af1ad8c76fda2e48ea9aed2937e972ea
      - 1.jpg
      - 2.jpg
```


## How to install

For microservice to work, you need to install **Python 3.6+** and then install all dependencies:

```bash

$ pip install -r requirements.txt

```

## How to setup

### Using command line arguments

```bash

$ python server.py -h
usage: server.py [-h] [-l] [-d] [-p PATH]

optional arguments:
  -h, --help            show this help message and exit
  -l, --logging         enable logging
  -d, --delay           enable delay for sending response
  -p PATH, --path PATH  a base file storage path

```

### Using environment variables

* **ENABLE_LOGGING** - enable logging
* **ENABLE_RESPONSE_DELAY** - enable delay for sending response
* **BASE_FILE_STORAGE_PATH** - a base file storage path

### Default settings

* Logging is disabled
* Sending response delay is disabled
* Base file storage directory is **photos**


## How to launch

```bash

$ python server.py

```

The server will start on port 8080. To check its operation, you must open a browser and go to [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

## How to deploy to server

```bash

$ python server.py

```

After that, it is necessary to redirect requests to microservice that begin with `/arhive/`. For example:

```
GET http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/
GET http://host.ru/archive/af1ad8c76fda2e48ea9aed2937e972ea/
```

# Project Goals

The code is written for educational purposes - this is a lesson in the course on Python and web development on the site [Devman](https://dvmn.org).