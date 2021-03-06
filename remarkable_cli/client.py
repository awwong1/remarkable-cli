# -*- coding: utf-8 -*-
import os
import logging
from collections import deque
from shutil import rmtree
from stat import S_ISDIR, S_ISREG

import paramiko


class Client:
    def __init__(self, args):
        log_format = "%(asctime)s [%(levelname)s]: %(message)s"
        logging.basicConfig(format=log_format, level=logging.INFO)
        # logging.basicConfig(format=log_format, level=logging.DEBUG)

        self._log = logging.getLogger(__name__)
        self.args = args
        self.ssh_client = None

        # create the backup directory if not exists
        os.makedirs(self.args.backup_dir, exist_ok=True)
        self.raw_backup = os.path.join(self.args.backup_dir, ".raw")
        os.makedirs(self.raw_backup, exist_ok=True)

    @staticmethod
    def sftp_walk(ftp_client, remote_path, sub_dirs=()):
        for file_attr in ftp_client.listdir_attr(os.path.join(remote_path, *sub_dirs)):
            if S_ISDIR(file_attr.st_mode):
                # directory, recurse into the folder
                nested_sub_dirs = list(sub_dirs)
                nested_sub_dirs.append(file_attr.filename)
                yield from Client.sftp_walk(
                    ftp_client, remote_path, sub_dirs=nested_sub_dirs
                )
            elif S_ISREG(file_attr.st_mode):
                # file, yield it out
                yield file_attr, os.path.join(*sub_dirs, file_attr.filename)
            else:
                # unsupported file type
                continue

    def run_actions(self):
        """Run all of the specified actions (push, pull)"""
        # dedupe the list of actions
        actions = deque([])
        for action in self.args.action:
            if action not in actions:
                actions.append(action)

        while actions:
            action = actions.popleft()
            self._log.debug("running action: %s", action)

            if action == "push":
                self.connect()
            elif action == "pull":
                self.connect()
                self.pull_files()
            elif action == "clean-local":
                self.clean_local()
            else:
                self._log.warning("unknown action: %s", action)

        self.close()

    def connect(self):
        """Connect to the reMarkable tablet using Paramiko SSH"""
        if self.ssh_client is None:
            username = self.args.username
            hostname = self.args.destination
            port = self.args.port
            password = self.args.password
            self._log.info("Connecting to %s@%s:%d", username, hostname, port)

            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.load_system_host_keys()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    hostname=hostname,
                    username=username,
                    port=port,
                    password=password,
                    timeout=5.0,
                )
                self.ssh_client = ssh_client
            except Exception:
                self._log.error("could not connect to reMarkable tablet")
                raise
        return self.ssh_client

    def close(self):
        """Close the SSH session if it exists"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def clean_local(self):
        if os.path.exists(self.raw_backup) and os.path.isdir(self.raw_backup):
            self._log.info("removing local directory %s", self.raw_backup)
            rmtree(self.raw_backup)

    def pull_files(self):
        """Copy files from remote xochitl directory to local raw backup directory.
        Keep the access and modified times of the file specified.
        """
        ftp_client = None
        try:
            counter = 0
            ftp_client = self.ssh_client.open_sftp()
            for pf_attr, pull_file in Client.sftp_walk(ftp_client, self.args.file_path):
                counter += 1
                remote_fp = os.path.join(self.args.file_path, pull_file)
                local_fp = os.path.join(self.raw_backup, pull_file)
                local_dir = os.path.dirname(local_fp)
                os.makedirs(local_dir, exist_ok=True)

                if os.path.isfile(local_fp):
                    local_stat = os.stat(local_fp)
                    if local_stat.st_mtime <= pf_attr.st_mtime:
                        self._log.debug("skipping file %s", pull_file)
                        continue

                self._log.info("copying file %s", pull_file)
                self._log.debug(pf_attr)
                self._log.debug(pf_attr.st_atime)
                self._log.debug(pf_attr.st_mtime)
                self._log.debug("remote_fp: %s", remote_fp)
                self._log.debug("local_fp: %s", local_fp)
                self._log.debug("local_dir: %s", local_dir)

                ftp_client.get(remote_fp, local_fp)
                os.utime(local_fp, (pf_attr.st_atime, pf_attr.st_mtime))
            self._log.info("copied %d files to %s", counter, self.raw_backup)
        except Exception:
            self._log.error("could not pull files")
            raise
        finally:
            if ftp_client:
                ftp_client.close()
