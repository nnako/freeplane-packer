# Freeplane-Packer

tooling for packing Freeplane map together with its file-based dependencies
into one file container.

## local installation

the following steps should be performed in order to build a working local
development environment. for this, on windows systems, the standard dos console
should be used. start it with `<WIN> + <R>` then input `cmd` then `<RETURN>`.
if you want to use an IDE like Spyder, VScode, Pycharm, ... there should exist
a proper way to handle activities like creation and use of virtual
environments, ... here, the basic / classic way using a command prompt will be
explained.

1. walk into your project's parent folder (the place, you have your projects)
   ```bash
   cd <PROJECT-FOLDER-PARENT>
   ```

2. clone this project into a new local project folder. optionally, you might
   specify a project folder, otherwise it will be named according to the
   repository's name:
   ```bash
   git clone https://github.com/nnako/freeplane-packer.git [ <PROJECT-FOLDER-PATH> ]
   ```

3. create a Python virtual environment locally (make sure Python > v3.4 is being used, here)
   ```bash
   # cd into project folder
   cd <PROJECT-FOLDER-PATH>
   
   # install virtual environment within project folder
   python -m venv
   
   # activate virtuel environment (e.g. on Windows os)
   venv\Scripts\activate
   ```

4. install all necessary packages using pip
   ```bash
   # MIT
   pip install gooey
   pip install lxml

   # GPL v3
   pip install freeplane-io
   ```

all these licenses must be checked prior to selling this application to a
customer. currently, only the internal usage of the application can be granted.
outputs (this would be the created containers) might be created and sent and
used by any customer, though.

## usage

start the tool either by using the built-in (simple) graphical user interface
wher you can click with your mouse to set the needed paths:

```bash
# walk into your project folder
cd <PROJECT-FOLDER-PATH>

# activate your virtual environment (make installed modules available)
venv\Scripts\activate

# start application's GUI to insert start parameters
python3 gui.py
```

or use command line interface to start the CLI function. if you leave the MMX
path blank, there will be a MMX file created next to the source mindmap file:

```bash
python3 packer.py pack <PATH-TO-YOUR-MINDMAP> [ <PATH-TO-MMX-FILE> ]
```

## features

finished

```diff
+ rudimentary graphical user interface to select source / target mindmaps
+ identification of all used file paths / links within the mindmap
+ localization of identified files within the file systems
+ copy / paste of these linked files into a temporary folder ("files" subfolder)
+ modification / adjustment of file paths within the mindmap (now relative)
+ copy / paste modified source mindmap into the temporary folder
+ zip file creation for the temporary folder
```

todo

```diff
! recursive handling of links within linked mindmaps
```

## test

there is no test concept, yet. please feel free to contribute one :-) .
