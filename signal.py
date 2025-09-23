
###########################################################

import sys  
import os
from PyQt5 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np

from PyQt5.QtCore    import * #Qt #* # импортировать все классы QtCore
from PyQt5.QtGui     import * # импортировать все классы QtGui
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QWidget, QPushButton, QListWidget, QSplitter, QVBoxLayout, QLabel, QLineEdit, QMessageBox #* # импортировать все классы QtWidget

from scipy.signal import savgol_filter


y2 = []
y = []
x = []

###################################################
#class CustomDialog(QtWidgets.QDialog):
class CustomDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.poly = 3
        self.win = 11
        self.result = 0

        self.setWindowTitle("Параметры вычисления сигнала")

        layout = QVBoxLayout()

        self.label_win = QLabel("Enter win value:")
        layout.addWidget(self.label_win)
        self.win_input = QLineEdit()
        self.win_input.setText(str(self.win));
        self.win_input.setInputMask("00")
        layout.addWidget(self.win_input)

        self.label_poly = QLabel("Enter poly value:")
        layout.addWidget(self.label_poly)
        self.poly_input = QLineEdit()
        self.poly_input.setText(str(self.poly))
        self.poly_input.setInputMask("00")
        layout.addWidget(self.poly_input)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.push_ok)
        layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.push_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def get_win(self):
        return self.win #self.name_input.text()

    def get_poly(self):
        return self.poly #self.name_input.text()
        
    def get_result(self):
        return self.result #self.name_input.text(
        
    def push_cancel(self):
        self.result=0
        self.close()#done(QDialog.Rejected)

    def push_ok(self):
        self.result = 2
        try:
            win = int(self.win_input.text())
            poly = int(self.poly_input.text())
            if(poly<win):
                #print(win, poly)
                self.win = win
                self.poly = poly
                self.result=1    
        except ValueError:
            print(f"'{string_value}'FATAL ERROR: is not a valid integer.")
            exit(1)
        
        self.close()#done(QDialog.Accepted)

    def closeEvent(self, event: QCloseEvent):
        if(self.result==2):
            QMessageBox.about(self, "Внимание", "Введены некорректные параметры (poly < win)")
            self.result=0
            event.ignore();
        else:
            event.accept();

    def get_poly(self):
        return self.poly
    def ok(self):
        self.poly= edit1.text.asint()
        self.win=edit2.text.asint()    
############################################

class MainWindow(QtWidgets.QMainWindow): # класс окна от базового класса QMainWindow

    def __init__(self, *args, **kwargs): # конструктор класса
        
        super(MainWindow, self).__init__(*args, **kwargs) # вызвать конструктор базового класса QMainWindow

        self.calcPlot = None
        
        #uic.loadUi('win.ui', self) # Загрузите файл описания интерфейса на QT в интерфейс окна (win.ui сздан в Qt Designer)
        
        #self.setGeometry(300, 300, 300, 150) # установить размер окна по умолчанию (можно не делать, потомучто потом окно максимизируется)
        
        self.centralwidget = QWidget() # создаем центральную обласьб окна, в которой будут все элементы
        self.GraphWidget = pg.PlotWidget()
        self.BFile = QPushButton('Файл')
        self.BCalc = QPushButton('Рассчитать')
        self.BClear = QPushButton('Очистить')
        self.listResult = QListWidget()
        self.setCentralWidget(self.centralwidget)
        
        self.BCalc.setEnabled(False)
        self.BClear.setEnabled(False)

        self.setWindowTitle("Расчет сигнала") # установить название окна

        grid = QtWidgets.QGridLayout(self.centralwidget) # создать табличный компановщик размещения элементов окна как основной центральный элемент окна
        grid.addWidget(self.BFile, 0, 0) # добавить в компановщик объект кнопки BFile, определенный в файла win.ui по координатам 0,0 (первая строка, первый столбец таблицы компановщика grid)
        grid.addWidget(self.BCalc, 1, 0) 
        grid.addWidget(self.BClear, 2, 0) 
        
        wg = QWidget() # создать объект пустого виджета
        grid.addWidget(wg, 3, 0) # добавить пустой виджет в третью строку первога столбца табличного компановщика grid

        split = QSplitter(Qt.Vertical) # создать объект сплиттер разделяющий окна по вертикали для изменения их размеров
        split.addWidget(self.GraphWidget) # добавить верхним элементом в сплиттер объект отображающий график GraphWidget, взятый из win.ui
        split.addWidget(self.listResult) # добавить нижним элементом в сплиттер объект отображающий результаты расчетов listResult, взятый из win.ui
        #split.addWidget(QPushButton('rrr'))
        split.setSizes([800, 200]) # установить пропорции элементов в сплиттере
        
        grid2 = QtWidgets.QGridLayout(wg) # создать табличный компановщик размещения элементов в пустом виджете wg
        grid2.addWidget(split) # добавить сплиттер со всеми ранее добавленными в него элементами в компановщик grid2
        #grid2.addWidget(QPushButton('qqq'))


        self.GraphWidget.clear() # очистить график
        self.GraphWidget.setBackground("k") # установить черный фон графика

        self.GraphWidget.addLegend() # разрешить отображать легенду на графике
        self.GraphWidget.setLabel(axis='left', text='V, В') # установить название оси Y на графике
        self.GraphWidget.setLabel(axis='bottom', text='t, ns') # установить название оси X на графике
        self.GraphWidget.getAxis('left').setTextPen('y') # установить желтый цвет подписи название оси Y на графике
        self.GraphWidget.getAxis('bottom').setTextPen('y') # установить желтый цвет подписи название оси X на графике

        self.BFile.clicked.connect(self.get_file) # установить функцию get_file как обработчик по нажатию на кнопку объекта BFile
        self.BCalc.clicked.connect(self.calc) # 
        self.BClear.clicked.connect(self.clear) #
            
        self.showMaximized() # сделать окно на весь экран

    def plot(self, x, y, desc, color): # функция класса MainWindow, рисующая график (desc - имя файла с данными)
        p = self.GraphWidget.plot(x, y,pen=color, name=desc) # нарисовать график заданным цветом (pen=color), и отобразить легенду в виде строки desc
        return p
    
    def clear(self):
        global y2
        global y
        global x

        if (self.calcPlot != None):
            self.GraphWidget.removeItem(self.calcPlot)
            self.calcPlot = None
            self.BClear.setEnabled(False)
            self.listResult.clear()
        
    def calc(self): # функция класса MainWindow, вычисляющая результаты обработки графика
        global y2
        global y
        global x

        if len(y)>0:
            y2 = []
            self.listResult.clear()

            if self.calcPlot != None:
                self.GraphWidget.removeItem(self.calcPlot)
                self.calcPlot = None

