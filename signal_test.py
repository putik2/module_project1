
import sys  
import os
from PyQt5 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np

from PyQt5.QtCore    import * 
from PyQt5.QtGui     import * 
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QWidget, QPushButton, QListWidget, QSplitter, QVBoxLayout, QLabel, QLineEdit, QMessageBox

from scipy.signal import savgol_filter
import scipy.signal as signal_s
from shapely.geometry import LineString


y2 = []
y = []
x = []

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
        return self.win

    def get_poly(self):
        return self.poly
        
    def get_result(self):
        return self.result
        
    def push_cancel(self):
        self.result=0
        self.close()

    def push_ok(self):
        self.result = 2
        try:
            win = int(self.win_input.text())
            poly = int(self.poly_input.text())
            if(poly<win):
                self.win = win
                self.poly = poly
                self.result=1    
        except ValueError:
            print(f"'{string_value}'FATAL ERROR: is not a valid integer.")
            exit(1)
        
        self.close()

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

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        
        super(MainWindow, self).__init__(*args, **kwargs) # вызвать конструктор базового класса QMainWindow

        self.calcPlot = None
        
        self.centralwidget = QWidget()
        self.GraphWidget = pg.PlotWidget()
        self.GraphWidgetResult = pg.PlotWidget()
        self.BFile = QPushButton('Файл')
        self.BCalc = QPushButton('Рассчитать')
        self.BClear = QPushButton('Очистить')
        self.listResult = QListWidget()
        self.listResult.setGeometry(0,0,500,200)
        self.setCentralWidget(self.centralwidget)
        
        self.BCalc.setEnabled(False)
        self.BClear.setEnabled(False)

        self.setWindowTitle("Расчет сигнала")

        grid = QtWidgets.QGridLayout(self.centralwidget)
        grid.addWidget(self.BFile, 0, 0)
        grid.addWidget(self.BCalc, 1, 0) 
        grid.addWidget(self.BClear, 2, 0) 
        
        wg = QWidget()
        grid.addWidget(wg, 3, 0)

        split = QSplitter(Qt.Vertical)
        split.addWidget(self.GraphWidget)
        split.addWidget(self.GraphWidgetResult)
        split.addWidget(self.listResult)
        
        grid2 = QtWidgets.QGridLayout(wg)
        grid2.addWidget(split)

        self.GraphWidget.clear()
        self.GraphWidget.setBackground("k")

        self.GraphWidget.addLegend()
        self.GraphWidget.setLabel(axis='left', text='V, В')
        self.GraphWidget.setLabel(axis='bottom', text='t, ns')
        self.GraphWidget.getAxis('left').setTextPen('y')
        self.GraphWidget.getAxis('bottom').setTextPen('y')

        self.GraphWidgetResult.addLegend()
        self.GraphWidgetResult.setLabel(axis='left', text='V, В')
        self.GraphWidgetResult.setLabel(axis='bottom', text='t, ns')
        self.GraphWidgetResult.getAxis('left').setTextPen('y')
        self.GraphWidgetResult.getAxis('bottom').setTextPen('y')

        self.BFile.clicked.connect(self.get_file)
        self.BCalc.clicked.connect(self.calc) 
        self.BClear.clicked.connect(self.clear)
            
        self.showMaximized()

    def plot(self, x, y, desc, color): 
        p = self.GraphWidget.plot(x, y,pen=color, name=desc)
        return p
    
    '''def hlines(self, lines, clr):
        p = self.GraphWidget.addLine(lines, color=clr)
        return p
    '''
    def clear(self):
        global y2
        global y
        global x

        if (self.calcPlot != None):
            self.GraphWidget.removeItem(self.calcPlot)
            self.GraphWidgetResult.clear()
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
                self.GraphWidgetResult.clear()
                self.calcPlot = None
                self.BClear.setEnabled(False)


            dlg = CustomDialog()
            dlg.exec_()

            if (dlg.get_result() == 1):
                win = dlg.get_win()
                poly = dlg.get_poly()
                    
                y2 = savgol_filter(y, win, poly) 
                legend_str = "Сглаженный сигнал: win= " + str(win) + " poly= " + str(poly)
                self.calcPlot = self.plot(x, y2, legend_str,'w') 

                zz, _= signal_s.find_peaks(y)

                self.GraphWidgetResult.clear()
                self.GraphWidgetResult.plot(x[zz], y[zz], pen='r', name="Пиковый сигнал")
                y4 = [] # амплитуда
                sko = np.std(y[zz]) 
                y3 = [] # среднее
                for t in range(len(y[zz])):
                    y3.append(sko)
                    y4.append(sko*2)
                self.GraphWidgetResult.plot(x[zz], y3, pen='y', name="Среднее")
                
                
                self.GraphWidgetResult.plot(x[zz], y4, pen='g', name="Амплитуда")

                
                t1  = np.max(y4)
                self.listResult.addItem("Амплитуда: "+"{:.2f}".format(t1)+" В")    
                
                first_line = LineString(np.column_stack((x[zz], y[zz])))
                second_line = LineString(np.column_stack((x[zz], y3)))
                intersection = first_line.intersection(second_line) #координаты точек пересечения красного и среднего
                #print(intersection)
                points = [p for p in intersection.geoms]
                #print(points)
                
                ps = [item[1] for item in sorted([(pt.x,pt) for pt in points])] # сортировка по X
                #print(ps)

                self.listResult.addItem("T: "+"{:.2f}".format(ps[1].x - ps[0].x)+" ns") 
                
                self.BCalc.setEnabled(True)
                self.BClear.setEnabled(True)

    def get_file(self):

        global x
        global y

        try:

            file_name, _ = QFileDialog.getOpenFileName(self, 'Signal Data', r"", "") # открыть диалог выбора файла, по закрытию диалога в переменную file_name возвратится полное имя файла
            if os.path.exists(file_name):              
                file = open(file_name,'r') 
            
                content_y = file.read().replace('[','').replace(']','').replace(' ','').split(",") 
                a = content_y
                y = np.asarray(a, dtype=float) 
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

            tmp = 0 
            x = [] 
            
            for t in range(len(y)): 
                x.append(tmp) 
                tmp = tmp + 50 
            x = np.array(x)
            self.listResult.clear()  
            self.GraphWidget.clear() 
            self.GraphWidgetResult.clear()
            self.plot(x, y, file_name,'g') 
            self.calcPlot = None
       
            self.BCalc.setEnabled(True)
            self.BClear.setEnabled(False)

         

if __name__ == '__main__': 
    app = QtWidgets.QApplication(sys.argv) 
    main = MainWindow() 
    main.show() 
    sys.exit(app.exec_()) 

