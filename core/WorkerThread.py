from PySide6.QtCore import QRunnable, Slot, QObject, Signal

class WorkerSignals(QObject):
    finished = Signal()
    success = Signal()
    error = Signal(str) 
    result = Signal(object)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
            self.signals.finished.emit()
            self.signals.success.emit()
        except Exception as e:
            self.signals.finished.emit()
            self.signals.error.emit(str(e))