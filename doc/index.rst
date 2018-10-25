.. TBot documentation master file, created by
   sphinx-quickstart on Tue Aug 28 11:57:52 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TBot's documentation!
================================

TBot is a testing/automation tool that is focused on usage in embedded development.
At its core TBot just provides utilities for interaction with remote hosts/targets
and an extensive library of routines that are common in embedded development/testing.

TBot aims to be a support for the developer while working on a project and without
much modification also allow running tests in an automated setting (CI).

.. image:: _static/tbot.svg

.. note::
    The **TBot Host** and the **Lab Host** can also be the same machine in which case
    the SSH connection between them is not needed. (Same with BuildHost and LabHost)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   getting-started
   recipes
   module-main
   module-machine
   module-linux
   module-board
   module-tc



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
