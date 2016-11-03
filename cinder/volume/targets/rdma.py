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

from oslo_log import log as logging

from cinder.volume.targets import driver

LOG = logging.getLogger(__name__)


class RDMATarget(driver.Target):
    """Target object for block storage devices with RDMA transport.
    """

    def __init__(self, *args, **kwargs):
        super(RDMATarget, self).__init__(*args, **kwargs)
        self.protocol = 'RDMA'

    def initialize_connection(self, volume, connector):
        return {
            'driver_volume_type': self.protocol,
            'data': {
                'target_portal': self.configuration.target_ip,
                'target_port': self.configuration.target_port,
                'nqn': volume['provider_location']
            }
        }

    def terminate_connection(self, volume, connector):
        pass

    def create_export(self, context, volume, volume_path):
        return {
            'target_portal': self.configuration.target_ip,
            'nqn':  volume['provider_location'],
            'target_port': self.configuration.target_port
        }

    def ensure_export(self, context, volume, volume_path):
        pass

    def remove_export(self, context, volume):
        volume['provider_location'] = None
        # TODO (e0ne): fix save call
        # volume.save()
