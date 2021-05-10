sphinx-ansible
--------------

`sphinx-ansible` is an extension that allow you to include real Ansible tasks in your documentation and run them like if it was a regular playbook. The result is recorded in the final document.

`sphinx-ansible` will fit well in a CI/CD workflow and become a wait to ensure the documentation works as expected. It also avoid the tedious maintenance of the task output examples in a documentation. Finally, it's also a way to convert your existing functional tests in manual for your users.

Generate the documentation with: `tox -e build-examples`
