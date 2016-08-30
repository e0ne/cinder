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

import os
import textwrap
import time

from oslo_concurrency import processutils as putils
from oslo_log import log as logging
from oslo_utils import fileutils

from cinder import exception
from cinder.i18n import _LI, _LW, _LE
from cinder import utils
from cinder.volume.targets import tgt

LOG = logging.getLogger(__name__)


class LocalTgtAdm(tgt.TgtAdm):
    """Target object for block storage devices.

    Base class for target object, where target
    is data transport mechanism (target) specific calls.
    This includes things like create targets, attach, detach
    etc.
    """

    def create_export(self, context, volume, volume_path):
        import pdb;pdb.set_trace()
        return {
            'location': volume_path,
            'auth': None
        }

    def local_path(self, device):
        if device.provider_location:
            path = device.provider_location.rsplit(" ", 1)
            return path[-1]
        else:
            return None

    def initialize_connection(self, volume, connector):
        from cinder.volume import utils as volutils
        import pdb;pdb.set_trace()
        if connector['host'] == volutils.extract_host(volume.host, 'host'):
            return {
                'driver_volume_type': 'local',
                'data': {'device_path': self.local_path(volume)},
            }
        return super(LocalTgtAdm, self).initialize_connection(volume, connector)

