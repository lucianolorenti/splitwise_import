import sys
from PyQt5.QtWidgets import QApplication, \
                            QWidget, \
                            QMainWindow, \
                            QVBoxLayout, \
                            QHBoxLayout, \
                            QPushButton, \
			    QLabel, \
                            QLineEdit, \
                            QFormLayout, \
                            QComboBox, \
                             QFileDialog, \
                            QTableView, \
                            QDateTimeEdit, \
                            QMessageBox
from splitwise import Splitwise

from splitwise.expense import Expense
from splitwise.user import ExpenseUser

import json
from simplecrypt import encrypt, decrypt
import webbrowser
from PyQt5.Qt import (QDesktopServices, QUrl, QUrlQuery, QStandardItemModel, QStandardItem, QDate)
from PyQt5.QtGui import (QIntValidator)
from config import config
from PyQt5.QtCore import Qt
from PyQt5.QtWebKitWidgets import QWebView
from pyexcel_ods import get_data
import traceback
def get_keys():
        with open("keys.data", "rb") as text_file:
            data = decrypt( "traselcristalyagrislanochecesa",text_file.read())                  .decode("utf-8")
            return json.loads(str(data))
        return null
def get_splitwise():
    keys = get_keys()
    sObj = Splitwise(keys["consumer_key"],keys["consumer_secret"])
    if config.is_authorized():
        sObj.setAccessToken(config.access_token())
    return sObj
class AuthorizeAppWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.sObj = get_splitwise()
        self.authorize_url, self.secret = self.sObj.getAuthorizeURL()
        self.init_gui()
        self.web_view = QWebView()
    def url_changed(self, url):
        if QUrlQuery(url).hasQueryItem("oauth_verifier"):
            self.app_authorized(QUrlQuery(url))
    def app_authorized(self, query):
        self.web_view.close()
        oauth_token = query.queryItemValue("oauth_token")
        oauth_verifier = query.queryItemValue("oauth_verifier")
        access_token = self.sObj.getAccessToken(oauth_token,self.secret,oauth_verifier)
        config.set_access_token(access_token)
        self.label_state.setText("Authorized")
    def get_authorize_url(self):
        self.web_view.load(QUrl(self.authorize_url))
        self.web_view.urlChanged.connect(self.url_changed)
        self.web_view.show()
    def init_gui(self):
        authorize_button = QPushButton("Authorize")
        url_link         = QLabel( self.authorize_url)
        self.label_state  = QLabel("")
        vbox = QVBoxLayout()

        vbox.addWidget(authorize_button)
        vbox.addWidget(url_link)
        vbox.addWidget(self.label_state)
        self.setLayout(vbox)
        authorize_button.clicked.connect(self.get_authorize_url)
        self.show()
