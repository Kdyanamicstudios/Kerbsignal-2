"""An offline coverage browser; only a selected map is deeply validated."""
import tkinter as tk
from tkinter import ttk
from . import theme
from .track_coverage import TrackCoverage


def show_coverage(parent, meta=None, appearance='Dark'):
    coverage = TrackCoverage()
    summary = coverage.summary()
    window = tk.Toplevel(parent)
    window.title('KerbSignal | Track coverage')
    window.geometry('1040x760')
    window.minsize(740, 560)
    page = ttk.Frame(window, padding=22)
    page.pack(fill='both', expand=True)
    ttk.Label(page, text='Track coverage', style='Title.TLabel').pack(anchor='w')
    ttk.Label(page, text='Maps show circuit geometry. Coaching needs a matching reference lap or guide.',
              wraplength=900).pack(anchor='w', pady=(6, 12))
    ttk.Label(page, text=(f"{summary['bundled_index_entries']} bundled map entries · "
              f"{summary['exact_layout_index_matches']} exact matches among {summary['layout_paths']} layout paths in the snapshot"),
              wraplength=900).pack(anchor='w')
    ttk.Label(page, text=(f"Official article modified {summary['source_modified']} · Reviewed {summary['retrieved']}. "
              'The article may omit newer layouts; venue folders and uncertain rows are excluded from the layout count.'),
              style='Subtitle.TLabel', wraplength=900).pack(anchor='w', pady=(5, 12))
    selected_status = tk.StringVar()
    detail = ttk.Label(page, textvariable=selected_status, wraplength=900, justify='left', padding=12)
    detail.pack(fill='x', pady=(0, 12))
    page.bind('<Configure>', lambda event: detail.configure(wraplength=max(200, event.width-30)), add='+')

    def describe(metadata, title=None):
        status = coverage.status_for(metadata)
        if not status['track_key']:
            selected_status.set('Current layout: connect iRacing to identify the exact configuration. Select a layout below to check its bundled map.')
            return
        name = title or status['official_name'] or status['track_key']
        if status['map_status'] == 'available':
            state = f"Included map checked · {status['map_point_count']:,} points"
        else:
            state = 'No usable exact bundled map · the app can learn an observed GPS route from valid telemetry'
        selected_status.set(f'{name}\n{state}\nCoaching is checked separately against the current car, layout and conditions. Map availability does not establish a fastest racing line or verified turn names.')

    describe(meta or {})
    search = tk.StringVar()
    search_row = ttk.Frame(page)
    search_row.pack(fill='x', pady=(0, 8))
    ttk.Label(search_row, text='Find a circuit or layout').pack(side='left', padx=(0, 10))
    entry = ttk.Entry(search_row, textvariable=search)
    entry.pack(side='left', fill='x', expand=True)
    listing = ttk.Frame(page)
    listing.pack(fill='both', expand=True)
    table = ttk.Treeview(listing, columns=('name', 'map'), show='headings', selectmode='browse')
    table.heading('name', text='CIRCUIT / LAYOUT')
    table.heading('map', text='BUNDLED MAP')
    table.column('name', width=600, minwidth=250)
    table.column('map', width=230, minwidth=170)
    scrollbar = ttk.Scrollbar(listing, orient='vertical', command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    rows = [row for row in coverage.layouts() if row['kind'] == 'layout']
    by_key = {row['key']: row for row in rows}
    index = coverage.atlas.index()

    def filter_rows(*args):
        table.delete(*table.get_children())
        term = search.get().strip().casefold()
        for row in rows:
            if term and term not in (row['official_name']+' '+row['key']).casefold():
                continue
            table.insert('', 'end', iid=row['key'], values=(row['official_name'],
                'Included · select to check' if row['key'] in index else 'No exact bundled map'))

    def select_row(event=None):
        selected = table.selection()
        if selected:
            row = by_key[selected[0]]
            describe({'track_name': row['key']}, row['official_name'])
    search.trace_add('write', filter_rows)
    table.bind('<<TreeviewSelect>>', select_row)
    filter_rows()
    ttk.Label(page, text='Index matches are checked when selected. Different scan years and similarly named layouts are kept separate.',
              style='Subtitle.TLabel', wraplength=900).pack(anchor='w', pady=(10, 6))
    ttk.Button(page, text='Close', command=window.destroy).pack(anchor='e')
    def reflow(event):
        for child in page.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(wraplength=max(200, event.width-30))
    page.bind('<Configure>', reflow, add='+')
    theme.apply(window, ttk.Style(window), appearance)
    window.coverage_table = table
    window.coverage_search = search
    window.coverage_status = selected_status
    return window
