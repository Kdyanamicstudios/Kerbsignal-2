import unittest
from engineer.map_atlas import MapAtlas
class MapTests(unittest.TestCase):
 def test_exact_spa_layout_loaded(self):
  result=MapAtlas().load({'track_name':'spa_2024_up'})
  self.assertIsNotNone(result);self.assertGreater(len(result['points']),900)
 def test_unknown_variant_does_not_guess(self):
  self.assertIsNone(MapAtlas().load({'track_name':'spa_2024_unlisted'}))
 def test_display_name_alone_not_used(self):
  self.assertIsNone(MapAtlas().load({'track':'Spa','config':'Grand Prix'}))
 def test_traversal_not_accepted(self):
  self.assertIsNone(MapAtlas().load({'track_name':'../../outside'}))
