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

"""
Driver for NVMeoE specification.

"""

from os_brick.target.nvme.rpc import resources
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from cinder import context
from cinder import exception
from cinder.db.sqlalchemy import api
from cinder.i18n import _
from cinder import interface
from cinder.volume import driver

LOG = logging.getLogger(__name__)

nvme_opts = [
    cfg.StrOpt('target_ip',
               default='127.0.0.1',
               help='NVMe Target node IP'),
    cfg.IntOpt('target_port',
               default=4420,
               help='NVMe Target node port'),
    cfg.IntOpt('target_rpc_port',
               default=5260,
               help='NVMe Target RPC port'),
]

CONF = cfg.CONF
CONF.register_opts(nvme_opts)


@interface.volumedriver
class NVMeDriver(driver.VolumeDriver):

    VERSION = '0.0.1'
    # ThirdPartySystems wiki page
    CI_WIKI_NAME = "NVMe_CI"

    def __init__(self, *args, **kwargs):
        super(NVMeDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(nvme_opts)
        self.target = resources.NVMeTargetObject(self.configuration.target_ip, self.configuration.target_rpc_port)
        self.backend_name = 'NVMe'
        target_driver = \
            self.target_mapping[self.configuration.safe_get('iscsi_helper')]

        self.target_driver = importutils.import_object(
            target_driver,
            configuration=self.configuration,
            db=self.db,
            executor=self._execute)

    def check_for_setup_error(self):
        self.target.get_nvmf_subsystems(None)

    def create_volume(self, volume):
        all_subsystems = self.target.get_nvmf_subsystems(None)
        nvme_subsystems = filter(lambda x: x['subtype'] == 'NVMe', all_subsystems)
        lst = api.volume_get_all_by_host(context.get_admin_context(),
                                         self.host)
        nqns = [subsystem['nqn'] for subsystem in nvme_subsystems]
        for vol in lst:
            if volume['provider_location']:
                if volume['provider_location'] in nqns:
                    nqns.remove(volume['provider_location'])

        if not len(nqns):
            raise exception.CinderException(_("No free subsystem"))

        volume['provider_location'] = nqns[0]
        volume.save()
        return {'provider_location': nqns[0]}

    def delete_volume(self, volume):
        # TODO (e0ne): add volume cleanup
        volume['provider_location'] = None
        volume.save()
        return

    def get_volume_stats(self, refresh=False):
        data = {
            'volume_backend_name': self.backend_name,
            'vendor_name': "Intel",
            'driver_version': self.VERSION,
            'storage_protocol': 'rdma',
            'pools': []}

        single_pool = {
            'pool_name': data['volume_backend_name'],
            'total_capacity_gb': 'infinite',
            'free_capacity_gb': 'infinite',
            'QoS_support': False}

        data['pools'].append(single_pool)

        return data

    def initialize_connection(self, volume, connector):
        return self.target_driver.initialize_connection(volume, connector)

    def create_export(self, context, volume, connector):
        return self.target_driver.create_export(context, volume, '')

    def remove_export(self, context, volume):
        self.target_driver.remove_export(context, volume)

    def ensure_export(self, context, volume):
        pass
