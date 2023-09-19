from math import pi
import unittest

import numpy as np

from spatial_effects import SE3, Transform, TransformTree, TransformForest

# Humanoid transform tree
skeleton = [
    Transform(SE3([1, 2, 3], [0, 0, 0]), "body", "origin"),
    Transform(SE3([0, 0, 0.5], [0, 0, -pi / 3]), "head", "body"),
    Transform(SE3([0, 1, 0], [0, 0, 0]), "l_shoulder", "body"),
    Transform(SE3([0, -1, 0], [0, 0, 0]), "r_shoulder", "body"),
    Transform(SE3([0, 0, -0.7], [0, -pi / 6, 0]), "l_elbow", "l_shoulder"),
    Transform(SE3([0, 0, -0.7], [0, -pi / 3, 0]), "r_elbow", "r_shoulder"),
    Transform(SE3([0, 0, -0.6], [0, 0, 0]), "l_wrist", "l_elbow"),
    Transform(SE3([0, 0, -0.6], [0, 0, 0]), "r_wrist", "r_elbow"),
    Transform(SE3([0, 0, -1], [0, 0, pi / 8]), "waist", "body"),
    Transform(SE3([0, 0.4, 0], [0, -pi / 4, 0]), "l_hip", "waist"),
    Transform(SE3([0, -0.4, 0], [0, 0, 0]), "r_hip", "waist"),
    Transform(SE3([0, 0, -1.2], [0, pi / 2, 0]), "l_knee", "l_hip"),
    Transform(SE3([0, 0, -1.2], [0, 0, 0]), "r_knee", "r_hip"),
    Transform(SE3([0, 0, -0.9], [0, -pi / 8, 0]), "l_ankle", "l_knee"),
    Transform(SE3([0, 0, -0.9], [0, 0, 0]), "r_ankle", "r_knee"),
    Transform(SE3([0.2, 0, 0], [0, 0, 0]), "l_foot", "l_ankle"),
    Transform(SE3([0.2, 0, 0], [0, 0, 0]), "r_foot", "r_ankle"),
]


class TransformTests(unittest.TestCase):
    def setUp(self) -> None:
        np.set_printoptions(precision=5, suppress=True)
        self.transform = Transform(SE3([0.2, 0, 0], [0, 0, 0]), "r_foot", "r_ankle")

    def test_transform_to_dict(self):
        print("\ntest_transform_to_dict")
        actual_serialized_transform = self.transform.to_dict()
        expected_serialized_transform = Transform.from_dict(actual_serialized_transform).to_dict()

        self.assertDictEqual(actual_serialized_transform, expected_serialized_transform)


class TransformTreeTests(unittest.TestCase):
    def setUp(self):
        """Runs before every test function."""
        np.set_printoptions(precision=5, suppress=True)

        self.tt = TransformTree(skeleton)

    def test_transform_tree_serialization(self):
        print("\ntest_transform_tree_serialization")
        actual_serialized_transform_tree = self.tt.to_list()
        new_tt = TransformTree.from_list(actual_serialized_transform_tree)

        with self.subTest("Test equality of serialized transform tree"):
            expected_serialized_transform_tree = new_tt.to_list()
            self.assertListEqual(
                actual_serialized_transform_tree, expected_serialized_transform_tree
            )

        with self.subTest("Test rendered transform tree match"):
            root_node = self.tt.root
            expected_transform_tree_str = new_tt.render(root_node)
            self.assertEqual(self.tt.render(root_node), expected_transform_tree_str)

    def test_tree_traversal_1(self):
        """Identity"""
        print("\ntest_tree_traversal_1")
        self.assertEqual(self.tt.get_se3("l_knee", "l_knee"), SE3())

    def test_tree_traversal_2(self):
        """Symmetry"""
        print("\ntest_tree_traversal_2")
        self.assertEqual(
            self.tt.get_se3("l_knee", "r_knee"),
            self.tt.get_se3("r_knee", "l_knee").inverse,
        )

    def test_tree_traversal_3(self):
        """Invalid frame name"""
        print("\ntest_tree_traversal_3")
        self.assertRaises(LookupError, self.tt.get_se3, "bogus_frame", "origin")

    def test_orphan_update(self):
        """Adding an orphaned coordinate frame"""
        print("\ntest_orphan_update")
        orphan = Transform(
            SE3([1, 0, 0], [0, 0, 0]), "disconnected_child", "disconnected_parent"
        )
        self.assertRaises(ValueError, self.tt.update, orphan)


class TransformForestTests(unittest.TestCase):
    def setUp(self):
        """Runs before every test function."""
        np.set_printoptions(precision=5, suppress=True)

        # Add a transform that has no connection to the skeleton
        orphan = Transform(
            SE3([1, 0, 0], [0, 0, 0]), "disconnected_child", "disconnected_parent"
        )

        self.tf = TransformForest([*skeleton, orphan])

    def check_eq(self, a, b, atol=1e-8):
        """Test for approximate equality."""
        self.assertTrue(np.allclose(a, b, atol=atol))

    def print_different(self, a, b):
        different = ~np.all(np.isclose(a, b), axis=1)
        for a, b in zip(a[different], b[different]):
            print(a, b)

    def test_forest_serialization(self):
        print("\ntest_forest_serialization")
        actual_serialized_transform_forest = self.tf.to_list()
        new_tf = TransformForest.from_list(actual_serialized_transform_forest)

        with self.subTest("Test equality of serialized transform forest"):
            expected_serialized_transform_forest = new_tf.to_list()
            self.assertListEqual(
                actual_serialized_transform_forest, expected_serialized_transform_forest
            )

        with self.subTest("Test rendered transform forest match"):
            expected_transform_forest_str = str(new_tf)
            self.assertEqual(str(self.tf), expected_transform_forest_str)

    def test_str(self):
        print("\ntest_forest_str_method")
        print(self.tf)

    def test_forest_traversal_1(self):
        """Identity"""
        print("\ntest_forest_traversal_1")
        self.assertEqual(self.tf.get_se3("l_knee", "l_knee"), SE3())

    def test_forest_traversal_2(self):
        """Symmetry"""
        print("\ntest_forest_traversal_2")
        self.assertEqual(
            self.tf.get_se3("l_knee", "r_knee"),
            self.tf.get_se3("r_knee", "l_knee").inverse,
        )

    def test_forest_traversal_3(self):
        """Invalid frame name"""
        print("\ntest_forest_traversal_3")
        self.assertRaises(LookupError, self.tf.get_se3, "bogus_frame", "origin")

    def test_forest_traversal_4(self):
        """Disconnected trees"""
        print("\ntest_forest_traversal_4")
        self.assertRaises(LookupError, self.tf.get_se3, "disconnected_child", "l_elbow")

    def test_forest_traversal_5(self):
        """Disconnected trees"""
        print("\ntest_forest_traversal_5")
        self.tf.get_se3("disconnected_child", "disconnected_parent")
