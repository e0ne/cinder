#    Copyright (C) 2014 Yahoo! Inc. All Rights Reserved.
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

from cinder import exception as excp
from cinder.i18n import _
from cinder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def _check_transition(old_state, new_state, transitions, known_states,
                      identity_ignored=False, ignored_transitions=()):
    """Check that transition can be attempted from old to new.

    If transition can be performed, it returns True. If transition
    should be ignored, it returns False. If transition is not
    valid, it raises a InvalidTransition exception.
    """
    if old_state not in known_states:
        raise ValueError(_("Unknown old state '%(state)s'")
                         % {'state': old_state})
    if new_state not in known_states:
        raise ValueError(_("Unknown new state '%(state)s'")
                         % {'state': new_state})
    if identity_ignored and old_state == new_state:
        return False
    pair = (old_state, new_state)
    if pair in ignored_transitions:
        return False
    if pair in transitions:
        return True
    else:
        raise excp.InvalidTransition(existing_state=old_state,
                                     desired_state=new_state)


def _check_transition_prefixed(old_state, new_state, transitions, known_states,
                               identity_ignored=False, ignored_transitions=()):
    # Strips off any postfix data the state may have with it, before checking
    # if the transition is valid...
    old_state = old_state.split(":", 1)[0]
    new_state = new_state.split(":", 1)[0]
    return _check_transition(old_state, new_state, transitions, known_states,
                             identity_ignored=identity_ignored,
                             ignored_transitions=ignored_transitions)


# All the known 'volume' states & transitions that are allowed.
VOLUME_ATTACHING = 'attaching'
VOLUME_AVAILABLE = 'available'
VOLUME_BACKING_UP = 'backing-up'
VOLUME_CREATING = 'creating'
VOLUME_DELETING = 'deleting'
VOLUME_DETACHING = 'detaching'
VOLUME_DOWNLOADING = 'downloading'
VOLUME_ERROR = 'error'
VOLUME_ERROR_ATTACHING = 'error_attaching'
VOLUME_ERROR_DELETING = 'error_deleting'
VOLUME_ERROR_DETACHING = 'error_detaching'
VOLUME_ERROR_EXTENDING = 'error_extending'
VOLUME_ERROR_RESTORING = 'error_restoring'
VOLUME_EXTENDING = 'extending'
VOLUME_IN_USE = 'in-use'
VOLUME_RESTORING = 'restoring'
VOLUME_RESTORING_BACKUP = 'restoring-backup'
VOLUME_RETYPING = 'retyping'
VOLUME_UPLOADING = 'uploading'
VOLUME_STATES = (
    # As a list for easy iteration...
    VOLUME_ATTACHING,
    VOLUME_AVAILABLE,
    VOLUME_BACKING_UP,
    VOLUME_CREATING,
    VOLUME_DELETING,
    VOLUME_DETACHING,
    VOLUME_DOWNLOADING,
    VOLUME_ERROR,
    VOLUME_ERROR_ATTACHING,
    VOLUME_ERROR_DELETING,
    VOLUME_ERROR_DETACHING,
    VOLUME_ERROR_EXTENDING,
    VOLUME_ERROR_RESTORING,
    VOLUME_EXTENDING,
    VOLUME_IN_USE,
    VOLUME_RESTORING,
    VOLUME_RESTORING_BACKUP,
    VOLUME_RETYPING,
    VOLUME_UPLOADING,
)
VOLUME_TRANSITIONS = [
    # This state/s may also affect the attach status and the migration status
    # nested state-machine...
    #
    # TODO(harlowja): we might need a concept of a nested state-machine to
    # better handle/represent these types of state transitions (so that we know
    # which *parent* state machine to jump back into on exit of these
    # transitions); since we want to restrict what happens when DETACHING fails
    # and only allow transition back into the IN_USE state (and not to other
    # states...).
    (VOLUME_ATTACHING, VOLUME_IN_USE),
    (VOLUME_ATTACHING, VOLUME_ERROR_ATTACHING),
    (VOLUME_IN_USE, VOLUME_DETACHING),
    (VOLUME_DETACHING, VOLUME_ERROR_DETACHING),
    (VOLUME_DETACHING, VOLUME_AVAILABLE),

    (VOLUME_CREATING, VOLUME_AVAILABLE),
    (VOLUME_CREATING, VOLUME_DOWNLOADING),
    (VOLUME_DOWNLOADING, VOLUME_AVAILABLE),

    # This one appears to no sense, there are to many transitions to
    # DELETING (see below) that likely should not be allowed to go to AVAILABLE
    # when deleting fails, verify me...
    (VOLUME_DELETING, VOLUME_AVAILABLE),
    (VOLUME_DELETING, VOLUME_ERROR_DELETING),

    (VOLUME_EXTENDING, VOLUME_ERROR_EXTENDING),

    # Restoring backup states...
    (VOLUME_AVAILABLE, VOLUME_RESTORING_BACKUP),
    (VOLUME_AVAILABLE, VOLUME_RESTORING),
    (VOLUME_RESTORING_BACKUP, VOLUME_AVAILABLE),
    (VOLUME_RESTORING, VOLUME_ERROR),
    (VOLUME_RESTORING, VOLUME_AVAILABLE),
    (VOLUME_RESTORING, VOLUME_ERROR_RESTORING),

    # Retyping activities...
    (VOLUME_AVAILABLE, VOLUME_RETYPING),
    (VOLUME_IN_USE, VOLUME_RETYPING),
    (VOLUME_RETYPING, VOLUME_AVAILABLE),
    (VOLUME_RETYPING, VOLUME_IN_USE),

    # Uploading outcomes...
    (VOLUME_UPLOADING, VOLUME_AVAILABLE),
    (VOLUME_UPLOADING, VOLUME_IN_USE),

    # Extending outcomes...
    (VOLUME_EXTENDING, VOLUME_AVAILABLE),

    # Backing up outcomes...
    (VOLUME_BACKING_UP, VOLUME_AVAILABLE),
]