############################################
        dlg = CustomDialog()
        dlg.exec_()
        
        if (dlg.get_result() == 1):
            win = dlg.get_win()
            poly = dlg.get_poly()
                
            y2 = savgol_filter(y, win, poly) # массив значений сглаженной функции, скоторыми можно делать рассчеты параметров
            legend_str = "Рассчетный сигнал: win= " + str(win) + " poly= " + str(poly)
            self.calcPlot = self.plot(x, y2, legend_str,'w') # вызвать функцию класса, которая нарисует график
                
            self.listResult.addItem("Va = 10 В") # добавить результат расчета параметра
            self.listResult.addItem("Vb = 5 В") # добавить результат расчета параметра
############################################                
            
            # win и poly - параметры функции сглаживания  savgol_filter надо подобрать. Сделать диалог с возможностью задавать эти параметры
            #dp= MayDialog()
            #dp.show()
            '''
            win = 11 # значение параметра окна сглаживания
            poly = 3 # значение степени полинома сглаживания (poly < win)

            y2 = savgol_filter(y, win, poly) # массив значений сглаженной функции, скоторыми можно делать рассчеты параметров
            self.calcPlot = self.plot(x, y2, "Рассчетный сигнал",'w') # вызвать функцию класса, которая нарисует график
            
            self.listResult.addItem("Va = 10 В") # добавить результат расчета параметра
            self.listResult.addItem("Vb = 5 В") # добавить результат расчета параметра
            '''
            self.GraphWidget.removeItem(dlg)

            self.BCalc.setEnabled(True)
            self.BClear.setEnabled(True)


    def get_file(self): # функция класса MainWindow, вызываемая при нажатии на кнопку BFile

        global x
        global y

        try:

            file_name, _ = QFileDialog.getOpenFileName(self, 'Signal Data', r"", "") # открыть диалог выбора файла, по закрытию диалога в переменную file_name возвратится полное имя файла
            if os.path.exists(file_name):  # проверить, что файл существует            
                file = open(file_name,'r') # открыть файл в переменную file
            
                content_y = file.read().replace('[','').replace(']','').replace(' ','').split(",") # считать данные из файла в массив строку удалив символы "[] ", где запятая - разделитель между элементами массива
                a = content_y
                y = np.asarray(a, dtype=float) # сформиовать массив Y, как массив из чисел с плавающей запятой
        except OSError:
            print("Ошибка OSError")
        except TypeError:
            print("Ошибка TypeError")
        except ValueError:
            print("Недопустимое значение. Невозможно считать данные из файла!")
        except IndexError:
            print("Огшибка IndexError")
        except ZeroDivisionError:
            print("Деление на ноль")
        except FileNotFoundError:
            print("Файл не найден.")
        else:

            tmp = 0 # значение первого элемента массива y
            x = [] # пустой массив X
            for t in range(len(y)): # в цикле от 0 до числа элементов в массиве y-1
                x.append(tmp) # добавить элемент в массив x
                tmp = tmp + 50 # сформиовать очередное значение элемента массива x
            
            self.listResult.clear()  # очистить результаты расчетов
            self.GraphWidget.clear() # очистить график
            self.plot(x, y, file_name,'g') # вызвать функцию класса, которая нарисует график
            self.calcPlot = None
       
            self.BCalc.setEnabled(True)
            self.BClear.setEnabled(False)

            

# Функция main - основная старт программы
if __name__ == '__main__': 
    app = QtWidgets.QApplication(sys.argv) # создать объект программы
    main = MainWindow() # создать объект окна класса MainWindow
    main.show() # отобразить  окно
    sys.exit(app.exec_()) # запустить объект программы, чтобы обрабатывались кнопки и события

