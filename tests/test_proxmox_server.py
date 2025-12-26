import unittest
from unittest import mock

from config import settings
from lib import common, helpers, utils


class TestProxmoxServer(unittest.TestCase):
    def test_reference_ips(self):
        self.assertTrue(utils.is_proxmox_server("192.168.30.10"))
        for ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"]:
            self.assertTrue(utils.is_proxmox_server(ip))
        self.assertFalse(utils.is_proxmox_server("192.168.20.31"))
        self.assertFalse(utils.is_proxmox_server("10.0.0.1"))

    def test_settings_exports_shared_function(self):
        self.assertIs(settings.is_proxmox_server, utils.is_proxmox_server)

    def test_helpers_delegate_to_utils(self):
        with mock.patch("lib.utils.is_proxmox_server", return_value=True) as mocked:
            result = helpers.is_proxmox_server("192.168.30.10")
        mocked.assert_called_once_with("192.168.30.10")
        self.assertTrue(result)

    def test_common_delegate_to_utils(self):
        with mock.patch("lib.utils.is_proxmox_server", return_value=False) as mocked:
            result = common.is_proxmox_server("10.0.0.1")
        mocked.assert_called_once_with("10.0.0.1")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
