"""Offline learning coverage and opt-in real Windows Tk reader verification."""
import os
import unittest

from engineer.racecraft import LESSONS, LESSON_DETAILS, lesson_detail, search_lessons


class LessonContentTests(unittest.TestCase):
    def test_every_offered_topic_is_complete_and_has_a_distinct_visual(self):
        self.assertEqual(len(LESSONS),22)
        self.assertEqual({lesson[0] for lesson in LESSONS},set(LESSON_DETAILS))
        diagrams=set()
        for lesson in LESSONS:
            detail=lesson_detail(lesson)
            self.assertEqual(detail['title'],lesson[0])
            self.assertEqual(len(detail['steps']),3)
            self.assertEqual(len(detail['mistakes']),2)
            for field in ('how','why','exercise','review','caveats','caption'):
                self.assertGreater(len(detail[field]),45,(lesson[0],field))
            self.assertTrue(detail['source'].startswith('https://www.iracing.com/'))
            diagrams.add(detail['diagram'])
        self.assertEqual(len(diagrams),len(LESSONS))

    def test_search_includes_mistakes_and_experiments_and_retains_tuple_format(self):
        matches=search_lessons('brake lights')
        self.assertEqual(matches[0][0],'Vision & reference points')
        self.assertIn('Defending without reactive blocking',[l[0] for l in search_lessons('reactive')])
        self.assertEqual(search_lessons('nonsensical absent phrase'),[])
        self.assertEqual(len(search_lessons('')),len(LESSONS))
        for lesson in matches:
            self.assertEqual(len(lesson),6)  # Radio answers retain concise fields.
            self.assertTrue(lesson[3].startswith('Practice:'))

    def test_caveats_keep_examples_separate_from_measured_advice(self):
        self.assertIn('not a world-record',lesson_detail('Racing line & late apex')['caveats'])
        self.assertIn('not measured hydraulic pressure',lesson_detail('Threshold braking')['caveats'])
        self.assertIn('not measured tire-slip',lesson_detail('Understeer & oversteer')['caveats'])
        self.assertIn('not a live strategy',lesson_detail('Fuel, stint pace & consistency')['caveats'])


@unittest.skipUnless(os.environ.get('KERBSIGNAL_NATIVE_TK')=='1','opt-in native Tk render test')
class NativeLessonViewTests(unittest.TestCase):
    def test_all_topics_both_themes_compact_annotations_and_reselection(self):
        import tkinter as tk
        from engineer.racecraft_view import RacecraftLessonView
        root=tk.Tk()
        root.attributes('-alpha',0)  # Exercise native geometry without a visible test window.
        try:
            view=RacecraftLessonView(root);view.pack(fill='both',expand=True)
            for width in (760,420,300):
                root.geometry(f'{width}x720+10000+10000');root.update()
                for theme in ('Dark','Light'):
                    view.set_theme(theme)
                    for lesson in LESSONS:
                        view.show_lesson(lesson);root.update()
                        diagram=view.diagram
                        self.assertTrue(diagram.winfo_exists())
                        self.assertEqual(diagram.colors['panel'],view.text.cget('background'))
                        boxes=[diagram.bbox(i) for i in diagram.annotation_ids]
                        for first,second in zip(boxes,boxes[1:]):
                            self.assertLess(first[3],second[1],(lesson[0],width))
                        bounds=diagram.bbox('all')
                        self.assertGreaterEqual(bounds[0],0,(lesson[0],width,bounds))
                        self.assertLessEqual(bounds[2],diagram.winfo_width()+2,(lesson[0],width,bounds))
                        self.assertLessEqual(bounds[3],diagram.winfo_height()+2,(lesson[0],width,bounds))
                        text=view.text.get('1.0','end')
                        self.assertIn('Common mistakes',text)
                        self.assertIn('Limits and judgment',text)
                        self.assertIn(lesson_detail(lesson)['exercise'],text)
                        view.text.yview_moveto(1);root.update()
                        self.assertGreater(view.text.yview()[0],0)
                        self.assertGreaterEqual(view.text.yview()[1],.99)
                    view.clear();root.update()
                    self.assertIsNone(view.lesson)
                    self.assertIsNone(view.diagram)
                    view.show_lesson(LESSONS[0]);root.update()
                    self.assertLess(view.text.yview()[0],.01)
                    self.assertTrue(view.diagram.winfo_exists())
        finally:
            root.destroy()


if __name__=='__main__':unittest.main()
