********************************
Here I will run a short playbook
********************************


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
