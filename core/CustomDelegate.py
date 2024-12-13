from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import Qt

class CustomItemDelegate(QStyledItemDelegate):
    # def paint(self, painter, option, index):
    #     if option.state & QStyle.State_Selected:
    #         painter.fillRect(option.rect, option.palette.highlight())
    #     else:
    #         painter.fillRect(option.rect, option.palette.base())

    #     text = index.data(Qt.DisplayRole)
    #     painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, text)

    def setModelData(self, editor, model, index):
        new_value = editor.text() #type: ignore
        model.setData(index, new_value, Qt.ItemDataRole.EditRole)

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        editor.setStyleSheet("background-color: rgb(40, 44, 52);")
        return editor