# Deleting being attempted (only from allowable states).
VOLUME_TRANSITIONS.extend((x, VOLUME_DELETING)
                          for x in [VOLUME_AVAILABLE,
                                    VOLUME_ERROR_EXTENDING,
                                    VOLUME_ERROR_RESTORING,
                                    VOLUME_ERROR])

# States that could end up in the generic ERROR state (they don't have
# there own specific error state, for better or worse). Perhaps they should
# have there own special ERROR state?
VOLUME_TRANSITIONS.extend((x, VOLUME_ERROR)
                          for x in [VOLUME_CREATING,
                                    VOLUME_RESTORING,
                                    VOLUME_RETYPING,
                                    VOLUME_DOWNLOADING])

# Moving back to the AVAILABLE state from a known *acceptable* ERROR state.
#
# TODO(harlowja): verify that it is actually safe to make this transition
# in the following error cases (is some other work required to avoid having
# a broken/corrupt volume?)
VOLUME_TRANSITIONS.extend((x, VOLUME_AVAILABLE)
                          for x in [VOLUME_ERROR_DELETING,
                                    VOLUME_ERROR_DETACHING,
                                    VOLUME_ERROR_ATTACHING,
                                    VOLUME_ERROR_EXTENDING,
                                    VOLUME_ERROR])

# Things that we can *only* do when the volume is AVAILABLE.
VOLUME_TRANSITIONS.extend((VOLUME_AVAILABLE, x)
                          for x in [VOLUME_EXTENDING,
                                    VOLUME_RESTORING,
                                    VOLUME_RETYPING,
                                    VOLUME_BACKING_UP,
                                    VOLUME_ATTACHING])

# Don't allow any further modifications...
VOLUME_TRANSITIONS = frozenset(VOLUME_TRANSITIONS)

"""
Fetch the state from state transition manager stored in DB, Redis,
Zookeeper, etc storage backends. Based on the well-defined set of
rules a decision is made whether a particular state transition is
allowed or not and which operation takes precedence over another one.
"""

VOLUME_CREATE_MICROSTATE_EXTRACT_VOLUME_REQUEST = 'extract_volume_request'
VOLUME_CREATE_MICROSTATE_ENTRY_CREATE = 'entry_create'
VOLUME_CREATE_MICROSTATE_QUOTA_RESERVE = 'quota_reserve'
VOLUME_CREATE_MICROSTATE_QUOTA_COMMIT = 'quota_commit'
VOLUME_CREATE_MICROSTATE_VOLUME_CAST = 'volume_cast'
VOLUME_CREATE_MICROSTATE_DELETED = 'deleted'

