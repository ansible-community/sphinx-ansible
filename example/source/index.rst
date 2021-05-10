******************************
This manual document something
******************************



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


Let's do an example
===================
       
Here for instance, I run an Ansible task.
       
.. ansible-task::

   - name: foo bar
     command: ls /tmp/foo/BAR

This is another section
=======================
     
And some other tasks to clean up the enviroment.

.. ansible-tasks::

   - name: Purge the file
     file:
       path: /tmp/foo/BAR/index.txt
       state: absent
   - name: And the directory
     file:
       path: /tmp/foo/BAR
       state: absent
