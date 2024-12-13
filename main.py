# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

from collections import deque
import json
from pathlib import Path
import sys
import os
import platform
from typing import Dict, List, Union
import unicodedata

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from core.CustomDelegate import CustomItemDelegate
from core.Searcher import Searcher
from core.SearcherController import SearcherController
from core.WorkerThread import Worker
from modules import *
from utils import docx_util, pptx_util
from widgets import *
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.list = []

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "PyDracula - Modern GUI"
        description = "PyDracula APP - Theme with colors based on Dracula for Python."
        # APPLY TEXTS
        self.setWindowTitle(title)
        self.ui.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        self.ui.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # LEFT MENUS
        self.ui.btn_home.clicked.connect(self.buttonClick)
        self.ui.list_btn.clicked.connect(self.buttonClick)

        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        self.ui.stackedWidget.setCurrentWidget(self.ui.home)
        self.ui.btn_home.setStyleSheet(UIFunctions.selectMenu(self.ui.btn_home.styleSheet()))
        
        self.ui.add_one.clicked.connect(self.add_one)
        self.ui.add_mult.clicked.connect(self.add_mult)
        self.ui.tiny_btn.clicked.connect(self.to_lower)

        # Aplica a validação ao QLineEdit
        self.ui.cpf_input.textChanged.connect(self.format_cpf_input)
        self.ui.birth_input.textChanged.connect(self.format_birth_input)
        self.ui.tel_input.textChanged.connect(self.format_tel_input)
        
        self.ui.find_btn.clicked.connect(self.start_search)
        
        self.threadpool_home = QThreadPool()
        self.progress_queue_home = deque()
        self.timer_home = QTimer(self)
        self.timer_home.timeout.connect(self.process_progress_queue_home)
        self.timer_home.start(100)
        self.status_percentage_home = 0
        self.ui.progressBar_home.setValue(0)
        
        self.threadpool = QThreadPool()
        self.progress_queue = deque()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_progress_queue)
        self.timer.start(100)
        self.status_percentage = 0
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setMaximumHeight(0)
        self.ui.progressBar.setMaximumWidth(0)
        self.buscados = 0
        
        self.start_table()
        self.start_configs()
        
        self.ui.capital_btn_list.clicked.connect(self.capitalize_list)
        self.ui.tiny_btn_list.clicked.connect(self.to_lower_list)
        self.ui.del_all_list.clicked.connect(self.del_all_list)
        self.ui.del_list.clicked.connect(self.del_selected_list)
        
        self.ui.save_model_name.clicked.connect(self.save_name_model)
        self.ui.choose_pptx.clicked.connect(self.choose_pptx)
        self.ui.choose_word.clicked.connect(self.choose_word)
        
        self.ui.open_name_list.clicked.connect(self.buttonClick)
        
        self.ui.cfg_btn.clicked.connect(self.buttonClick)
            
        self.documents_folder = Path.home() / "Documents"
        
        self.ui.generate_word.clicked.connect(self.generate_word)
        self.word_folder = self.documents_folder / "PyCertificate" / "Word"
        os.makedirs(self.word_folder, exist_ok=True)
        self.ui.open_word_folder.clicked.connect(self.open_word_folder)
        
        self.ui.generate_ppt.clicked.connect(self.generate_pptx)
        self.pptx_folder = self.documents_folder / "PyCertificate" / "Powerpoint"
        os.makedirs(self.pptx_folder, exist_ok=True)
        self.ui.open_ppt_folder.clicked.connect(self.open_pptx_folder)
        
        self.ui.save_parallel.clicked.connect(self.save_parallel)
        
        self.ui.generate_pdf.stateChanged.connect(self.save_generate_pdf)
    
    def save_generate_pdf(self, state):
        cfgs = self.get_cfgs()
        cfgs["generate_pdf"] = bool(state)
        self.save_configs(cfgs)
    
    def save_parallel(self):
        cfgs = self.get_cfgs()
        cfgs["parallel"] = int(self.ui.parallel_pages.text())
        self.save_configs(cfgs)
        
    def open_pptx_folder(self):
        os.startfile(self.pptx_folder)
        
    def open_word_folder(self):
        os.startfile(self.word_folder)
        
    def generate_word(self):
        self.ui.progressBar_home.setValue(0)
        self.ui.generate_word.setEnabled(False)
        worker = Worker(self._generate_word, self.status_callback_home)
        worker.signals.error.connect(self.handle_error_home)
        worker.signals.finished.connect(lambda: self.ui.generate_word.setEnabled(True))
        self.threadpool.start(worker)

    def _generate_word(self, callback):
        percentage = 99/len(self.list)
        for i, person in enumerate(self.list):
            callback(f'Gerando word para: {person["name"]}', 0)
            model_path = self.ui.word_model.text()
            output_path = self.word_folder / (self.ui.name_model.text().replace("{nome}", person["name"]) + ".docx")
            docx_util.replace_placeholders(model_path, person["name"], person["cpf"], output_path)
            callback(f'Gerado word para: {person["name"]}', (percentage/2))
            if self.ui.generate_pdf.isChecked():
                callback(f'Gerando pdf para: {person["name"]}', 0)
                docx_util.save_as_pdf(str(output_path),str(output_path.with_suffix(".pdf")))
                callback(f'Gerado pdf para: {person["name"]}', (percentage/2))
            else:
                callback(f'Gerado word para: {person["name"]}', (percentage/2)) 
        callback("Finalizado", 100)
    
    def generate_pptx(self):
        self.ui.progressBar_home.setValue(0)
        self.ui.generate_ppt.setEnabled(False)
        worker = Worker(self._generate_pptx, self.status_callback_home)
        worker.signals.error.connect(self.handle_error_home)
        worker.signals.finished.connect(lambda: self.ui.generate_ppt.setEnabled(True))
        self.threadpool.start(worker)
            
    def _generate_pptx(self, callback):
        percentage = 99/len(self.list)
        for i, person in enumerate(self.list):
            callback(f'Gerando Powerpoint para: {person["name"]}', 0)
            model_path = self.ui.powerpoint_model.text()
            output_path = self.pptx_folder / (self.ui.name_model.text().replace("{nome}", person["name"]) + ".pptx")
            pptx_util.replace_placeholders(model_path, person["name"], person["cpf"], output_path)
            callback(f'Gerado Powerpoint para: {person["name"]}', (percentage/2))
            if self.ui.generate_pdf.isChecked():
                callback(f'Gerando pdf para: {person["name"]}', 0)
                pptx_util.save_as_pdf(str(output_path),str(output_path.with_suffix(".pdf")))
                callback(f'Gerado pdf para: {person["name"]}', (percentage/2))
            else:
                callback(f'Gerado Powerpoint para: {person["name"]}', (percentage/2))
        callback("Finalizado", 100)
        
    def start_configs(self):
        cfgs = self.get_cfgs()
        self.ui.name_model.setText(cfgs["name_model"])
        self.ui.word_model.setText(cfgs["word_model"])
        self.ui.powerpoint_model.setText(cfgs["pptx_model"])
        self.ui.parallel_pages.setText(str(cfgs["parallel"]))
        self.ui.generate_pdf.setChecked(cfgs["generate_pdf"])
    
    def get_cfgs(self):
        with open("config/general.json", "r") as file:
            return json.load(file)
    
    def save_configs(self, cfg):
        with open("config/general.json", "w") as file:
            json.dump(cfg, file, indent=4)
            
    def save_name_model(self):
        cfgs = self.get_cfgs()
        cfgs["name_model"] = self.ui.name_model.text()
        self.save_configs(cfgs)
    
    def choose_word(self):
        file = self.choose_file()
        if file:
            cfgs = self.get_cfgs()
            self.ui.word_model.setText(file)
            cfgs["word_model"] = file
            self.save_configs(cfgs)
        
    def choose_pptx(self):
        file = self.choose_file()
        if file:
            cfgs = self.get_cfgs()
            self.ui.powerpoint_model.setText(file)
            cfgs["pptx_model"] = file
            self.save_configs(cfgs)
        
    def choose_file(self) -> str:
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            return file_path
        else:
            return ""
        
    def detect_ctrl_c(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selecteds()
        else:
            super(QTableWidget, self.ui.list_table).keyPressEvent(event)

    def copy_selecteds(self):
        ranges = self.ui.list_table.selectedRanges()
        if not ranges:
            return
        tabela_texto = ""
        for range_ in ranges:
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                linha = []
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    item = self.ui.list_table.item(row, col)
                    linha.append(item.text() if item else "")
                tabela_texto += "\t".join(linha) + "\n"

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(tabela_texto)
        
    def del_all_list(self):
        btn = QMessageBox.warning(
            self,
            "Deletar Tudo",
            "Essa ação deletará todas as linhas\nTem certeza de que deseja continuar?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.Yes
        )
        if btn == QMessageBox.StandardButton.Yes:
            self.ui.list_table.setRowCount(0)
            self.list = []
    
    def del_selected_list(self):
        table = self.ui.list_table
        selecteds = table.selectedItems()
        if len(selecteds)>1:
            btn = QMessageBox.warning(
                self,
                "Mais de uma linha está selecionada",
                "Clicar em 'Yes' deletará todas as selecionadas. Tem certeza de que deseja continuar?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.Yes
            )
            if btn == QMessageBox.StandardButton.No:
                return
        for item in selecteds:
            table.removeRow(item.row())
        self.on_table_change()
        
    def start_table(self):
        table = self.ui.list_table
        table.setItemDelegate(CustomItemDelegate())
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.itemChanged.connect(self.on_table_change)
        table.setSelectionMode(QTableWidget.SelectionMode.ContiguousSelection)
        table.keyPressEvent = self.detect_ctrl_c
        
    def on_table_change(self, item=None):
        table = self.ui.list_table
        self.list = []
        cols = ["name", "birth", "cpf", "tel", "email"]
        for row in range(table.rowCount()):
            line = {}
            for col in range(table.columnCount()):
                value = table.item(row,col).text()
                line[cols[col]] = value
            self.list.append(line)
            
    def add_item(self, obj: dict):
        table = self.ui.list_table
        table.blockSignals(True)
        table.setRowCount(table.rowCount()+1)
        cols = ["name", "birth", "cpf", "tel", "email"]
        for col in range(table.columnCount()):
            table.setItem(table.rowCount()-1,col,QTableWidgetItem(obj[cols[col]]))
        table.blockSignals(False)

    def handle_error_home(self, error):
        self.progress_queue_home = deque()
        self.progress_queue_home.append(100)
        self.ui.progressBar_home.setValue(100)
        
        self.ui.status_home.setWordWrap(True)
        self.ui.status_home.setFixedWidth(300)

        if "Permission denied" in error: 
            file_name = error.split("\\")[-1]
            error+=f' Check if there is a file named "{file_name}" open. Close it!'
        self.ui.status_home.setText(f"<div style='text-align: center; color: lightcoral;'>Terminated with the following error:<br>{error}</div>") 

    def handle_error(self, error):
        self.progress_queue = deque()
        self.progress_queue.append(100)
        self.ui.progressBar.setValue(100)
        
        self.ui.status.setWordWrap(True)
        self.ui.status.setFixedWidth(300)

        if "Permission denied" in error: 
            file_name = error.split("\\")[-1]
            error+=f' Check if there is a file named "{file_name}" open. Close it!'
        self.ui.status.setText(f"<div style='text-align: center; color: lightcoral;'>Terminated with the following error:<br>{error}</div>") 
        
    def finished(self):
        ...
        
    def start_search(self):
        self.ui.progressBar.setMaximumHeight(16777215)
        self.ui.progressBar.setMaximumWidth(16777215)
        self.progress_queue = deque()
        self.status_percentage = 0
        self.ui.progressBar.setValue(0)
        worker = Worker(self._start_search)
        worker.signals.error.connect(self.handle_error)
        # worker.signals.finished.connect(self.finished)
        self.threadpool.start(worker)
        
    @Slot(str)
    def update_item(self, new_item_json: str):
        new_item = json.loads(new_item_json)
        table = self.ui.list_table
        cols = ["name", "birth", "cpf"]
        for row in range(table.rowCount()):
            if table.item(row,2).text().replace(".","").replace("-","") == new_item["old_cpf"].replace(".","").replace("-",""):
                for col in range(table.columnCount()-2):
                    table.setItem(row,col,QTableWidgetItem(new_item[cols[col]]))
        self.on_table_change()
        
    def _start_search(self):
        pessoas = []
        self.buscados = 0
        for pessoa in self.list:
            pessoas.append((pessoa["cpf"].replace(".","").replace("-",""), pessoa["birth"].replace("/","")))
        if len(pessoas)>0:
            sc = SearcherController(int(self.ui.parallel_pages.text()),False)
            qtt = SearcherController.qtt_tests(pessoas)
            btn = self.show_message_from_thread(
                f"{qtt} nomes",
                f"{qtt} nomes serão buscados. Tem certeza de que deseja continuar?",
                buttons=[QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No],
                defaultButton=QMessageBox.StandardButton.Yes
            )
            self.status_callback(f"Nomes buscados 0/{qtt}", 0)
            percentage = 100/qtt
            def result(result: List[Dict[str, str]]):
                self.buscados += len(result)
                self.status_callback(f"Nomes buscados: {self.buscados}/{qtt}", len(result)*percentage if self.buscados!=qtt else 100)
                for value in result:
                    value_json = json.dumps(value)
                    QMetaObject.invokeMethod(self, "update_item", Qt.ConnectionType.QueuedConnection, Q_ARG(str, value_json))
            if btn == "&Yes":
                sc.search_list(pessoas, lambda x: print("Subtitle: ", x), result)
        
    def format_tel_input(self):
        text = self.ui.tel_input.text()
        text = ''.join(c for c in text if c.isdigit())
        if len(text) > 11:
            text=text[:11]
        if len(text) > 2:
            text = f"{text[:2]} " + text[2:]
        if len(text) > 10:
            text = text[:10] + '-' + text[10:]
        self.ui.tel_input.setText(text)
        
    def format_birth_input(self):
        text = self.ui.birth_input.text()
        text = ''.join(c for c in text if c.isdigit() or str.lower(c) == "x")
        if len(text) > 8:
            text=text[:8]
        if len(text) > 2:
            text = text[:2] + '/' + text[2:]
        if len(text) > 5:
            text = text[:5] + '/' + text[5:]
        self.ui.birth_input.setText(text)
        
    def format_cpf_input(self):
        text = self.ui.cpf_input.text()
        text = ''.join(c for c in text if c.isdigit() or c.upper() == 'X')
        if len(text) > 11:
            text=text[:11]
        if len(text) > 3:
            text = text[:3] + '.' + text[3:]
        if len(text) > 7:
            text = text[:7] + '.' + text[7:]
        if len(text) > 11:
            text = text[:11] + '-' + text[11:]
        self.ui.cpf_input.setText(text)
        
    def normalize_name(self, name):
        nfkd_form = unicodedata.normalize('NFKD', name)
        return str.lower(''.join([c for c in nfkd_form if not unicodedata.combining(c)]))
        
    def capitalize_word(self, word):
        word = str.lower(word)
        if word == "da" or word =="do" or word == "dos" or word =="das" or word == "de" or word == "des":
            return word
        return str.capitalize(word)
        
    def capitalize_list(self):
        table = self.ui.list_table
        for row in range(table.rowCount()):
            new_word = []
            for word in table.item(row,0).text().split():
                new_word.append(self.capitalize_word(word))
            table.setItem(row,0,QTableWidgetItem(" ".join(new_word)))
            
    def to_lower_list(self):
        table = self.ui.list_table
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                table.setItem(row,col,QTableWidgetItem(str.lower(table.item(row,col).text())))
        
    def to_lower(self):
        self.ui.mult_input.setPlainText(str.lower(self.ui.mult_input.toPlainText()))
    
    def invalid_cpf(self, cpf):
        only_digits = ''.join(filter(str.isdigit, cpf))
        return not "x" in str.lower(cpf) and not Searcher.valida_cpf(cpf) and len(only_digits)==11
    
    def add_one(self):
        if (self.ui.birth_input and self.ui.cpf_input) and (self.ui.cpf_input.text() and self.ui.birth_input.text()):
            if self.invalid_cpf(self.ui.cpf_input.text()):
                QMessageBox.warning(
                    self,
                    "CPF inválido!",
                    f"O CPF {self.ui.cpf_input.text()} é inválido!",
                    defaultButton=QMessageBox.StandardButton.Ok
                )
                return
            new_obj = {
                    "name": "",
                    "birth": self.ui.birth_input.text(),
                    "cpf": self.ui.cpf_input.text(),
                    "tel": self.ui.tel_input.text() if self.ui.tel_input else "",
                    "email": self.ui.email_input.text() if self.ui.email_input else ""  
                }
            self.list.append(new_obj)
            self.add_item(new_obj)
            inputs = [self.ui.birth_input, self.ui.cpf_input, self.ui.tel_input, self.ui.email_input]
            for input in inputs:
                input.setText("")
            return
        QMessageBox.warning(
            self,
            "Valores vazios!",
            "Obrigatoriamente preencha a Data de nascimento e CPF",
            defaultButton=QMessageBox.StandardButton.Ok
        )
        
    def add_mult(self):
        lines = self.ui.mult_input.toPlainText().splitlines()
        for i, line in enumerate(lines):
            values = []
            splitted = line.split()
            values.append(splitted[0])
            values.append(splitted[1])
            tel = []
            if len(splitted) >= 4:
                for value in splitted[2:-1]:
                    tel.append(value)
                values.append(" ".join(tel))
                values.append(splitted[-1])
                    
            if len(values) != 2 and len(values) != 4:
                QMessageBox.warning(
                    self,
                    "Entrada inválida!",
                    f"""A entrada na linha {i+1} é inválida!
                        Essa linha não contém o tamanho adequado de valores
                        Quantidade de valores: 
                            2 - Data de nascimento e CPF ou 
                            4 - Data de nascimento, CPF, Telefone e Email""",
                    defaultButton=QMessageBox.StandardButton.Ok
                )
                return
            if len(values) == 2: values.append(""); values.append("")
            if self.invalid_cpf(values[1]):
                QMessageBox.warning(
                    self,
                    "CPF inválido!",
                    f"O CPF {values[1]} na linha {i+1} é inválido!",
                    defaultButton=QMessageBox.StandardButton.Ok
                )
                return
            new_obj = {
                    "name": "",
                    "birth": values[0],
                    "cpf": values[1],
                    "tel": values[2],
                    "email": values[3]
                }
            self.list.append(new_obj)
            self.add_item(new_obj)
        self.ui.mult_input.setPlainText("")

    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            self.ui.stackedWidget.setCurrentWidget(self.ui.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btnName == "list_btn":
            self.ui.stackedWidget.setCurrentWidget(self.ui.list_view)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btnName == "open_name_list":
            self.ui.list_btn.click()
            
        if btnName == "cfg_btn":
            self.ui.stackedWidget.setCurrentWidget(self.ui.script_config)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

    def resizeEvent(self, event):
        UIFunctions.resize_grips(self) #type: ignore
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.ui.add_one.click()
            self.ui.add_mult.click()
            self.ui.birth_input.setFocus()

    def mousePressEvent(self, event):
        self.dragPos = QCursor.pos()
        
        # if event.buttons() == Qt.MouseButton.LeftButton:
        #     print('Mouse click: LEFT CLICK')
        # if event.buttons() == Qt.MouseButton.RightButton:
        #     print('Mouse click: RIGHT CLICK')
            
            
    def show_message_from_thread(self, title: str, text: str, buttons: List[Union[int, str]], defaultButton: int) -> str:
        return QMetaObject.invokeMethod(
            self,
            "_show_message_internal",
            Qt.ConnectionType.BlockingQueuedConnection,
            Q_RETURN_ARG(str),
            Q_ARG(str, title),
            Q_ARG(str, text),
            Q_ARG('QVariantList', buttons),
            Q_ARG(int, defaultButton)
        )
        
    @Slot(str, str, 'QVariantList', int, result=str)
    def _show_message_internal(self, title: str, text: str, buttons: List[Union[int, str]], defaultButton: int) -> str:
        message_box = QMessageBox(self)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        started_btns = []
        for btn in buttons:
            if isinstance(btn, int):
                started_btns.append(btn)
            elif isinstance(btn, str):
                started_btns.append(QPushButton(btn))
        for btn in started_btns:
            if isinstance(btn, int):
                message_box.addButton(QMessageBox.StandardButton(btn))
            else:
                message_box.addButton(btn, QMessageBox.ButtonRole.NoRole)
        message_box.setDefaultButton(QMessageBox.StandardButton(defaultButton))
        message_box.exec()
        clicked_button = message_box.clickedButton()
        return clicked_button.text() if clicked_button else ""
        
    @Slot()
    def process_progress_queue_home(self):
        if self.progress_queue_home:
            new_value = self.progress_queue_home.popleft()
            QMetaObject.invokeMethod(self, "animate_progress_home", Qt.ConnectionType.QueuedConnection, Q_ARG(int, new_value))  # type: ignore
        
    def status_callback_home(self, message: str, percentage: float):
        max_lenght = 56
        if len(message) > max_lenght:
            message = message[:max_lenght] + "..."
        self.status_percentage_home += percentage
        self.status_percentage_home = min(max(self.status_percentage_home, 0), 99) if percentage < 100 else 100
        if percentage >= 100:
            self.progress_queue_home = deque()
        self.progress_queue_home.append(int(self.status_percentage_home))
        QMetaObject.invokeMethod(self.ui.status_home, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, message))  # type: ignore
        
    @Slot(int)
    def animate_progress_home(self, new_value):
        self.animation = QPropertyAnimation(self.ui.progressBar_home, b"value")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.ui.progressBar_home.value())
        self.animation.setEndValue(new_value)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
    
    @Slot()
    def process_progress_queue(self):
        if self.progress_queue:
            new_value = self.progress_queue.popleft()
            QMetaObject.invokeMethod(self, "animate_progress", Qt.QueuedConnection, Q_ARG(int, new_value))  # type: ignore
            
    def status_callback(self, message: str, percentage: float):
        max_lenght = 56
        if len(message) > max_lenght:
            message = message[:max_lenght] + "..."
        self.status_percentage += percentage
        self.status_percentage = min(max(self.status_percentage, 0), 99) if percentage < 100 else 100
        if percentage >= 100:
            self.progress_queue = deque()
        self.progress_queue.append(int(self.status_percentage))
        QMetaObject.invokeMethod(self.ui.status, "setText", Qt.QueuedConnection, Q_ARG(str, message))  # type: ignore
        
    @Slot(int)
    def animate_progress(self, new_value):
        self.animation = QPropertyAnimation(self.ui.progressBar, b"value")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.ui.progressBar.value())
        self.animation.setEndValue(new_value)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec())
