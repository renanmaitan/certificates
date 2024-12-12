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
import sys
import os
import platform
from typing import List, Union
import unicodedata

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from core.Searcher import Searcher
from core.SearcherController import SearcherController
from core.WorkerThread import Worker
from modules import *
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
        
        self.ui.generate_word.clicked.connect(self.start_search)
        
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
        
    def _start_search(self):
        pessoas = []
        for pessoa in self.list:
            pessoas.append((pessoa["cpf"].replace(".","").replace("-",""), pessoa["birth"].replace("/","")))
        if len(pessoas)>0:
            sc = SearcherController(2,False)
            qtt = SearcherController.qtt_tests(pessoas)
            btn = self.show_message_from_thread(
                f"{qtt} nomes",
                f"{qtt} nomes serão buscados. Tem certeza de que deseja continuar?",
                buttons=[QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No],
                defaultButton=QMessageBox.StandardButton.Yes
            )
            self.status_callback(f"Nomes buscados 0/{qtt}", 5)
            percentage = 80/qtt
            def result(result):
                self.buscados += len(result)
                self.status_callback(f"Nomes buscados: {self.buscados}/{qtt}", len(result)*percentage)
                print("Resultado: ", result)
            if btn == "&Yes":
                sc.search_list(pessoas, lambda x: print("Subtitle: ", x), result)
        
    def format_tel_input(self):
        text = self.ui.tel_input.text()
        text = ''.join(c for c in text if c.isdigit())
        if len(text) > 11:
            text=text[:11]
        if len(text) > 2:
            text = f"({text[:2]}) " + text[2:]
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
        if word == "da" or word =="do" or word == "dos" or word =="das":
            return word
        return str.capitalize(word)
        
    def capitalize(self, inv=False):
        lines = self.ui.mult_input.toPlainText().splitlines()
        new_values = []
        for i, line in enumerate(lines):
            splitted = line.split()
            for j, value in enumerate(splitted):
                if not value.isalpha():
                    break
                value = self.capitalize_word(value)
                splitted[j] = value
            new_values.append(" ".join(splitted))
        self.ui.mult_input.setPlainText("\n".join(new_values))
        
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
            self.list.append(
                {
                    "birth": self.ui.birth_input.text(),
                    "cpf": self.ui.cpf_input.text(),
                    "tel": self.ui.tel_input.text() if self.ui.tel_input else "",
                    "email": self.ui.email_input.text() if self.ui.email_input else ""  
                }
            )
            print(self.list)
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
        to_add = []
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
            to_add.append(
                {
                    "birth": values[0],
                    "cpf": values[1],
                    "tel": values[2],
                    "email": values[3]
                }
            )
        self.list.extend(to_add)
        self.ui.mult_input.setPlainText("")
        print(self.list)

    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            self.ui.stackedWidget.setCurrentWidget(self.ui.home)
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
