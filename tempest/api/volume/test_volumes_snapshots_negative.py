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

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class VolumesV2SnapshotNegativeTestJSON(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesV2SnapshotNegativeTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @test.attr(type=['negative'])
    @decorators.idempotent_id('e3e466af-70ab-4f4b-a967-ab04e3532ea7')
    def test_create_snapshot_with_nonexistent_volume_id(self):
        # Create a snapshot with nonexistent volume id
        s_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.create_snapshot,
                          volume_id=data_utils.rand_uuid(),
                          display_name=s_name)

    @test.attr(type=['negative'])
    @decorators.idempotent_id('bb9da53e-d335-4309-9c15-7e76fd5e4d6d')
    def test_create_snapshot_without_passing_volume_id(self):
        # Create a snapshot without passing volume id
        s_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.create_snapshot,
                          volume_id=None, display_name=s_name)

    @decorators.idempotent_id('677863d1-34f9-456d-b6ac-9924f667a7f4')
    def test_volume_from_snapshot_decreasing_size(self):
        # Creates a volume a snapshot passing a size different from the source
        src_size = CONF.volume.volume_size + 1

        src_vol = self.create_volume(size=src_size)
        src_snap = self.create_snapshot(src_vol['id'])

        # Destination volume smaller than source
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume,
                          size=src_size - 1,
                          snapshot_id=src_snap['id'])


class VolumesV1SnapshotNegativeTestJSON(VolumesV2SnapshotNegativeTestJSON):
    _api_version = 1