class ImportWidget(QWidget):
    def __init__(self):
        super().__init__()
        self .init_gui()
    def read_sheet(self, file_data,sheet_name):
        self.model.clear()
        for row in file_data[sheet_name]:
            items = [QStandardItem(str(field)) for field in row ]
            self.model.appendRow(items)
    def open_filename(self):
        filename = QFileDialog.getOpenFileName(self,self.tr("Abrir archivo"),
                                                 "/home/luciano",
                                                self.tr("Hojas de Cálculo (*.ods)"))
        if filename[0] != "":
            self._enable_widgets(True)
            self.file_data = get_data(filename[0])
            for key in self.file_data.keys():
                self.cmb_ods_sheets.addItem(key)
            self.read_sheet(self.file_data, list(self.file_data.keys())[0])

    def import_expenses(self):
        try:
            row = int(self.le_initial_row.text()) -1
            description_col = int(self.le_description_col.text()) -1
            date_col        = int(self.le_date_col.text()) -1
            default_date    = self.default_date.date()
            date_format     = self.le_date_format.text()
            percent = 1.0/len(list(self.current_group.getMembers()))
            while self.model.item(row) is not None:
                print("Row ", row)

                expense = Expense()
                expense.setDescription(self.model.item(row,description_col).text())
                print("Expense: ", expense.getDescription())
                date = QDate.fromString(self.model.item(row,date_col).text(), date_format)
                if not date.isValid():
                    date = default_date
                expense.setDate(date.toString(Qt.ISODate))
                print("Date: ", expense.getDate())

                cost = 0
                users = []
                for member in self.current_group.getMembers():
                    print("Processing member ", member.getFirstName())
                    member_column  = int(self.member_widget_map[member.getId()].text()) -1
                    paid = 0
                    try:
                        paid = float(self.model.item(row,member_column).text())
                        print("Expense: ", self.model.item(row,member_column).text())
                    except:
                        pass
                    cost = cost + paid
                    expense_user = ExpenseUser()
                    expense_user.setId(member.getId())
                    expense_user.setPaidShare(str(paid))
                    users.append(expense_user)
                for expense_user in users:
                    expense_user.setOwedShare( str(cost*percent))
                if cost ==0 :
                    raise Exception(self.tr('No se ha introducido monto para el gasto'))
                expense.setCost(str(cost))
                expense.setUsers(users)
                expense.setGroupId(self.current_group.id)
                self.sObj.createExpense(expense)
                row = row + 1
                self.le_initial_row.setText(str(row+1))
        except  Exception as inst:
            QMessageBox.critical(self,self.tr("Error"), self.tr("Se ha producido un error en la fila") + str(row+1) + "\n" + str(inst))
            traceback.print_exc()
    def _enable_widgets(self, state):
        self.le_initial_row.setEnabled(state)
        self.cmb_group.setEnabled(state)
        self.cmb_ods_sheets.setEnabled(state)
        self.le_date_col.setEnabled(state)
        self.default_date.setEnabled(state)
        self.le_description_col.setEnabled(state)
        self.btn_import.setEnabled(state)
        self.le_date_format.setEnabled(state)
    def sheet_changed(self, sheet_name):
        self.read_sheet(self.file_data,sheet_name)
    def current_group_changed(self, idx):
        item = self.vlayout.takeAt(1)
        item.layout().deleteLater()
        item.invalidate()
        item = None
        self.vlayout.invalidate()
        self.group_members_layout = QFormLayout()
        self.current_group = self.cmb_group.itemData(idx)
        column_number = 1
        self.member_widget_map = {}
        for member in self.current_group.getMembers():
            self.member_widget_map[member.getId()] = QLineEdit(str(column_number))
            self.group_members_layout.addRow(self.tr("Columna " +
                member.getFirstName()),self.member_widget_map[member.getId()])
            column_number=column_number + 1
        self.vlayout.insertLayout(1,self.group_members_layout)
    def init_gui(self):
        self.form_layout        = QFormLayout()
        self.cmb_ods_sheets     = QComboBox()
        self.le_initial_row     = QLineEdit("1")
        self.le_initial_row.setValidator(QIntValidator(1,99999))
        self.cmb_group          = QComboBox()
        self.le_date_col        = QLineEdit("1")
        self.le_date_col.setValidator(QIntValidator(1,999999))
        self.default_date       = QDateTimeEdit(QDate.currentDate());
        self.default_date.setMinimumDate(QDate.currentDate().addDays(-365));
        self.default_date.setMaximumDate(QDate.currentDate().addDays(365));
        self.default_date.setDisplayFormat("dd.MM.yyyy")
        self.default_date.setCalendarPopup(True)
        self.le_date_format = QLineEdit("d/M/yyyy")

        self.le_description_col = QLineEdit("2")
        self.le_description_col.setValidator(QIntValidator(1,9999))
        self.sObj                    = get_splitwise()
        groups                  = self.sObj.getGroups()

        self.cmb_ods_sheets.currentTextChanged.connect(self.sheet_changed)
        for group in groups:
            self.cmb_group.addItem(group.getName(),group)
        self.cmb_group.currentIndexChanged.connect(self.current_group_changed)
        self.cmb_group.setCurrentIndex(0)
        btn_open_filename = QPushButton("Open")
        btn_open_filename.clicked.connect(self.open_filename)
        self.form_layout.addRow(self.tr("Archivo"),btn_open_filename )
        self.form_layout.addRow(self.tr("Hoja"),self.cmb_ods_sheets)
        self.form_layout.addRow(self.tr("Grupos"),self.cmb_group)
        self.form_layout.addRow(self.tr("Fila Inicial"), self.le_initial_row)
        self.form_layout.addRow(self.tr("Columna Fecha"), self.le_date_col)
        self.form_layout.addRow(self.tr("Formato de fecha"), self.le_date_format)
        self.form_layout.addRow(self.tr("Fecha por defecto"), self.default_date)
        self.form_layout.addRow(self.tr("Columna Concepto"), self.le_description_col)

        self.group_members_layout = QFormLayout()

        self.btn_import =QPushButton(self.tr("Importar"))
        self.btn_import.clicked.connect(self.import_expenses)

        self.model = QStandardItemModel(self)
        tableView = QTableView(self)
        tableView.setModel(self.model)

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.form_layout)
        self.vlayout.addLayout(self.group_members_layout)
        self.vlayout.addWidget(self.btn_import)
        self.vlayout.setStretch(1,1)

        hlayout = QHBoxLayout()
        hlayout.addWidget(tableView)
        hlayout.addLayout(self.vlayout)

        hlayout.setStretch(1,0)
        hlayout.setStretch(0,1)
        self.setLayout(hlayout)
        self._enable_widgets(False)
        self.show()

class MainWindow(QMainWindow):
      def __init__(self):
        super().__init__()
        if not config.is_authorized():
            auth = AuthorizeAppWidget()
            self.setCentralWidget(auth)
            self.show()
        else:
            w   = ImportWidget()
            self.setCentralWidget(w)
            self.show()
        self.showMaximized()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = MainWindow()
    w.setWindowTitle('Simple')
    w.show()

    sys.exit(app.exec_())
