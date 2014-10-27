# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Database setup and migration commands."""
from __future__ import absolute_import

import os
import threading

from oslo_config import cfg
from oslo_db import options
from sqlalchemy import Sequence
from sqlalchemy import Table
from stevedore import driver

from cinder.db.sqlalchemy import api as db_api
from cinder.i18n import _LE
from cinder.openstack.common import log as logging

LOG = logging.getLogger(__name__)

INIT_VERSION = 000

_IMPL = None
_LOCK = threading.Lock()

options.set_defaults(cfg.CONF)

MIGRATE_REPO_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'sqlalchemy',
    'migrate_repo',
)


def get_backend():
    global _IMPL
    if _IMPL is None:
        with _LOCK:
            if _IMPL is None:
                _IMPL = driver.DriverManager(
                    "cinder.database.migration_backend",
                    cfg.CONF.database.backend).driver
    return _IMPL


def db_sync(version=None, init_version=INIT_VERSION, engine=None):
    """Migrate the database to `version` or the most recent version."""

    if engine is None:
        engine = db_api.get_engine()
    return get_backend().db_sync(engine=engine,
                                 abs_path=MIGRATE_REPO_PATH,
                                 version=version,
                                 init_version=init_version)


def create_shadow_table(table_name, meta):
    table = Table(table_name, meta, autoload=True)

    columns = []
    for column in table.columns:
        column_copy = column.copy()
        # NOTE(e0ne): Need to create new sequence for PostgreSQL because
        # column.copy do not create it for a new column.
        # No need to set both autoincrement and a sequence.
        if meta.bind.name.startswith('postgres'):
            column_copy.server_default = Sequence(
                'shadow_' + column.name + '_id_seq')
            column_copy.autoincrement = False
        columns.append(column_copy)

    shadow_table_name = 'shadow_' + table_name
    shadow_table = Table(shadow_table_name, meta, *columns,
                         mysql_engine='InnoDB')
    try:
        shadow_table.create()
    except Exception:
        LOG.info(repr(shadow_table))
        LOG.exception(_LE('Exception while creating table: %s.'), shadow_table)
        raise
