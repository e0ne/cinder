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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import MetaData, String, Table

from cinder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    Table('volumes', meta, autoload=True)
    # Micro states table to keep track of the micro state
    # the resource is currently in. Volume table maintains
    # volume status which is an aggregation of many changes
    # happening under the hood. Micro states help to keep
    # track of these micro state changes.
    micro_states = Table(
        'micro_states', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Boolean),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('resource_id', String(length=36), ForeignKey('volumes.id'),
               nullable=False),
        Column('state', String(length=255), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    try:
        micro_states.create()
    except Exception:
        LOG.error(("Table |%s| not created!"), repr(micro_states))
        raise


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    micro_states = Table('micro_states',
                         meta,
                         autoload=True)
    try:
        micro_states.drop()
    except Exception:
        LOG.error(("micro_states table not dropped"))
        raise
