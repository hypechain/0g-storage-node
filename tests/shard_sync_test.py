#!/usr/bin/env python3
import time

from test_framework.test_framework import TestFramework
from utility.submission import create_submission, submit_data
from utility.utils import wait_until, assert_equal


class PrunerTest(TestFramework):

    def setup_params(self):
        self.num_blockchain_nodes = 1
        self.num_nodes = 3
        self.zgs_node_configs[0] = {
            "db_max_num_chunks": 2 ** 30,
            "shard_position": "0/2"
        }
        self.zgs_node_configs[1] = {
            "db_max_num_chunks": 2 ** 30,
            "shard_position": "1/2"
        }

    def run_test(self):
        client = self.nodes[0]

        chunk_data = b"\x02" * 8 * 256 * 1024
        submissions, data_root = create_submission(chunk_data)
        self.contract.submit(submissions)
        wait_until(lambda: self.contract.num_submissions() == 1)
        wait_until(lambda: client.zgs_get_file_info(data_root) is not None)

        # Submit data to two nodes with different shards.
        segment = submit_data(client, chunk_data)
        submit_data(self.nodes[1], chunk_data)

        self.nodes[2].admin_start_sync_file(0)
        wait_until(lambda: self.nodes[2].sycn_status_is_completed_or_unknown(0))
        wait_until(lambda: self.nodes[2].zgs_get_file_info(data_root)["finalized"])

        for i in range(len(segment)):
            index_store = i % 2
            index_empty = 1 - i % 2
            seg0 = self.nodes[index_store].zgs_download_segment(data_root, i * 1024, (i + 1) * 1024)
            seg1 = self.nodes[index_empty].zgs_download_segment(data_root, i * 1024, (i + 1) * 1024)
            seg2 = self.nodes[2].zgs_download_segment(data_root, i * 1024, (i + 1) * 1024)
            # base64 encoding size
            assert_equal(len(seg0), 349528)
            assert_equal(seg1, None)
            # node 2 should save all data
            assert_equal(len(seg2), 349528)


if __name__ == "__main__":
    PrunerTest().main()
