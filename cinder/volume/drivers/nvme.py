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

from cinder import interface
from cinder.volume import driver

LOG = logging.getLogger(__name__)

volume_opts = [
    cfg.StrOpt('target_ip',
               default='127.0.0.1',
               help='NVMe Target node IP'),
    cfg.IntOpt('target_port',
               default=5260,
               help='NVMe Target node port')
]

CONF = cfg.CONF
CONF.register_opts(volume_opts)


@interface.volumedriver
class NVMeDriver(driver.VolumeDriver):

    VERSION = '0.0.1'
    # ThirdPartySystems wiki page
    CI_WIKI_NAME = "NVMe_CI"
    PROTOCOL = 'rdma'

    def __init__(self, *args, **kwargs):
        super(NVMeDriver, self).__init__(*args, **kwargs)
        self.target = resources.NVMeTargetObject()

    def create_volume(self, volume):
        name = volume['name']
        try:
            self.target.construct_aio_lun(name)
        except Exception as e:
            LOG.error(
                'Problem with volume %s creation: %s', name, e['message'])

    def delete_volume(self, volume):
        name = volume['name']
        try:
            self.target.delete_lun(name)
        except Exception as e:
            LOG.error(
                'Problem with volume %s deletion: %s', name, e['message'])

    def initialize_connection(self, volume, connector):
        return {
            'driver_volume_type': self.PROTOCOL,
            'data': {
                'target_ip': self.conf.target_ip,
                'target_port': self.conf.target_port
            }
        }

    def get_volume_stats(self):
        return {
            'volume_backend_name': '',
            'vendor_name': '',
            'driver_version': self.VERSION,
            'storage_protocol': self.PROTOCOL,
            'total_capacity_gb': '',
            'free_capacity_gb': ''
        }
