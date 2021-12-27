import os.path
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready, wait_for_logs

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class SshContainer(DockerContainer):
    def __init__(self):
        super().__init__('docker.io/panubo/sshd')
        self.with_env("SSH_ENABLE_ROOT", "true")
        self.with_volume_mapping(os.path.join(root_dir, 'examples'), '/examples')
        self.with_volume_mapping(os.path.join(root_dir, 'test/id_rsa.pub'), '/root/.ssh/authorized_keys', mode='rw')
        self.with_exposed_ports("22")

    @wait_container_is_ready()
    def get_address(self):
        return self.get_container_host_ip(), self.get_exposed_port("22")

    def start(self, timeout=60):
        super().start()
        wait_for_logs(self, r'Server listening on', timeout=timeout)
        return self