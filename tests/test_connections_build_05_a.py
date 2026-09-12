"""Mock topology migration coverage for Build 05-A."""

import importlib.util
import pathlib
import sys
import types
import unittest


class Connections(list):
    def add(self):
        item = types.SimpleNamespace(target_object=None, target_endpoint="START")
        self.append(item)
        return item

    def remove(self, index):
        del self[index]


class Wall:
    def __init__(self, name):
        self.name = name
        self.users_collection = [object()]
        self.jhm_wall = types.SimpleNamespace(
            is_wall=True,
            start_connections=Connections(),
            end_connections=Connections(),
        )


class ObjectRegistry(list):
    def get(self, name):
        return next((item for item in self if item.name == name), None)


ROOT = pathlib.Path(__file__).parents[1]
bpy = types.ModuleType("bpy")
bpy.data = types.SimpleNamespace(objects=ObjectRegistry())
sys.modules["bpy"] = bpy
SPEC = importlib.util.spec_from_file_location(
    "build05_connections", ROOT / "japanese_house_modeler" / "connections.py"
)
connections = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(connections)


class EndpointTransferTests(unittest.TestCase):
    def setUp(self):
        bpy.data.objects.clear()

    def walls(self, count):
        result = [Wall(f"wall-{index}") for index in range(count)]
        bpy.data.objects.extend(result)
        return result

    def test_no_connections_is_safe(self):
        source, destination = self.walls(2)
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        self.assertEqual(len(source.jhm_wall.end_connections), 0)
        self.assertEqual(len(destination.jhm_wall.end_connections), 0)

    def test_one_connection_moves_reciprocally(self):
        source, destination, peer = self.walls(3)
        connections.add_reciprocal(source, "END", peer, "START")
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        self.assertEqual(connections.valid_connection_count(source, "END"), 0)
        self.assertEqual(connections.valid_connection_count(destination, "END"), 1)
        target = peer.jhm_wall.start_connections[0]
        self.assertIs(target.target_object, destination)
        self.assertEqual(target.target_endpoint, "END")

    def test_one_sided_connection_is_not_promoted_during_transfer(self):
        source, destination, peer = self.walls(3)
        copied = source.jhm_wall.end_connections.add()
        copied.target_object = peer
        copied.target_endpoint = "START"

        connections.transfer_endpoint_connections(
            source, "END", destination, "END"
        )

        self.assertEqual(len(source.jhm_wall.end_connections), 0)
        self.assertEqual(len(destination.jhm_wall.end_connections), 0)
        self.assertEqual(len(peer.jhm_wall.start_connections), 0)

    def test_multiple_connections_preserve_peer_edges_and_no_duplicates(self):
        source, destination, first, second = self.walls(4)
        connections.add_reciprocal(source, "END", first, "START")
        connections.add_reciprocal(source, "END", second, "START")
        connections.add_reciprocal(first, "START", second, "START")
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        self.assertEqual(connections.valid_connection_count(destination, "END"), 2)
        self.assertEqual(connections.valid_connection_count(first, "START"), 2)
        self.assertEqual(connections.valid_connection_count(second, "START"), 2)

    def test_invalid_target_is_purged(self):
        source, destination, stale = self.walls(3)
        connections.add_reciprocal(source, "END", stale, "START")
        bpy.data.objects.remove(stale)
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        self.assertEqual(len(source.jhm_wall.end_connections), 0)
        self.assertEqual(len(destination.jhm_wall.end_connections), 0)

    def test_topology_snapshot_can_roll_back_a_partial_transfer(self):
        source, destination, peer = self.walls(3)
        connections.add_reciprocal(source, "END", peer, "START")
        snapshot = connections.snapshot_topology()
        connections.transfer_endpoint_connections(source, "END", destination, "END")
        connections.restore_topology(snapshot)
        self.assertEqual(connections.valid_connection_count(source, "END"), 1)
        self.assertEqual(connections.valid_connection_count(destination, "END"), 0)
        self.assertIs(peer.jhm_wall.start_connections[0].target_object, source)

    def test_reciprocal_edge_is_trusted(self):
        source, peer = self.walls(2)
        connections.add_reciprocal(source, "START", peer, "END")
        edge = source.jhm_wall.start_connections[0]
        self.assertTrue(connections.is_reciprocal_connection(source, "START", edge))
        self.assertTrue(connections.topology_is_consistent(source))

    def test_shift_duplicate_one_sided_edge_is_not_trusted_and_is_cleaned(self):
        source, peer = self.walls(2)
        edge = source.jhm_wall.start_connections.add()
        edge.target_object = peer
        edge.target_endpoint = "END"
        self.assertFalse(connections.is_reciprocal_connection(source, "START", edge))
        self.assertFalse(connections.topology_is_consistent(source))
        connections.cleanup_untrusted_connections(source)
        self.assertEqual(len(source.jhm_wall.start_connections), 0)

    def test_cleanup_preserves_complete_peer_graph(self):
        source, first, second, stale = self.walls(4)
        connections.add_reciprocal(source, "END", first, "START")
        connections.add_reciprocal(source, "END", second, "START")
        connections.add_reciprocal(first, "START", second, "START")
        bad = source.jhm_wall.end_connections.add()
        bad.target_object = stale
        bad.target_endpoint = "START"
        bpy.data.objects.remove(stale)
        connections.cleanup_untrusted_connections(source)
        self.assertEqual(connections.valid_connection_count(source, "END"), 2)
        self.assertEqual(connections.valid_connection_count(first, "START"), 2)
        self.assertEqual(connections.valid_connection_count(second, "START"), 2)


if __name__ == "__main__":
    unittest.main()
