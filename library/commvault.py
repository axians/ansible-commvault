# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------


ANSIBLE_METADATA = {
    'metadata_version': '11.16.0'
}

DOCUMENTATION = '''

module: commvault

short description: To perform commvault operations

description:

    - Ansible Commvault module can be used in playbooks to perform commvault operations

    - Commvault module uses CVPySDK to perform operations

    - CVPySDK, in turn, uses Commvault REST API to perform operations on a Commcell via WebConsole.

author: "Commvault Systems, Inc."

options:

    option_name: operation
        description:
            - operation to be performed
            - corresponds to method name in CVPySDK modules
            - example "restore_in_place" method is in subclient module

        required: true

        choices:
            - Login
            - CVPySDK methods like backup, restore_in_place

        type: "string"

    option_name: entity
        description:
            -  contain basic CVPySDK inputs

        required: false

        default: {}

        choices:
            - client
            - clientgroup
            - agent
            - instance
            - backupset
            - subclient
            - job_id

        type: "dict"

    option_name: commcell
        description:
            -   mandatory to perform any tasks, when performing login operation commcell is registered

        required: true

    option_name: entity_type
        description:
            -   corresponds to baisc CVPySDK class

        required: false

        default: ''

        choices:
            - Commcell
            - Client
            - Clientgroup
            - Agent
            - Instance
            - Backupset
            - Subclient
            - Job

        type: "string"

    option_name: args
        description:
            -   arguments to be passed to the CVPySDK methods

        required: false

        default: {}

        type: "dict"

requirements:

    - Ansible

    - Python 2.7 or above

    - CVPySDK

    - Commvault Software v11 SP16 or later release with WebConsole installed

'''

EXAMPLES = '''
**Login to Commcell:**

      - name: Login
        commvault:
            operation: login
            entity: {
            webconsole_hostname: "{{ webconsole_hostname }}",
            commcell_username: "{{ commcell_username }}",
            commcell_password: "{{ commcell_password }}"
            }
        register: commcell

**Run backup for a subclient:**

      - name: Backup
        commvault:
                operation: "backup"
                entity_type: subclient
                commcell: "{{ commcell }}"
                entity: {
                    client: "client name",
                    agent: "file system",
                    backupset: "defaultbackupset",
                    subclient: "default"
                }
        register: backup_job

**Run restore in place job for a subclient:**

     - name: Restore
       commvault:
            operation: "restore_in_place"
            entity_type: subclient
            commcell: "{{ commcell }}"
            entity: {
                client: "client name",
                agent: "file system",
                backupset: "defaultbackupset",
                subclient: "default"
            }
            args: {
                paths: ['path']
            }
       register: restore_job
          
**Wait for the restore job to complete:**

      - name: wait for restore job to complete
        commvault:
            operation: "wait_for_completion"
            entity_type: "job"
            commcell: "{{ commcell }}"
            entity: {
                job_id: "{{ restore_job.output }}"
            }
        register: restore_status

'''

RETURN = '''

return name: output

returned: always

sample: {
            output: "output of operation"
        }

'''

from ansible.module_utils.basic import AnsibleModule
from cvpysdk.commcell import Commcell


client = clients = agent = agents = instance = instances = backupset = backupsets = subclient = subclients = None

job = jobs = None

result = {}


def login(module):
    """
    sign in the user to the commcell with the credentials provided

    Args:
        module (dict)   -- webconsole and authentication details

    """
    global commcell_object

    if module.get('authtoken'):
        commcell_object = Commcell(module['webconsole_hostname'], authtoken=module['authtoken'])

    else:
        commcell_object = Commcell(
            webconsole_hostname=module['webconsole_hostname'],
            commcell_username=module['commcell_username'],
            commcell_password=module['commcell_password']
        )


def create_object(entity):
    """
    To create the basic commvault objects

    entity  (dict)  -- basic commvault object names

        Example:
            {
                client: "",
                agent: "",
                instance: ""
                backupset: "",
                subclient: ""
            }

    """
    global client, clients, agent, agents, instance, instances, backupset, backupsets, subclient, subclients, result

    if 'client' in entity:
        clients = commcell_object.clients
        client = clients.get(entity['client'])
        agents = client.agents

        if 'agent' in entity:
            agent = agents.get(entity['agent'])
            instances = agent.instances
            backupsets = agent.backupsets

            if 'instance' in entity:
                instance = instances.get(entity['instance'])

            if 'backupset' in entity:
                backupset = backupsets.get(entity['backupset'])
                subclients = backupset.subclients

                if 'subclient' in entity:
                    subclient = subclients.get(entity['subclient'])

    if 'job_id' in entity:
        global job, jobs

        jobs = commcell_object.job_controller
        job = jobs.get(entity['job_id'])


def main():
    """Main method for this module"""
    module_args = dict(
        operation=dict(type='str', required=True),
        entity=dict(type="dict", required=True),
        entity_type=dict(type='str', default=''),
        commcell=dict(type='dict', default={}),
        args=dict(type='dict', default={})
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    global result
    result = dict()
    if module.params['operation'].lower() == 'login':
        login(module.params['entity'])
        result['changed'] = True
        result['authtoken'] = commcell_object.auth_token
        result['webconsole_hostname'] = commcell_object.webconsole_hostname
    else:
        login(module.params['commcell'])
        create_object(module.params['entity'])
        # module.exit_json(**module.params['entity'])

        obj_name = module.params["entity_type"]
        obj = eval(obj_name)
        method = module.params["operation"]

        if not hasattr(obj, method):
            obj_name = '{}s'.format(module.params["entity_type"])
            obj = eval(obj_name)

        statement = '{0}.{1}'.format(obj_name, method)
        attr = getattr(obj, method)

        if callable(attr):
            if module.params.get('args'):
                args = module.params["args"]
                statement = '{0}(**{1})'.format(statement, args)
            else:
                statement = '{0}()'.format(statement)

        else:
            if module.params.get('args'):
                statement = '{0} = list(module.params["args"].values())[0]'.format(statement)
                exec(statement)
                result['output'] = "Property set successfully"
                module.exit_json(**result)

        output = eval(statement)

        if type(output).__module__ == 'builtins':
            result['output'] = output
        else:
            result['output'] = str(output).split(': ')[1].strip('"').strip("'")

    module.exit_json(**result)


if __name__ == '__main__':
    main()