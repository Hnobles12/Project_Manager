import pathlib
import PySimpleGUI as sg
import subprocess
from pathlib import Path
import os
import yaml
import shutil
import datetime
import tinydb as tdb
import git

GIT_USER = "user"
GIT_USER_EMAIL = "user@domain.com"

PDM_WL = "\\\\ftwusers\data\e\e433679\PDM Work Location"
FC_EXE = "C:/Users/e433679/Programs/FreeCommanderXE/FreeCommander.exe"

PM_DIR = 'C:/Users/e433679/Documents/Project_Manager/'
# PM_DIR_UNIX = '/c/Users/e433679/Documents/Project_Manager/'
#PM_DIR = '/home/hnobles12/Documents/Project_Manager/'
PM_DB_FILE = PM_DIR+'pm_db.json'

PM_PATH = Path('/c/Users/e433679/Documents/Project_Manager/')

COMPLETION_STATUS = ['NEW', 'IN-PROGRESS', 'COMPLETE', 'REWORK']
DISPOSITION = ['PASS', 'FAIL', 'UNKNOWN']
sg.theme('DarkBlack1')


def copy2clip(txt):
    cmd = 'echo '+txt.strip()+'|clip'
    return subprocess.check_call(cmd, shell=True)


class Db:

    def __init__(self, db_file):
        self.db = tdb.TinyDB(db_file)
        self.Pkg = tdb.Query()

    def get_pkg(self, pkg_name):
        pkg_data = self.db.search(self.Pkg.name == pkg_name)
        return pkg_data

    def get_pkg_names(self) -> list[str]:
        return [d.get('name') for d in self.db.all()]

    def get_CRs(self) -> list[str]:
        CRs = [d.get('CR') for d in self.db.all()]
        return [*set(CRs)]

    def get_pkg_names_by_CR(self, CR):
        return [d.get('name') for d in self.db.search(self.Pkg.CR == CR)]
    
    def get_pkg_names_by_CS(self, CS):
        return [d.get('name') for d in self.db.search(self.Pkg.PROJ_STATUS == CS)]
    def get_pkg_names_by_DSP(self, DISP):
        return [d.get('name') for d in self.db.search(self.Pkg.PROJ_DISPOSITION == DISP)]

    def insert_pkg(self, pkg: dict):
        self.db.insert(pkg)

    def update_pkg(self, pkg_name, pkg_dict):

        for pkg in self.get_pkg(pkg_name):
            self.db.update(pkg_dict, self.Pkg.name == pkg_name)


# Windows:
# Project Main Window


