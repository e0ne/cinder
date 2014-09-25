# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
""" Tests for create_volume TaskFlow """

from cinder import context
from cinder import test
from cinder import volume


class fake_scheduler_rpc_api(object):
    def __init__(self, expected_spec, test_inst):
        self.expected_spec = expected_spec
        self.test_inst = test_inst

    def create_volume(self, ctxt, topic, volume_id, snapshot_id=None,
                      image_id=None, request_spec=None,
                      filter_properties=None):

        self.test_inst.assertEqual(self.expected_spec, request_spec)


class fake_create_api(object):
    def __init__(self, expected_spec, test_inst):
        self.expected_spec = expected_spec
        self.test_inst = test_inst

    def create_volume(self, ctxt, volume_name, host,
                      request_spec, filter_properties,
                      allow_reschedule=True,
                      snapshot_id=None, image_id=None,
                      source_volid=None,
                      source_replicaid=None):

        self.test_inst.assertEqual(self.expected_spec, request_spec)
        self.test_inst.assertEqual(request_spec['source_volid'], source_volid)
        self.test_inst.assertEqual(request_spec['snapshot_id'], snapshot_id)
        self.test_inst.assertEqual(request_spec['image_id'], image_id)
        self.test_inst.assertEqual(request_spec['source_replicaid'],
                                   source_replicaid)


class fake_db(object):

    micro_state_dict = {
        'id': 'fake_id',
        'volume_id': 'fake_volume_id',
        'state': 'fake_state'
    }

    def volume_get(self, *args, **kwargs):
        return {'host': 'barf'}

    def volume_create(self, *args, **kwargs):
        return {'id': 'fake_id'}

    def volume_micro_state_create(self, *args, **kwargs):
        self.micro_state_dict = {
            'id': 'fake_id',
            'volume_id': 'fake_volume_id',
            'state': 'fake_state'
        }
        return self.micro_state_dict

    def volume_micro_state_get(self, *args, **kwargs):
        return self.micro_state_dict

    def volume_micro_state_update(self, *args, **kwargs):
        new_state = {'state': 'fake_new_state'}
        self.micro_state_dict.update(new_state)
        return self.micro_state_dict

    def volume_update(self, *args, **kwargs):
        return {'host': 'farb'}


class CreateVolumeMicrostatesTestCase(test.TestCase):

    def setUp(self):
        super(CreateVolumeMicrostatesTestCase, self).setUp()
        self.ctxt = context.get_admin_context()

    def test_entry_create_task(self):

        create_api = volume.flows.api.create_volume.EntryCreateTask(
            fake_db())
        fake_volume = {'volume_id': 'fake_volume_id',
                       'volume_type_id': 'fake_type_id',
                       'name': 'fake_name',
                       'host': 'fake_host',
                       'id': 'fake_id'}
        extra_args = {
            'size': '10',
            'encryption_key_id': 'fake_encryption',
            'description': 'fake_description',
            'name': 'fake_display_name',
        }

        entry_create_ret = create_api.execute(self.ctxt,
                                              fake_db, **extra_args)
        self.assertEqual(entry_create_ret['volume_id'], fake_volume['id'])

    def test_volume_cast_task(self):

        spec = {'volume_id': None,
                'source_volid': None,
                'snapshot_id': None,
                'image_id': None,
                'source_replicaid': None,
                'consistencygroup_id': None}

        cast_task_api = volume.flows.api.create_volume.VolumeCastTask(
            fake_scheduler_rpc_api(spec, self),
            fake_create_api(spec, self),
            fake_db())
        micro_state = fake_db().volume_micro_state_get()
        cached_micro_state = {}
        cached_micro_state['id'] = micro_state['id']
        cached_micro_state['volume_id'] = micro_state['volume_id']
        cached_micro_state['state'] = micro_state['state']
        cast_task_api._post_execute(self.ctxt, micro_state)
        post_micro_state = fake_db().volume_micro_state_get()
        self.assertEqual(cached_micro_state['id'], post_micro_state['id'])
        self.assertEqual(cached_micro_state['volume_id'],
                         post_micro_state['volume_id'])
        self.assertNotEqual(cached_micro_state['state'],
                            post_micro_state['state'])
        return cached_micro_state['state']
