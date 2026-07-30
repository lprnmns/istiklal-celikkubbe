from __future__ import annotations

import argparse
import importlib.util
import os
import socket
import tempfile
import unittest
from pathlib import Path


ONE_CLICK = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launcher = load_module("one_click_launcher", ONE_CLICK / "launcher.py")
docker_toggle = load_module("docker_one_click_launcher", ONE_CLICK / "docker" / "docker_toggle.py")


class NativeLauncherTests(unittest.TestCase):
    def test_occupied_port_is_not_reported_available(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("0.0.0.0", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            self.assertFalse(launcher.port_available(port))

    def test_operation_lock_rejects_rapid_second_click(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_runtime = launcher.RUNTIME_DIR
            original_lock = launcher.LOCK_PATH
            launcher.RUNTIME_DIR = Path(directory)
            launcher.LOCK_PATH = Path(directory) / "operation.lock"
            try:
                with launcher.operation_lock():
                    with self.assertRaises(launcher.OperationBusy):
                        with launcher.operation_lock():
                            pass
            finally:
                launcher.RUNTIME_DIR = original_runtime
                launcher.LOCK_PATH = original_lock

    def test_stop_never_kills_unrelated_reused_pid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_state = launcher.STATE_PATH
            launcher.STATE_PATH = Path(directory) / "runtime.json"
            launcher.save_state(
                {
                    "pid": os.getpid(),
                    "port": 65534,
                    "process_create_time": 1.0,
                }
            )
            try:
                with self.assertRaises(launcher.LaunchError):
                    launcher.stop(argparse.Namespace(gui=False))
                self.assertTrue(launcher.process_exists(os.getpid()))
            finally:
                launcher.STATE_PATH = original_state


class DockerLauncherTests(unittest.TestCase):
    def test_operation_lock_rejects_rapid_second_click(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original_lock = docker_toggle.LOCK_FILE
            docker_toggle.LOCK_FILE = Path(directory) / "operation.lock"
            try:
                with docker_toggle.operation_lock():
                    with self.assertRaises(docker_toggle.OperationBusy):
                        with docker_toggle.operation_lock():
                            pass
            finally:
                docker_toggle.LOCK_FILE = original_lock


if __name__ == "__main__":
    unittest.main()
