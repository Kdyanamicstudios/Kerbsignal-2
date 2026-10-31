"""Verify the coverage UI uses exact layouts and distinguishes gaps."""
import os
import unittest


@unittest.skipUnless(os.environ.get('KERBSIGNAL_NATIVE_TK')=='1','opt-in native Tk render test')
class CoverageViewTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from engineer.coverage_view import show_coverage
        self.root=tk.Tk();self.root.withdraw()
        self.window=show_coverage(self.root,{'track_name':'spa_2024_up'})
        self.window.attributes('-alpha',0)
        self.window.geometry('740x560+10000+10000')
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_filter_and_selected_map_checks_do_not_hide_missing_layouts(self):
        table=self.window.coverage_table
        self.assertEqual(len(table.get_children()),436)
        self.assertIn('Included map checked',self.window.coverage_status.get())
        self.window.coverage_search.set('Spa-Francorchamps')
        self.assertEqual(len(table.get_children()),7)
        self.window.coverage_search.set('Miami')
        self.assertIn('miami_gp',table.get_children())
        table.selection_set('miami_gp');table.event_generate('<<TreeviewSelect>>');self.root.update()
        self.assertIn('No usable exact bundled map',self.window.coverage_status.get())
        self.assertIn('Coaching is checked separately',self.window.coverage_status.get())
        self.window.coverage_search.set('NoSuchTrackOrLayout')
        self.assertEqual(table.get_children(),())

    def test_dialog_at_compact_size_keeps_coverage_table_scrollable(self):
        table=self.window.coverage_table
        self.assertGreater(table.winfo_height(),60)
        table.yview_moveto(1);self.root.update()
        self.assertGreater(table.yview()[0],0)
        self.assertAlmostEqual(table.yview()[1],1)


if __name__=='__main__':unittest.main()