class ProjWin:

    def __init__(self, cr, pkg, new=False):
        self.cr = cr
        self.pkg = pkg
        self.new = new

        self.width = 1000
        self.height = 250

        self.proj_path = PM_DIR + f"{self.cr}/{self.pkg}/"
        os.environ["PM_CWD"] = self.proj_path        

        self.get_proj_files()
        self.load_proj_data()
        
        self.load_repo()

        print('proj_data: ', self.proj_data)

        l_col_layout = [[sg.Frame("Documentation:", layout=[[sg.Listbox(values=self.doc_files, size=(125, 10), key="_DOC_LB_")],
                                                            [sg.Button('Open', key='_OPEN_DOC_'), sg.FilesBrowse('Add Files', enable_events=True, key='_ADD_DOC_FILES_', target='_ADD_DOC_FILES_',initial_folder=self.proj_path+'/Documentation'), sg.Button('', key="__DOC_FILES_", visible=False), sg.Button("PDM WL", key='_OPEN_PDM_WL_'), sg.Button("FC", key="_OPEN_FC_")]])],

                        [sg.Frame('Analysis:', layout=[[sg.Listbox(values=self.analysis_files, size=(125, 10), key="_ANAL_LB_")],
                                                       [sg.Button('Open', key='_OPEN_ANALYSIS_'), sg.FilesBrowse('Add Files', enable_events=True, target="_ADD_ANAL_FILES_", key='_ADD_ANAL_FILES_',initial_folder=self.proj_path+'/Analysis')]])],

                        [sg.Frame('Results:', layout=[[sg.Listbox(values=self.results_files, size=(125, 10), key="_RES_LB_")],
                                                      [sg.Button('Open', key='_OPEN_RESULTS_'), sg.FilesBrowse('Add Files', enable_events=True, target="_ADD_RES_FILES_", key='_ADD_RES_FILES_',initial_folder=self.proj_path+'/Results')]])],
                        ]

        r_col_layout = [[sg.Frame('Work Status:', layout=[
            [sg.Text("Task Status: ", size=(10, 1)), sg.Combo(COMPLETION_STATUS,
                                                              default_value=self.proj_data.get('PROJ_STATUS') or "NEW", key="_STAT_COMBO_", size=(12, 1))],
            [sg.Text("Disposition: ", size=(10, 1)), sg.Combo(DISPOSITION, default_value=self.proj_data.get("PROJ_DISP") or "UNKNOWN", key="_DISP_COMBO_", size=(12, 1))],
        ], border_width=1)],
            [sg.Frame("Notes:", layout=[[sg.Multiline(default_text=self.proj_data.get(
                'PROJ_NOTES') or "PKG: \n\nCN TITLE: \n\nCN DESCRIPTION: \n", size=(75, 15), key='_PROJ_NOTES_')]])],
            [sg.Frame("TODOs:", layout=[[sg.Multiline(default_text=self.proj_data.get(
                'PROJ_TODOS'), size=(75, 15), key='_PROJ_TODOS_')]])],
            [sg.Button("Save", key="_UPDATE_STATUS_", bind_return_key=True), sg.Button(
                'Refresh', key='_REFRESH_'), sg.Button('Close', key="Quit")],
        ]

        top_row_details_frame = sg.Frame("Task Details:",
                                         layout=[[sg.Text('CR:', size=(10, 1)), sg.InputText(self.cr, disabled=True, size=(28, 1)), sg.Text(f'Created: {self.proj_data.get("created")}')],
                                                 [sg.Text(f'PKG/TASK:', size=(10, 1)), sg.InputText(self.pkg, disabled=True, size=(
                                                     28, 1)),sg.Text(f'Updated: {self.proj_data.get("updated")}') ],
                                                 [sg.Text(f"IO:", size=(10, 1)), sg.InputText(key='_PROJ_IO_', default_text=self.proj_data.get(
                                                     "PROJ_IO"), size=(28, 1))]])

        top_row_model_details_frame = sg.Frame('TVE Details:', layout=[
            [sg.Text('TVE: ', size=(15, 1)), sg.Multiline(
                self.proj_data.get('PROJ_TVE'), autoscroll=True, key='_PROJ_TVE_', size=(40, 5))],
        ])
        top_row_model_details_frame2 = sg.Frame('Model Details:', layout=[
            [sg.Column(layout=[[sg.Text('Models: ', size=(15, 1))],[sg.Button('Open', key='_OPEN_MODEL_'), sg.FilesBrowse('Add Files',enable_events=True, target='_ADD_MODEL_FILES_', key='_ADD_MODEL_FILES_', initial_folder=self.proj_path+'/Models')]]), sg.Listbox(self.models_files, key='_MODELS_LB_', size=(30, 5)), ],
        ])

        top_row_stats_frame = sg.Frame('Details:', layout=[[sg.Text(f'Created: {self.proj_data.get("created")}')],[sg.Text(f'Updated: {self.proj_data.get("updated")}')]])

        self.layout = [
            [top_row_details_frame, top_row_model_details_frame,
                top_row_model_details_frame2],
            [sg.HorizontalSeparator()],
            [sg.Column(l_col_layout), sg.VerticalSeparator(
                pad=(10, 10)), sg.Column(r_col_layout)]
        ]
        self.window = sg.Window(title="ProjManager V1",
                                layout=self.layout, resizable=True, finalize=True)
        
        self.window.bind('<Ctrl_L><s>', '_UPDATE_STATUS_')
        
    def get_proj_files(self):
        doc_files = []
        analysis_files = []
        results_files = []
        models_files = []

        for file in os.listdir(self.proj_path+"Documentation"):
            if os.path.isfile(os.path.join(self.proj_path, f"Documentation/{file}")):
                doc_files.append(file)

        for file in os.listdir(self.proj_path+"Analysis"):
            # if os.path.isfile(os.path.join(self.proj_path, f"Analysis/{file}")):
            #     analysis_files.append(file)
            analysis_files.append(file)
        for file in os.listdir(self.proj_path+"Results"):
            # if os.path.isfile(os.path.join(self.proj_path, f"Results/{file}")):
            #     results_files.append(file)
            results_files.append(file)
        for file in os.listdir(self.proj_path+"Models"):
            # if os.path.isfile(os.path.join(self.proj_path, f"Models/{file}")):
            #     models_files.append(file)
            models_files.append(file)

        self.doc_files = doc_files
        self.analysis_files = analysis_files
        self.results_files = results_files
        self.models_files = models_files
        
    def load_repo(self):
        self.actor = git.Actor(GIT_USER, GIT_USER_EMAIL)
        
        try: 
            self.repo = git.Repo(self.proj_path)
            print("GIT: Repo found.")
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.proj_path)
            print("GIT: Creating repo.")
            
        if self.repo.is_dirty():
            print("GIT: Working tree is dirty.")
        else:
            print("GIT: Working tree is clean.")
            
        self.untracked = self.repo.untracked_files
        
        # print(f"Untracked files: {self.untracked}")
        
    def check_repo_files(self)-> bool:
        self.untracked = self.repo.untracked_files
        self.modified = [item.a_path for item in self.repo.index.diff(None)]
        self.index = self.repo.index
        if len(self.untracked) != 0 or self.repo.is_dirty():
            print(f"GIT: Adding untracked files: {self.untracked}")
            self.index.add(self.untracked)
            print(f"GIT: Added untracked files.")
            # print(f"GIT: Adding modified files: {self.modified}")
            # self.index.add(all=True)
            # self.index.add(self.modified)
            # print(f"GIT: Added modified files.")
            self.repo.git.add(all=True)
            print("GIT: Added all files.")
            return True
        
        elif self.repo.is_dirty(): return True
        
        else: return False
             
    def commit_msg_popup(self) -> str:
        layout = [[sg.Text("Enter Commit Message")],
                      [sg.InputText(default_text='', size=(40, 3), key='COMMIT_MSG')],
                      [sg.Button("Commit Changes",key="COMMIT", bind_return_key=True), sg.Button("Cancel")]]
        window = sg.Window("Commit Message", layout, modal=True, finalize=True)
        while True:
            event, values = window.read()
            if event == "COMMIT":
                if values["COMMIT_MSG"] == '':
                    sg.Popup("Commit message box empty, please enter commit message.")
                    continue
                elif values["COMMIT_MSG"] == None:
                    message = None
                    break
                else:
                    message = values["COMMIT_MSG"]
                    break
                
            elif event == "Cancel":
                message = None
                break
        window.close()
        return message
    
    def commit_changes(self):
        message = self.commit_msg_popup()
        print(f"GIT: Committed changes with msg: \"{message}\"")
        if message != None and message != '':
            self.index.commit(message, author=self.actor, committer=self.actor)
        elif message == '':
            sg.Popup()
        else:
            sg.Popup("Canceled commit action, working tree is still dirty.")
            
            
            

    def load_proj_data(self):
        self.proj_data = db.get_pkg(self.pkg)[0]

    def save_project_data(self):
        db.update_pkg(self.pkg, self.proj_data)

    def add_files(self, dir, files):
        print(files.split(';'))
        files = files.split(';')
        for file in files:
            if file == '':
                continue
            shutil.copy2(file, dir)

    def spawn(self):
        while True:

            if self.new:
                event, values = self.window.read(timeout=250)
                event = "_UPDATE_STATUS_"
                
            
            else:
                event, values = self.window.read()

            print(event)

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "Quit":
                break
            elif event == "_CPY_CR_":
                copy2clip(f'{self.cr}'.strip().strip('/n'))
            elif event == "_CPY_PKG_":
                copy2clip(f'{self.pkg}'.strip().strip('/n'))
            elif event == "_CPY_IO_":
                copy2clip(f'{self.io}'.strip().strip('/n'))
            elif event == '_OPEN_DOC_':
                if self.window["_DOC_LB_"].get_indexes() == ():
                    os.startfile(self.proj_path+'Documentation')
                
                for i in self.window['_DOC_LB_'].get_indexes():
                    os.startfile(self.proj_path +
                                 'Documentation/'+self.doc_files[i])
                    break
            elif event == "_OPEN_PDM_WL_":
                try:
                    os.startfile(PDM_WL)
                except FileNotFoundError:
                    print("Error: Cannot open PDM Work Location. File not found.")
            elif event == '_OPEN_ANALYSIS_':
                if self.window["_ANAL_LB_"].get_indexes() == ():
                    os.startfile(self.proj_path+'Analysis')
                
                for i in self.window['_ANAL_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Analysis/' +
                                 self.analysis_files[i])
            elif event == '_OPEN_RESULTS_':
                if self.window["_RES_LB_"].get_indexes() == ():
                    os.startfile(self.proj_path+'Results')

                for i in self.window['_RES_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Results/' +
                                 self.results_files[i])
            elif event == '_OPEN_MODEL_':
                if self.window["_MODELS_LB_"].get_indexes() == ():
                    os.startfile(self.proj_path+'Models')

                for i in self.window['_MODELS_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Models/' +
                                 self.models_files[i])
            elif event == '_UPDATE_STATUS_':
                if self.new:
                    self.new = False
                self.proj_data['PROJ_STATUS'] = values['_STAT_COMBO_']
                self.proj_data['PROJ_DISPOSITION'] = values['_DISP_COMBO_']
                self.proj_data['PROJ_NOTES'] = values["_PROJ_NOTES_"]
                self.proj_data['PROJ_TODOS'] = values['_PROJ_TODOS_']
                self.proj_data['PROJ_IO'] = values['_PROJ_IO_']
                self.proj_data['PROJ_TVE'] = values['_PROJ_TVE_']
                self.proj_data['updated'] = datetime.datetime.now().isoformat()
                self.save_project_data()
                self.get_proj_files()
                self.window['_DOC_LB_'].update(values=self.doc_files)
                self.window['_ANAL_LB_'].update(values=self.analysis_files)
                self.window['_RES_LB_'].update(values=self.results_files)
                self.window['_MODELS_LB_'].update(values=self.models_files)
                
                if self.check_repo_files():
                    self.commit_changes()
                
                
                self.window.refresh()
            elif event == '_ADD_DOC_FILES_':
                self.add_files(self.proj_path+"/Documentation",
                               values['_ADD_DOC_FILES_'])
                self.get_proj_files()
                self.window['_DOC_LB_'].update(values=self.doc_files)
                self.window.refresh()
            elif event == '_ADD_ANAL_FILES_':
                self.add_files(self.proj_path+"/Analysis",
                               values['_ADD_ANAL_FILES_'])
                self.get_proj_files()
                self.window['_ANAL_LB_'].update(values=self.analysis_files)
                self.window.refresh()
            elif event == '_ADD_RES_FILES_':
                self.add_files(self.proj_path+"/Results",
                               values['_ADD_RES_FILES_'])
                self.get_proj_files()
                self.window['_RES_LB_'].update(values=self.results_files)
                self.window.refresh()
            elif event == '_ADD_MODEL_FILES_':
                self.add_files(self.proj_path+"/Models",
                               values['_ADD_MODEL_FILES_'])
                self.get_proj_files()
                self.window['_MODEL_LB_'].update(values=self.models_files)
                self.window.refresh()
            elif event == '_REFRESH_':
                self.get_proj_files()
                self.window['_DOC_LB_'].update(values=self.doc_files)
                self.window['_ANAL_LB_'].update(values=self.analysis_files)
                self.window['_RES_LB_'].update(values=self.results_files)
                self.window['_MODELS_LB_'].update(values=self.models_files)
                self.window.refresh()
            elif event == "_OPEN_FC_":
                subprocess.Popen([FC_EXE, "-c", self.proj_path])
                

        self.window.close()


