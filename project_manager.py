import pathlib
import PySimpleGUI as sg
import subprocess
from pathlib import Path
import os
import yaml
import shutil
import datetime
import tinydb as tdb

PM_DIR = 'C:/Users/e433679/Documents/Project_Manager/'
#PM_DIR = '/home/hnobles12/Documents/Project_Manager/'
PM_DB_FILE = PM_DIR+'pm_db.json'

PM_PATH = Path('/c/Users/e433679/Documents/Project_Manager/')

COMPLETION_STATUS = ['NEW', 'IN-PROGRESS', 'COMPLETE', 'REWORK']
DISPOSITION = ['PASS', 'FAIL', 'UNKNOWN']
sg.theme('Topanga')


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

    def __init__(self, cr, pkg):
        self.cr = cr
        self.pkg = pkg

        self.width = 1000
        self.height = 250

        self.proj_path = PM_DIR + f"{self.cr}/{self.pkg}/"

        self.get_proj_files()
        self.load_proj_data()

        print('proj_data: ', self.proj_data)

        l_col_layout = [[sg.Frame("Documentation:", layout=[[sg.Listbox(values=self.doc_files, size=(125, 10), key="_DOC_LB_")],
                                                            [sg.Button('Open', key='_OPEN_DOC_'), sg.FilesBrowse('Add Files', enable_events=True, key='_ADD_DOC_FILES_', target='_ADD_DOC_FILES_',initial_folder=self.proj_path+'/Documentation'), sg.Button('', key="__DOC_FILES_", visible=False)]])],

                        [sg.Frame('Analysis:', layout=[[sg.Listbox(values=self.analysis_files, size=(125, 10), key="_ANAL_LB_")],
                                                       [sg.Button('Open', key='_OPEN_ANALYSIS_'), sg.FilesBrowse('Add Files', enable_events=True, target="_ADD_ANAL_FILES_", key='_ADD_ANAL_FILES_',initial_folder=self.proj_path+'/Analysis')]])],

                        [sg.Frame('Results:', layout=[[sg.Listbox(values=self.results_files, size=(125, 10), key="_RES_LB_")],
                                                      [sg.Button('Open', key='_OPEN_RESULTS_'), sg.FilesBrowse('Add Files', enable_events=True, target="_ADD_RES_FILES_", key='_ADD_RES_FILES_',initial_folder=self.proj_path+'/Results')]])],
                        ]

        r_col_layout = [[sg.Frame('Work Status:', layout=[
            [sg.Text("Task Status: ", size=(10, 1)), sg.Combo(COMPLETION_STATUS,
                                                              default_value=self.proj_data.get('PROJ_STATUS') or "NEW", key="_STAT_COMBO_", size=(10, 1))],
            [sg.Text("Disposition: ", size=(10, 1)), sg.Combo(DISPOSITION, default_value=self.proj_data.get(
                'PROJ_DISPOSITION'), key="_DISP_COMBO_", size=(10, 1))],
        ], border_width=1)],
            [sg.Frame("Notes:", layout=[[sg.Multiline(default_text=self.proj_data.get(
                'PROJ_NOTES'), size=(75, 15), key='_PROJ_NOTES_')]])],
            [sg.Frame("TODOs:", layout=[[sg.Multiline(default_text=self.proj_data.get(
                'PROJ_TODOS'), size=(75, 15), key='_PROJ_TODOS_')]])],
            [sg.Button("Save", key="_UPDATE_STATUS_", bind_return_key=True), sg.Button(
                'Refresh', key='_REFRESH_'), sg.Button('Close', key="Quit")],
        ]

        top_row_details_frame = sg.Frame("Task Details:",
                                         layout=[[sg.Text('CR:', size=(10, 1)), sg.InputText(self.cr, disabled=True, size=(28, 1)), ],
                                                 [sg.Text(f'PKG/TASK:', size=(10, 1)), sg.InputText(self.pkg, disabled=True, size=(
                                                     28, 1)), ],
                                                 [sg.Text(f"IO:", size=(10, 1)), sg.InputText(key='_PROJ_IO_', default_text=self.proj_data.get(
                                                     "PROJ_IO"), size=(28, 1))]])

        top_row_model_details_frame = sg.Frame('TVE Details:', layout=[
            [sg.Text('TVE: ', size=(15, 1)), sg.Multiline(
                self.proj_data.get('PROJ_TVE'), autoscroll=True, key='_PROJ_TVE_', size=(40, 5))],
        ])
        top_row_model_details_frame2 = sg.Frame('Model Details:', layout=[
            [sg.Column(layout=[[sg.Text('Models: ', size=(15, 1))],[sg.Button('Open', key='_OPEN_MODEL_'), sg.FilesBrowse('Add Files',enable_events=True, target='_ADD_MODEL_FILES_', key='_ADD_MODEL_FILES_', initial_folder=self.proj_path+'/Models')]]), sg.Listbox(self.models_files, key='_MODELS_LB_', size=(20, 4)), ],
        ])

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
            if os.path.isfile(os.path.join(self.proj_path, f"Analysis/{file}")):
                analysis_files.append(file)
        for file in os.listdir(self.proj_path+"Results"):
            if os.path.isfile(os.path.join(self.proj_path, f"Results/{file}")):
                results_files.append(file)
        for file in os.listdir(self.proj_path+"Models"):
            if os.path.isfile(os.path.join(self.proj_path, f"Models/{file}")):
                models_files.append(file)

        self.doc_files = doc_files
        self.analysis_files = analysis_files
        self.results_files = results_files
        self.models_files = models_files

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
                for i in self.window['_DOC_LB_'].get_indexes():
                    os.startfile(self.proj_path +
                                 'Documentation/'+self.doc_files[i])
            elif event == '_OPEN_ANALYSIS_':
                for i in self.window['_ANAL_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Analysis/' +
                                 self.analysis_files[i])
            elif event == '_OPEN_RESULTS_':
                for i in self.window['_RES_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Results/' +
                                 self.results_files[i])
            elif event == '_OPEN_MODEL_':
                for i in self.window['_MODELS_LB_'].get_indexes():
                    os.startfile(self.proj_path+'Models/' +
                                 self.models_files[i])
            elif event == '_UPDATE_STATUS_':
                self.proj_data['PROJ_STATUS'] = values['_STAT_COMBO_']
                self.proj_data['PROJ_DISPOSITION'] = values['_DISP_COMBO_']
                self.proj_data['PROJ_NOTES'] = values["_PROJ_NOTES_"]
                self.proj_data['PROJ_TODOS'] = values['_PROJ_TODOS_']
                self.proj_data['PROJ_IO'] = values['_PROJ_IO_']
                self.proj_data['PROJ_TVE'] = values['_PROJ_TVE_']
                self.save_project_data()
                self.get_proj_files()
                self.window['_DOC_LB_'].update(values=self.doc_files)
                self.window['_ANAL_LB_'].update(values=self.analysis_files)
                self.window['_RES_LB_'].update(values=self.results_files)
                self.window['_MODELS_LB_'].update(values=self.models_files)
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

        self.window.close()


# New Project Window
class NewProjWin:

    def __init__(self):
        self.layout = [
            [sg.Text('New Project')],
            [sg.Text("CR/Proj Number: ", size=(20, 1)), sg.InputText()],
            [sg.Text("Pkg. Number (Name): ", size=(20, 1)), sg.InputText()],
            [sg.Button("Create", bind_return_key=True)]


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

                db.insert_pkg({'name': pkg, 'CR': cr})

                self.window.close()

                proj_win = ProjWin(cr, pkg)
                proj_win.spawn()
            elif datetime.datetime.now() - self.time > 10:
                pass

        self.window.close()

# Open Task Window


class OpenProjWin:

    def __init__(self):

        self.crs = []
        self.packages = []
        self.competion_status = []

        self.load_CRs()

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

        self.layout = [
            [sg.Column(l_col)],
            [sg.Button("Open", key='_OPEN_PROJ_', bind_return_key=True), sg.Button('Migrate Pkgs',key='_MIGRATE_')]
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
                    if values['_PKG_NAME_'] in name:
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
