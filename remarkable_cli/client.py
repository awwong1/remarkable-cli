# -*- coding: utf-8 -*-
import json
import logging
import os
from argparse import Namespace
from collections import deque
from glob import glob
from shutil import rmtree
from stat import S_ISDIR, S_ISREG

import paramiko
from requests import Request, Session, adapters

from .convert_rm import ConvertRM


class Client:
    LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]

    def __init__(self, args: Namespace):
        log_format = "%(asctime)s [%(levelname)s]: %(message)s"
        log_level = Client.LOG_LEVELS[min(args.log_level, len(Client.LOG_LEVELS) - 1)]
        logging.basicConfig(format=log_format, level=logging.getLevelName(log_level))

        self._log = logging.getLogger(__name__)
        self.args = args
        self.ssh_client = None

        # create the backup directory if not exists
        os.makedirs(self.args.backup_dir, exist_ok=True)
        self.backup_dir = self.args.backup_dir
        self.raw_backup_dir = os.path.join(self.args.backup_dir, ".raw")
        self.templates_dir = os.path.join(self.args.backup_dir, "templates")
        self.pdf_backup_dir = os.path.join(self.args.backup_dir, "My files")
        self.trash_backup_dir = os.path.join(self.args.backup_dir, "Trash")

    @staticmethod
    def sftp_walk(ftp_client, remote_path, sub_dirs=()):
        """Walk through the remote reMarkable directory structure"""
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

    @staticmethod
    def _get_path(meta_id, metadata, dir_hierarchy: deque = []):
        """Get the entity relative path"""
        meta = metadata.get(meta_id)
        if meta is None:
            raise RuntimeError(f"meta_id: {meta_id} does not exist")
        visible_name = meta.get("visibleName")

        parent_id = meta.get("parent")
        is_trash = False
        if parent_id == "trash":
            is_trash = True
        elif parent_id:
            nested_dir_hierarchy = deque(dir_hierarchy)
            nested_dir_hierarchy.appendleft(visible_name)
            return Client._get_path(
                parent_id, metadata, dir_hierarchy=nested_dir_hierarchy
            )

        basename = os.path.join(visible_name, *dir_hierarchy)
        return basename, is_trash

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
                self._log.warning("not implemented")
            elif action == "pull":
                self.connect()
                self.pull_template_files()
                self.pull_xochitl_files()
                self.convert_xochitl_files()
            elif action == "pull-raw":
                self.connect()
                self.pull_xochitl_files()
            elif action == "pull-web":
                self.pull_pdf_files()
            elif action == "convert-raw":
                self.convert_xochitl_files()
            elif action == "clean-local":
                self.clean_local()
            else:
                self._log.warning("unknown action: %s", action)

        self.close()
        self._log.info("actions completed, see %s", self.backup_dir)

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
        """Remove the local xochitl and pdf backup directories if exists."""
        backup_dirs = [
            self.raw_backup_dir,
            self.templates_dir,
            self.pdf_backup_dir,
            self.trash_backup_dir,
        ]
        for backup_dir in backup_dirs:
            if os.path.exists(backup_dir) and os.path.isdir(backup_dir):
                self._log.info("removing local directory %s", backup_dir)
                rmtree(backup_dir)

    def _pull_sftp_files(self, remote_path, local_path):
        ftp_client = None
        try:
            counter = 0
            ftp_client = self.ssh_client.open_sftp()
            for pf_attr, pull_file in Client.sftp_walk(ftp_client, remote_path):
                counter += 1
                remote_fp = os.path.join(remote_path, pull_file)
                local_fp = os.path.join(local_path, pull_file)
                local_dir = os.path.dirname(local_fp)
                os.makedirs(local_dir, exist_ok=True)

                if os.path.isfile(local_fp):
                    local_stat = os.stat(local_fp)
                    if local_stat.st_mtime >= pf_attr.st_mtime:
                        self._log.debug("skipping file %s", pull_file)
                        continue

                self._log.info("copying file %s", pull_file)
                self._log.debug(pf_attr)
                self._log.debug("remote stat access time: %d", pf_attr.st_atime)
                self._log.debug("remote stat modified time: %d", pf_attr.st_mtime)
                self._log.debug("remote_fp: %s", remote_fp)
                self._log.debug("local_fp: %s", local_fp)
                self._log.debug("local_dir: %s", local_dir)

                ftp_client.get(remote_fp, local_fp)
                os.utime(local_fp, (pf_attr.st_atime, pf_attr.st_mtime))
            self._log.info("pulled %d files to %s", counter, local_path)
        except Exception:
            self._log.error("could not pull files")
            raise
        finally:
            if ftp_client:
                ftp_client.close()

    def pull_xochitl_files(self):
        """Copy files from remote xochitl directory to local raw backup directory.
        Keep the access and modified times of the file specified.
        """
        os.makedirs(self.raw_backup_dir, exist_ok=True)
        self._pull_sftp_files(self.args.file_path, self.raw_backup_dir)

    def pull_template_files(self):
        """Copy files from remote templates directory to local templates directory."""
        os.makedirs(self.templates_dir, exist_ok=True)
        self._pull_sftp_files(self.args.templates_path, self.templates_dir)

    def _derive_metadata(self):
        metadata = {}
        # get the xochitl metadata into memory from disk
        meta_fps = glob(os.path.join(self.raw_backup_dir, "*.metadata"))
        for meta_fp in meta_fps:
            with open(meta_fp, "r") as fh:
                meta = json.load(fh)
            meta_id = os.path.splitext(os.path.basename(meta_fp))[0]
            metadata[meta_id] = meta
        return metadata

    def _request_file_entity(self, session: Session, url: str, timeout=(9.03, 30.03)):
        headers = {
            "Host": self.args.destination,
            "Accept": (
                "text/html,application/xhtml+xml,"
                + "application/xml;q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": f"http://{self.args.destination}/",
            "Upgrade-Insecure-Requests": "1",
            "Sec-GPC": "1",
        }
        try:
            req = Request("GET", url, headers=headers)
            prepped = session.prepare_request(req)
            self._log.debug("GET %s", url)
            res = session.send(prepped, timeout=timeout)

            if res.status_code != 200:
                raise ConnectionError(f"failed to GET {url}")
            return res
        except Exception:
            self._log.warning("failed to GET %s", url)
            raise

    def pull_pdf_files(self):
        """Use the web interface to download pdfs.
        This should really be a conversion of the local xochitl files instead."""
        os.makedirs(self.pdf_backup_dir, exist_ok=True)
        os.makedirs(self.trash_backup_dir, exist_ok=True)
        metadata = self._derive_metadata()

        counter_ok = 0
        counter_total = 0

        with Session() as session:
            adapter = adapters.HTTPAdapter(max_retries=0)
            session.mount("http://", adapter)

            for meta_id, meta in metadata.items():
                path, is_trash = Client._get_path(meta_id, metadata)
                self._log.debug(path)
                self._log.debug(meta)

                local_dir = self.trash_backup_dir if is_trash else self.pdf_backup_dir
                meta_type = meta.get("type")
                meta_deleted = meta.get("deleted", False)

                if meta_deleted:
                    continue

                if meta_type == "DocumentType":
                    # is file, download as a PDF
                    rel_fp = f"{path}{os.path.extsep}pdf"
                    path = os.path.join(local_dir, rel_fp)
                    os.makedirs(os.path.dirname(path), exist_ok=True)

                    # if local file exists and has up-to-date modified time, ignore
                    last_modified = int(meta.get("lastModified", "0"))
                    if os.path.isfile(path):
                        local_stat = os.stat(path)
                        if local_stat.st_mtime >= last_modified:
                            self._log.debug("skipping %s", rel_fp)
                            continue

                    self._log.info("retrieving %s", rel_fp)
                    url = (
                        f"http://{self.args.destination}/download/{meta_id}/placeholder"
                    )
                    try:
                        res = self._request_file_entity(session, url)
                        with open(path, "wb") as fh:
                            fh.write(res.content)
                        os.utime(path, (last_modified, last_modified))
                        counter_ok += 1
                    except Exception:
                        self._log.warning("skipping %s", rel_fp)
                        continue
                    finally:
                        counter_total += 1

                elif meta_type == "CollectionType":
                    # is a folder, ensure exists and continue
                    os.makedirs(os.path.join(local_dir, path), exist_ok=True)
                else:
                    self._log.warning(
                        "entity %s has unsupported type: %s", meta_id, meta_type
                    )
                    continue

        self._log.info(
            "pulled %d/%d pdf files to %s",
            counter_ok,
            counter_total,
            self.args.backup_dir,
        )

    def convert_xochitl_files(self):
        os.makedirs(self.pdf_backup_dir, exist_ok=True)
        os.makedirs(self.trash_backup_dir, exist_ok=True)

        metadata = self._derive_metadata()
        meta_fps = glob(os.path.join(self.raw_backup_dir, "*.metadata"))
        for meta_fp in meta_fps:
            uuid_fp = os.path.splitext(meta_fp)[0]
            if not os.path.isdir(uuid_fp):
                self._log.debug("skipping %s", meta_fp)
                continue
            meta_id = os.path.basename(uuid_fp)
            meta = metadata[meta_id]

            path, is_trash = Client._get_path(meta_id, metadata)
            local_dir = self.trash_backup_dir if is_trash else self.pdf_backup_dir
            rel_fp = f"{path}{os.path.extsep}pdf"
            path = os.path.join(local_dir, rel_fp)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # if local file exists and has up-to-date modified time, ignore
            last_modified = int(meta.get("lastModified", "0"))
            if os.path.isfile(path):
                local_stat = os.stat(path)
                if local_stat.st_mtime >= last_modified:
                    self._log.debug("skipping %s", rel_fp)
                    continue

            converter = ConvertRM(uuid_fp, self.templates_dir, logger=self._log)

            disp_fp = (
                os.path.join("trash", rel_fp)
                if is_trash
                else os.path.join("My files", rel_fp)
            )
            self._log.info("rendering %s", disp_fp)
            converter.convert_document(path)
            os.utime(path, (last_modified, last_modified))
