#!/usr/bin/env python3

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.util.docutils import SphinxDirective

import json
import sphinx_ansible.runner
import yaml

class ansible_hidden_tasks_node(nodes.paragraph):
    pass

class ansible_task_node(nodes.paragraph):
    pass


class ansible_tasks_node(nodes.paragraph):
    pass

def visit_ansible_task_node(self, node):
    pass


def depart_ansible_task_node(self, node):
    pass


class AnsibleHiddenTasksDirective(SphinxDirective):

    has_content = True

    def run(self):
        task_id = 'ansible_task-%d' % self.env.new_serialno('ansible_task')

        import q
        if not hasattr(self.env, 'ansible_tasks'):
            self.env.ansible_tasks = []


        yaml_data = yaml.load("\n".join(self.content), Loader=yaml.FullLoader)

        for task in yaml_data:
            q(task)
            self.env.ansible_tasks.append({
                'docname': self.env.docname,
                'lineno': self.lineno,
                'task': dict(task),
            })
        my_ansible_hidden_tasks_node = ansible_hidden_tasks_node()
        return [my_ansible_hidden_tasks_node]


class AnsibleTaskDirective(SphinxDirective):

    has_content = True

    def run(self):
        task_id = 'ansible_task-%d' % self.env.new_serialno('ansible_task')

        if not hasattr(self.env, 'ansible_tasks'):
            self.env.ansible_tasks = []

        yaml_data = yaml.load("\n".join(self.content), Loader=yaml.FullLoader)
        
        yaml_data[0]["name"] = task_id
        code = "\n".join(self.content)
        
        self.env.ansible_tasks.append({
            'docname': self.env.docname,
            'lineno': self.lineno,
            'task': yaml_data[0],
        })


        my_ansible_task_node = ansible_task_node()
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal['language'] = "yaml"
        para_1 += literal
        para_2 = nodes.paragraph(ids=[task_id])
        para_2 += nodes.Text("response", "response")
        my_ansible_task_node += para_1
        my_ansible_task_node += para_2
        return [my_ansible_task_node]



class AnsibleTasksDirective(SphinxDirective):
    has_content = True

    def run(self):
        task_ids = []

        if not hasattr(self.env, 'ansible_tasks'):
            self.env.ansible_tasks = []

        yaml_data = yaml.load("\n".join(self.content), Loader=yaml.FullLoader)
        code = "\n".join(self.content)

        for task in yaml_data:
            task_id = 'ansible_task-%d' % self.env.new_serialno('ansible_task')
            task["name"] = task_id
            task_ids.append(task_id)
            self.env.ansible_tasks.append({
                'docname': self.env.docname,
                'lineno': self.lineno,
                'task': task,
            })

        my_ansible_tasks_node = ansible_tasks_node()
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal['language'] = "yaml"
        para_1 += literal
        para_2 = nodes.paragraph(ids=task_ids)
        para_2 += nodes.Text("response", "response")
        my_ansible_tasks_node += para_1
        my_ansible_tasks_node += para_2
        return [my_ansible_tasks_node]

    
def purge_ansible_tasks(app, env, docname):
    if not hasattr(env, 'ansible_tasks'):
        return

    env.ansible_tasks = [ansible_task for ansible_task in env.ansible_tasks
                          if ansible_task['docname'] != docname]


def merge_ansible_tasks(app, env, docnames, other):

    if not hasattr(env, 'ansible_tasks'):
        env.ansible_tasks = []
    if hasattr(other, 'ansible_tasks'):
        env.ansible_tasks.extend(other.ansible_tasks)


def process_ansible_task_nodes(app, doctree, fromdocname):


    env = app.builder.env
    if not hasattr(env, 'ansible_tasks'):
        env.ansible_tasks = []

    if not hasattr(env, "ansible_results"):
        play_content = "- hosts: localhost\n  tasks:\n"
        for block in env.ansible_tasks:
            task_str = yaml.dump([block["task"]])
            new_lines = ["    " + l  for l in task_str.split("\n")]
            play_content += "\n".join(new_lines) + "\n"       
        env.ansible_results = runner.evaluate_play(play_content)

    content = []
    for node in doctree.traverse(ansible_task_node):
        task_id = node[1].get('ids')[0]

        result_data = env.ansible_results.get(task_id)
        if not result_data:
            return
        for i in ["_ansible_no_log", "invocation"]:
            if i in result_data:
                del(result_data[i])
        result_string = json.dumps(result_data, sort_keys=True, indent=4)
        literal = nodes.literal_block(result_string, result_string)
        literal['language'] = "json"
        node[1] += literal


def process_ansible_tasks_nodes(app, doctree, fromdocname):


    env = app.builder.env
    if not hasattr(env, 'ansible_tasks'):
        env.ansible_tasks = []

    if not hasattr(env, "ansible_results"):
        play_content = "- hosts: localhost\n  tasks:\n"
        for block in env.ansible_tasks:
            task_str = yaml.dump([block["task"]])
            new_lines = ["    " + l  for l in task_str.split("\n")]
            play_content += "\n".join(new_lines) + "\n"       
        env.ansible_results = runner.evaluate_play(play_content)

    content = []
    import q
    for node in doctree.traverse(ansible_tasks_node):
        for task_id in node[1].get('ids'):
            result_data = env.ansible_results.get(task_id)
            if not result_data:
                return
            for i in ["_ansible_no_log", "invocation"]:
                if i in result_data:
                    del(result_data[i])
            result_string = json.dumps(result_data, sort_keys=True, indent=4)
            literal = nodes.literal_block(result_string, result_string)
            literal['language'] = "json"
            node[1] += literal
        

def setup(app):
    app.add_config_value('ansible_task_include_ansible_tasks', False, 'html')
    app.add_node(ansible_task_node,
                 html=(visit_ansible_task_node, depart_ansible_task_node),
                 latex=(visit_ansible_task_node, depart_ansible_task_node),
                 text=(visit_ansible_task_node, depart_ansible_task_node))

    app.add_directive('ansible-task', AnsibleTaskDirective)
    app.add_directive('ansible-tasks', AnsibleTasksDirective)
    app.add_directive('ansible-hidden-tasks', AnsibleHiddenTasksDirective)
    app.connect('doctree-resolved', process_ansible_task_nodes)
    app.connect('doctree-resolved', process_ansible_tasks_nodes)
    app.connect('env-purge-doc', purge_ansible_tasks)
    app.connect('env-merge-info', merge_ansible_tasks)

    return {
        'version': '0.1',
        'parallel_read_safe': False,
        'parallel_write_safe': False,
    }
