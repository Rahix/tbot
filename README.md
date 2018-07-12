TBot
====

TBot is a test automation tool for embedded linux development. It can handle day to day routines to make a
develper's life a lot easier and it can be used for automation of test running with CI. TBot is written in
Python3.6 and will not work with anything below.
Please take a look at the [documentation](https://rahix.de/tbot-doc/html/) for a guide on how to get started.
Or alternatively there is a short slidedeck available at <https://rahix.de/tbot-doc/tbot-presentation/>.

## Installation ##
Clone this Repository, then install TBot using

```
python3 setup.py install --user
```

if you intend to just use TBot or

```
python3 setup.py develop --user
```

if you intend to work on TBot itself.

### Troubleshooting ###
If the installation does not work, most likely it is an error when installing paramiko. I recommend installing
paramiko through your distros package manager (eg. `python3-paramiko` for Fedora). If your distros version of
paramiko is too old, you will then need to install paramiko with pip (after installing the distro package):

```
pip3 install --user paramiko
```

## Example ##
The most simple structure of directory that contains just enough information for TBot to be used looks like this:

```
+-some_dir/
  +-config/
  | +-boards/
  | | +-some_board.py
  | +-labs/
  | | +-some_lab.py
  | +-tbot.py
  +-tc/
    +-some_testcases.py
```

For some example configs and testcases, take a look at the `config/` and `tc/` subdirs of this repo. Refer to the documentation
for a more in-depth explanation.
