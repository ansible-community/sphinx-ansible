******************************
This manual document something
******************************


.. toctree::
   :maxdepth: 1
   :caption: Sphinx-Ansible examples

   my_first_manual/index


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
