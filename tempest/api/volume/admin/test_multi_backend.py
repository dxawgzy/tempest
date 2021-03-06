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

import six
from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumeMultiBackendV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(VolumeMultiBackendV2Test, cls).skip_checks()

        if not CONF.volume_feature_enabled.multi_backend:
            raise cls.skipException("Cinder multi-backend feature disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumeMultiBackendV2Test, cls).resource_setup()

        # read backend name from a list .
        cls.backend_names = set(CONF.volume.backend_names)

        cls.name_field = cls.special_fields['name_field']
        cls.volume_type_id_list = []
        cls.volume_id_list_with_prefix = []
        cls.volume_id_list_without_prefix = []

        # Volume/Type creation (uses volume_backend_name)
        # It is not allowed to create the same backend name twice
        if len(cls.backend_names) < 2:
            raise cls.skipException("Requires at least two different "
                                    "backend names")
        for backend_name in cls.backend_names:
            # Volume/Type creation (uses backend_name)
            cls._create_type_and_volume(backend_name, False)
            # Volume/Type creation (uses capabilities:volume_backend_name)
            cls._create_type_and_volume(backend_name, True)

    @classmethod
    def _create_type_and_volume(cls, backend_name_key, with_prefix):
        # Volume/Type creation
        type_name = data_utils.rand_name(cls.__name__ + '-Type')
        vol_name = data_utils.rand_name(cls.__name__ + '-Volume')
        spec_key_with_prefix = "capabilities:volume_backend_name"
        spec_key_without_prefix = "volume_backend_name"
        if with_prefix:
            extra_specs = {spec_key_with_prefix: backend_name_key}
        else:
            extra_specs = {spec_key_without_prefix: backend_name_key}
        cls.type = cls.create_volume_type(name=type_name,
                                          extra_specs=extra_specs)

        params = {cls.name_field: vol_name, 'volume_type': type_name,
                  'size': CONF.volume.volume_size}
        cls.volume = cls.admin_volume_client.create_volume(
            **params)['volume']
        if with_prefix:
            cls.volume_id_list_with_prefix.append(cls.volume['id'])
        else:
            cls.volume_id_list_without_prefix.append(
                cls.volume['id'])
        waiters.wait_for_volume_status(cls.admin_volume_client,
                                       cls.volume['id'], 'available')

    @classmethod
    def resource_cleanup(cls):
        # volumes deletion
        vid_prefix = getattr(cls, 'volume_id_list_with_prefix', [])
        for volume_id in vid_prefix:
            cls.admin_volume_client.delete_volume(volume_id)
            cls.admin_volume_client.wait_for_resource_deletion(volume_id)

        vid_no_pre = getattr(cls, 'volume_id_list_without_prefix', [])
        for volume_id in vid_no_pre:
            cls.admin_volume_client.delete_volume(volume_id)
            cls.admin_volume_client.wait_for_resource_deletion(volume_id)

        super(VolumeMultiBackendV2Test, cls).resource_cleanup()

    @decorators.idempotent_id('c1a41f3f-9dad-493e-9f09-3ff197d477cc')
    def test_backend_name_reporting(self):
        # get volume id which created by type without prefix
        for volume_id in self.volume_id_list_without_prefix:
            self._test_backend_name_reporting_by_volume_id(volume_id)

    @decorators.idempotent_id('f38e647f-ab42-4a31-a2e7-ca86a6485215')
    def test_backend_name_reporting_with_prefix(self):
        # get volume id which created by type with prefix
        for volume_id in self.volume_id_list_with_prefix:
            self._test_backend_name_reporting_by_volume_id(volume_id)

    @decorators.idempotent_id('46435ab1-a0af-4401-8373-f14e66b0dd58')
    def test_backend_name_distinction(self):
        # get volume ids which created by type without prefix
        self._test_backend_name_distinction(self.volume_id_list_without_prefix)

    @decorators.idempotent_id('4236305b-b65a-4bfc-a9d2-69cb5b2bf2ed')
    def test_backend_name_distinction_with_prefix(self):
        # get volume ids which created by type without prefix
        self._test_backend_name_distinction(self.volume_id_list_with_prefix)

    def _get_volume_host(self, volume_id):
        return self.admin_volume_client.show_volume(
            volume_id)['volume']['os-vol-host-attr:host']

    def _test_backend_name_reporting_by_volume_id(self, volume_id):
        # this test checks if os-vol-attr:host is populated correctly after
        # the multi backend feature has been enabled
        # if multi-backend is enabled: os-vol-attr:host should be like:
        # host@backend_name
        volume = self.admin_volume_client.show_volume(volume_id)['volume']

        volume1_host = volume['os-vol-host-attr:host']
        msg = ("multi-backend reporting incorrect values for volume %s" %
               volume_id)
        self.assertGreater(len(volume1_host.split("@")), 1, msg)

    def _test_backend_name_distinction(self, volume_id_list):
        # this test checks that the volumes created at setUp don't
        # belong to the same backend (if they are, than the
        # volume backend distinction is not working properly)
        volume_hosts = [self._get_volume_host(volume) for volume in
                        volume_id_list]
        # assert that volumes are each created on separate hosts:
        msg = ("volumes %s were created in the same backend" % ", "
               .join(volume_hosts))
        six.assertCountEqual(self, volume_hosts, set(volume_hosts), msg)


class VolumeMultiBackendV1Test(VolumeMultiBackendV2Test):
    _api_version = 1