# New Project Window
class NewProjWin:

    def __init__(self):
        self.layout = [
            [sg.Text('New Project')],
            [sg.Text("CR/Proj Number: ", size=(20, 1)), sg.InputText()],
            [sg.Text("Pkg. Number (Name): ", size=(20, 1)), sg.InputText()],
            [sg.Button("Create", bind_return_key=True), sg.Button("Back")]


        ]
        self.window = sg.Window(
            title="ProjManager V1", layout=self.layout, margins=(5, 5))

    def mk_proj_dir(self, cr, pkg):
        dirs = [PM_DIR+cr, PM_DIR+f'{cr}/{pkg}', PM_DIR+f'{cr}/{pkg}/Documentation',
                PM_DIR+f'{cr}/{pkg}/Analysis', PM_DIR+f'{cr}/{pkg}/Results', PM_DIR+f'{cr}/{pkg}/Models']
        try:
            os.mkdir(dirs[0])
        except:
            pass
        for dir in dirs[1:]:
            try:
                os.mkdir(dir)
            except:
                pass

        return True
    
    def migrate_setup_pkg(self, pkgs_dict):
        for cr in pkgs_dict:
            print(f'Migrating CR: {cr}')
            for pkg in pkgs_dict.get(cr):
                if len(db.get_pkg(pkg)) == 0:    
                    print(f'Migrating pkg: {pkg}')
                    self.mk_proj_dir(cr, pkg)
                    db.insert_pkg({'name':pkg, 'CR':cr})

    def spawn(self):
        self.time = datetime.datetime.now()
        while True:
            event, values = self.window.read()
            print(event)

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "Quit":
                break
            elif event == "Create":
                cr, pkg = values[0], values[1]
                if cr == '' or pkg == '':
                    sg.popup('One or more fields blank. Please enter all data.')
                    continue
                if not self.mk_proj_dir(cr, pkg):
                    sg.popup('Project(s) already exist at location.')
                    continue

                db.insert_pkg({'name': pkg, 'CR': cr, 'created':datetime.datetime.now().isoformat()})

                self.window.close()

                proj_win = ProjWin(cr, pkg, new=True)
                proj_win.spawn()
            # elif datetime.datetime.now() - self.time > 10:
            #     pass
            elif event == "Back":
                self.window.close()

        self.window.close()

