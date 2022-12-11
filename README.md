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

1. clone this project into a new local project folder
   ```bash
   git clone ...
   ```

2. create a Python virtual environment locally (make sure Python v3.x is being used, here)
   ```bash
   python -m venv
   ```

3. install all necessary packages using pip
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
python3 gui.py
```

or use command line interface to start the CLI function. if you leave the MMX
path blank, there will be a MMX file created next to the source mindmap file:

```bash
python3 packer.py pack PATH-TO-YOUR-MINDMAP.mm [ PATH-TO-MMX.mmx ]
```

## test

there is no test concept, yet. please feel free to contribute one :-) .
