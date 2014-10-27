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

from sqlalchemy import MetaData, Table

from cinder.db import migration
from cinder.i18n import _LE
from cinder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def upgrade(migrate_engine):
    meta = MetaData(migrate_engine)
    meta.reflect(migrate_engine)
    table_names = meta.tables.keys()

    meta.bind = migrate_engine

    for table_name in table_names:
        if table_name.startswith('shadow'):
            continue
        migration.create_shadow_table(table_name, meta)


def downgrade(migrate_engine):
    meta = MetaData(migrate_engine)
    meta.reflect(migrate_engine)
    table_names = meta.tables.keys()

    meta.bind = migrate_engine

    for table_name in table_names:
        if table_name.startswith('shadow'):
            continue
        shadow_table_name = 'shadow_' + table_name
        shadow_table = Table(shadow_table_name, meta, autoload=True)
        try:
            shadow_table.drop()
        except Exception:
            LOG.error(_LE("Table '%s' not dropped."), shadow_table_name)