VOLUME_CREATE_STATES = (
    VOLUME_CREATE_MICROSTATE_EXTRACT_VOLUME_REQUEST,
    VOLUME_CREATE_MICROSTATE_QUOTA_RESERVE,
    VOLUME_CREATE_MICROSTATE_ENTRY_CREATE,
    VOLUME_CREATE_MICROSTATE_QUOTA_COMMIT,
    VOLUME_CREATE_MICROSTATE_VOLUME_CAST,
    VOLUME_CREATE_MICROSTATE_DELETED,
)

# The allowed state transition
VOLUME_CREATE_MICROSTATE_TRANSITIONS = frozenset([
    (VOLUME_CREATE_MICROSTATE_ENTRY_CREATE,
     VOLUME_CREATE_MICROSTATE_QUOTA_COMMIT),
    (VOLUME_CREATE_MICROSTATE_QUOTA_COMMIT,
     VOLUME_CREATE_MICROSTATE_VOLUME_CAST),
])

# All the known 'migration' *substates* & transitions that are allowed.
#
# NOTE(harlowja): this should also be akin to a nested state-machine since
# these states are intrinsically connected to the volume status and to the
# attach status and vice-versa...
MIGRATION_COMPLETING = 'completing'
MIGRATION_ERROR = 'error'
MIGRATION_INITIAL_END = None  # TODO(harlowja): is this None or 'none'?
MIGRATION_MIGRATING = 'migrating'
MIGRATION_STARTING = 'starting'
# This seems postfixed typically with the volume id (need to fix that).
MIGRATION_TARGETING = 'target'
MIGRATION_STATES = (
    MIGRATION_COMPLETING,
    MIGRATION_ERROR,
    MIGRATION_INITIAL_END,
    MIGRATION_MIGRATING,
    MIGRATION_STARTING,
    # This needs to be reworked to not put metadata about the state inside the
    # state name itself, there is a reason metadata keys and values exist and
    # this is one of them... (this appears to be a new initial state that a
    # migrated copy starts off in...)
    MIGRATION_TARGETING,
)
MIGRATION_TRANSITIONS = frozenset([
    (MIGRATION_INITIAL_END, MIGRATION_MIGRATING),
    (MIGRATION_MIGRATING, MIGRATION_ERROR),
    # This seems to happen when an update occurs to set to the migrating
    # status, we also need to let it occur if the migrating process gets
    # killed before it goes further in the process...
    (MIGRATION_MIGRATING, MIGRATION_INITIAL_END),
    (MIGRATION_MIGRATING, MIGRATION_STARTING),
])

# All the known 'attach' *substates* & transitions that are allowed.
#
# NOTE(harlowja): this should also be akin to a nested state-machine since
# these states are intrinsically connected to the volume status and to the
# migration status and vice-versa...
ATTACH_ATTACHED = 'attached'
ATTACH_DETACHED = 'detached'
ATTACH_STATES = (
    ATTACH_ATTACHED,
    ATTACH_DETACHED,
)
ATTACH_TRANSITIONS = frozenset([
    (ATTACH_ATTACHED, ATTACH_DETACHED),
    (ATTACH_DETACHED, ATTACH_ATTACHED),
])

transition_states_map = {'attach': [ATTACH_TRANSITIONS, ATTACH_STATES],
                         'micro_states': [VOLUME_CREATE_MICROSTATE_TRANSITIONS,
                                          VOLUME_CREATE_STATES],
                         'migration': [MIGRATION_TRANSITIONS,
                                       MIGRATION_STATES],
                         'volume': [VOLUME_TRANSITIONS, VOLUME_STATES]}


# Verify if the state transition is allowed from previous state to new state
def validate_transition(state,
                        new_state, key,
                        quiet=False):
    """Check that a volume create microstate can transition.

    If transition can be performed, it returns True. If transition
    should be ignored, it returns False. If transition is not
    valid, it raises a InvalidTransition exception (if quiet is True then
    the exception is *not* raised and a warning is written to the LOG
    instead and True is returned).
    """
    try:
        return _check_transition_prefixed(state, new_state,
                                          transition_states_map[key][0],
                                          transition_states_map[key][1],
                                          identity_ignored=True)
    except (ValueError, excp.InvalidTransition) as e:
        if quiet:
            LOG.warn(_("Invalid/unknown 'attach' state transition attempted:"
                       " %(details)s"), {'details': e})
            return True
        else:
            raise
