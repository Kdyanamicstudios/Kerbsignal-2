"""Windows desktop race engineer. Packaged Windows runtime and local voice models."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import sys
import threading
import time
import webbrowser
import sqlite3
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from engineer.core import Coach, Sample, context, line_offset, reference_payload, supported
from engineer.sdk import LiveReader
from engineer.storage import Store
from engineer.voice import Speech
from engineer.demo import META, frame
from engineer.setup import SYMPTOMS, recommendation, verdict
from engineer.youtube import YouTubeMusic
from engineer.cues import DrivingCues, PHRASES
from engineer.cue_audio import CueAudio
from engineer.personality import Personality, VoiceSettings, STYLES
from engineer.local_engineer import LocalEngineer
from engineer.local_ai import LocalAI
from engineer.neural_voice import NeuralVoice, VOICES as FREE_VOICES, DEFAULT_VOICE
from engineer.external_reference import csv_reference
from engineer.cars import car_identity
from engineer.position import PositionTracker, SignalTrace, MPH
from engineer.drive_workspace import DriveWorkspace
from engineer.spotter import Spotter, TRAFFIC_PHRASES
from engineer.driving import FlowCoach, Encouragement, driving
from engineer.cockpit import Overlay
from engineer import updater
from engineer.audio import AudioOutput
from engineer.microphone import MicrophoneCapture
from engineer.session_review import TireMonitor,build_recap,tire_text,explain
from engineer.opponents import OpponentScout
from engineer.ibt_reference import import_ibt
from engineer.ui_behavior import MouseWheelRouter,connection_state
from engineer.startup import StartupAnimation
from engineer.pit_engineer import PitEngineer,session_kind
from engineer.technique import live_target,live_steering,spoken_review,live_reason
from engineer.situation import SituationCoach,RelativeTraffic
from engineer.straight import StraightBriefing
from engineer.devices import enumerate_controllers
from engineer import theme
from engineer.time_format import elapsed,lap_time
from engineer.guides import SOURCES, validate_guide, profile_key


def duration(seconds):
    return lap_time(seconds)


def data_directory():
    override = os.environ.get('RACE_ENGINEER_DATA')
    if override:
        return Path(override)
    base=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))
    folder=base/'RaceEngineer';legacy=base/('RaceEngineer'+'GR86')
    if not folder.exists() and legacy.is_dir():
        folder.mkdir(parents=True,exist_ok=True)
        for path in legacy.glob('*.json'):shutil.copy2(path,folder/path.name)
        if (legacy/'history.sqlite3').exists():
            with sqlite3.connect(str(legacy/'history.sqlite3')) as source,sqlite3.connect(str(folder/'history.sqlite3')) as target:source.backup(target)
    return folder


class App:
    def __init__(self, root):
        self.root = root
        root.title('KerbSignal | Live Race Engineer | '+updater.VERSION)
        try:
            screen_w=int(root.winfo_screenwidth());screen_h=int(root.winfo_screenheight())
            width=min(1360,max(800,screen_w-60));height=min(900,max(560,screen_h-90))
        except (TypeError,ValueError):width,height=1360,900
        root.geometry(f'{width}x{height}');root.minsize(min(1050,width),min(760,height))
        root.configure(bg='#0a101b')
        style = ttk.Style(root); style.theme_use('clam')
        style.configure('.',background='#121e2e',foreground='#edf5ff',font=('Segoe UI',10))
        style.configure('TFrame',background='#0a101b')
        style.configure('TLabel',background='#0a101b',foreground='#edf5ff')
        style.configure('Title.TLabel',font=('Segoe UI',22,'bold'),foreground='#53d7ea')
        style.configure('Metric.TLabel',font=('Segoe UI',26,'bold'),foreground='#edf5ff',background='#121e2e')
        style.configure('Card.TFrame',background='#121e2e')
        style.configure('Card.TLabel',background='#121e2e',foreground='#8295ad',font=('Segoe UI',9))
        style.configure('TButton',padding=(12,9),background='#1b2d43',borderwidth=0)
        style.map('TButton',background=[('active','#2b4b68')],foreground=[('disabled','#62748b')])
        style.configure('TEntry',fieldbackground='#121e2e',foreground='#edf5ff',insertcolor='#edf5ff')
        style.configure('TCombobox',fieldbackground='#121e2e',foreground='#edf5ff',background='#1b2d43',arrowcolor='#53d7ea')
        style.map('TCombobox',fieldbackground=[('readonly','#121e2e')],foreground=[('readonly','#edf5ff')])
        style.configure('Accent.TButton',background='#176572',foreground='white')
        style.configure('Nav.TButton',anchor='w',padding=(14,12),background='#101b2a')
        style.layout('Workspace.TNotebook.Tab',[])
        style.configure('Workspace.TNotebook',background='#0a101b',borderwidth=0)
        style.configure('TNotebook.Tab',padding=(12,8))
        style.configure('Treeview',background='#121e2e',fieldbackground='#121e2e',foreground='#edf5ff',rowheight=30,borderwidth=0)
        style.map('Treeview',background=[('selected','#254b66')])
        style.configure('Treeview.Heading',background='#1b2d43',foreground='#9bb4cc',padding=8)
        self.folder = data_directory(); self.folder.mkdir(parents=True,exist_ok=True)
        self.first_launch=not any((self.folder/name).exists() for name in ('history.sqlite3','driving_options.json'))
        self.store = Store(self.folder/'history.sqlite3')
        self.position=PositionTracker(self.folder/'track_maps');self.signals=SignalTrace();self.seeded_reference=None
        self.last_record_time=-1e9;self.last_channels_draw=0.;self.last_slow_draw=0.
        self.last_guide_context=None
        self.output=AudioOutput()
        self.speech = Speech(); self.reader = LiveReader(); self.coach = Coach()
        self.voice_settings=VoiceSettings(self.folder/'engineer_voice.json')
        self.speech.voice_id=self.voice_settings.voice_id
        self.personality=Personality(self.voice_settings.style)
        self.live_voice=LocalEngineer();self.prefer_live=False
        self.local_ai=LocalAI(self.folder/"local_ai");self.reply_queue=[];self.chat_stream=""
        self.neural=NeuralVoice(Path(__file__).resolve().parent/'engineer/neural_assets',self.folder/'neural_audio')
        self.neural.output=self.output
        self.use_neural=True;self.free_voice=DEFAULT_VOICE
        try:
            free=json.loads((self.folder/'free_voice.json').read_text(encoding='utf-8'))
            if free.get('voice') in {v[0] for v in FREE_VOICES.values()}:self.free_voice=free['voice']
            if free.get('style') in STYLES:self.personality=Personality(free['style'])
        except (OSError,ValueError,TypeError):pass
        self.speech.neural=self.neural;self.speech.neural_voice=self.free_voice
        self.voice_choices={'Windows default':''}
        if self.voice_settings.voice_id:self.voice_choices[self.voice_settings.label]=self.voice_settings.voice_id
        self.youtube = YouTubeMusic(self.folder/'youtube_music.json')
        self.cues=DrivingCues(auto_ack=False);self.cue_audio=self.make_cue_audio(self.speech.voice_id)
        self.mode = None; self.key = None; self.data = {}; self.meta = {}
        self.best_lap_time=None;self.last_lap = None; self.demo_t = 128.; self.last_seen = time.monotonic()
        self.last_draw = 0.; self.selected_samples = None; self.selected_label = ''
        self.mic_on = False; self.last_history = 0.; self.sample_counter = 0
        self.last_error = ''; self.lap_rows = {}; self.session_rows = {}
        self.ibt_events=queue.Queue();self.ibt_busy=False;self.ibt_cancel=threading.Event();self.ibt_candidate=None
        self.reference_events=queue.Queue();self.external_candidate=None;self.reference_search_busy=False
        self.setup_run = self.store.latest_test() or {}
        self.setup_phase = None; self.setup_warmup = 0
        try:self.cues.lead_seconds=min(1.,max(0,float(json.loads((self.folder/'cue_timing.json').read_text())['lead_ms'])/1000))
        except (OSError,ValueError,TypeError,KeyError):pass
        self.spotter=Spotter();self.flow=FlowCoach();self.praise=Encouragement();self.situations=SituationCoach();self.relatives=RelativeTraffic();self.straights=StraightBriefing()
        self.pit_engineer=PitEngineer();self.saved_pit_reports=0;self.tire_monitor=TireMonitor();self.opponent_scout=OpponentScout();self.recap_requested=None;self.recap_worker=None;self.recap_cancel=threading.Event()
        self.traffic_until=0.;self.last_instruction='Ready when you are';self.instruction_at=-1e9;self.last_detail='Automatic coaching • Live inputs • Traffic awareness'
        self.last_live_why='';self.last_live_why_at=-1e9
        self.options=dict(auto_coach=True,spotter=True,theme='Dark',praise=True,situational=True,input_feedback=True,straight_briefings=True,volume=80,output='System default',tutorial_completed=False,wheel='Auto',pedals='Auto')
        try:self.options.update(json.loads((self.folder/'driving_options.json').read_text()))
        except (OSError,ValueError,TypeError):pass
        self.speech.wake.enabled=bool(self.options.get("wake_enabled",True))
        self.background_events=queue.Queue();self.device_rows=[];self.device_busy=False;self.last_device_scan=-1e9;self.audio_notice='Preparing audio'
        self.update_events=queue.Queue();self.update_candidate=None;self.updating=False;self.update_cancel=threading.Event()
        self.overlay=Overlay(root,self.folder) if sys.platform=='win32' else None
        self.wheel_router=MouseWheelRouter(root)
        self.build_ui()
        self.output.configure(float(self.options.get('volume',80))/100,self.options.get('output','System default'))
        self.neural.output=self.output
        self.apply_theme()
        self.scan_devices()
        self.cue_audio.prepare()
        self.cues.enabled=bool(self.options.get('auto_coach',True))
        if self.cues.enabled:self.set_cues(True,persist=False)
        if self.overlay and self.overlay.prefs['visible']:self.overlay.show()

        self.update_setup_report()
        self.refresh_history()
        self.speech.refresh_voices()
        if (self.neural.assets/'kokoro-v1.0.int8.onnx').exists():self.neural.load(self.free_voice)
        if self.youtube.load_error:self.log(self.youtube.load_error)
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.after(16,self.tick)
        root.after(500,lambda:self.start('LIVE') if self.mode is None else None)
        if self.first_launch and not self.options.get('tutorial_completed'):root.after(800,self.show_tutorial)
        if updater.RELEASE_MANIFEST and self.options.get('auto_update_check',True):root.after(5000,self.check_updates)
        if sys.platform=='win32' and self.options.get('startup_animation',True):self.startup_animation=StartupAnimation(root,Path(__file__).resolve().parent/'engineer/assets',appearance=self.options.get('theme','Dark'))

    def build_ui(self):
        self.shell=ttk.Frame(self.root);self.shell.pack(fill='both',expand=True)
        self.sidebar=ttk.Frame(self.shell,width=184,padding=(12,18,12,12),style='Rail.TFrame')
        self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
        content=ttk.Frame(self.shell,padding=(18,0,18,12));content.pack(side='left',fill='both',expand=True)
        brand=ttk.Frame(self.sidebar,style='Rail.TFrame');brand.pack(fill='x',pady=(0,24))
        self.brand_icon=None
        if sys.platform=='win32':
            self.brand_icon=tk.PhotoImage(file=str(Path(__file__).resolve().parent/'engineer/assets/kerbsignal-32.png'))
            ttk.Label(brand,image=self.brand_icon,style='Rail.TLabel').pack(anchor='w',pady=(0,10))
        ttk.Label(brand,text='KERBSIGNAL',style='RailBrand.TLabel').pack(anchor='w')
        ttk.Label(brand,text='YOUR RACE ENGINEER',style='RailMuted.TLabel').pack(anchor='w',pady=(3,0))
        top=ttk.Frame(content,padding=(0,18,0,16));top.pack(fill='x')
        titles=ttk.Frame(top);titles.pack(side='left',fill='x',expand=True)
        self.page_title=tk.StringVar(value='Live driving')
        ttk.Label(titles,textvariable=self.page_title,style='Title.TLabel').pack(anchor='w')
        self.track_display=tk.StringVar(value='Car and exact circuit detected automatically')
        ttk.Label(titles,textvariable=self.track_display,style='Subtitle.TLabel',wraplength=640).pack(anchor='w',pady=(2,0))
        self.connection_badge=tk.StringVar(value='OFFLINE')
        self.connection_pill=ttk.Label(top,textvariable=self.connection_badge,font=('Segoe UI',9,'bold'),padding=(12,8));self.connection_pill.pack(side='right')
        self.connection=tk.StringVar(value='Ready. Connect iRacing, or run the synthetic demo.')
        self.footer=ttk.Frame(content);self.footer.pack(side='bottom',fill='x',pady=(8,0))
        self.footer_status=tk.StringVar(value='LOCAL TELEMETRY  /  Waiting for iRacing')
        ttk.Label(self.footer,textvariable=self.footer_status,style='Subtitle.TLabel').pack(side='left')
        ttk.Label(self.footer,text='v'+updater.VERSION+' · PIT WALL',style='Subtitle.TLabel').pack(side='right')
        workspace=ttk.Frame(content);workspace.pack(fill='both',expand=True)
        self.tabs=ttk.Notebook(workspace,style='Workspace.TNotebook');self.nav_buttons={}
        self.tabs.bind('<<NotebookTabChanged>>',lambda event:self.highlight_nav())
        self.tabs.pack(side='top',fill='both',expand=True)
        self.nav_groups=[('DRIVE',[(0,'Live cockpit')]),('ANALYZE',[(11,'Corner analysis'),(13,'Session recap'),(1,'Lap history'),(2,'Racing line'),(3,'Telemetry'),(8,'Reference laps')]),('RACECRAFT',[(12,'Technique library')]),('GARAGE',[(5,'Setup tests')]),('ENGINEER',[(7,'Voice studio'),(9,'Coaching & timing'),(6,'Focus music'),(14,'Radio transcript')]),('SETTINGS',[(10,'Settings')]),('HELP',[(4,'Getting started')])]
        controls=ttk.Frame(self.sidebar,style='Rail.TFrame');controls.pack(side='bottom',fill='x')
        self.connect_button=ttk.Button(controls,text='Connect iRacing',style='Accent.TButton',command=lambda:self.start('LIVE'));self.connect_button.pack(fill='x',pady=(0,6))
        for label,command in [('Preview cockpit',lambda:self.start('DEMO')),('Stop recording',self.stop)]:
            ttk.Button(controls,text=label,style='Rail.TButton',command=command).pack(fill='x',pady=2)
        self.mic_button=ttk.Button(controls,text='Enable microphone',style='Rail.TButton',command=self.toggle_mic);self.mic_button.pack(fill='x',pady=(12,2))
        self.mute_button=ttk.Button(controls,text='Mute voice',style='Rail.TButton',command=self.toggle_mute);self.mute_button.pack(fill='x',pady=2)
        # Both navigation levels stay down the side. The rail scrolls separately
        # so expanded Analyze/Engineer options fit smaller desktop windows.
        navigation_host=ttk.Frame(self.sidebar,style='Rail.TFrame');navigation_host.pack(side='top',fill='both',expand=True,pady=(0,12))
        navigation=self.scrollable(navigation_host,rail=True)
        ttk.Label(navigation,text='WORKSPACE',style='RailMuted.TLabel').pack(anchor='w',padx=10,pady=(0,10))
        self.group_buttons=[];self.group_subnavigation={}
        for n,(title,items) in enumerate(self.nav_groups):
            group=ttk.Frame(navigation,style='Rail.TFrame');group.pack(fill='x',pady=3)
            button=ttk.Button(group,text=title,style='Nav.TButton',command=lambda i=items[0][0]:self.tabs.select(i));button.pack(fill='x');self.group_buttons.append(button)
            submenu=ttk.Frame(group,style='Rail.TFrame',padding=(8,0,0,2));self.group_subnavigation[n]=submenu
            for index,label in items:
                self.nav_buttons[index]=ttk.Button(submenu,text=label,command=lambda i=index:self.tabs.select(i))
        live=ttk.Frame(self.tabs);self.tabs.add(live,text='DRIVE')
        history = ttk.Frame(self.tabs,padding=14); self.tabs.add(history,text='History')
        line = ttk.Frame(self.tabs,padding=14); self.tabs.add(line,text='Racing line')
        channels = ttk.Frame(self.tabs,padding=14); self.tabs.add(channels,text='Signals')
        help_tab = ttk.Frame(self.tabs,padding=14); self.tabs.add(help_tab,text='Help')
        setup_tab = ttk.Frame(self.tabs,padding=14); self.tabs.add(setup_tab,text='Setup tests')
        music_tab = ttk.Frame(self.tabs,padding=14); self.tabs.add(music_tab,text='YouTube')
        voices_tab=ttk.Frame(self.tabs,padding=8);self.tabs.add(voices_tab,text='Voices')
        voice_tabs=ttk.Notebook(voices_tab);self.voice_tabs=voice_tabs;voice_tabs.pack(fill='both',expand=True)
        free_tab=ttk.Frame(voice_tabs,padding=14);voice_tabs.add(free_tab,text='Free voices')
        ai_tab=ttk.Frame(voice_tabs,padding=14);voice_tabs.add(ai_tab,text='AI conversation')
        engineer_tab=ttk.Frame(voice_tabs,padding=14);voice_tabs.add(engineer_tab,text='Installed Windows voices')
        ref_tab=ttk.Frame(self.tabs,padding=14);self.tabs.add(ref_tab,text='References')
        guide_tab=ttk.Frame(self.tabs,padding=14);self.tabs.add(guide_tab,text='Coach guides')
        self.build_guide_ui(guide_tab)
        app_tab=ttk.Frame(self.tabs,padding=18);self.tabs.add(app_tab,text='Settings')
        self.build_app_settings(app_tab)
        training=ttk.Frame(self.tabs,padding=22);self.tabs.add(training,text='Training')
        ttk.Label(training,text='MAKE THE NEXT LAP COUNT',style='Title.TLabel').pack(anchor='w')
        ttk.Label(training,text='Ranked corner losses and one measurable change at a time.',padding=(0,8)).pack(anchor='w')
        self.training_focus=tk.StringVar(value='All techniques')
        focus=ttk.Combobox(training,textvariable=self.training_focus,values=['All techniques','Braking point','Peak brake input','Throttle pickup','Steering'],state='readonly',width=25)
        focus.pack(anchor='w',pady=10);focus.bind('<<ComboboxSelected>>',lambda event:self.refresh_training())
        self.training_table=ttk.Treeview(training,columns=('corner','loss','action','confidence'),show='headings',height=14)
        for key,title,width in [('corner','CORNER',180),('loss','TIME LOST',100),('action','NEXT-LAP ACTION',540),('confidence','EVIDENCE',280)]:
            self.training_table.heading(key,text=title);self.training_table.column(key,width=width)
        self.training_table.bind('<<TreeviewSelect>>',lambda event:self.training_explanation())
        self.training_why=tk.StringVar(value='Select a corner to understand why the suggested change may help.')
        ttk.Label(training,textvariable=self.training_why,wraplength=1000,padding=10).pack(fill='x')
        self.training_table.pack(fill='both',expand=True,pady=12)
        ttk.Label(training,text='Live pedal targets appear in Cockpit during comparable braking. Meter and percentage-point recommendations are reference-relative, not proof of the cause of time loss. Match car, layout and conditions; begin in practice.',wraplength=1000).pack(anchor='w')
        self.build_racecraft_ui()
        self.build_recap_ui()
        self.car_status=tk.StringVar(value='Car and exact circuit detected automatically')
        self.metrics={key:tk.StringVar(value='—') for key in ('SPEED mph','GEAR','BRAKE %','THROTTLE %','LAP','LAST LAP','CURRENT LAP','BEST LAP','DELTA')}
        self.straight_status=tk.StringVar(value='Next braking zone: waiting for matching corner markers')
        self.praise_status=tk.StringVar(value='Clean improvements earn a brief milestone call.')
        self.technique_status=tk.StringVar(value='Braking comparison waits for a matched reference.')
        self.steering_status=tk.StringVar(value='Steering comparison waits for a matched reference.')
        self.gap_values={key:tk.StringVar(value='—') for key in ('ahead','behind')}
        self.gap_trends={key:tk.StringVar(value='Learning gap trend') for key in ('ahead','behind')}
        self.situation_status=tk.StringVar(value='Session conditions appear after connection.')
        self.tire_status=tk.StringVar(value='Tires: reported/pit readings, not live grip')
        self.scout_status=tk.StringVar(value='Opponent scouting: learning section pace')
        self.hardware_status=tk.StringVar(value='Detecting wheel and pedals…')
        self.position_status=tk.StringVar(value='Waiting for live GPS / lap distance')
        self.coach_status=tk.StringVar(value=self.coach.status)
        self.reference_status=tk.StringVar(value=self.coach.reference_label)
        ttk.Label(guide_tab,textvariable=self.reference_status,foreground='#ffb65c').pack(anchor='w')
        self.auto_coaching=tk.BooleanVar(value=bool(self.options.get('detailed_feedback',True)))
        self.cue_status=tk.StringVar(value='Automatic coaching armed. Positioned calls require a matched reference or guide.')
        self.conditions=tk.StringVar(value='Waiting for session conditions')
        actions=ttk.Frame(live,padding=(0,10,0,0));actions.pack(side='bottom',fill='x')
        self.cue_button=ttk.Button(actions,text='Pause coach',style='Accent.TButton',command=lambda:self.set_cues(not self.cues.enabled));self.cue_button.pack(side='left')
        ttk.Button(actions,text='Session recap',command=self.open_session_recap).pack(side='left',padx=8)
        ttk.Button(actions,text='Reference & timing',command=lambda:self.tabs.select(9)).pack(side='left')
        ttk.Button(actions,text='Live details',command=lambda:self.tabs.select(14)).pack(side='right')
        self.dashboard=DriveWorkspace(live,tk.Canvas)
        radio_page=ttk.Frame(self.tabs,padding=18);self.tabs.add(radio_page,text='Radio transcript')
        ttk.Label(radio_page,text='Engineer radio & live details',style='Title.TLabel').pack(anchor='w',pady=(0,12))
        for var in (self.coach_status,self.technique_status,self.steering_status,self.situation_status,self.tire_status,self.scout_status,self.position_status,self.hardware_status):
            ttk.Label(radio_page,textvariable=var,wraplength=900).pack(fill='x',pady=3)
        self.boolean_control(radio_page,'Detailed coaching',self.auto_coaching,self.save_detail_feedback).pack(fill='x',pady=8)
        self.radio=tk.Text(radio_page,height=8,wrap='word',font=('Segoe UI',10),relief='flat',padx=14,pady=10,state='disabled');self.radio.pack(fill='both',expand=True,pady=(8,0));self.radio.tag_configure('time',foreground='#93a5bc')
        timing_row=ttk.Frame(guide_tab);timing_row.pack(fill='x',pady=8)
        ttk.Label(timing_row,text='Audio lead (milliseconds)').pack(side='left')
        self.cue_lead=tk.StringVar(value=str(round(self.cues.lead_seconds*1000)))
        ttk.Entry(timing_row,textvariable=self.cue_lead,width=8).pack(side='left',padx=8)
        ttk.Button(timing_row,text='Save timing',command=self.save_cue_timing).pack(side='left')
        ttk.Button(timing_row,text='−50 ms',command=lambda:self.adjust_cue_lead(-50)).pack(side='left',padx=5)
        ttk.Button(timing_row,text='+50 ms',command=lambda:self.adjust_cue_lead(50)).pack(side='left',padx=5)
        ttk.Button(guide_tab,text='Reset learned reference',command=self.reset_reference).pack(anchor='w',pady=8)
        ttk.Button(guide_tab,text='Save diagnostics',command=self.export_diagnostics).pack(anchor='w',pady=8)
        ttk.Button(ref_tab,text='Import reference JSON',command=self.import_reference).pack(anchor='w',pady=8)

        ttk.Label(history,text='Recorded sessions — duration covers only the time this app recorded.').pack(anchor='w')
        self.sessions = self.table(history,('id','date','mode','type','duration','laps'),(55,180,70,100,110,80),height=4)
        ttk.Button(history,text='Open selected session recap',command=self.open_session_recap).pack(anchor='w',pady=6)
        ttk.Label(history,text='Completed recorded laps — select a lap to review its line or export it.',padding=(0,10)).pack(anchor='w')
        self.laps = self.table(history,('id','session','lap','time','validity','mode','date'),(50,65,50,100,120,70,160),height=8)
        self.laps.bind('<<TreeviewSelect>>',self.select_lap)
        bar = ttk.Frame(history); bar.pack(fill='x',pady=10)
        for label,cmd in [('Refresh',self.refresh_history),('Export lap times CSV',self.export_csv),('Export selected reference',self.export_reference),('Compare selected lap to reference',self.show_selected_line)]:
            ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=(0,6))
        self.review_text = tk.StringVar(value='Select a recorded lap to see its validation and corner review.')
        ttk.Label(history,textvariable=self.review_text,wraplength=1000,justify='left').pack(fill='x')

        self.line_note = tk.StringVar(value='Orange: recorded / current line. Cyan: reference line. Reference optimality is unverified.')
        ttk.Label(line,textvariable=self.line_note,wraplength=1000).pack(fill='x')
        linebar = ttk.Frame(line); linebar.pack(fill='x',pady=8)
        ttk.Button(linebar,text='Show current lap',command=self.show_current_line).pack(side='left')
        ttk.Button(linebar,text='Show selected historical lap',command=self.show_selected_line).pack(side='left',padx=8)
        ttk.Button(linebar,text='Load selected clean lap as reference',command=self.selected_as_reference).pack(side='left')
        self.canvas = tk.Canvas(line,bg='#0c1017',highlightthickness=0); self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.draw_line())
        ttk.Label(line,text='GPS projection, meters · 2D line separation is descriptive; a closer line is not automatically faster.',foreground='#93a5bc',padding=(0,8)).pack(anchor='w')
        self.channel_tree = self.table(channels,('channel','value','interpretation'),(250,170,520),height=18)
        ttk.Label(channels,text='Tire readings are displayed as reported / freshness unknown, never advertised as live tire measurements.',wraplength=1000,padding=(0,12)).pack(anchor='w')
        ttk.Label(setup_tab,text='ONE CHANGE AT A TIME',style='Title.TLabel').pack(anchor='w')
        ttk.Label(setup_tab,text='Record a baseline, report a repeatable handling issue, test a change, then compare runs.',wraplength=1000,padding=(0,12)).pack(anchor='w')
        self.symptom=tk.StringVar(value=self.setup_run.get('symptom',SYMPTOMS[0]))
        self.garage=tk.StringVar(value=self.setup_run.get('garage','Unknown / fixed'))
        self.arb_size=tk.StringVar(value=self.setup_run.get('arb_size','Unknown'))
        self.arb_setting=tk.StringVar(value=self.setup_run.get('arb_setting','Unknown'))
        for label,var,options in [('Driver-reported issue',self.symptom,SYMPTOMS),('Garage availability',self.garage,('Unknown / fixed','Open / adjustable'))]:
            row=ttk.Frame(setup_tab);row.pack(fill='x',pady=3)
            ttk.Label(row,text=label,width=28).pack(side='left')
            ttk.Combobox(row,textvariable=var,values=options,state='readonly',width=42).pack(side='left')
        self.change_note=tk.StringVar(value=self.setup_run.get('change',''))
        row=ttk.Frame(setup_tab);row.pack(fill='x',pady=8)
        ttk.Label(row,text='Change actually tested',width=28).pack(side='left')
        ttk.Entry(row,textvariable=self.change_note,width=65).pack(side='left')
        self.controlled=tk.BooleanVar(value=False)
        self.boolean_control(setup_tab,'I used comparable tire condition and fuel loads, clear traffic, and changed only the recorded setting.',self.controlled,self.update_setup_report).pack(fill='x',pady=8)
        row=ttk.Frame(setup_tab);row.pack(fill='x',pady=10)
        for text,cmd in [('Start fresh baseline',lambda:self.begin_setup('baseline')),('Start changed run',lambda:self.begin_setup('test')),('Recommend / compare',self.update_setup_report),('Export test report',self.export_setup)]:
            ttk.Button(row,text=text,command=cmd).pack(side='left',padx=(0,6))
        self.setup_report=tk.StringVar(value='Start a baseline run. One warm-up lap and three clean measured laps are required.')
        ttk.Label(setup_tab,textvariable=self.setup_report,wraplength=1000,justify='left',padding=(0,12)).pack(fill='x')
        ttk.Label(setup_tab,text='All cars can run baseline/change tests. Report handling and confirm garage availability. Available SDK garage values are recorded; numeric ranges and adjustment directions are not assumed for other cars. Say “Engineer setup” to hear the report.',wraplength=1000,foreground='#93a5bc').pack(anchor='w',pady=10)
        ttk.Label(music_tab,text='FOCUS MUSIC ON YOUTUBE',style='Title.TLabel').pack(anchor='w')
        ttk.Label(music_tab,text='Say “Engineer play focus music” to open YouTube in your default browser.',wraplength=1000,padding=(0,14)).pack(anchor='w')
        self.youtube_url=tk.StringVar(value=self.youtube.url)
        ttk.Label(music_tab,text='Your preferred YouTube video or playlist link').pack(anchor='w')
        ttk.Entry(music_tab,textvariable=self.youtube_url,width=100).pack(fill='x',pady=10)
        music_controls=ttk.Frame(music_tab);music_controls.pack(fill='x',pady=8)
        ttk.Button(music_controls,text='Save YouTube link',command=self.save_youtube).pack(side='left',padx=(0,8))
        ttk.Button(music_controls,text='Open YouTube focus music',command=self.open_youtube).pack(side='left')
        self.youtube_status=tk.StringVar(value='Default: YouTube search for instrumental focus music. Save a video/playlist link to open it directly.')
        ttk.Label(music_tab,textvariable=self.youtube_status,wraplength=1000,padding=(0,16)).pack(anchor='w')
        ttk.Label(music_tab,text='The default opens search results for you to choose a track. A saved video/playlist requests autoplay, but YouTube may require Play. Pause, volume and playback stay in the browser. Engineer voice mute does not mute YouTube. Opening a browser can take focus away from iRacing.',wraplength=1000,foreground='#93a5bc').pack(anchor='w')
        ttk.Label(engineer_tab,text='LOCAL WINDOWS VOICE',style='Title.TLabel').pack(anchor='w')
        ttk.Label(engineer_tab,text='Choose an installed Windows SAPI voice for the accent, then set how much your engineer swears.',wraplength=1000,padding=(0,12)).pack(anchor='w')
        ttk.Label(engineer_tab,text='Voice / accent').pack(anchor='w')
        self.voice_choice=tk.StringVar(value=self.voice_settings.label if self.voice_settings.voice_id else 'Windows default')
        self.voice_dropdown=ttk.Combobox(engineer_tab,textvariable=self.voice_choice,values=list(self.voice_choices),state='readonly',width=72)
        self.voice_dropdown.pack(anchor='w',pady=7)
        ttk.Label(engineer_tab,text='Radio language').pack(anchor='w',pady=(10,0))
        self.radio_style=tk.StringVar(value=self.voice_settings.style)
        ttk.Combobox(engineer_tab,textvariable=self.radio_style,values=STYLES,state='readonly',width=28).pack(anchor='w',pady=7)
        ttk.Label(engineer_tab,text='Clean: no added swearing  ·  Mild: occasional “bloody”  ·  Unfiltered: frequent adult language',wraplength=1000).pack(anchor='w')
        row=ttk.Frame(engineer_tab);row.pack(fill='x',pady=14)
        ttk.Button(row,text='Refresh installed voices',command=self.speech.refresh_voices).pack(side='left',padx=(0,8))
        ttk.Button(row,text='Save engineer',command=self.save_engineer).pack(side='left',padx=(0,8))
        ttk.Button(row,text='Preview engineer',command=self.preview_engineer).pack(side='left')
        self.engineer_status=tk.StringVar(value='Refresh after installing a voice. Each accent depends on the SAPI voices installed on this PC.')
        ttk.Label(engineer_tab,textvariable=self.engineer_status,wraplength=1000,padding=(0,12),foreground='#99b8d5').pack(anchor='w')
        ttk.Label(engineer_tab,text='Voice settings apply to engineer speech and braking clips. Swearing is reserved for coaching commentary; countdowns and pedal calls remain clear. Voice packs are installed separately.',wraplength=1000,foreground='#93a5bc').pack(anchor='w')
        ttk.Label(ai_tab,text='KERBY · LOCAL CHAT',style='Title.TLabel').pack(anchor='w')
        ttk.Label(ai_tab,text='Talk to your racing engineer on this PC. No account, API key, subscription usage or per-message charge.',wraplength=900,padding=(0,12)).pack(anchor='w')
        self.chat_question=tk.StringVar(value='')
        entry=ttk.Entry(ai_tab,textvariable=self.chat_question,width=80);entry.pack(fill='x',pady=8)
        entry.bind('<Return>',lambda event:self.ask_engineer())
        row=ttk.Frame(ai_tab);row.pack(fill='x',pady=8)
        ttk.Button(row,text='Ask Kerby',style='Accent.TButton',command=self.ask_engineer).pack(side='left')
        self.talk_button=ttk.Button(row,text='Enable microphone',command=self.toggle_live_talk);self.talk_button.pack(side='left',padx=8)
        ttk.Button(row,text='Stop local AI',command=self.stop_local_ai).pack(side='left')
        self.live_status=tk.StringVar(value='Built-in racing answers ready. Say Hey Kerby after enabling the microphone.')
        ttk.Label(ai_tab,textvariable=self.live_status,wraplength=900,padding=(0,10),foreground='#99b8d5').pack(anchor='w')
        self.chat_answer=tk.StringVar(value='Ask about a measured corner, or say “explain trail braking” and then “how do I practice that?”')
        ttk.Label(ai_tab,textvariable=self.chat_answer,wraplength=900,justify='left',font=('Segoe UI',12),padding=(0,12)).pack(fill='x')
        ttk.Button(ai_tab,text='Install free local AI · about 632 MB once',command=self.install_local_ai).pack(anchor='w',pady=12)
        ttk.Label(ai_tab,text='Extended chat uses a small Qwen model running locally after a one-time free download. It can make mistakes and does not have hosted Codex capabilities. Built-in telemetry answers remain available without this download. Extended model chat is paused while driving to protect simulator performance; braking and spotter calls always take priority.',wraplength=900,foreground='#93a5bc').pack(anchor='w')
        ttk.Label(free_tab,text='FREE NATURAL ENGLISH VOICES',style='Title.TLabel').pack(anchor='w')
        ttk.Label(free_tab,text='Offline neural speech for live coaching and driving cues. No subscription, API key, or internet required.',wraplength=1000,padding=(0,12)).pack(anchor='w')
        self.free_choice=tk.StringVar(value=next(label for label,value in FREE_VOICES.items() if value[0]==self.free_voice))
        self.free_style=tk.StringVar(value=self.personality.style)
        ttk.Combobox(free_tab,textvariable=self.free_choice,values=list(FREE_VOICES),state='readonly',width=48).pack(anchor='w',pady=8)
        ttk.Combobox(free_tab,textvariable=self.free_style,values=STYLES,state='readonly',width=24).pack(anchor='w',pady=8)
        row=ttk.Frame(free_tab);row.pack(fill='x',pady=12)
        ttk.Button(row,text='Use this free voice',command=self.save_free_voice).pack(side='left',padx=(0,8))
        ttk.Button(row,text='Hear a preview',command=self.preview_free_voice).pack(side='left')
        self.free_status=tk.StringVar(value='New Bill, Peter and Michael male voices, plus legacy American and British options. Use Hear a preview to compare them.')
        ttk.Label(free_tab,textvariable=self.free_status,wraplength=1000,foreground='#99b8d5',padding=(0,12)).pack(anchor='w')
        ttk.Label(free_tab,text='The new voice pack runs locally and includes three English-speaking male voices. These are synthetic voices. Short driving and spotter calls are cached ahead of time; explanations are generated as needed. Racing questions and optional extended AI chat run locally on your PC.',wraplength=1000).pack(anchor='w')
        ttk.Label(ref_tab,text='FAST REFERENCE LAPS',style='Title.TLabel').pack(anchor='w')
        ttk.Label(ref_tab,text='Use your own clean laps or import recordings for this exact car and layout. Reference imports do not require an API key or account.',wraplength=1000,padding=(0,12)).pack(anchor='w')
        self.reference_match=tk.BooleanVar(value=False)
        self.boolean_control(ref_tab,'I have matched the reference conditions, tires, car setup and ABS/TC settings.',self.reference_match).pack(fill='x',pady=10)
        ttk.Label(ref_tab,text='NATIVE IRACING RECORDINGS',font=('Segoe UI',15,'bold')).pack(anchor='w',pady=(18,6))
        ttk.Label(ref_tab,text='Import an .ibt recording from Documents/iRacing/telemetry. The app selects its fastest complete clean lap using recorded timestamps and exact SDK identity.',wraplength=1000).pack(anchor='w')
        self.ibt_status=tk.StringVar(value='Local recordings stay on your PC. Import while stopped, then inspect and activate the candidate.')
        ttk.Label(ref_tab,textvariable=self.ibt_status,wraplength=1000).pack(anchor='w',pady=8)
        ibtrow=ttk.Frame(ref_tab);ibtrow.pack(fill='x',pady=6)
        ttk.Button(ibtrow,text='Import native .ibt recording',command=self.browse_ibt).pack(side='left')
        ttk.Button(ibtrow,text='Cancel import',command=self.ibt_cancel.set).pack(side='left',padx=8)
        ttk.Button(ibtrow,text='Use imported IBT reference',command=self.use_ibt_reference).pack(side='left')
        self.external_status=tk.StringVar(value='Your own clean references are saved automatically by car, exact layout and weather/aid settings.')
        ttk.Label(ref_tab,textvariable=self.external_status,wraplength=1000,padding=(0,12),foreground='#99b8d5').pack(anchor='w')
        ttk.Label(ref_tab,text='An imported clean lap is not a verified world record. Track and car IDs must match exactly. No private or paid telemetry is redistributed in this download. Imported CSV timing is reconstructed and checked against its declared lap time.',wraplength=1000).pack(anchor='w')
        self.build_tutorial(help_tab)
        ttk.Button(help_tab,text='Browse track & layout coverage',command=self.show_track_coverage).pack(anchor='w',pady=12)

    def show_track_coverage(self):
        from engineer.coverage_view import show_coverage
        return show_coverage(self.root,self.meta,self.options.get('theme','Dark'))

    def boolean_control(self,parent,text,variable,command=None):
        """A full-row native switch with a spoken/readable state and keyboard focus."""
        control=ttk.Checkbutton(parent,variable=variable,command=command,style='Switch.TCheckbutton',takefocus=True)
        def refresh(*args):
            control.configure(text=f'{text}  ·  {"On" if variable.get() else "Off"}')
        refresh()
        # Updating the shared variable elsewhere also updates this view. Traces
        # never run the command, preserving explicit-save and immediate-save rules.
        if hasattr(variable,'trace_add'):
            token=variable.trace_add('write',refresh)
            def cleanup(event):
                if event.widget is control:variable.trace_remove('write',token)
            control.bind('<Destroy>',cleanup,add='+')
        # ttk's label does not wrap on Windows. Reflow its words to the current
        # row width instead of letting long conditions clip on compact displays.
        def reflow(event):
            try:
                import tkinter.font as tkfont
                font=tkfont.Font(root=self.root,font=('Segoe UI',11))
                available=max(100,event.width-90);lines=[];line=''
                for word in f'{text}  ·  {"On" if variable.get() else "Off"}'.split():
                    proposed=f'{line} {word}'.strip()
                    if line and font.measure(proposed)>available:lines.append(line);line=word
                    else:line=proposed
                lines.append(line);control.configure(text='\n'.join(lines))
            except (tk.TclError,AttributeError,TypeError):pass
        control.bind('<Configure>',reflow,add='+')
        if not hasattr(self,'boolean_controls'):self.boolean_controls=[]
        self.boolean_controls.append(control)
        return control

    def build_app_settings(self,parent):
        ttk.Label(parent,text='Make it yours',style='Title.TLabel').pack(anchor='w')
        ttk.Label(parent,text='Your preferences, devices and engineer. Choose a section on the left.',style='Subtitle.TLabel',wraplength=680).pack(anchor='w',pady=(4,18))
        layout=ttk.Frame(parent);layout.pack(fill='both',expand=True)
        rail=ttk.Frame(layout,style='SettingsRail.TFrame',padding=(6,8),width=156)
        self.settings_rail=rail
        rail.pack(side='left',fill='y',padx=(0,16));rail.pack_propagate(False)
        self.settings_tabs=ttk.Notebook(layout,style='Workspace.TNotebook');self.settings_tabs.pack(side='left',fill='both',expand=True)
        self.settings_pages=[];self.settings_buttons=[]
        for index,name in enumerate(('General','Voice & audio','Overlay','Devices','Updates')):
            frame=ttk.Frame(self.settings_tabs);self.settings_tabs.add(frame,text=name)
            page=self.scrollable(frame);self.settings_pages.append(page)
            button=ttk.Button(rail,text=name,style='SettingsNav.TButton',command=lambda i=index:self.settings_tabs.select(i),takefocus=True)
            button.pack(fill='x',pady=3);self.settings_buttons.append(button)
        def select_section(event=None):
            try:selected=self.settings_tabs.index(self.settings_tabs.select())
            except (tk.TclError,TypeError):return
            for index,button in enumerate(self.settings_buttons):button.configure(style='SelectedSettingsNav.TButton' if index==selected else 'SettingsNav.TButton')
        self.settings_tabs.bind('<<NotebookTabChanged>>',select_section,add='+')
        select_section()
        # Native notebook traversal remains available with Ctrl+Tab, even though
        # the visible section controls sit vertically beside the content.
        if isinstance(self.settings_tabs,ttk.Notebook):self.settings_tabs.enable_traversal()
        general,audio,overlay,devices,updates=self.settings_pages
        def text(parent,value=None,variable=None,muted=False):
            label=ttk.Label(parent,text=value,textvariable=variable,style='SettingsMuted.TLabel' if muted else 'SettingsText.TLabel',wraplength=460,justify='left')
            label.pack(fill='x',anchor='w',pady=(4,8))
            parent.bind('<Configure>',lambda event:label.configure(wraplength=max(120,event.width-40)),add='+')
            return label
        def intro(parent,title,description):
            ttk.Label(parent,text=title,font=('Segoe UI',19,'bold')).pack(anchor='w',pady=(2,4))
            label=ttk.Label(parent,text=description,style='Subtitle.TLabel',wraplength=460,justify='left');label.pack(fill='x',pady=(0,16))
            parent.bind('<Configure>',lambda event:label.configure(wraplength=max(120,event.width-12)),add='+')
        def section(parent,title,description=None):
            card=ttk.Frame(parent,style='SettingsCard.TFrame',padding=(18,14));card.pack(fill='x',pady=(0,14),padx=(0,8))
            ttk.Label(card,text=title,style='SettingsSection.TLabel').pack(anchor='w',pady=(0,8))
            if description:text(card,description,muted=True)
            return card
        def field(parent,title,variable,values,readonly=True):
            ttk.Label(parent,text=title,style='SettingsText.TLabel').pack(anchor='w',pady=(10,5))
            combo=ttk.Combobox(parent,textvariable=variable,values=values,state='readonly' if readonly else 'normal',width=1,font=('Segoe UI',11),style='Settings.TCombobox')
            combo.pack(fill='x',pady=(0,6));return combo
        def action(parent,title,command,primary=False):
            button=ttk.Button(parent,text=title,command=command,style='Accent.TButton' if primary else 'TButton')
            button.pack(anchor='w',pady=(6,2));return button

        intro(general,'General','Appearance and driving preferences. Save this section to apply your changes.')
        appearance=section(general,'Appearance')
        self.theme_choice=tk.StringVar(value=self.options.get('theme','Dark'))
        field(appearance,'Color theme',self.theme_choice,['Dark','Light'])
        self.setting_startup=tk.BooleanVar(value=bool(self.options.get('startup_animation',True)))
        self.boolean_control(appearance,'Show startup animation',self.setting_startup).pack(fill='x',pady=(8,0))
        coaching=section(general,'Engineer & coaching','Choose which calls you hear. Safety and spotter calls retain their priority.')
        self.radio_verbosity=tk.StringVar(value=self.options.get('radio_verbosity','Chatty'))
        field(coaching,'Engineer chattiness',self.radio_verbosity,['Quiet','Standard','Chatty'])
        self.setting_straights=tk.BooleanVar(value=bool(self.options.get('straight_briefings',True)))
        self.setting_details=tk.BooleanVar(value=bool(self.options.get('detailed_feedback',True)))
        self.setting_auto=tk.BooleanVar(value=bool(self.options.get('auto_coach',True)))
        self.setting_praise=tk.BooleanVar(value=bool(self.options.get('praise',True)))
        self.setting_situations=tk.BooleanVar(value=bool(self.options.get('situational',True)))
        self.setting_inputs=tk.BooleanVar(value=bool(self.options.get('input_feedback',True)))
        self.spotter_enabled=tk.BooleanVar(value=bool(self.options.get('spotter',True)))
        for label,variable in (('Automatic driving coach',self.setting_auto),('Detailed straightaway briefings',self.setting_straights),('Detailed corner reviews on straights',self.setting_details),('Praise milestones · at least 90 seconds apart',self.setting_praise),('Session, tire, traffic-gap and passing briefings',self.setting_situations),('Observed input feedback while learning markers',self.setting_inputs),('Left / right audio traffic spotter',self.spotter_enabled)):
            self.boolean_control(coaching,label,variable).pack(fill='x',pady=3)
        action(general,'Save general settings',self.apply_settings,True)
        action(general,'Replay guided tutorial',self.show_tutorial)

        intro(audio,'Voice & audio','Pick your engineer, check your devices and calibrate timed calls. All speech stays local.')
        engineer=section(audio,'Your engineer')
        label=next((label for label,v in FREE_VOICES.items() if v[0]==self.free_voice),next(iter(FREE_VOICES)))
        self.settings_voice=tk.StringVar(value=label);self.settings_style=tk.StringVar(value=self.personality.style)
        field(engineer,'Voice',self.settings_voice,list(FREE_VOICES))
        field(engineer,'Language style',self.settings_style,list(STYLES))
        self.settings_volume=tk.StringVar(value=str(self.options.get('volume',80)))
        field(engineer,'Volume (%)',self.settings_volume,[str(i) for i in range(0,101,10)],False)
        self.settings_output=tk.StringVar(value=self.options.get('output','System default'))
        self.audio_devices=field(engineer,'Output device',self.settings_output,['System default'])
        self.audio_status=tk.StringVar(value='Preparing audio…');text(engineer,variable=self.audio_status)
        text(engineer,'Output and volume apply to local neural speech and timed calls. Installed Windows voices use their system output.',muted=True)
        action(engineer,'Save voice & audio',self.save_audio_settings,True)
        action(engineer,'Test engineer voice',self.preview_free_voice)
        action(engineer,'Play timed brake sample',self.test_timed_audio)
        microphone=section(audio,'Microphone & recognition','Test your input here before enabling driving commands.')
        self.settings_mic=tk.StringVar(value=self.options.get('microphone','System default'))
        self.mic_devices=field(microphone,'Microphone input',self.settings_mic,['System default'])
        self.settings_gain=tk.StringVar(value=str(self.options.get('mic_gain',1)))
        field(microphone,'Microphone gain (0.1–3.0)',self.settings_gain,['0.5','1','1.5','2','3'],False)
        self.mic_meter=tk.Canvas(microphone,width=1,height=28,highlightthickness=0,bg='#101925');self.mic_meter.pack(fill='x',pady=8)
        self.mic_test_status=tk.StringVar(value='Start test and say “Engineer microphone check”. Audio stays local. Test mode does not execute driving commands.')
        text(microphone,variable=self.mic_test_status)
        self.mic_input_status=tk.StringVar(value='Input is stopped.');self.mic_transcript=tk.StringVar(value='Recognized speech will appear here.')
        text(microphone,variable=self.mic_input_status,muted=True);text(microphone,variable=self.mic_transcript)
        action(microphone,'Start microphone test',self.test_microphone)
        action(microphone,'Stop test',self.stop_microphone)
        action(microphone,'Rescan devices',self.scan_devices)
        self.setting_wake=tk.BooleanVar(value=bool(self.options.get('wake_enabled',True)))
        self.boolean_control(microphone,'Respond to Hey Kerby while microphone is enabled',self.setting_wake,self.save_wake_setting).pack(fill='x',pady=10)
        text(microphone,'Wake-word changes save immediately. Voice, volume and device choices use Save voice & audio above.',muted=True)
        action(microphone,'Local AI chat & installation',self.open_local_chat)
        action(microphone,'Advanced microphone options',lambda:self.tabs.select(7))
        timing=section(audio,'Timing calibration','Adjust for your audio device and reaction preference.')
        self.settings_lead=tk.StringVar(value=str(round(self.cues.lead_seconds*1000)))
        field(timing,'Audio lead (milliseconds)',self.settings_lead,[str(i) for i in range(0,1001,50)])
        text(timing,'Use the +50 / −50 controls in Engineer → Coaching & timing after testing the exact car/layout.',muted=True)
        action(timing,'Open corner timing controls',lambda:self.tabs.select(9))

        intro(overlay,'Overlay','A compact view of coaching, lap timer, MPH / gear and the 2 g lateral / longitudinal circle.')
        overlay_card=section(overlay,'Display & position')
        text(overlay_card,'Use borderless / windowed iRacing. Exclusive fullscreen and VR are unsupported.',muted=True)
        for label,command in (('Show overlay',lambda:self.overlay_action(True)),('Hide overlay',lambda:self.overlay_action(False)),('Reset / unlock overlay',self.reset_overlay)):action(overlay_card,label,command)
        prefs=self.overlay.prefs if self.overlay else dict(locked=False,opacity=.9,width=360)
        self.overlay_locked=tk.BooleanVar(value=prefs['locked'])
        self.boolean_control(overlay_card,'Lock overlay and pass mouse clicks through',self.overlay_locked).pack(fill='x',pady=(14,4))
        text(overlay_card,'Unlock here to move the overlay again.',muted=True)
        self.overlay_size=tk.StringVar(value=str(prefs['width']))
        field(overlay_card,'Width in pixels (160–1200)',self.overlay_size,['160','180','200','220','240','280','320','360','420','480','520','650','780'],False)
        self.overlay_opacity=tk.StringVar(value=str(round(prefs['opacity']*100)))
        field(overlay_card,'Opacity (%)',self.overlay_opacity,['35','50','65','80','90','100'])
        action(overlay_card,'Save overlay',self.apply_overlay,True)

        intro(devices,'Devices','Identify your racing controls and save the wheel and pedal names you use.')
        devices_card=section(devices,'Connected racing controls')
        self.device_status=tk.StringVar(value='Scanning Windows controllers…');text(devices_card,variable=self.device_status)
        text(devices_card,'Read-only detection identifies attached controllers. iRacing does not expose Windows input bindings. Pedals through a wheel base may appear as one combined device.',muted=True)
        self.device_tree=self.table(devices_card,('name','role','source'),(260,200,130),height=6)
        self.wheel_choice=tk.StringVar(value=self.options.get('wheel','Auto'));self.pedal_choice=tk.StringVar(value=self.options.get('pedals','Auto'))
        self.device_assignments=[]
        for title,variable in (('Wheel base',self.wheel_choice),('Pedals',self.pedal_choice)):
            self.device_assignments.append(field(devices_card,title,variable,['Auto']))
        action(devices_card,'Save assignments',self.save_device_settings,True)
        action(devices_card,'Rescan controllers / audio',self.scan_devices)

        intro(updates,'Updates','Keep KerbSignal current while retaining your lap history and saved settings.')
        update_card=section(updates,'App updates')
        self.update_status=tk.StringVar(value='Updates are checked through the KerbSignal release feed. Your history and settings are retained.')
        self.auto_updates=tk.BooleanVar(value=bool(self.options.get('auto_update_check',True)))
        self.boolean_control(update_card,'Check for new versions at startup',self.auto_updates,self.save_update_preferences).pack(fill='x',pady=6)
        text(update_card,'This preference saves immediately.',muted=True)
        text(update_card,variable=self.update_status)
        action(update_card,'Check for updates',self.check_updates,True)
        action(update_card,'Install update and restart',self.install_update)
        action(update_card,'Pause download',self.update_cancel.set)
        text(update_card,'Interrupted downloads reuse verified parts. Installation waits until recording is stopped.',muted=True)

    def build_recap_ui(self):
        page=ttk.Frame(self.tabs,padding=22);self.tabs.add(page,text='Session recap')
        ttk.Label(page,text='UNDERSTAND THE LAP',style='Title.TLabel').pack(anchor='w')
        self.recap_status=tk.StringVar(value='Select a recorded session in Analyze → Lap history, then open its recap.')
        ttk.Label(page,textvariable=self.recap_status,padding=(0,10),wraplength=1000).pack(fill='x')
        ttk.Button(page,text='Refresh selected / latest session recap',command=self.open_session_recap).pack(anchor='w',pady=6)
        recap_body=ttk.Frame(page);recap_body.pack(fill='both',expand=True)
        self.recap_text=tk.Text(recap_body,wrap='word',font=('Segoe UI',12),padx=20,pady=18,relief='flat',state='disabled')
        self.recap_text.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(recap_body,orient='vertical',command=self.recap_text.yview);scrollbar.pack(side='right',fill='y');self.recap_text.configure(yscrollcommand=scrollbar.set)

    def open_session_recap(self):
        selected=self.sessions.selection()
        latest=self.store.sessions()
        sid=int(selected[0]) if selected else (self.store.session or (latest[0][0] if latest else None))
        if sid is None:self.recap_status.set('No recorded session yet. Connect and drive, then return here.');self.tabs.select(13);return
        self.request_recap(int(sid),True)

    def request_recap(self,sid,show=False):
        if self.recap_worker and self.recap_worker.is_alive():
            self.recap_status.set(f'Already analyzing session {self.recap_requested}; please wait.')
            if show:self.tabs.select(13)
            return
        self.recap_cancel.clear()
        self.recap_requested=sid;self.recap_status.set(f'Analyzing recorded session {sid}…')
        if show:self.tabs.select(13)
        database=self.store.path
        def work():
            try:self.background_events.put(('recap',(sid,build_recap(database,sid,self.recap_cancel))))
            except Exception as exc:self.background_events.put(('recap',(sid,'Session recap unavailable: '+str(exc))))
        self.recap_worker=threading.Thread(target=work,daemon=True);self.recap_worker.start()

    def training_explanation(self):
        selected=self.training_table.selection()
        r=self.training_review_rows.get(selected[0]) if selected else None
        if r:self.training_why.set(r['evidence']+'\nWHY: '+r.get('why',explain(r)))

    def build_racecraft_ui(self):
        from engineer.racecraft import LESSONS
        from engineer.racecraft_view import RacecraftLessonView
        self.racecraft_lessons=LESSONS
        page=ttk.Frame(self.tabs,padding=22);self.tabs.add(page,text='Racecraft')
        ttk.Label(page,text='THE RACECRAFT LIBRARY',style='Title.TLabel').pack(anchor='w')
        ttk.Label(page,text='Learn the technique. Practice one change. Review the evidence.',padding=(0,8)).pack(anchor='w')
        self.racecraft_search=tk.StringVar(value='')
        ttk.Entry(page,textvariable=self.racecraft_search,width=54).pack(anchor='w',pady=8)
        ttk.Button(page,text='Search topics',command=self.filter_racecraft).pack(anchor='w')
        ttk.Button(page,text='Open selected topic’s official learning resource',command=self.open_racecraft_source).pack(side='bottom',anchor='w',pady=(8,0))
        body=ttk.Frame(page);body.pack(fill='both',expand=True,pady=14)
        index_frame=ttk.Frame(body,width=330,height=145);index_frame.pack_propagate(False)
        self.racecraft_index=ttk.Treeview(index_frame,columns=('topic','category'),show='headings',height=18,selectmode='browse')
        self.racecraft_index.heading('topic',text='TECHNIQUE');self.racecraft_index.column('topic',width=220,minwidth=140)
        self.racecraft_index.heading('category',text='CATEGORY');self.racecraft_index.column('category',width=90,minwidth=80)
        index_scroll=ttk.Scrollbar(index_frame,orient='vertical',command=self.racecraft_index.yview)
        self.racecraft_index.configure(yscrollcommand=index_scroll.set)
        index_scroll.pack(side='right',fill='y');self.racecraft_index.pack(side='left',fill='both',expand=True)
        self.racecraft_index.bind('<<TreeviewSelect>>',lambda event:self.select_racecraft())
        self.racecraft_view=RacecraftLessonView(body,theme=self.options.get('theme','Dark'))
        self.racecraft_text=self.racecraft_view.text
        layout_state={'stacked':None}
        def layout(event):
            stacked=event.width<740
            if layout_state['stacked'] is stacked:return
            layout_state['stacked']=stacked
            index_frame.pack_forget();self.racecraft_view.pack_forget()
            index_frame.pack(side='top' if stacked else 'left',fill='x' if stacked else 'y',padx=(0,0 if stacked else 14),pady=(0,10 if stacked else 0))
            self.racecraft_view.pack(side='top' if stacked else 'left',fill='both',expand=True)
        body.bind('<Configure>',layout)
        index_frame.pack(side='left',fill='y',padx=(0,14));self.racecraft_view.pack(side='left',fill='both',expand=True)
        self.filter_racecraft()

    def filter_racecraft(self):
        from engineer.racecraft import search_lessons
        self.racecraft_index.delete(*self.racecraft_index.get_children())
        matches={lesson[0] for lesson in search_lessons(self.racecraft_search.get())}
        for n,lesson in enumerate(self.racecraft_lessons):
            if lesson[0] in matches:self.racecraft_index.insert('','end',iid=str(n),values=lesson[:2])
        found=self.racecraft_index.get_children()
        if found:
            self.racecraft_index.selection_set(found[0]);self.select_racecraft()
        else:self.racecraft_view.clear()

    def select_racecraft(self):
        selected=self.racecraft_index.selection()
        if not selected:return
        lesson=self.racecraft_lessons[int(selected[0])]
        self.racecraft_view.show_lesson(lesson)

    def open_racecraft_source(self):
        selected=self.racecraft_index.selection()
        if selected:webbrowser.open(self.racecraft_lessons[int(selected[0])][5])

    def highlight_nav(self):
        selected=self.tabs.index(self.tabs.select())
        for button in self.nav_buttons.values():button.pack_forget()
        for submenu in self.group_subnavigation.values():submenu.pack_forget()
        for n,(title,items) in enumerate(self.nav_groups):
            active=any(i==selected for i,label in items)
            self.group_buttons[n].configure(style='ActiveNav.TButton' if active else 'Nav.TButton')
            if active:
                self.page_title.set('Live driving' if title=='DRIVE' else title.title())
                if len(items)>1:
                    self.group_subnavigation[n].pack(fill='x',pady=(2,4))
                    for index,label in items:
                        button=self.nav_buttons[index];button.configure(style='SelectedSubnav.TButton' if index==selected else 'Subnav.TButton');button.pack(fill='x',pady=1)

    def save_detail_feedback(self):
        self.options['detailed_feedback']=bool(self.auto_coaching.get());self.setting_details.set(self.options['detailed_feedback']);self.save_driving_options()

    def test_timed_audio(self):
        self.speech.interrupt()
        if self.cue_audio.play('brake'):self.log('Timed audio test: Brake now')
        else:self.audio_status.set('Timed audio is not ready. Check the selected output device.')

    def apply_theme(self):
        name=self.options.get('theme','Dark');theme.apply(self.root,ttk.Style(self.root),name)
        if hasattr(self,'dashboard'):self.dashboard.set_theme(name)
        if hasattr(self,'racecraft_view'):self.racecraft_view.set_theme(name)
        if hasattr(self,'settings_rail'):
            self.root.update_idletasks()
            widths=[button.winfo_reqwidth() for button in self.settings_buttons]
            if widths and all(isinstance(width,int) for width in widths):self.settings_rail.configure(width=max(156,max(widths)+12))

    def apply_settings(self):
        self.options.update(radio_verbosity=self.radio_verbosity.get(),startup_animation=bool(self.setting_startup.get()),straight_briefings=bool(self.setting_straights.get()),detailed_feedback=bool(self.setting_details.get()),theme=self.theme_choice.get(),praise=bool(self.setting_praise.get()),situational=bool(self.setting_situations.get()),input_feedback=bool(self.setting_inputs.get()),spotter=bool(self.spotter_enabled.get()))
        self.auto_coaching.set(self.options['detailed_feedback'])
        if not self.options['praise']:self.praise.pending=None
        if bool(self.setting_auto.get())!=self.cues.enabled:self.set_cues(bool(self.setting_auto.get()))
        self.save_driving_options();self.apply_theme();self.log('General settings saved.')

    def save_audio_settings(self):
        try:
            volume=max(0,min(100,int(self.settings_volume.get())));device=self.settings_output.get();lead=int(self.settings_lead.get())
            if not 0<=lead<=1000:raise ValueError('Audio lead must be between 0 and 1000 ms.')
            gain=float(self.settings_gain.get())
            if not .1<=gain<=3:raise ValueError('Microphone gain must be between 0.1 and 3.')
            self.options.update(volume=volume,output=device,microphone=self.settings_mic.get(),mic_gain=gain);self.save_driving_options()
            self.output.configure(volume/100,device)
            self.cue_lead.set(str(lead));self.save_cue_timing()
            self.free_choice.set(self.settings_voice.get());self.free_style.set(self.settings_style.get());self.save_free_voice()
            self.audio_status.set('Saved. Preparing the selected output device…')
        except (ValueError,OSError) as exc:self.audio_status.set(str(exc))

    def save_device_settings(self):
        self.options.update(wheel=self.wheel_choice.get(),pedals=self.pedal_choice.get());self.save_driving_options();self.receive_devices(dict(controllers=self.device_rows,outputs=None))

    def scan_devices(self):
        if self.device_busy:return
        self.device_busy=True;self.last_device_scan=time.monotonic()
        def worker():
            try:
                rows=enumerate_controllers()
                try:outputs=AudioOutput.devices()
                except Exception:outputs=['System default']
                try:inputs=MicrophoneCapture.devices()
                except Exception:inputs=['System default']
                self.background_events.put(('devices',dict(controllers=rows,outputs=outputs,inputs=inputs)))
            except Exception as exc:self.background_events.put(('error','Controller scan unavailable: '+str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def receive_devices(self,result):
        self.device_rows=result['controllers'];names=['Auto']+[r['name'] for r in self.device_rows]
        for combo in self.device_assignments:combo.configure(values=names)
        if result.get('outputs') is not None:self.audio_devices.configure(values=result['outputs'])
        if result.get('inputs') is not None:self.mic_devices.configure(values=result['inputs'])
        self.device_tree.delete(*self.device_tree.get_children())
        for row in self.device_rows:self.device_tree.insert('', 'end', values=(row['name'],row['role'],row['source']))
        def chosen(kind,needle):
            choice=self.options.get(kind,'Auto')
            if choice!='Auto':return choice if any(r['name']==choice for r in self.device_rows) else choice+' (not detected)'
            return next((r['name'] for r in self.device_rows if needle in r['role']), 'Not separately identified')
        summary='Wheel: '+chosen('wheel','Wheel')+' • Pedals: '+chosen('pedals','Pedals')
        self.device_status.set(summary);self.hardware_status.set(summary)

    def g_force(self):
        values=(self.data.get('LatAccel'),self.data.get('LongAccel'))
        return tuple(v/9.80665 for v in values) if all(isinstance(v,(int,float)) and math.isfinite(v) for v in values) else None

    def coaching_state(self):
        if not self.cues.enabled:return 'Coach paused • Settings controls speech and spotter'
        if not self.cue_audio.ready or not self.output.stream or not getattr(self.output.stream,'active',True):return 'Audio not ready • Check Settings → Voice & audio'
        if self.cues.source.startswith('Guide conditions changed'):return self.cues.source
        if getattr(self.cues,'pause_reason',''):return self.cues.pause_reason
        return f'Corner calls ready • {len(self.cues.plans)} markers' if self.cues.plans else 'Learning corner markers • Complete a clean lap or import an aligned guide'

    def situation_text(self):
        return self.situations.summary(self.meta)

    def build_tutorial(self,parent):
        self.tutorial_page=0
        self.tutorial_steps=[
            ('Welcome to KerbSignal','Your engineer reads iRacing telemetry locally. Open iRacing, join a session and get in the car. KerbSignal connects automatically. The synthetic demo is separate and is never used as a live fallback.'),
            ('Make sure the engineer can hear and speak','In Settings → Voice & audio, choose a voice, output device and volume. Save, then test the voice. The local microphone starts off; enable it only if you want voice commands. Try “Engineer what track am I on”, “Engineer tires”, or “Engineer enable braking cues”. Say “Hey Kerby” and ask your question. Extended local chat has an optional free one-time model download; no sign-in or subscription is required.'),
            ('Understand learning versus corner calls','Input feedback starts as you drive. Precise brake / turn / throttle calls require a guide for the exact car/layout, or a complete clean lap so the app can learn your spatial markers. Learned markers reproduce observed inputs; they are not automatically the fastest line.'),
            ('Read your driving screen','CURRENT LAP is your live simulator lap timer. The map follows GPS or lap-distance position on a learned route. Bundled circuit geometry is used when the exact layout is available. Other layouts use an observed GPS route; lap progress remains live. Gray / stale states mean the app has lost fresh telemetry.'),
            ('Make the timing fit your audio','In Engineer → Coaching & timing, start with the current Audio lead. If the call is late, add 50 ms; if early, subtract 50 ms. Test the same corner in solo practice. This adjusts output lead, not the corner landmark. Diagnostics records whether calls played or were suppressed.'),
            ('Use a smaller overlay','Open Settings → Overlay. Choose a width from 160 pixels upward, opacity and lock state. Drag while unlocked. Lock enables click-through; unlock or reset from Settings. The circle plots lateral and longitudinal acceleration with a 2 g radius. Use borderless / windowed iRacing.'),
            ('Confirm your wheel and pedals','Settings → Devices scans attached Windows controllers and suggests roles from their product names. Confirm assignments if needed. Pedals plugged into a base may be combined. This identifies connected hardware; it does not change calibration or iRacing bindings.'),
            ('Listen to useful session information','Briefings identify practice / qualifying / race from the session. Gap reports use estimated passage times and a measured trend window. Tires can be pit-updated and brake temperatures may be absent: warm-up advice is not a claim that a measured temperature is cold. Praise is sparse and tied to clean-lap milestones.'),
            ('Review and improve','Use Analyze for lap history, lines and session recaps with explanations. Analyze includes ranked corner feedback; Racecraft opens the technique library. Use Garage for controlled setup tests with one change at a time. Reopen this tutorial anytime from Settings. If timing is wrong, save diagnostics with the exact car/layout and your audio device.')]
        self.tutorial_progress=tk.StringVar();self.tutorial_title=tk.StringVar();self.tutorial_body=tk.StringVar()
        ttk.Label(parent,textvariable=self.tutorial_progress,foreground='#8295ad').pack(anchor='w',pady=12)
        ttk.Label(parent,textvariable=self.tutorial_title,style='Title.TLabel',wraplength=800).pack(anchor='w',pady=12)
        ttk.Label(parent,textvariable=self.tutorial_body,wraplength=800,justify='left',font=('Segoe UI',12)).pack(fill='x',pady=16)
        row=ttk.Frame(parent);row.pack(fill='x',pady=20)
        ttk.Button(row,text='Back',command=lambda:self.tutorial_move(-1)).pack(side='left')
        ttk.Button(row,text='Next',style='Accent.TButton',command=lambda:self.tutorial_move(1)).pack(side='left',padx=8)
        ttk.Button(row,text='Finish / skip',command=self.finish_tutorial).pack(side='right')
        ttk.Button(parent,text='Open Settings',command=lambda:self.tabs.select(10)).pack(anchor='w',pady=10)
        ttk.Button(parent,text='Try the synthetic demo',command=lambda:(self.start('DEMO'),self.tabs.select(0))).pack(anchor='w')
        self.tutorial_move(0)

    def tutorial_move(self,direction):
        target=self.tutorial_page+direction
        if target>=len(self.tutorial_steps):self.finish_tutorial();return
        self.tutorial_page=max(0,target);title,body=self.tutorial_steps[self.tutorial_page]
        self.tutorial_progress.set(f'QUICK START  /  {self.tutorial_page+1} OF {len(self.tutorial_steps)}')
        self.tutorial_title.set(title);self.tutorial_body.set(body)

    def show_tutorial(self):self.tabs.select(4);self.tutorial_page=0;self.tutorial_move(0)

    def finish_tutorial(self):
        self.options['tutorial_completed']=True;self.save_driving_options();self.tabs.select(0)

    def save_driving_options(self):
        (self.folder/'driving_options.json').write_text(json.dumps(self.options))

    def save_spotter(self):
        self.options['spotter']=bool(self.spotter_enabled.get());self.spotter.reset();self.save_driving_options()

    def overlay_action(self,visible):
        if self.overlay:self.overlay.show(visible)
        else:self.log('The desktop overlay is available in the Windows build.')

    def apply_overlay(self):
        try:
            if self.overlay:self.overlay.configure(self.overlay_locked.get(),float(self.overlay_opacity.get())/100,int(self.overlay_size.get()))
            self.log('Overlay settings saved.')
        except (ValueError,OSError) as exc:self.log('Overlay settings: '+str(exc))

    def reset_overlay(self):
        if self.overlay:
            self.overlay_locked.set(False);self.overlay.prefs.update(x=50,y=50,locked=False)
            if self.overlay.window:self.overlay.window.geometry('+50+50')
            self.overlay.show();self.apply_overlay()

    def cockpit_model(self):
        fresh=connection_state(self.mode,self.data,self.meta,time.monotonic()-self.last_seen)['label']=='IRACING CONNECTED'
        if self.mode=='DEMO':fresh=bool(self.data)
        instruction=self.last_instruction
        if self.data.get('SessionTime',0)-self.instruction_at>6:
            info=self.cues.diagnostic
            if self.spotter.available and (self.spotter.left or self.spotter.right):instruction='Hold your line — car alongside'
            elif not self.cues.enabled:instruction='Coaching paused'
            elif self.pit_engineer.state=='box':instruction='IN THE BOX • Pit briefing active'
            elif self.data.get('OnPitRoad'):instruction='PIT LANE • Watch pit speed'
            elif not driving(self.data):instruction='Coach armed — ready when you move'
            elif info:instruction=info['corner']+' / '+info['phase'].replace('_',' ').title()
            elif self.cues.plans:instruction='Eyes up. Next corner ahead.'
            else:instruction='Coach active — learning your clean lap'
        detail=(self.meta.get('car','')+' • '+self.meta.get('track','')+' / '+self.meta.get('config','Default layout')) if fresh else 'Connect iRacing • Start driving • Coaching engages automatically'
        why=self.last_live_why if fresh and 0<=self.data.get('SessionTime',0)-self.last_live_why_at<45 else ''
        return dict(theme=self.options.get('theme','Dark'),lap_time=duration(self.data.get('LapCurrentLapTime')) if fresh else '—',g_force=self.g_force(),coach_state=self.coaching_state(),mode=self.mode,fresh=fresh,instruction=instruction,detail=detail,why=why,
            speed=round(self.data.get('Speed',0)*MPH),gear=self.data.get('Gear','—'),traffic=self.spotter.snapshot())

    def instruct(self,text,key=None):
        self.last_instruction=text if len(text)<85 else text[:82]+'…'
        self.instruction_at=self.data.get('SessionTime',0);self.cue_status.set(text)
        if self.speech.muted:return False
        if key and (not self.cue_audio.ready or not self.output.stream):return False
        self.speech.interrupt();self.live_voice.prioritize_driving(True)
        if key:
            played=self.cue_audio.play(key);self.speech.cue_until=self.cue_audio.until
            if key.startswith('traffic_'):self.traffic_until=self.cue_audio.until
            if played:self.log(text)
            return played
        quiet=self.speech.quiet;self.speech.quiet=False
        self.speech.say(text);self.speech.quiet=quiet
        self.log(text);return bool(self.speech.speaking)

    def save_update_preferences(self):
        self.options['auto_update_check']=bool(self.auto_updates.get());self.save_driving_options()

    def check_updates(self):
        if self.updating:return
        if not updater.RELEASE_MANIFEST:
            self.update_status.set('Automatic delivery needs a hosted release channel. It is not connected in this build.');return
        self.updating=True;self.update_status.set('Checking for updates…')
        def worker():
            try:
                candidate=updater.check()
                self.update_events.put(('available',candidate) if candidate else ('status','You have the latest published release.'))
            except Exception as exc:self.update_events.put(('status','Update check failed: '+str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def install_update(self):
        if self.mode:self.update_status.set('Stop recording before installing an update.');return
        if self.updating:return
        if getattr(self,'staged_update',None):
            updater.launch_when_closed(self.staged_update);self.close();return
        if not self.update_candidate:self.check_updates();return
        self.update_cancel.clear()
        self.updating=True;self.update_status.set('Downloading and verifying the update…')
        def worker():
            last=[0.]
            def progress(done,total):
                now=time.monotonic()
                if done==total or now-last[0]>=.25:
                    last[0]=now;self.update_events.put(('progress',f'Downloading update: {done/total*100:.0f}% • {done/1048576:.1f} / {total/1048576:.1f} MB'))
            try:self.update_events.put(('downloaded',updater.download(self.update_candidate,self.folder/'updates',progress=progress,cancel=self.update_cancel)))
            except Exception as exc:self.update_events.put(('status',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def table(self,parent,columns,widths,height):
        frame = ttk.Frame(parent); frame.pack(fill='both',expand=True)
        tree = ttk.Treeview(frame,columns=columns,show='headings',height=height,selectmode='browse')
        for c,w in zip(columns,widths):
            tree.heading(c,text=c.upper()); tree.column(c,width=w,minwidth=45)
        scrollbar = ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left',fill='both',expand=True); scrollbar.pack(side='right',fill='y')
        return tree

    def scrollable(self,parent,rail=False):
        viewport=tk.Canvas(parent,bg=theme.palette(self.options.get('theme','Dark'))['rail' if rail else 'panel'],highlightthickness=0,yscrollincrement=24)
        viewport._theme_background_role='rail' if rail else 'panel'
        scrollbar=ttk.Scrollbar(parent,orient='vertical',command=viewport.yview)
        scrollbar.pack(side='right',fill='y');viewport.pack(side='left',fill='both',expand=True)
        viewport.configure(yscrollcommand=scrollbar.set)
        content=ttk.Frame(viewport,style='Rail.TFrame' if rail else 'TFrame');window=viewport.create_window(0,0,window=content,anchor='nw')
        content.bind('<Configure>',lambda e:viewport.configure(scrollregion=viewport.bbox('all')))
        viewport.bind('<Configure>',lambda e:viewport.itemconfigure(window,width=e.width))
        viewport._wheel_canvas=viewport;content._wheel_canvas=viewport
        return content

    def build_guide_ui(self,tab):
        tab=self.scrollable(tab)
        ttk.Label(tab,text='POSITION-BASED COACHING',style='Title.TLabel').pack(anchor='w')
        ttk.Label(tab,text='Coach calls are anchored to distance around the detected layout, not a video timestamp or target lap time. Use a matching guide, learn markers from a drive, or align a video’s visual landmarks below.',wraplength=1100,padding=(0,8)).pack(fill='x')
        self.guide_fields={}
        for key,label in [('name','Corner name'),('brake','Start braking (meters from start)'),('release','Start brake release (meters)'),('turn','Turn in (meters)'),('throttle','Feed throttle (meters)'),('end','Corner end (meters; optional)'),('video','Source video URL / note')]:
            row=ttk.Frame(tab);row.pack(fill='x',pady=2)
            ttk.Label(row,text=label,width=37).pack(side='left')
            var=tk.StringVar(value='');self.guide_fields[key]=var
            ttk.Entry(row,textvariable=var,width=65 if key=='video' else 24).pack(side='left')
            if key not in ('name','video'):ttk.Button(row,text='Use current position',command=lambda k=key:self.capture_marker(k)).pack(side='left',padx=5)
        self.guide_match=tk.BooleanVar(value=False)
        self.boolean_control(tab,'These markers are aligned to the detected car/layout and current conditions.',self.guide_match).pack(fill='x',pady=6)
        row=ttk.Frame(tab);row.pack(fill='x',pady=5)
        for label,command in [('Save corner / activate guide',self.save_corner),('Import positioned guide',self.import_guide),('Export active guide',self.export_guide),('Use learned markers instead',self.use_learned_markers)]:
            ttk.Button(row,text=label,command=command).pack(side='left',padx=(0,5))
        self.guide_status=tk.StringVar(value='Guide positions are not inferred from a video’s playback time. Verify landmark alignment before enabling live calls.')
        ttk.Label(tab,textvariable=self.guide_status,wraplength=1100,foreground='#61caff',padding=(0,8)).pack(fill='x')
        ttk.Label(tab,text='COACHING VIDEO SOURCES',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(10,3))
        for source in SOURCES:
            row=ttk.Frame(tab);row.pack(fill='x',pady=3)
            ttk.Button(row,text=source['name'],command=lambda url=source['url']:webbrowser.open(url,new=2)).pack(side='left')
            ttk.Label(row,text=source['note'],wraplength=820,padding=(10,0)).pack(side='left')

    def guide_path(self,meta):
        folder=self.folder/'coach_guides';folder.mkdir(exist_ok=True)
        return folder/(hashlib.sha256(json.dumps(profile_key(meta)).encode()).hexdigest()+'.json')

    def load_position_guide(self,meta,d):
        try:
            guide=validate_guide(json.loads(self.guide_path(meta).read_text()),meta)
            if guide.get('context') is not None and tuple(guide['context'])!=context(d):return
            self.cues.install_guide(guide);self.guide_status.set('Loaded '+str(len(guide['corners']))+' aligned corners for '+meta['track']+'.')
        except (OSError,ValueError,KeyError,TypeError):pass

    def capture_marker(self,key):
        pos=self.position.snapshot()
        if not pos.get('valid'):self.guide_status.set('A fresh live track position is required.');return
        self.guide_fields[key].set(str(round(pos['distance_m'],1)))
        self.guide_status.set('Captured '+key+' at '+str(pos['distance_m'])+' m on '+str(pos['track'])+'.')

    def save_corner(self):
        try:
            if not self.data or not supported(self.meta):raise ValueError('Connect to the car and exact track/layout first.')
            if not self.guide_match.get():raise ValueError('Confirm marker alignment for this exact car/layout and conditions.')
            length=self.meta['length'];fields=self.guide_fields
            row={k:(float(fields[k].get())/length if fields[k].get().strip() else None) for k in ('brake','release','turn','throttle','end')}
            row['name']=fields['name'].get().strip() or 'Corner '+str(len(self.cues.plans)+1)
            row['hold']=None;row['unwind']=None
            if row['end'] is None:row['end']=min(1,max(v for v in row.values() if isinstance(v,(int,float)))+80/length)
            if row['brake'] is not None and row['release'] is not None and (row['release']-row['brake'])*length>12:row['hold']=row['brake']+10/length
            existing=list(self.cues.guide['corners']) if self.cues.guide else []
            existing=[x for x in existing if x['name']!=row['name']]+[row]
            payload=dict(format='race-engineer-coach-v1',profile=dict(self.meta),context=list(context(self.data)),
                source=fields['video'].get().strip() or 'Driver-aligned track landmarks',corners=existing)
            guide=validate_guide(payload,self.meta);self.guide_path(self.meta).write_text(json.dumps(guide,indent=2))
            self.cues.install_guide(guide);self.guide_status.set('Saved '+row['name']+'; '+str(len(existing))+' spatial corners active. Lap time is not used for call timing.')
        except (ValueError,TypeError,KeyError,OSError) as exc:self.guide_status.set(str(exc))

    def import_guide(self):
        path=filedialog.askopenfilename(filetypes=[('Position coach guide','*.json')])
        if not path:return
        try:
            if not self.data or not supported(self.meta):raise ValueError('Connect to the current car/layout before importing a positioned guide.')
            if not self.guide_match.get():raise ValueError('Confirm alignment to this exact car/layout and conditions before importing the guide.')
            if Path(path).stat().st_size>2_000_000:raise ValueError('Guide is too large.')
            guide=validate_guide(json.loads(Path(path).read_text()),self.meta)
            if guide.get('context') is not None and tuple(guide['context'])!=context(self.data):raise ValueError('Guide weather/aid settings differ. Verify and realign it before using it.')
            self.guide_path(self.meta).write_text(json.dumps(guide,indent=2));self.cues.install_guide(guide)
            self.guide_status.set('Imported '+str(len(guide['corners']))+' positioned corners; no reference lap time is required.')
        except (ValueError,KeyError,TypeError,OSError) as exc:self.guide_status.set(str(exc))

    def export_guide(self):
        if not self.cues.guide:self.guide_status.set('Save aligned corner markers before exporting.');return
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='Position_Coach_Guide.json')
        if path:Path(path).write_text(json.dumps(self.cues.guide,indent=2))

    def use_learned_markers(self):
        self.cues.clear_guide();self.guide_status.set('Using observed corner positions from a clean driving trace; elapsed lap time does not trigger calls.')

    def adjust_timing(self,delta):
        self.cue_lead.set(str(max(0,min(1000,round(self.cues.lead_seconds*1000)+delta))));self.save_cue_timing()

    def export_diagnostics(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='RaceEngineer_Diagnostics.json')
        if not path:return
        record=dict(version=updater.VERSION,metadata=self.meta,telemetry=self.telemetry_snapshot(),position=self.position.snapshot(),
            audio=dict(onsets=list(self.output.onsets),status=self.audio_notice,device=self.output.device_name,reported_latency_ms=round(self.output.latency*1000),requested=self.output.requested,last_onset=self.output.last_onset),cue_history=list(self.cues.history),cue_diagnostic=self.cues.diagnostic,cue_source=self.cues.source,plans=self.cues.plans,
            last_signals=list(self.signals.points)[-200:])
        try:Path(path).write_text(json.dumps(record,indent=2,allow_nan=False));self.log('Saved track / position / cue diagnostics. API keys and microphone audio are excluded.')
        except (OSError,ValueError) as exc:self.log(str(exc))

    def log(self,text,speak=False,force=False):
        self.radio.configure(state='normal')
        self.radio.insert('end',time.strftime('%H:%M:%S')+'  ','time')
        self.radio.insert('end',text+'\n\n')
        self.radio.see('end'); self.radio.configure(state='disabled')
        if speak:
            if self.live_voice.connected:
                if not self.speech.muted:self.live_voice.coaching(text,self.telemetry_snapshot())
            elif not self.prefer_live:self.speech.say(text,force)

    def start(self,mode):
        self.stop()
        self.coach = Coach(); self.mode = mode; self.key = None
        self.last_lap = None; self.selected_samples = None; self.demo_t = 128.
        self.last_seen = time.monotonic(); self.last_error = ''
        self.connection.set('SYNTHETIC DEMO — not the live simulator or a real circuit.' if mode=='DEMO' else 'Connecting to iRacing…')
        self.flow.reset();self.spotter.reset();self.praise.reset();self.situations.reset();self.relatives.reset();self.straights.reset()
        self.log('Demo started. Results are synthetic.' if mode=='DEMO' else 'Live connection requested. Waiting for the simulator.')

    def stop(self):
        recap_session=self.store.session
        if self.mode:
            self.log('Recording stopped. Session history saved.')
        self.speech.interrupt()
        self.mode = None; self.reader.close(); self.store.finish(); self.key = None
        self.data = {}; self.meta = {}; self.coach.pending.clear()
        self.flow.reset();self.spotter.reset();self.praise.reset();self.situations.reset();self.relatives.reset();self.straights.reset()
        self.last_instruction='Ready when you are'
        self.track_display.set('WAITING FOR IRACING TRACK / LAYOUT')
        self.signals.clear();self.position.current={};self.position.route={};self.position.layout={};self.position.key=None;self.position.trace.clear()
        self.live_voice.set_car(None)
        self.car_status.set('Current car: waiting for the player’s iRacing entry')
        self.setup_phase=None
        self.cues.clear_guide();self.cue_audio.stop();self.speech.quiet=False
        self.connection.set('Stopped. Saved history remains available.')
        self.refresh_history()
        if recap_session:self.request_recap(recap_session,False)

    def begin_setup(self,phase):
        if not self.mode or not self.data or not supported(self.meta):
            self.log('Connect to an identified car and track before starting a setup test.');return
        if phase=='baseline':
            self.setup_run=dict(profile=dict(self.meta),mode=self.mode,symptom=self.symptom.get(),garage=self.garage.get(),arb_size=self.arb_size.get(),arb_setting=self.arb_setting.get(),change='',baseline=[],test=[])
        else:
            if len(self.setup_run.get('baseline',[]))<3:
                self.log('Collect at least three clean baseline laps first.');return
            if self.setup_run.get('mode')!=self.mode or any(self.setup_run.get('profile',{}).get(k)!=self.meta.get(k) for k in ('car_path','car_id','track_id','config')):
                self.log('The baseline car / track layout does not match. Start a new baseline.');return
            if not self.change_note.get().strip():
                self.log('Enter the single setup change you actually made before starting the changed run.');return
            self.setup_run['change']=self.change_note.get().strip()
            self.setup_run['test']=[]
        self.setup_phase=phase;self.setup_warmup=1
        self.coach=Coach()  # A garage change must not inherit the previous setup reference.
        self.store.save_test(self.setup_run)
        self.log(phase.title()+' setup run started. First clean lap is warm-up; then record three clean measured laps.')
        self.update_setup_report()

    def tag_setup_lap(self,lap,lap_id,d):
        if not self.setup_phase:return
        if not lap['clean']:
            self.log('Setup test: excluded lap ignored.');return
        if self.setup_warmup:
            self.setup_warmup-=1;self.log('Setup warm-up lap complete. Measured laps begin now.');return
        phase=self.setup_phase
        self.setup_run[phase].append(dict(lap_id=lap_id,lap_time=lap['lap_time'],wetness=lap['context'][1],abs=lap['context'][2],tc=lap['context'][3],track_temp=d.get('TrackTemp'),fuel=d.get('FuelLevel')))
        self.store.save_test(self.setup_run)
        if len(self.setup_run[phase])>=3:
            self.setup_phase=None;self.log(phase.title()+' run has three clean measured laps. Review the setup test report.')
        self.update_setup_report()

    def update_setup_report(self):
        if not self.setup_run:
            self.setup_report.set('Start a baseline run. One warm-up lap and three clean measured laps are required.');return
        run=self.setup_run
        baseline=run.get('baseline',[]);test=run.get('test',[])
        # Refresh driver feedback without silently altering the recorded original setup.
        run['symptom']=self.symptom.get()
        advice=recommendation(baseline,run['symptom'],run['garage'],run['arb_size'],run['arb_setting'],run.get('profile'))
        text=f"{run.get('mode','')} · {run.get('profile',{}).get('car','Unknown car')} · Baseline: {len(baseline)} measured laps · Changed: {len(test)} measured laps"
        if self.setup_phase:text+=f' · Recording {self.setup_phase}; warm-up remaining {self.setup_warmup}'
        text+='\n\n'+advice
        if test:text+='\n\nTested change: '+run.get('change','')+'\n'+verdict(baseline,test,self.controlled.get())
        self.setup_report.set(text)

    def export_setup(self):
        if not self.setup_run:
            self.log('No setup experiment is recorded yet.');return
        self.update_setup_report()
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='car_setup_test.json',filetypes=[('Setup report JSON','*.json')])
        if path:
            try:
                report=dict(self.setup_run,report=self.setup_report.get(),controlled_confirmed=bool(self.controlled.get()))
                Path(path).write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
                self.store.save_test(report)
                self.log('Setup experiment exported.')
            except OSError as exc:messagebox.showerror('Export',str(exc))

    def reset_reference(self):
        self.coach = Coach();self.cues.clear_guide();self.log('Learned corner markers cleared. Align a guide or complete a fresh clean drive.')

    def tick(self):
        try:
            if self.mode:
                packet = None
                if self.mode=='DEMO':
                    # 8x simulated speed with intervening 20 Hz samples retained.
                    for _ in range(1 if self.cues.enabled else 8):
                        self.demo_t += .05; self.ingest(frame(self.demo_t),dict(META))
                else:
                    try:packet = self.reader.read()
                    except OSError as exc:
                        message=str(exc);self.connection.set(message)
                        if message!=self.last_error:self.log(message);self.last_error=message
                        packet=None
                    if packet:
                        self.ingest(*packet); self.last_error = ''
                    elif time.monotonic()-self.last_seen > 2:
                        self.connection.set('Telemetry stalled. Lap invalidated; waiting for new data.')
                        self.coach.invalid.add('telemetry stalled'); self.coach.pending.clear()
                        self.live_voice.set_car(None)
                        self.car_status.set('Current car: telemetry stale — waiting for fresh player data')
            while True:
                try:kind,value=self.output.events.get_nowait()
                except queue.Empty:break
                self.audio_notice=value;self.audio_status.set(value)
                if kind=='error':self.log(value)
            while True:
                try:kind,value=self.background_events.get_nowait()
                except queue.Empty:break
                if kind=='recap':
                    sid,text=value
                    if sid==self.recap_requested:
                        self.recap_status.set(f'Session {sid} • evidence, possible explanations and practice plan')
                        self.recap_text.configure(state='normal');self.recap_text.delete('1.0','end');self.recap_text.insert('end',text);self.recap_text.configure(state='disabled')
                else:
                    self.device_busy=False
                    if kind=='devices':self.receive_devices(value)
                    else:self.device_status.set(value)
            if time.monotonic()-self.last_device_scan>20 and not self.device_busy:self.scan_devices()
            while True:
                try:kind,value=self.update_events.get_nowait()
                except queue.Empty:break
                if kind=='progress':self.update_status.set(value);continue
                self.updating=False
                if kind=='available':
                    self.update_candidate=value;self.update_status.set('Version '+value['version']+' is ready. Stop driving, then choose Install update.')
                elif kind=='downloaded':
                    if self.mode:
                        self.update_status.set('Update verified and staged. Stop recording before installing.');self.staged_update=value
                    else:
                        updater.launch_when_closed(value);self.close();return
                else:self.update_status.set(value)
            while True:
                try:kind,value=self.ibt_events.get_nowait()
                except queue.Empty:break
                self.ibt_busy=False
                if kind=='candidate':
                    self.ibt_candidate=value;m=value['profile'];p=value['provenance']
                    self.ibt_status.set(f"Candidate: {m['car']} at {m['track']} / {m['config']} • {duration(value['lap_time'])} • {p['clean_laps']} clean laps • recorded timestamps. Confirm conditions before use.")
                    self.reference_match.set(False)
                else:self.ibt_status.set(value)
            while True:
                try:kind,value=self.reference_events.get_nowait()
                except queue.Empty:break
                self.reference_search_busy=False
                if kind=='candidate':
                    self.external_candidate=value
                    lap=value['lap'];info=value['info']
                    self.external_status.set('Fetched '+duration(lap['lapTime'])+' at '+value['profile']['track']+' / '+value['profile']['config']+'. Track temperature '+str(lap.get('trackTemp'))+'°C; wetness '+str(lap.get('trackWetness'))+'%. Searched '+str(info['searched'])+' accessible records. Confirm matching conditions to use it.')
                else:self.external_status.set(str(value))
            while True:
                try:kind,value=self.neural.events.get_nowait()
                except queue.Empty:break
                self.free_status.set(value)
                if kind=='error':self.log(value)
            while True:
                try:kind,value=self.local_ai.events.get_nowait()
                except queue.Empty:break
                if kind=='delta':self.chat_stream+=value;self.chat_answer.set(self.chat_stream)
                elif kind=='answer':
                    self.chat_answer.set(value);self.live_status.set('Local AI reply · check advice against your measured data.')
                    self.log('Local AI: '+value)
                    if self.options.get('read_local_chat',False):self.reply_queue.append(('answer',value,time.monotonic()+30))
                else:self.live_status.set(value)
            if self.local_ai.busy and self.mode and self.data.get('Speed',0)>3:self.local_ai.stop()
            while True:
                try:kind,value=self.live_voice.events.get_nowait()
                except queue.Empty:break
                self.live_status.set(value)
                if kind=='transcript':self.log('Engineer: '+value)
                elif kind in ('error','connected','notice','disconnected'):self.log(value)
            while True:
                try:kind,value=self.cue_audio.events.get_nowait()
                except queue.Empty:break
                self.log(value)
                self.cue_status.set(value)
                if kind=='error':self.set_cues(False,persist=False)
            while True:
                try:
                    kind,value = self.speech.events.get_nowait()
                except queue.Empty:
                    break
                if kind=='input_ready':self.mic_input_status.set(value)
                elif kind=='partial':self.mic_transcript.set('Hearing: '+str(value) if value else 'Listening…')
                elif kind=='heard':self.mic_transcript.set('Recognized: '+str(value))
                if kind in ('heard','ready','error','stopped','mic_error'):
                    self.mic_test_status.set(('Recognized: ' if kind=='heard' else '')+str(value))
                if kind=='ready':
                    self.mic_on=True;self.mic_button.configure(text='Disable microphone')
                elif kind=='mic_error':
                    self.speech.stop_mic();self.mic_on=False;self.mic_button.configure(text='Enable microphone');self.mic_input_status.set('Input or recognition failed. Check device selection and Windows microphone access.')
                if kind=='partial':continue
                if kind=='wake':
                    self.live_status.set('Kerby is listening for your question.')
                    self.reply_queue.append(('answer',self.live_voice.acknowledgment(),time.monotonic()+6));continue
                if kind=='question':self.ask_engineer(value);continue
                if kind=='voices':
                    self.update_voice_list(value)
                elif kind=='command':
                    self.log('Heard: '+value.replace('_',' ')); self.command(value)
                else:
                    self.log(value)
                    if kind=='stopped':
                        self.mic_on=False; self.mic_button.configure(text='Enable microphone')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            message = str(exc)
            self.connection.set(message)
            self.coach.invalid.add('telemetry unavailable'); self.coach.pending.clear()
            if message != self.last_error:
                self.log(message); self.last_error = message
        except Exception as exc:
            self.mode=None; self.reader.close(); self.store.finish()
            self.connection.set('Recording stopped after an error: '+str(exc))
            self.log('Error: '+str(exc))
        if self.mode=='LIVE' and time.monotonic()-self.last_seen>.35:
            self.speech.interrupt();self.cue_audio.stop();self.live_voice.prioritize_driving(True)
            self.spotter.reset();self.flow.active=False;self.flow.previous=None;self.relatives.reset();self.straights.snapshot={}
        if time.monotonic()-self.last_draw>.05:
            try:self.render()
            except Exception as exc:
                self.connection.set('Dashboard refresh error: '+str(exc))
            self.last_draw=time.monotonic()
        self.pump_driver_reply()
        self.root.after(50 if self.mode=='DEMO' else 16,self.tick)

    def ingest(self,d,meta):
        if not supported(meta):
            self.connection.set('Waiting for stable car / track metadata. Coaching paused.');return
        key = (self.mode,meta.get('sim_session'),meta.get('track_id'),meta.get('config'),meta.get('car_path'),meta.get('car_id'),d.get('SessionNum'),d.get('PlayerCarIdx'))
        if key != self.key or (self.data and d['SessionTime'] < self.data.get('SessionTime',0)):
            self.guide_match.set(False)
            for value in self.guide_fields.values():value.set('')
            self.speech.interrupt();self.cue_audio.stop();self.cues.clear_guide();self.signals.clear();self.last_record_time=-1e9;self.seeded_reference=None
            self.coach = Coach(); self.store.start(self.mode,meta,d['SessionTime']); self.key=key
            self.reference_meta=meta
            if supported(meta):
                saved=self.store.reference(meta,context(d),self.mode)
                if saved:
                    try:
                        self.coach.import_reference(saved,meta,context(d))
                        self.coach.reference_label=('Saved Garage 61 reference for this car and exact layout' if saved.get('provenance') else 'Saved clean reference for this car and exact layout')
                        self.log('Loaded saved reference: '+meta['track']+' / '+meta['config'])
                    except (ValueError,KeyError,TypeError):pass
            self.pit_engineer=PitEngineer();self.saved_pit_reports=0;self.tire_monitor=TireMonitor();self.opponent_scout=OpponentScout()
            self.last_live_why='';self.last_live_why_at=-1e9
            self.position.select(meta);self.load_position_guide(meta,d)
            self.last_lap = None;self.best_lap_time=self.store.personal_best(meta,context(d),self.mode)
            self.refresh_training();self.spotter.reset();self.flow.reset();self.praise.reset();self.situations.reset();self.relatives.reset();self.straights.reset()
            if self.setup_phase:
                self.setup_phase=None
                self.log('Setup run paused because the simulator session changed.')
        self.data,self.meta=d,meta
        if self.last_guide_context!=context(d):
            self.guide_match.set(False);self.last_guide_context=context(d);self.opponent_scout=OpponentScout()
        if self.mode=='LIVE':self.last_seen=time.monotonic()
        identity=car_identity(meta,d);self.live_voice.set_car(identity)
        self.car_status.set((session_kind(meta).upper()+'  •  CAR  '+identity['name']+'  •  '+str(identity['car_class'] or '')) if identity else 'Current car: identity unavailable; waiting for the player’s entry')
        self.track_display.set(meta['track']+' / '+(meta.get('config') or 'Default layout'))
        self.position.update(d,meta);self.signals.append(d)
        if d['SessionTime']-self.last_record_time>=.049:
            self.store.record(d);self.last_record_time=d['SessionTime']
        self.situations.update(d,meta);self.relatives.update(d)
        self.tire_monitor.update(d);self.opponent_scout.update(d,self.relatives.latest)
        tire_wear=[v['tread_min'] for v in self.tire_monitor.current if v['tread_min'] is not None]
        self.tire_status.set(f'Tires • lowest reported tread {min(tire_wear):.0f}% • pit data, not live grip' if tire_wear else 'Tires • live temperature/wear unavailable; reported snapshots in session recap')
        self.scout_status.set(self.opponent_scout.summary())
        lap,reviews = self.coach.update(d,meta)
        if lap:
            best=self.store.personal_best(meta,lap['context'],self.mode)
            praise=self.praise.completed(lap,best,self.mode,d['SessionTime']) if self.options.get('praise',True) else None
            if praise:self.praise_status.set('Last milestone: '+praise)
            if lap['clean']:self.best_lap_time=min(self.best_lap_time or lap['lap_time'],lap['lap_time'])
            self.pit_engineer.completed(lap,d)
            lap_id=self.store.lap(lap); self.last_lap=lap
            candidates=[r for r in lap.get('reviews',[]) if r.get('tip') and r.get('loss',0)>=.15]
            if lap['clean'] and candidates:
                priority=max(candidates,key=lambda r:r['loss'])
                self.coach.pending=[(d['SessionTime'],'Lap complete. '+spoken_review(priority,int(lap['lap'])),priority)]
            self.store.save_reference(lap,meta,self.mode)
            self.tag_setup_lap(lap,lap_id,d)
            self.log(f'Lap {lap["lap"]}: {duration(lap["lap_time"])} — '+('clean' if lap['clean'] else 'excluded: '+', '.join(lap['reasons'])))
            self.refresh_history()
        for review in reviews:
            self.log(review['evidence']+' '+review['tip'])
        if reviews or lap:self.refresh_training()
        if self.coach.reference and self.seeded_reference!=id(self.coach.reference):
            self.position.seed(self.coach.reference);self.seeded_reference=id(self.coach.reference)
        verbosity=self.options.get('radio_verbosity','Chatty')
        self.straights.cooldown={'Quiet':90,'Standard':30,'Chatty':18}.get(verbosity,30)
        self.relatives.cooldown={'Quiet':90,'Standard':40,'Chatty':25}.get(verbosity,40)
        previous_pit_state=self.pit_engineer.state
        self.pit_engineer.update(d,meta,self.relatives.latest,verbosity)
        if self.pit_engineer.report_count>self.saved_pit_reports:
            self.store.save_pit_report(self.pit_engineer.report);self.saved_pit_reports=self.pit_engineer.report_count
        if previous_pit_state=='box' and self.pit_engineer.state!='box':self.speech.interrupt();self.live_voice.prioritize_driving(True)
        if self.pit_engineer.last_event=='box' and any(v['priority']>=5 for v in self.pit_engineer.queue):self.speech.interrupt();self.live_voice.prioritize_driving(True)
        traffic=self.spotter.update(d) if self.options.get('spotter',True) else None
        if not self.options.get('spotter',True):self.spotter.reset()
        moving=bool(driving(d))
        aligned_guide=self.cues.guide and (self.cues.guide.get('context') is None or tuple(self.cues.guide['context'])==context(d))
        # Geometry and speech windows must remain available independently of
        # whether the short cue audio has finished preparing.
        cue=self.cues.update(d,meta,self.coach)
        marker_ready=bool(aligned_guide or self.coach.reference) and not self.cues.pause_reason
        if marker_ready:self.straights.update(d,meta,self.cues.plans,self.coach.reference)
        else:self.straights.snapshot={}
        flow_call=self.flow.update(d,self.cues.enabled and self.options.get('input_feedback',True),marker_ready)
        occupied=self.spotter.available and bool(self.spotter.left or self.spotter.right)
        self.speech.quiet=occupied or (self.cues.enabled and self.cues.approaching)
        self.live_voice.prioritize_driving(self.speech.quiet or self.cue_audio.busy or self.speech.speaking)
        # Traffic occupancy always precedes driving instructions. Never queue stale countdowns.
        dispatched=False;cue_played=False
        if traffic:
            dispatched=self.instruct(TRAFFIC_PHRASES[traffic],'traffic_'+traffic)
        elif cue and not occupied and time.monotonic()>=self.traffic_until and (not self.cue_audio.busy or cue in ('brake','turn','release')):
            dispatched=self.instruct(PHRASES[cue],cue);cue_played=bool(dispatched)
        elif flow_call and not self.speech.quiet and not self.cue_audio.busy and not getattr(self.live_voice,'pending',False):
            dispatched=self.instruct(flow_call)
        if cue:self.cues.acknowledge(cue_played,'traffic' if occupied or traffic else 'muted' if self.speech.muted else 'audio busy / not ready')
        if not moving and self.cues.enabled:
            self.cue_status.set('Automatic coach armed • waiting for forward driving on track')
        elif self.cues.enabled and not (self.cues.guide or self.coach.reference):
            self.cue_status.set('Coach active • observing inputs and learning a clean lap before positioned corner calls')
        quiet=self.speech.quiet or self.cue_audio.busy or self.speech.speaking or self.speech.muted or bool(dispatched) or getattr(self.live_voice,'pending',False) or getattr(self.live_voice,'recording',False)
        if not quiet and self.options.get('situational',True):
            pit_call=self.pit_engineer.take(d)
            if pit_call:self.instruct(pit_call);quiet=True
        if moving and not quiet:
            # Detailed review gets a window before routine straight chatter.
            # Critical positioned calls and traffic were already handled above.
            available=self.straights.snapshot.get('eta_s',12.)
            call=self.coach.voice(d,available_seconds=available) if self.cues.enabled and self.auto_coaching.get() else None
            if call:
                review=self.coach.last_spoken_review
                self.last_live_why=live_reason(review) if review else ''
                self.last_live_why_at=d['SessionTime']
                if self.live_voice.connected:self.live_voice.coaching(self.personality.decorate(call),self.telemetry_snapshot())
                else:self.instruct(self.personality.decorate(call))
            else:
                report=self.straights.voice(d,self.relatives.latest) if self.cues.enabled and self.options.get('straight_briefings',True) else None
                if not report and self.options.get('situational',True):report=self.tire_monitor.voice(d) or self.situations.take(d) or self.relatives.voice(d) or self.opponent_scout.voice(d,occupied)
                if report:self.instruct(report)
                elif self.cues.enabled and self.options.get('praise',True):
                    encouragement=self.praise.take(d)
                    if encouragement:self.instruct(encouragement)
        self.connection.set(f'{self.mode} · {meta["car"]} · {meta["track"]} / {meta["config"]} · {meta["session_type"]} · recording locally')

    def render(self):
        state=connection_state(self.mode,self.data,self.meta,time.monotonic()-self.last_seen)
        self.connection_badge.set(state['label']);self.connect_button.configure(text=state['button'],state='disabled' if state['button']=='iRacing connected' else 'normal',style='Connected.TButton' if state['button']=='iRacing connected' else 'Accent.TButton')
        self.connection_pill.configure(foreground=theme.palette(self.options.get('theme','Dark'))[state['color']])
        capture=self.speech.capture
        db=capture.level_db if capture else -80
        self.mic_meter.delete('all')
        meter_width=max(1,self.mic_meter.winfo_width())
        self.mic_meter.create_rectangle(0,0,max(0,min(meter_width,(db+80)/80*meter_width)),28,fill=theme.palette(self.options.get('theme','Dark'))['green' if db< -3 else 'brake'],outline='')
        clipping=bool(capture and capture.clipping)
        self.mic_meter.create_text(12,14,anchor='w',text=f'INPUT  {db:.0f} dBFS'+('  •  CLIPPING' if clipping else ''),fill=theme.palette(self.options.get('theme','Dark'))['text'])
        fresh=self.mode!='LIVE' or time.monotonic()-self.last_seen<.35
        target=live_target(self.data,self.coach.reference) if self.data and fresh else None
        steering=live_steering(self.data,self.coach.reference) if self.data and fresh else None
        if steering:
            delta_angle=steering['difference_deg']
            self.steering_status.set(f"STEERING  {steering['actual_deg']:.0f}°  /  REF {steering['reference_deg']:.0f}°  •  {abs(delta_angle):.0f}° {'more' if delta_angle>0 else 'less'} wheel angle • Same steering ratio required")
        else:self.steering_status.set('Steering comparison activates while cornering' if self.coach.reference else 'Steering comparison starts with a matched reference')
        if target:
            delta=target['difference_pp'];direction='less' if delta>0 else 'more'
            self.technique_status.set(f"BRAKE INPUT  {target['actual']:.0f}%  /  REFERENCE  {target['target']:.0f}%  •  {abs(delta):.0f} percentage points {direction} to match")
        else:self.technique_status.set('Reference ready • Brake targets appear in comparable braking zones' if self.coach.reference else 'Learning • Complete a clean lap or import a matched reference')

        d=self.data
        if d:
            self.metrics['SPEED mph'].set(f'{d.get("Speed",0)*MPH:.0f}')
            self.metrics['GEAR'].set(str(d.get('Gear','—')))
            self.metrics['BRAKE %'].set(f'{d.get("Brake",0)*100:.0f}')
            self.metrics['THROTTLE %'].set(f'{d.get("Throttle",0)*100:.0f}')
            self.metrics['LAP'].set(str(d.get('Lap','--')))
            self.metrics['CURRENT LAP'].set(duration(d.get('LapCurrentLapTime')))
            self.metrics['BEST LAP'].set(duration(d.get('LapBestLapTime') or self.best_lap_time))
            delta=d.get('LapDeltaToSessionBestLap')
            self.metrics['DELTA'].set(f'{delta:+.3f}' if d.get('LapDeltaToSessionBestLap_OK') and isinstance(delta,(int,float)) else '—')
            self.metrics['LAST LAP'].set(duration(self.last_lap['lap_time'] if self.last_lap else d.get('LapLastLapTime')))
            if self.mode=='LIVE' and state['label']!='IRACING CONNECTED':
                for key in ('SPEED mph','GEAR','BRAKE %','THROTTLE %','CURRENT LAP','DELTA'):self.metrics[key].set('—')

            self.conditions.set(self.weather_text()+f'  |  ABS {d.get("dcABS","unavailable")}  ·  TC {d.get("dcTractionControl","unavailable")}')
        guide_valid=self.cues.guide and (self.cues.guide.get('context') is None or tuple(self.cues.guide['context'])==context(d))
        self.coach_status.set('Guide conditions changed — positioned calls paused.' if self.cues.guide and not guide_valid else ('Live coach: aligned corner guide ready. Calls follow your current position and inputs.' if guide_valid else self.coach.status))
        self.reference_status.set(self.cues.source+f' • {len(self.cues.plans)} positioned corners')
        self.dashboard.set_theme(self.options.get('theme','Dark'))
        self.situation_status.set(self.situation_text())
        fresh=bool(self.mode=='DEMO' or state['label']=='IRACING CONNECTED')
        self.straight_status.set(self.straights.hud(self.relatives.latest) if fresh else 'Next braking zone: waiting for fresh telemetry')
        for key in ('ahead','behind'):
            gap=self.relatives.latest.get(key) if fresh else None
            self.gap_values[key].set('~'+elapsed(gap['gap_s']) if gap else '—')
            trend='Passage-time estimate • collecting trend' if gap else 'Waiting for sufficient opponent history'
            if gap and gap['gain_s'] is not None:
                gain=gap['gain_s'];who='You gained' if key=='ahead' else 'Behind gained'
                trend=(who if gain>0 else 'Gap opened')+f' {abs(gain):.1f}s over {elapsed(gap["window_s"],0)} • estimated'
            self.gap_trends[key].set(trend)
        model=self.cockpit_model()
        if self.overlay:self.overlay.draw(model)
        pos=self.position.snapshot()
        tab_index=self.tabs.index(self.tabs.select())
        model.update(metrics={key:value.get() for key,value in self.metrics.items()},straight=self.straight_status.get(),gaps={key:value.get() for key,value in self.gap_values.items()},session_time=d.get('SessionTime'))
        self.dashboard.model=model
        if tab_index in (None,0):self.dashboard.draw(self.signals,self.position,self.cues.plans,self.coach.reference)
        if self.data and state['label']=='IRACING CONNECTED':
            kind=session_kind(self.meta)
            self.track_display.set(f'{kind.title()}  /  {self.meta.get("car","Car")}  /  {self.meta.get("track","Circuit")} · {self.meta.get("config") or "Default layout"}')
        elif self.mode=='DEMO':self.track_display.set('SYNTHETIC DEMO / Illustrative telemetry and route')
        self.footer_status.set((self.conditions.get() if model['fresh'] else state['label']+' / Waiting for fresh telemetry')[:115])
        diagnostic=self.cues.diagnostic
        distance=f'{pos.get("distance_m",0):.0f} m / {pos.get("lap_percent",0):.1f}%' if pos.get('distance_m') is not None else 'unavailable'
        section=(' • '+str(diagnostic.get('corner'))+': '+str(diagnostic.get('phase'))) if diagnostic and diagnostic.get('phase')!='approach' else (f' • Next {diagnostic.get("corner")} in {diagnostic.get("distance_m")} m' if diagnostic else '')
        self.position_status.set(f'Position {distance} • {pos.get("source","waiting")} • age {pos.get("age_ms",0)} ms'+section)
        if time.monotonic()-self.last_slow_draw<.5:return
        self.last_slow_draw=time.monotonic()
        if tab_index==2:self.draw_line()
        if tab_index not in (None,3):return
        self.channel_tree.delete(*self.channel_tree.get_children())
        for name,value in sorted(d.items()):
            if name.startswith('_'):continue
            meaning = 'Reported telemetry'
            if name=='Speed' and isinstance(value,(int,float)):
                value=value*MPH;meaning='mph, converted from the SDK’s m/s'
            if any(name.startswith(w) for w in ('LF','RF','LR','RR')):
                meaning = 'Reported tire value; freshness unknown / may be pit-updated'
            elif name.startswith('dc'):
                meaning = 'Setting only; intervention is not measured'
            elif name in ('Lat','Lon'):
                meaning = 'Position used for line mapping; absent channels disable line view'
            elif name=='Precipitation':
                meaning = 'Reported precipitation intensity (not a probability forecast)'
            elif name=='TrackWetness':
                meaning = 'iRacing track wetness category, not a percentage'
            self.channel_tree.insert('', 'end', values=(name,str(round(value,5) if isinstance(value,float) else value),meaning))

    def weather_text(self):
        d=self.data
        def temp(key):
            value=d.get(key)
            return f'{value:.1f}°C' if isinstance(value,(int,float)) else 'unavailable'
        wet={0:'unknown',1:'dry',2:'mostly dry',3:'very lightly wet',4:'lightly wet',5:'moderately wet',6:'very wet',7:'extremely wet'}.get(d.get('TrackWetness'),'unavailable')
        return f'Air {temp("AirTemp")}; track {temp("TrackTemp")}; wetness {wet}.'

    def command(self,name):
        if name=='recap':
            self.open_session_recap();self.log('Your session recap is available in Analyze → Session recap.',True);return
        if name=='mic_check':
            self.log('I can hear you. Microphone recognition is working.',True);return
        if name in ('enable_cues','disable_cues'):
            self.set_cues(name=='enable_cues');return
        if name=='focus_music':
            self.open_youtube();return
        if name=='mute':
            self.speech.muted=True;self.live_voice.muted=True;self.speech.interrupt();self.cue_audio.stop(); self.mute_button.configure(text='Unmute voice'); self.log('Voice muted. Microphone remains available.'); return
        if name=='unmute':
            self.speech.muted=False;self.live_voice.muted=False; self.mute_button.configure(text='Mute voice'); self.log('Voice enabled.',True); return
        if not self.data:
            self.log('No current telemetry. Connect iRacing or run the demo.',True); return
        if self.mode=='LIVE' and time.monotonic()-self.last_seen>2:
            self.live_voice.set_car(None)
            self.log('Telemetry is stale. Waiting for fresh player-car data before answering.',True);return
        if name=='setup':
            saved=self.setup_run.get('profile',{})
            if saved and (self.setup_run.get('mode')!=self.mode or any(saved.get(k)!=self.meta.get(k) for k in ('car_path','car_id','track_id','config'))):
                self.log('The saved setup test belongs to '+saved.get('car','another car')+'. Start a fresh baseline for '+self.meta.get('car','the current car')+' and this layout.',True);return
            self.update_setup_report()
            self.log(self.setup_report.get(),True); return
        if name=='track':
            text='You are at '+self.meta.get('track','an unidentified track')+', '+(self.meta.get('config') or 'the default layout')+'.'
        elif name=='position':
            pos=self.position.snapshot()
            text=(f'You are {pos["lap_percent"]:.1f} percent around the lap, {pos["distance_m"]:.0f} meters from the start.' if pos.get('valid') else 'Fresh track position is unavailable. Waiting for live telemetry.')
            if pos.get('valid') and self.cues.enabled and self.cues.diagnostic:text+=' Current section: '+self.cues.diagnostic['corner']+'.'
        elif name=='car':
            identity=car_identity(self.meta,self.data)
            text=('You are driving '+identity['name']+('. Class '+identity['car_class'] if identity['car_class'] else '')+'.') if identity else 'The player’s car identity is unavailable. Waiting for fresh iRacing data.'
        elif name=='last_lap':
            text = f'Last recorded lap: {duration(self.last_lap["lap_time"])}.' if self.last_lap else 'No complete lap recorded yet.'
        elif name=='weather':
            text=self.weather_text()+' Rain forecasting is not available in this version.'
        elif name=='tires':
            text=tire_text(self.tire_monitor.current)
        elif name in ('abs','tc'):
            key='dcABS' if name=='abs' else 'dcTractionControl'
            label='ABS' if name=='abs' else 'traction control'
            value=self.data.get(key)
            text=f'{label} setting is {value}.' if value is not None else f'{label} setting is unavailable.'
            text+=' Ranges and assistance direction depend on this vehicle. Review the reported controls and the car’s garage before changing a setting.'
        elif name=='opportunities':
            text=self.opponent_scout.summary()
        elif name=='explain':
            reviews=self.coach.reviews or (self.last_lap or {}).get('reviews',[])
            text='For the most recently analyzed corner: '+explain(reviews[-1]) if reviews else 'I need a comparable corner before explaining a specific instruction. The racecraft library includes the general concepts.'
        elif name=='review':
            reviews=self.coach.reviews or (self.last_lap or {}).get('reviews',[])
            if not reviews:
                text='I need a clean reference and a comparable section before identifying time losses.'
            else:
                r=max(reviews,key=lambda r:r['loss'])
                text=spoken_review(r) or r['evidence'] if r['loss'] >= .15 else 'No section has lost at least fifteen hundredths against the reference so far.'
        elif name=='line':
            offset=line_offset(Sample.from_data(self.data),self.coach.reference)
            text=f'You are approximately {offset:.1f} meters from the reference path here. This does not establish which line is faster.' if offset is not None else 'Line comparison needs position telemetry and a compatible reference lap.'
        else:
            text=self.coach.status+'. '+self.coach.reference_label+'.'
        self.log(text,True)

    def open_local_chat(self):
        self.tabs.select(7);self.voice_tabs.select(1)

    def save_wake_setting(self):
        self.options['wake_enabled']=bool(self.setting_wake.get())
        self.speech.wake.enabled=self.options['wake_enabled'];self.speech.wake.reset()
        self.save_driving_options()

    def connect_live(self):
        if not self.mic_on:self.toggle_mic()

    def disconnect_live(self):
        self.stop_microphone();self.stop_local_ai()

    def toggle_live_talk(self):
        self.toggle_mic()
        self.talk_button.configure(text='Disable microphone' if self.mic_on else 'Enable microphone')

    def install_local_ai(self):
        if self.mode and self.data.get('Speed',0)>1:
            self.live_status.set('Stop the car before installing the optional local model.');return
        try:
            if self.local_ai.install():self.live_status.set('Installing free local AI. Download only; no account or payment.')
        except OSError as exc:self.live_status.set(str(exc))

    def stop_local_ai(self):
        self.local_ai.stop();self.live_status.set('Extended AI stopped; its memory will be released. Built-in racing answers remain ready.')

    def ask_engineer(self,question=None):
        text=str(question if question is not None else self.chat_question.get()).strip()[:1200]
        if not text:return
        if question is None:self.chat_question.set('')
        self.reply_queue.append(('question',text,time.monotonic()+30))
        self.reply_queue=self.reply_queue[-4:]
        self.live_status.set('Question queued. Critical driving calls have priority.')

    def pump_driver_reply(self):
        now=time.monotonic()
        self.reply_queue=[x for x in self.reply_queue if x[2]>now]
        if not self.reply_queue or self.local_ai.busy:return
        if self.speech.speaking or self.speech.quiet or self.cue_audio.busy or now<self.speech.cue_until or now<self.traffic_until:return
        if self.mode=='LIVE' and now-self.last_seen>.35:return
        eta=self.straights.snapshot.get('eta_s')
        if self.mode and self.data.get('Speed',0)>3 and (eta is None or eta<18):return
        kind,value,_=self.reply_queue.pop(0)
        if kind=='answer':
            self.chat_answer.set(value);self.log(value,True);return
        snapshot=self.telemetry_snapshot();reply=self.live_voice.answer(value,snapshot)
        if reply.command:self.command(reply.command);return
        if reply.text:
            self.chat_answer.set(reply.text);self.live_status.set('Answered locally from racing knowledge or current telemetry.')
            self.log(reply.text,True);return
        if self.mode and self.data.get('Speed',0)>3:
            self.chat_answer.set('Extended AI chat is available when stopped. While driving, ask about your corner, next braking zone, tires or a racing technique.');return
        if not self.local_ai.installed():
            self.chat_answer.set('Install the free local AI for open-ended chat. Built-in racing questions and technique explanations already work offline.');return
        self.chat_stream='';self.chat_answer.set('Thinking locally…')
        self.local_ai.ask(value,self.live_voice.context(value,snapshot))

    def telemetry_snapshot(self):
        if self.mode is None or (self.mode=='LIVE' and time.monotonic()-self.last_seen>2):
            self.live_voice.set_car(None)
            return dict(mode='not connected or telemetry stale',current_car=None)
        d=self.data;reviews=self.coach.reviews or (self.last_lap or {}).get('reviews',[])
        identity=car_identity(self.meta,d);self.live_voice.set_car(identity)
        return dict(mode=self.mode,current_car=identity,car=self.meta.get('car'),track=self.meta.get('track'),
            next_braking_zone=dict(self.straights.snapshot),traffic=self.spotter.snapshot(),position=self.position.snapshot(),next_corner=dict(self.cues.diagnostic),guide_source=self.cues.source,
            track_id=self.meta.get('track_id'),layout=self.meta.get('config'),
            lap=d.get('Lap'),speed_mph=round(d['Speed']*MPH,1) if isinstance(d.get('Speed'),(int,float)) else None,
            gear=d.get('Gear'),rpm=d.get('RPM'),brake=d.get('Brake'),throttle=d.get('Throttle'),steering_angle=d.get('SteeringWheelAngle'),
            last_lap_s=(self.last_lap or {}).get('lap_time'),track_temp_c=d.get('TrackTemp'),air_temp_c=d.get('AirTemp'),
            wetness=d.get('TrackWetness'),abs=d.get('dcABS'),tc=d.get('dcTractionControl'),
            reference=self.coach.reference_label,coaching_status=self.coach.status,recent_sections=reviews[-3:],
            tire_report=dict(values=self.tire_monitor.current,freshness='reported/pit snapshots; not live tire condition'),
            pit_phase=self.pit_engineer.state,pit_report=self.pit_engineer.report,session_type=session_kind(self.meta),opponent_opportunity=dict(self.opponent_scout.latest),opponent_data_limit='longitudinal position timing only; no opponent pedal or steering inputs',steering_units='radians at steering wheel')

    def adjust_cue_lead(self,delta):
        try:self.cue_lead.set(str(max(0,min(1000,int(self.cue_lead.get())+delta))));self.save_cue_timing()
        except ValueError:self.log('Enter a numeric audio lead first.')

    def save_cue_timing(self):
        try:
            lead=int(self.cue_lead.get())
            if not 0<=lead<=1000:raise ValueError()
            self.cues.lead_seconds=lead/1000
            self.settings_lead.set(str(lead))
            (self.folder/'cue_timing.json').write_text(json.dumps(dict(lead_ms=lead)))
            self.log(f'Driving cue audio lead set to {lead} ms. Verify in solo practice; actual audio latency varies by device.')
        except (ValueError,OSError):self.log('Could not apply cue timing.')

    def browse_ibt(self):
        if self.mode:self.ibt_status.set('Stop recording before importing an IBT file.');return
        if self.ibt_busy:return
        path=filedialog.askopenfilename(filetypes=[('iRacing telemetry','*.ibt')])
        if not path:return
        self.ibt_busy=True;self.ibt_candidate=None;self.ibt_cancel.clear();self.ibt_status.set('Reading native telemetry and checking complete clean laps…')
        def work():
            try:self.ibt_events.put(('candidate',import_ibt(path,cancel=self.ibt_cancel)))
            except Exception as exc:self.ibt_events.put(('error',str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def use_ibt_reference(self):
        payload=self.ibt_candidate
        if not payload:self.ibt_status.set('Import a valid IBT candidate first.');return
        if not self.reference_match.get():self.ibt_status.set('Confirm matching conditions, tires, setup and aids before activating this reference.');return
        try:
            meta=self.meta or payload['profile']
            self.coach.import_reference(payload,meta,context(self.data) if self.data else None)
            payload['provenance']['conditions_confirmed_by_user']=True
            self.store.save_external_reference(payload,'LIVE');self.reference_meta=dict(payload['profile'])
            self.coach.reference_label='Native IBT clean reference • recorded timestamps'
            self.ibt_status.set('Saved for this exact car/layout and recorded conditions. It will load automatically when you connect a matching session.')
            self.log('Native IBT reference activated. Optimality is unverified.')
        except (ValueError,KeyError,TypeError) as exc:self.ibt_status.set(str(exc))

    def save_free_voice(self):
        label=self.free_choice.get()
        if label not in FREE_VOICES:return
        self.prefer_live=False
        self.speech.interrupt();self.cue_audio.stop();self.cues.reset();self.cues.enabled=bool(self.options.get('auto_coach',True))
        self.free_voice=FREE_VOICES[label][0];self.use_neural=True
        self.speech.neural=self.neural;self.speech.neural_voice=self.free_voice
        self.personality=Personality(self.free_style.get());self.speech.quiet=False;self.speech.cue_until=0.
        self.cue_audio=self.make_cue_audio('');self.cue_audio.prepare()
        self.set_cues(self.cues.enabled,persist=False)
        self.free_status.set('Selected '+label+'. Free offline coaching voice enabled.')
        try:(self.folder/'free_voice.json').write_text(json.dumps(dict(voice=self.free_voice,style=self.personality.style)),encoding='utf-8')
        except OSError:self.log('Could not save the free-voice preference.')

    def preview_free_voice(self):
        if FREE_VOICES[self.free_choice.get()][0]!=self.free_voice or not self.use_neural:
            self.free_status.set('Click Use this free voice before previewing.');return
        self.log('Let us work on one change at a time. Ease the brake as the steering builds, then feed the power in as the wheel opens. The aim is a smooth, repeatable exit.',True)

    def make_cue_audio(self,voice_id):
        if self.use_neural:return CueAudio(self.folder/'neural_cues',bundled_clips=self.neural.clips(self.free_voice),output=self.output)
        cache=hashlib.sha256((voice_id or 'windows-default').encode('utf-8')).hexdigest()[:16]
        return CueAudio(self.folder/'cue_audio_v3'/cache,voice_id,output=self.output)

    def update_voice_list(self,voices):
        choices={'Windows default':''}
        language_names={'c09':'Australian English','809':'British English','409':'American English','1009':'Canadian English','1809':'Irish English','1409':'New Zealand English'}
        for item in voices:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id']:continue
            name=str(item.get('name','Windows voice'))[:160]
            locale=str(item.get('language','')).split(';')[0].lower().lstrip('0')
            accent=language_names.get(locale,('language '+locale if locale else 'accent unknown'))
            gender=str(item.get('gender','unknown'))[:30] or 'unknown'
            label=f'{name} — {accent}, {gender}'
            base=label;n=2
            while label in choices:label=f'{base} ({n})';n+=1
            choices[label]=item['id']
        selected=self.voice_settings.voice_id
        matched=next((label for label,ident in choices.items() if selected and ident==selected),None)
        if selected and not matched:
            label='Unavailable: '+self.voice_settings.label
            choices[label]=selected;matched=label
        self.voice_choices=choices
        self.voice_dropdown.configure(values=list(choices))
        self.voice_choice.set(matched or 'Windows default')
        count=len(choices)-1-(1 if selected and matched and matched.startswith('Unavailable: ') else 0)
        self.engineer_status.set(f'{count} installed SAPI voices found. Choose a voice and click Save engineer.' + (' Selected voice is unavailable; install it or choose another.' if selected and matched and matched.startswith('Unavailable: ') else ''))

    def save_engineer(self):
        try:
            label=self.voice_choice.get()
            if label not in self.voice_choices or label.startswith('Unavailable: '):
                raise ValueError('Choose an installed voice from the list.')
            voice_id=self.voice_choices[label];style=self.radio_style.get()
            self.voice_settings.save(voice_id,label,style)
            self.speech.interrupt();self.cue_audio.stop();self.cues.reset();self.cues.enabled=bool(self.options.get('auto_coach',True))
            self.use_neural=False;self.speech.neural=None
            self.speech.quiet=False;self.speech.cue_until=0.;self.speech.voice_id=voice_id
            self.personality=Personality(style);self.cue_audio=self.make_cue_audio(voice_id);self.cue_audio.prepare()
            self.set_cues(self.cues.enabled,persist=False)
            self.cue_status.set('Selected voice saved. Automatic coach preference retained.')
            self.engineer_status.set(f'Saved: {label} · {style}. Automatic coach preference retained; preparing short voice calls.')
            self.log('Engineer voice and radio language saved.')
        except (OSError,ValueError) as exc:self.engineer_status.set(str(exc));self.log(str(exc))

    def preview_engineer(self):
        # Preview the saved configuration, so the exact selected voice is used.
        if self.voice_choices.get(self.voice_choice.get())!=self.voice_settings.voice_id or self.radio_style.get()!=self.voice_settings.style:
            self.engineer_status.set('Save engineer before previewing the new selection.');return
        preview=Personality(self.personality.style)
        if preview.style=='Mild':preview.calls=2
        text=preview.decorate('Good lap. Let us work on that corner exit next time.')
        self.log('Engineer preview: '+text,True)

    def set_cues(self,enabled,persist=True):
        self.setting_auto.set(bool(enabled))
        if persist:
            self.options['auto_coach']=bool(enabled);self.save_driving_options()
        self.flow.reset()
        self.cues.reset();self.cues.enabled=enabled
        self.cue_button.configure(text='Pause automatic coach' if enabled else 'Resume automatic coach')
        if enabled:
            self.cue_status.set('Preparing direct audio calls. Position guide or learned corner markers required.')
            self.cue_audio.prepare()
            if self.cue_audio.ready:self.cue_status.set('Live coach enabled. Calls follow track position, current approach rate and your audio lead.')
            self.log('Live coach enabled. Positioned calls follow spatial markers. The separate traffic spotter has priority.')
        else:
            self.cue_audio.stop();self.speech.quiet=False;self.speech.cue_until=0.;self.live_voice.prioritize_driving(False)
            self.cue_status.set('Coach paused. Traffic spotter remains controlled separately.');self.log('Automatic coach paused.')

    def save_youtube(self):
        try:
            self.youtube.save(self.youtube_url.get())
            self.youtube_status.set('YouTube link saved. Say “Engineer play focus music” to open it.')
            self.log('YouTube focus-music link saved.')
        except (OSError,ValueError) as exc:
            self.youtube_status.set(str(exc));self.log(str(exc))

    def open_youtube(self):
        try:
            self.youtube.open()
            text='Opened YouTube in your browser. Choose a track or press Play if needed.'
            self.youtube_status.set(text)
            self.log(text,True)
        except (OSError,ValueError,webbrowser.Error) as exc:
            self.youtube_status.set(str(exc));self.log('YouTube: '+str(exc))

    def toggle_mute(self):
        self.command('unmute' if self.speech.muted else 'mute')

    def toggle_mic(self):
        if self.mic_on:
            self.speech.stop_mic(); self.mic_on=False; self.mic_button.configure(text='Enable microphone')
        else:
            self.mic_on=bool(self.speech.start_mic(self.options.get('microphone','System default'),self.options.get('mic_gain',1)))
            self.mic_button.configure(text='Disable microphone' if self.mic_on else 'Enable microphone')

    def refresh_training(self):
        if not hasattr(self,'training_table'):return
        self.training_table.delete(*self.training_table.get_children());self.training_review_rows={}
        rows=self.coach.reviews or (self.last_lap or {}).get('reviews',[])
        focus=self.training_focus.get()
        for r in sorted(rows,key=lambda row:row['loss'],reverse=True):
            metric=r.get('action_metric','')
            if focus=='Braking point' and metric!='braking distance':continue
            if focus=='Peak brake input' and metric!='brake input percentage points':continue
            if focus=='Steering' and r.get('steering_delta_deg') is None:continue
            if focus=='Throttle pickup' and r.get('pickup_m') is None:continue
            row_id=self.training_table.insert('','end',values=(r['name'],f"{'~' if r.get('timing_estimated') else ''}{r['loss']:+.3f} s",r.get('tip') or 'Reference matched; keep it consistent',r.get('confidence','Reference comparison')))
            self.training_review_rows[row_id]=r

    def test_microphone(self):
        try:
            gain=float(self.settings_gain.get())
            if not .1<=gain<=3:raise ValueError('Gain must be 0.1–3.0.')
            self.mic_on=bool(self.speech.start_mic(self.settings_mic.get(),gain,test=True))
            self.mic_button.configure(text='Disable microphone' if self.mic_on else 'Enable microphone')
            self.mic_transcript.set('Listening for your test phrase…')
            self.mic_test_status.set('Opening the selected microphone and local recognizer…' if self.mic_on else 'Microphone test could not start. Check the selected input and microphone access.')
        except ValueError as exc:self.mic_test_status.set(str(exc))

    def stop_microphone(self):
        self.speech.stop_mic();self.mic_on=False;self.mic_button.configure(text='Enable microphone');self.mic_test_status.set('Microphone stopped. Audio is not being captured.');self.mic_input_status.set('Input is stopped.')

    def refresh_history(self):
        selected = self.laps.selection() if hasattr(self,'laps') else ()
        if not hasattr(self,'laps'):
            return
        self.laps.delete(*self.laps.get_children()); self.lap_rows={}
        for row in self.store.history():
            lid,lap,elapsed,clean,started,mode,profile,recorded,sid=row
            self.lap_rows[str(lid)]=row
            self.laps.insert('','end',iid=str(lid),values=(lid,sid,lap,duration(elapsed),'clean' if clean else 'excluded',mode,started[:19].replace('T',' ')+' UTC'))
        if selected and selected[0] in self.lap_rows:
            self.laps.selection_set(selected[0])
        self.sessions.delete(*self.sessions.get_children())
        for sid,started,mode,profile,recorded,count in self.store.sessions():
            m=json.loads(profile)
            self.sessions.insert('','end',iid=str(sid),values=(sid,started[:19].replace('T',' ')+' UTC',mode,m.get('session_type'),duration(recorded),count))

    def get_selected(self):
        selection=self.laps.selection()
        if not selection:
            raise ValueError('Select a saved lap in Session & lap history first.')
        return self.store.get_lap(int(selection[0]))

    def select_lap(self,event=None):
        try:
            lap=self.get_selected()
            reviews=sorted(lap['reviews'],key=lambda r:r['loss'],reverse=True)[:3]
            self.review_text.set('Lap '+str(lap['lap'])+' · '+duration(lap['lap_time'])+' · '+('clean' if lap['clean'] else ', '.join(lap['reasons']))+'\n'+'\n'.join(r['evidence']+' '+r['tip'] for r in reviews))
        except ValueError:
            pass

    def show_current_line(self):
        self.selected_samples=None; self.selected_label=''; self.draw_line()

    def show_selected_line(self):
        try:
            lap=self.get_selected()
            self.selected_samples=[Sample(**s) for s in lap['samples']]
            self.selected_label=f'Historical lap {lap["lap"]} · {duration(lap["lap_time"])}'
            self.selected_meta=lap['profile']
            self.tabs.select(2); self.draw_line()
        except ValueError as exc:
            messagebox.showinfo('Select a lap',str(exc))

    def selected_as_reference(self):
        try:
            lap=self.get_selected()
            if not lap['clean']:
                raise ValueError('Only clean recorded laps can be references.')
            meta=self.meta or lap['profile']
            payload=dict(format='race-engineer-reference-v1',profile=lap['profile'],lap_time=lap['lap_time'],context=lap['context'],samples=lap['samples'])
            self.coach.import_reference(payload,meta,context(self.data) if self.data else None)
            self.reference_meta=meta
            self.log('Loaded recorded lap as reference. Its optimality is unverified.'); self.draw_line()
        except (ValueError,KeyError,TypeError) as exc:
            messagebox.showerror('Reference',str(exc))

    def export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='race_lap_history.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        try:
            with open(path,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['lap_id','session_id','started_utc','mode','session_type','car','track','layout','lap','lap_time_seconds','clean','recorded_session_seconds'])
                for lid,lap,elapsed,clean,started,mode,profile,recorded,sid in self.store.history():
                    m=json.loads(profile)
                    w.writerow([lid,sid,started,mode,m.get('session_type'),m.get('car'),m.get('track'),m.get('config'),lap,elapsed,clean,recorded])
            self.log('Lap times exported to '+str(Path(path).name))
        except OSError as exc:messagebox.showerror('Export',str(exc))

    def export_reference(self):
        try:
            lap=self.get_selected()
            if not lap['clean']:raise ValueError('Choose a clean lap to export as a reference.')
            payload=dict(format='race-engineer-reference-v1',profile=lap['profile'],lap_time=lap['lap_time'],context=lap['context'],label='Recorded clean lap; optimality unverified',samples=lap['samples'])
            path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='iracing_reference.json',filetypes=[('Reference JSON','*.json')])
            if path:Path(path).write_text(json.dumps(payload,allow_nan=False),encoding='utf-8')
        except (ValueError,OSError) as exc:messagebox.showerror('Export',str(exc))

    def import_reference(self):
        path=filedialog.askopenfilename(filetypes=[('Reference JSON','*.json')])
        if not path:return
        try:
            if Path(path).stat().st_size > 20_000_000:raise ValueError('Reference file too large.')
            payload=json.loads(Path(path).read_text(encoding='utf-8'))
            meta=self.meta or payload['profile']
            if not supported(meta):raise ValueError('Reference needs an identified iRacing car, track ID and layout.')
            self.coach.import_reference(payload,meta,context(self.data) if self.data else None)
            self.reference_meta=meta
            self.log('Imported reference. Optimality is unverified.'); self.draw_line()
        except (ValueError,OSError,KeyError,TypeError) as exc:messagebox.showerror('Import reference',str(exc))

    def draw_line(self):
        c=self.canvas; c.delete('all'); width,height=c.winfo_width(),c.winfo_height()
        if width < 20:return
        samples=self.coach.samples if self.selected_samples is None else self.selected_samples
        ref=self.coach.reference
        meta=self.meta if self.selected_samples is None else getattr(self,'selected_meta',{})
        refmeta=getattr(self,'reference_meta',self.meta)
        if any(meta.get(k)!=refmeta.get(k) for k in ('car_path','track_id','config')):
            ref=[]
        actual=[s for s in samples if s.lat is not None and s.lon is not None]
        reference=[s for s in ref if s.lat is not None and s.lon is not None]
        if len(actual)+len(reference)<2:
            c.create_text(width/2,height/2,text='Waiting for position telemetry and a recorded lap.\nMissing GPS channels disable this view.',fill='#93a5bc',font=('Segoe UI',12),justify='center');return
        points=actual+reference
        lat0=sum(s.lat for s in points)/len(points); lon0=sum(s.lon for s in points)/len(points)
        sx=111320*math.cos(math.radians(lat0)); sy=111320
        xy=lambda s:((s.lon-lon0)*sx,(s.lat-lat0)*sy)
        all_xy=[xy(s) for s in points]
        minx,maxx=min(p[0] for p in all_xy),max(p[0] for p in all_xy)
        miny,maxy=min(p[1] for p in all_xy),max(p[1] for p in all_xy)
        scale=min((width-90)/max(maxx-minx,1),(height-100)/max(maxy-miny,1))
        convert=lambda s:(45+(xy(s)[0]-minx)*scale,height-45-(xy(s)[1]-miny)*scale)
        for seq,color in ((reference,'#59d4db'),(actual,'#ffb65c')):
            if len(seq)>1:
                stride=max(1,len(seq)//2200)
                coords=[v for s in seq[::stride] for v in convert(s)]
                c.create_line(*coords,fill=color,width=2)
        if actual:
            x,y=convert(actual[-1]);c.create_oval(x-5,y-5,x+5,y+5,fill='#ffb65c',outline='')
        offsets=[v for s in actual[::max(1,len(actual)//150)] if (v:=line_offset(s,reference)) is not None]
        title=self.selected_label or 'Current lap'
        if offsets:title+=f' · mean sampled line separation {sum(offsets)/len(offsets):.1f} m'
        c.create_text(16,20,text=title,anchor='w',fill='#e7edf5',font=('Segoe UI',11))
        self.line_note.set('Orange: '+('historical lap' if self.selected_samples is not None else 'current lap')+'. Cyan: reference (optimality unverified).'+(' DEMO GEOMETRY.' if self.mode=='DEMO' else ''))

    def close(self):
        self.ibt_cancel.set()
        self.update_cancel.set()
        self.recap_cancel.set()
        if self.recap_worker and self.recap_worker.is_alive():self.recap_worker.join(timeout=5)
        self.local_ai.close()
        self.output.close(permanent=True);self.live_voice.close();self.speech.stop_mic();self.speech.interrupt();self.cue_audio.stop(); self.reader.close(); self.store.close()
        if self.overlay:self.overlay.close()
        self.root.destroy()


if __name__=='__main__':
    App(tk.Tk()).root.mainloop()
