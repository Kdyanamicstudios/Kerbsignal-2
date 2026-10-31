"""Exercise real native switches; controller mocks cannot check ttk semantics."""
import tkinter as tk
from tkinter import ttk
import unittest

import app
from engineer import theme


class NativeSettingsControls(unittest.TestCase):
    def setUp(self):
        try:self.root=tk.Tk()
        except tk.TclError as exc:self.skipTest('Native Tk display unavailable: '+str(exc))
        self.root.withdraw()
        self.style=ttk.Style(self.root);self.style.theme_use('clam')
        self.ui=app.App.__new__(app.App);self.ui.root=self.root
        self.value=tk.BooleanVar(self.root,value=False);self.calls=[]
        self.control=self.ui.boolean_control(self.root,'Respond to the engineer',self.value,lambda:self.calls.append(self.value.get()))
        self.control.pack(fill='x')
        theme.apply(self.root,self.style,'Dark')

    def tearDown(self):
        if hasattr(self,'root'):self.root.destroy()

    def test_invocation_and_disabled_state_preserve_callback_semantics(self):
        self.control.invoke()
        self.assertTrue(self.value.get());self.assertEqual(self.calls,[True])
        self.assertTrue(self.control.instate(['selected']))
        self.assertTrue(self.control.cget('text').endswith('On'))
        self.control.state(['disabled']);self.control.invoke()
        self.assertTrue(self.value.get());self.assertEqual(self.calls,[True])
        self.control.state(['!disabled']);self.control.invoke()
        self.assertFalse(self.value.get());self.assertEqual(self.calls,[True,False])

    def test_shared_value_changes_refresh_without_saving_and_remove_trace(self):
        self.value.set(True)
        self.assertTrue(self.control.instate(['selected']))
        self.assertTrue(self.control.cget('text').endswith('On'))
        self.assertEqual(self.calls,[])
        self.control.destroy()
        # Destroying a page must not leave a callback to a dead Tcl widget.
        self.value.set(False)
        self.assertEqual(self.value.trace_info(),[])

    def test_keyboard_focus_space_and_theme_changes(self):
        if self.root.tk.call('tk','windowingsystem')=='win32':self.root.attributes('-alpha',0.)
        self.root.geometry('420x160+0+0');self.root.deiconify();self.root.update()
        self.control.focus_force();self.root.update()
        self.assertEqual(self.root.focus_get(),self.control)
        self.control.event_generate('<KeyPress-space>');self.control.event_generate('<KeyRelease-space>');self.root.update()
        self.assertTrue(self.value.get());self.assertEqual(self.calls,[True])
        for name in ('Light','Dark','Light'):
            theme.apply(self.root,self.style,name);self.root.update()
            self.assertEqual(self.control.instate(['selected']),self.value.get())
            self.control.invoke()
            self.assertEqual(self.control.cget('text').endswith('On'),self.value.get())
            self.assertGreaterEqual(self.root._switch_images[0].width(),56)

    def test_theming_child_dialog_uses_shared_interpreter_elements(self):
        for name in ('Dark','Light','Dark'):
            dialog=tk.Toplevel(self.root);dialog.withdraw()
            theme.apply(dialog,ttk.Style(dialog),name)
            dialog.destroy()
            self.control.invoke()
            self.assertEqual(self.control.instate(['selected']),self.value.get())
            self.root.update_idletasks()


if __name__=='__main__':unittest.main()