# Open Task Window


class OpenProjWin:

    def __init__(self):

        self.crs = []
        self.packages = []
        self.competion_status = []

        self.load_CRs()
        self.get_stats()

        l_col = [
            [sg.Text('CR Number: '), sg.Combo(self.crs, size=(
                12, 1), key='_CR_COMBO_', change_submits=True, enable_events=True)],
            [sg.Text('Completion Status:'), sg.Combo(COMPLETION_STATUS, size=(12,1), key='_CS_COMBO_', change_submits=True, enable_events=True)],
            [sg.Text('Disposition:'), sg.Combo(DISPOSITION, size=(12,1), key='_DISP_COMBO_', change_submits=True, enable_events=True)],
            [sg.Text('PKG Search: '), sg.InputText('', key='_PKG_NAME_', size=(15, 1),
                                                   enable_events=True, change_submits=True)],
            [sg.Frame('Packages/Tasks', layout=[
                [sg.Listbox(
                    self.packages, key="_PKG_LB_", size=(30, 10))],
            ])]
        ]

        r_col= [
            [sg.Frame('Stats:',layout=[[sg.Text(f'Packages: {self.stats.get("total")}')],[sg.HorizontalSeparator()],[sg.Text(f'New: {self.stats.get("new")}')],[sg.Text(f'In-Progress: {self.stats.get("in_prog")}')],[sg.Text(f'Completed: {self.stats.get("complete")}')],
                                       [sg.Text(f'Rework: {self.stats.get("rework")}')],[sg.HorizontalSeparator()],[sg.Text(f'Passed: {self.stats.get("passed")}')], [sg.Text(f'Failed: {self.stats.get("failed")}')], [sg.Text(f'Unknown: {self.stats.get("unknown")}')]])
                ],
        ]

        self.layout = [
            [sg.Column(l_col), sg.Column(r_col)],
            [sg.Button("Open", key='_OPEN_PROJ_', bind_return_key=True), sg.Button("Back"), sg.Button('Migrate Pkgs',key='_MIGRATE_')]
        ]

        self.window = sg.Window(
            title="ProjManager V1", layout=self.layout, margins=(5, 5), finalize=True)

    def load_CRs(self):
        self.crs = []
        for dir in os.listdir(PM_DIR):
            if os.path.isdir(PM_DIR+dir):
                self.crs.append(dir)

    def get_packages(self, cr):
        self.packages = []
        for dir in os.listdir(PM_DIR+cr):
            if os.path.isdir(PM_DIR+cr+'/'+dir):
                self.packages.append(dir)

    def get_stats(self):
        self.stats = {}
        total = len(db.db.all())
        complete = len(db.db.search(db.Pkg.PROJ_STATUS == 'COMPLETE'))
        in_prog = len(db.db.search(db.Pkg.PROJ_STATUS == 'IN-PROGRESS'))
        rework = len(db.db.search(db.Pkg.PROJ_STATUS == 'REWORK'))
        new = len(db.db.search(db.Pkg.PROJ_STATUS == 'NEW'))
        failed = len(db.db.search(db.Pkg.PROJ_DISPOSITION == 'FAIL'))
        passed = len(db.db.search(db.Pkg.PROJ_DISPOSITION == 'PASS'))
        unknown = len(db.db.search(db.Pkg.PROJ_DISPOSITION == 'UNKNOWN'))
        self.stats.update({'total':total, 'complete':complete, 'in_prog':in_prog,'rework':rework,'new':new, 'failed':failed, 'passed':passed, 'unknown':unknown})
            
    def migrate_all(self):
        all_pkgs = {}
        all_crs = []
        self.load_CRs()
        
        for cr in self.crs:
            self.get_packages(cr)
            all_pkgs[cr] = self.packages

        new_win = NewProjWin()
        
        print('Starting migration.')
        new_win.migrate_setup_pkg(all_pkgs)
        print('Migration Complete.')

    def spawn(self):
        self.packages = db.get_pkg_names() # load all packages with newest first
        self.packages.reverse()
        self.window['_PKG_LB_'].update(values=self.packages)
        self.window.refresh()
        
        while True:
            event, values = self.window.read()
            print(event)

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "Quit":
                break
            elif event == '_CR_COMBO_':
                self.get_packages(values["_CR_COMBO_"])
                self.window['_PKG_LB_'].update(values=self.packages)
                self.window.refresh()
            elif event == '_CS_COMBO_':
                self.packages = db.get_pkg_names_by_CS(values['_CS_COMBO_'])
                self.window['_PKG_LB_'].update(values=self.packages)
                self.window.refresh()
            elif event == '_DISP_COMBO_':
                self.packages = db.get_pkg_names_by_DSP(values['_DISP_COMBO_'])
                self.window['_PKG_LB_'].update(values=self.packages)
                self.window.refresh()

            elif event == '_PKG_NAME_':
                self.packages = []
                names = db.get_pkg_names()
                for name in names:
                    if values['_PKG_NAME_'].upper() in name:
                        self.packages.append(name)
                print(names)
                self.window['_PKG_LB_'].update(values=self.packages)
                self.window.refresh()
            elif event == '_MIGRATE_':
                self.migrate_all()
            elif event == "_OPEN_PROJ_":
                cr = values["_CR_COMBO_"]
                pkg = values["_PKG_LB_"][0]

                if pkg == '':
                    sg.popup('Please select a Package.')
                    continue

                elif cr == '':
                    pkg_data = db.get_pkg(pkg)[0]
                    cr = pkg_data.get('CR')

                self.window.close()
                proj_win = ProjWin(cr, pkg)
                proj_win.spawn()
            elif event=="Back":
                self.window.close()

        self.window.close()


# Start Win.

class StartWin:

    def __init__(self):

        start_layout = [
            [sg.Button("New Task", key='_NEW_TASK_', size=(50, 1))],
            [sg.Button("Open Task", key='_OPEN_TASK_', size=(50, 1))],
            [sg.Button("Quit", size=(50, 1))]]

        self.layout = [
            [sg.Frame('Project Manager V1', layout=start_layout, pad=(25, 25))]]
        self.window = sg.Window(title="ProjManager V1",
                                layout=self.layout, margins=(5, 5))

    def spawn(self):
        while True:
            event, values = self.window.read()
            print(event)

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "Quit":
                break
            elif event == "_NEW_TASK_":
                self.window.hide()
                new_proj_win = NewProjWin()
                new_proj_win.spawn()
                self.window.un_hide()
                continue

            elif event == '_OPEN_TASK_':
                self.window.hide()
                open_proj_win = OpenProjWin()
                open_proj_win.spawn()
                self.window.un_hide()

        self.window.close()


db = Db(PM_DB_FILE)
start = StartWin()
start.spawn()
