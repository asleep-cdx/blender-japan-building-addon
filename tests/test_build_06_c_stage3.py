"""Pure coverage for Build 06-C Stage 3 Profile preview/browser behavior."""

import ast
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).parents[1]
package = types.ModuleType("japanese_house_modeler")
package.__path__ = [str(ROOT / "japanese_house_modeler")]
sys.modules.setdefault("japanese_house_modeler", package)

from japanese_house_modeler.finish_custom_profiles import make_snapshot
from japanese_house_modeler.finish_profile_previews import (
    PREVIEW_PADDING, PREVIEW_SIZE, browser_items, fit_contour, orient_preview,
    preview_cache_key, rasterize_preview, stable_profile_identity,
    STANDARD_REVISIONS, validated_profile_identity,
)
from japanese_house_modeler.finish_profiles import (
    BEVEL_PROFILE_REVISION, ROUNDED_PROFILE_REVISION,
    SIMPLE_PROFILE_REVISION,
)


def definition(profile_id="CUSTOM-z", contour=((0, 0), (0, 2), (1, 2), (1, 0)),
               source_type="POLY"):
    return types.SimpleNamespace(
        profile_id=profile_id, profile_revision=1, schema_version=1,
        display_name="Saved snapshot", source_type=source_type,
        points=[types.SimpleNamespace(x=x, y=y) for x, y in contour])


class PreviewMathTests(unittest.TestCase):
    def test_fit_preserves_aspect_ratio(self):
        fitted = fit_contour(((0, 0), (0, 4), (2, 4), (2, 0)))
        width = max(x for x, _ in fitted) - min(x for x, _ in fitted)
        height = max(y for _, y in fitted) - min(y for _, y in fitted)
        self.assertAlmostEqual(width / height, .5)

    def test_fit_respects_padding_and_centres_short_axis(self):
        fitted = fit_contour(((0, 0), (0, 4), (2, 4), (2, 0)))
        self.assertAlmostEqual(min(y for _, y in fitted), PREVIEW_PADDING)
        self.assertAlmostEqual(max(y for _, y in fitted), PREVIEW_SIZE - PREVIEW_PADDING)
        self.assertAlmostEqual(min(x for x, _ in fitted) + max(x for x, _ in fitted),
                               PREVIEW_SIZE)

    def test_fit_is_deterministic(self):
        contour = ((3, 7), (3, 9), (8, 9), (8, 7))
        self.assertEqual(fit_contour(contour), fit_contour(contour))

    def test_invalid_contour_has_textual_fallback_path(self):
        item = browser_items([definition(contour=())])[-1]
        self.assertTrue(item.fallback)
        with self.assertRaisesRegex(ValueError, "fallback"):
            rasterize_preview(item)


class IdentityAndOrderingTests(unittest.TestCase):
    def test_stable_identity_uses_schema_not_row(self):
        item = definition("CUSTOM-id")
        self.assertEqual(stable_profile_identity(item), ("CUSTOM-id", 1, 1))

    def test_standards_then_custom_identity_order(self):
        items = browser_items([definition("CUSTOM-z"), definition("CUSTOM-a")])
        self.assertEqual(tuple(item.profile_id for item in items),
                         ("SIMPLE", "BEVEL", "ROUNDED", "CUSTOM-a", "CUSTOM-z"))

    def test_standard_shapes_are_visually_distinct(self):
        items = browser_items(())[:3]
        self.assertEqual(len({item.contour for item in items}), 3)

    def test_cache_key_uses_content_and_context(self):
        first = browser_items([definition()])[-1]
        changed = browser_items([definition(contour=((0, 0), (0, 3), (1, 2), (1, 0)))])[-1]
        self.assertNotEqual(preview_cache_key(first), preview_cache_key(changed))
        self.assertNotEqual(preview_cache_key(first, "BASEBOARD"),
                            preview_cache_key(first, "CROWN"))

    def test_standard_revision_mapping_uses_family_constants(self):
        self.assertEqual(STANDARD_REVISIONS, {
            "SIMPLE": SIMPLE_PROFILE_REVISION,
            "BEVEL": BEVEL_PROFILE_REVISION,
            "ROUNDED": ROUNDED_PROFILE_REVISION,
        })

    def test_exact_three_part_custom_identity_is_required(self):
        library = [definition("CUSTOM-id")]
        self.assertEqual(
            validated_profile_identity("CUSTOM-id", 1, 1, library),
            ("CUSTOM-id", 1, 1))
        for stale in (("CUSTOM-id", 2, 1), ("CUSTOM-id", 1, 2)):
            with self.assertRaisesRegex(ValueError, "identity"):
                validated_profile_identity(*stale, library)

    def test_standard_identity_rejects_stale_revision_or_schema(self):
        with self.assertRaisesRegex(ValueError, "identity"):
            validated_profile_identity("BEVEL", BEVEL_PROFILE_REVISION + 1, 1, ())
        with self.assertRaisesRegex(ValueError, "identity"):
            validated_profile_identity("ROUNDED", ROUNDED_PROFILE_REVISION, 2, ())


