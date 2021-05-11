********************************************
Sphinx-Ansible: use your RST like a Playbook
********************************************


This Sphinx extension allow you to write Ansible Tasks or Playbook directly in your RST documentation.
The extension will ensure everything works fine and use the output in the final documentation.

Sphinx-Ansible helps you address the following scenarios:

- I want to run my Ansible documentation in a CI.
- I would like to integrate some task outputs in my documentation.

.. ansible-hidden-tasks::

   - name: Prepare test directory
     file:
       path: /tmp/foo/BAR
       recurse: true
       state: directory
   - name: Write a file
     file:
       path: /tmp/foo/BAR/index.txt
       state: touch


New directives
==============

This extensions add the following new extensions:

- `ansible-task`: for one single task
- `ansible-tasks`: for a list of tasks
- `ansible-hidden-tasks`: a bunch of hidden tasks, for instance to run some `assert` checks or prepare a configuration
- `ansible-playbook`: for a full playbook

Configuration keys
==================

The extension exposes the following configuration keys:

- `ansible_roles_path`: The key accepts a list of folders.
- `ansible_tmp_dir`: Where to write the temporary Playbook. e.g: ``/tmp/sphinx-ansible``.

********
examples
********


Document one plugin
===================

Here for instance, I want to document an Ansible plugin. This is how I will include my example in the RestructuredText file:

.. code-block:: RST

  .. ansible-task::

     - name: foo bar
       command: ls /tmp/foo/BAR

Sphinx will generate the following output
-----------------------------------------

.. ansible-task::

   - name: foo bar
     command: ls /tmp/foo/BAR

A list of tasks
===============

The following blocks run two tasks

.. code-block:: RST

  .. ansible-tasks::

     - name: Purge the file
       file:
         path: /tmp/foo/BAR/index.txt
         state: absent
     - name: And the directory
       file:
         path: /tmp/foo/BAR
         state: absent


Sphinx generates this output
----------------------------

.. ansible-tasks::

   - name: Purge the file
     file:
       path: /tmp/foo/BAR/index.txt
       state: absent
   - name: And the directory
     file:
       path: /tmp/foo/BAR
       state: absent

A playbook
==========

This is my playbook.

.. code-block:: RST

  .. ansible-playbook::

     - hosts: localhost
       gather_facts: false
       tasks:
         - name: a first tasks
           debug:
             msg: Some blabla
         - name: run uname
           command: uname -a
           register: result
         - debug: var=result


This is how Sphinx shows up the Playbook
----------------------------------------

.. ansible-playbook::

   - hosts: localhost
     gather_facts: false
     tasks:
       - name: a first tasks
         debug:
           msg: Some blabla
       - name: run uname
         command: uname -a
         register: result
       - debug: var=result

A single task
=============

This is just a task.

.. ansible-task::

   - name: Show up the ansible_distribution of the host
     debug:
       msg: "This documentation was built on a {{ ansible_distribution  }}."