class OrientationAndSnapshotTests(unittest.TestCase):
    def test_baseboard_rises_up(self):
        result = orient_preview(((0, 0), (1, 2)), "BASEBOARD")
        self.assertEqual(result, ((0.0, 0.0), (1.0, 2.0)))

    def test_crown_hangs_down(self):
        result = orient_preview(((0, 0), (1, 2)), "CROWN")
        self.assertEqual(result, ((0.0, -0.0), (1.0, -2.0)))

    def test_preview_does_not_mutate_snapshot(self):
        source = definition(contour=((.1, .2), (.1, 2), (1, 2), (1, .2)))
        before = tuple((point.x, point.y) for point in source.points)
        rasterize_preview(browser_items([source])[-1], "CROWN", 32)
        self.assertEqual(tuple((point.x, point.y) for point in source.points), before)

    def test_custom_preview_uses_persisted_snapshot_only(self):
        snapshot = make_snapshot("POLY", points=((0, 0), (0, 2), (1, 2), (1, 0)),
                                 profile_id="CUSTOM-snapshot")
        item = browser_items([definition(snapshot.profile_id, snapshot.contour)])[-1]
        self.assertEqual(item.contour, snapshot.contour)
        self.assertFalse(hasattr(item, "source_object_name"))


class ProductionRoutingStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "japanese_house_modeler" / "finish_operators.py").read_text()
        cls.tree = ast.parse(cls.source)

    def _function(self, name):
        return next(node for node in ast.walk(self.tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name)

    def test_thumbnail_values_helper_has_no_assignment_to_finish(self):
        node = self._function("thumbnail_profile_values")
        targets = [target for child in ast.walk(node) if isinstance(child, ast.Assign)
                   for target in child.targets]
        self.assertFalse(any(isinstance(target, ast.Attribute)
                             and isinstance(target.value, ast.Name)
                             and target.value.id == "finish" for target in targets))

    def test_apply_routes_through_transactional_profile_edit(self):
        execute = next(node for node in ast.walk(self.tree)
                       if isinstance(node, ast.ClassDef)
                       and node.name == "JHM_OT_apply_profile_thumbnail")
        calls = {node.func.id for node in ast.walk(execute)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertIn("transactional_profile_edit", calls)
        self.assertIn("prepare_finish_regeneration", ast.unparse(execute))

    def test_operator_and_ui_pass_complete_identity(self):
        operator = next(node for node in ast.walk(self.tree)
                        if isinstance(node, ast.ClassDef)
                        and node.name == "JHM_OT_apply_profile_thumbnail")
        operator_source = ast.unparse(operator)
        for field in ("profile_id", "profile_revision", "profile_schema_version"):
            self.assertIn(field, operator_source)
        ui_source = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        self.assertIn("button.profile_revision", ui_source)
        self.assertIn("button.profile_schema_version", ui_source)

    def test_file_load_cache_handler_is_registered_once_and_removed(self):
        cache_source = (ROOT / "japanese_house_modeler" /
                        "finish_preview_images.py").read_text()
        init_source = (ROOT / "japanese_house_modeler" / "__init__.py").read_text()
        self.assertIn("@persistent\ndef clear_preview_cache", cache_source)
        self.assertIn("if clear_preview_cache not in bpy.app.handlers.load_post",
                      cache_source)
        self.assertIn("bpy.app.handlers.load_post.append(clear_preview_cache)",
                      cache_source)
        self.assertIn("bpy.app.handlers.load_post.remove(clear_preview_cache)",
                      cache_source)
        self.assertIn("register_load_handler()", init_source)
        self.assertIn("unregister_load_handler()", init_source)

    def test_finish_cards_render_large_thumbnail_before_apply_button(self):
        ui_source = (ROOT / "japanese_house_modeler" / "ui.py").read_text()
        thumbnail = ui_source.index("card.template_icon(icon_value=icon, scale=3.0)")
        apply_button = ui_source.index('card.operator("jhm.apply_profile_thumbnail"')
        self.assertLess(thumbnail, apply_button)

    def test_referenced_profile_deletion_guard_is_unchanged(self):
        deletion = next(node for node in ast.walk(self.tree)
                        if isinstance(node, ast.ClassDef)
                        and node.name == "JHM_OT_delete_custom_profile")
        self.assertIn("profile_is_referenced", ast.unparse(deletion))


if __name__ == "__main__":
    unittest.main()
