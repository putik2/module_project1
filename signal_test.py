# -*- coding: utf-8 -*-

import sys  
import time
import os
from PyQt5 import QtWidgets, uic
import pyqtgraph as pg
import numpy as np

from PyQt5.QtCore    import  * 
from PyQt5.QtGui     import * 
from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QMainWindow, QWidget, QPushButton, QListWidget, QSplitter, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QToolBox, QAction, QToolBar,  QToolButton

from scipy.signal import savgol_filter, find_peaks
import scipy.signal as signal_s

from shapely.geometry import LineString

from PyQt5.QtWebEngineWidgets import QWebEngineView
import PyQt5.QtWebEngineWidgets as QtWebEngineWidgets
from PyQt5.QtCore import QUrl

# глобальные переменные
signal_y = [] # массив данных сигнала из файла
signal_x = [] # сгенерированный массив данных временных отсчетов сигнала из файла
savgol_y = [] # массив данных сглаженного сигнала

DLG_CLOSE_CANCEL = 0 # Диалог закрыт не по кнопке Отмена
DLG_CLOSE_OK = 1 # Диалог закрыт не по кнопке OK
DLG_CLOSE_IGNORE = 2 # Признак отмены закрытия окна


#class WebPDFViewer(QDialog):
class WebPDFViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.web_view = QWebEngineView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.web_view.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)

    def load_pdf(self, path):
       self.web_view.load(path)

'''
Класс:
Диалог формирования параметров функции сглаживания исходного сигнала
'''
class SavGol_Dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # параметры фильтра сглаживающей функции по умолчанию
        self.poly = 10 # параметр полинома
        self.win = 11 # параметр размера окна фильтра (Условие: poly < win) (11;10 - максимально приближено)
        
        # результат закрытия диалога
        self.result = DLG_CLOSE_CANCEL

        self.setWindowTitle("Параметры функции сглаживания")

        layout = QVBoxLayout() # менеджер размещения элеменов диалога

        self.label_win = QLabel("Введите параметра окна:")
        layout.addWidget(self.label_win)
        self.win_input = QLineEdit() # параметр окна функции сглаживания
        self.win_input.setText(str(self.win))
        self.win_input.setInputMask("00")
        layout.addWidget(self.win_input)

        self.label_poly = QLabel("Введите параметр полинома:")
        layout.addWidget(self.label_poly)
        self.poly_input = QLineEdit() # параметр полинома функции сглаживания
        self.poly_input.setText(str(self.poly))
        self.poly_input.setInputMask("00")
        layout.addWidget(self.poly_input)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.push_ok) # установка функции обработки при нажатии на кнопку OK
        layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.push_cancel) # установка функции обработки при нажатии на кнопку Отмена
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    '''
    функция: 
    Возвращает параметр окна функции сглаживания
    '''
    def get_win(self):
        return self.win

    '''
    функция: 
    Возвращает параметр полинома функции сглаживания
    '''
    def get_poly(self):
        return self.poly

    '''
    функция: 
    Возвращает результат закрытия диалога
    '''    
    def get_result(self):
        return self.result
    
    '''
    функция: 
    Обработчик нажатия на кнопку Отмена
    '''
    def push_cancel(self):
        self.result = DLG_CLOSE_CANCEL
        self.close() # закрыть диалог

    '''
    функция: 
    Обработчик нажатия на кнопку ОК
    '''
    def push_ok(self):
        self.result = DLG_CLOSE_IGNORE
        try:
            win = int(self.win_input.text()) # числовое значение параметра окна функции сглаживания
            poly = int(self.poly_input.text()) # числовое значение параметра полинома функции сглаживания
            if(poly<win):
                self.win = win
                self.poly = poly
                self.result = DLG_CLOSE_OK    
        except ValueError:
            print("Критическая ошибка: параметр не целое число")
            exit(1)
        
        self.close() # закрыть диалог

    '''
    функция: 
    Обработчик при закрытии окна диалога
    '''
    def closeEvent(self, event: QCloseEvent):
        if(self.result==DLG_CLOSE_IGNORE):
            QMessageBox.about(self, "Внимание", "Введены некорректные параметры (полином < окно)")
            self.result=DLG_CLOSE_CANCEL
            event.ignore() # не закрывать окно
        else:
            event.accept() # закрыть окно

'''
Класс:
основное окно программы
'''
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        
        super(MainWindow, self).__init__(*args, **kwargs) # вызвать конструктор базового класса QMainWindow

        self.calcPlot = None # график функции сглаживания

        self.setWindowTitle("Расчет сигнала") # установка названия окна программы

#////////////////////////////////////
        mainMenu = self.menuBar()
        
        fileMenu = mainMenu.addMenu('Сигнал')
        self.action_File = QAction("Файл", self)
        self.action_File.triggered.connect(self.get_file)
        self.action_File.setShortcut("Ctrl+F")
        self.action_File.setToolTip("Открыть файл с данными сигнала Ctrl+F")
        fileMenu.addAction(self.action_File)
        fileMenu.addSeparator()
        self.action_Close = QAction("Закрыть", self)
        self.action_Close.triggered.connect(self.close)
        self.action_Close.setShortcut("Ctrl+Q")
        fileMenu.addAction(self.action_Close)
        
        helpMenu = mainMenu.addMenu('Справка')
        
        self.action_Info = QAction("Параметры сигнала", self)
        self.action_Info.triggered.connect(self.showInfo)
        self.action_Info.setShortcut("Ctrl+H")
        
        self.action_Ruk = QAction("Руководство", self)
        self.action_Ruk.triggered.connect(self.showRuk)
        self.action_Ruk.setShortcut("Ctrl+R")
        
        self.action_About = QAction("О программе", self)
        self.action_About.triggered.connect(self.showAbout)
        self.action_About.setShortcut("F1")
        
        helpMenu.addAction(self.action_Ruk)       
        helpMenu.addAction(self.action_Info)   
        helpMenu.addSeparator()
        helpMenu.addAction(self.action_About)   
       
#/////////////////
        ctlToolBar = QToolBar("Управление", self)
        ctlToolBar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, ctlToolBar)
        
        self.action_Calc = QAction("Рассчитать", self)
        self.action_Calc.triggered.connect(self.calc)
        self.action_Calc.setShortcut("Ctrl+S")
        self.action_Calc.setToolTip("Рассчитать параметры сигнала Ctrl+S")
        ctlToolBar.addAction(self.action_Calc)

        self.action_Clear = QAction("Очистить", self)
        self.action_Clear.triggered.connect(self.clear)
        self.action_Clear.setShortcut("Ctrl+C")
        self.action_Clear.setToolTip("Удалить рассчеты параметров сигнала Ctrl+C")
        ctlToolBar.addAction(self.action_Clear)

        


#/////////////////

        self.centralwidget = QWidget() # основная область окна
        self.GraphWidget = pg.PlotWidget() # виджет отображения графика исходных данных
        self.GraphWidget.showGrid(True, True, 0.5)
        self.GraphWidgetResult = pg.PlotWidget() # виджет отображения графика результатов рассчета сигнала
        self.GraphWidgetResult.showGrid(True, True, 0.5)

        self.BFile = QToolButton()
        self.BFile.setDefaultAction(self.action_File)
        
        self.BCalc = QToolButton()
        self.BCalc.setDefaultAction(self.action_Calc)
        
        self.BClear = QToolButton()
        self.BClear.setDefaultAction(self.action_Clear)
                
        self.listResult = QListWidget() # поле списка вычисления результатов параметров сигнала
        self.listResult.setGeometry(0,0,500,200)
        self.setCentralWidget(self.centralwidget)
        
        self.action_Calc.setEnabled(False) # запретить рассчет результатов
        self.action_Clear.setEnabled(False) # запретить очистку результатов
        
        widget_buttons = QWidget() # виджет кнопок
        layout_buttons = QtWidgets.QHBoxLayout(widget_buttons) # менеджер размещения кнопок
        layout_buttons.setAlignment(Qt.AlignLeft)
        layout_buttons.addWidget(self.BFile)
        layout_buttons.addWidget(self.BCalc) 
        layout_buttons.addWidget(self.BClear) 
        
        layout_main = QtWidgets.QVBoxLayout(self.centralwidget) # основной менеджер размещения элементов окна
        layout_main.addWidget(widget_buttons)

        widget_result = QWidget() # виджет элементов отображения данных
        layout_result = QtWidgets.QVBoxLayout(widget_result)
        layout_main.addWidget(widget_result)
        
        split_result = QSplitter(Qt.Vertical) # виджет-сплиттер управления виджетами отображения обработки сигнала
        split_result.addWidget(self.GraphWidget)
        split_result.addWidget(self.GraphWidgetResult)
        split_result.addWidget(self.listResult)
        layout_result.addWidget(split_result)

        self.GraphWidget.clear() # очистка графика исходного сигнала
        self.GraphWidget.setBackground("k") # фон графика сигнала - черный

        self.GraphWidget.addLegend() # разрешить отображение легенды на графике
        self.GraphWidget.setLabel(axis='left', text='V, В') # параметры вертикальной оси 
        self.GraphWidget.setLabel(axis='bottom', text='t, ns') # параметры горизонтальной оси
        self.GraphWidget.getAxis('left').setTextPen('y') # цвет надписей вертикальной оси
        self.GraphWidget.getAxis('bottom').setTextPen('y') # цвет надписей горизонтальной оси

        self.GraphWidgetResult.addLegend() # разрешить отображение легенды на графике
        self.GraphWidgetResult.setLabel(axis='left', text='V, В') # параметры вертикальной оси 
        self.GraphWidgetResult.setLabel(axis='bottom', text='t, ns') # параметры горизонтальной оси
        self.GraphWidgetResult.getAxis('left').setTextPen('y') # цвет надписей вертикальной оси
        self.GraphWidgetResult.getAxis('bottom').setTextPen('y') # цвет надписей горизонтальной оси

        self.info_signal = WebPDFViewer()
        self.info_signal.setWindowTitle("Структура сигнала")
        self.info_signal.setGeometry(100, 100, 800, 600)

        self.info_ruk = WebPDFViewer()
        self.info_ruk.setWindowTitle("Руководство")
        self.info_ruk.setGeometry(100, 100, 800, 600)

        self.statusbar = self.statusBar()
        self.text_status = "Не заданы входные данные"
        self.statLabel = QLabel(f"{self.text_status}")
        self.statusbar.addPermanentWidget(self.statLabel, 1)

        self.showMaximized()

    '''
    Функция
    открывает окно О программе
    '''
    def showAbout(self):
        QMessageBox.information(self, 'О программе', 'Программа расчета параметров сигнала v 0.1/2025')

    '''
    Функция
    открывает окно с информацией о параметрах сигнала
    '''
    def showInfo(self):
        self.info_signal.load_pdf(QUrl("file:///sig_info.pdf"))
        #self.info_signal.exec_() #QDialog
        self.info_signal.show()

    '''
    Функция
    открывает окно с информацией о структуре программы
    '''
    def showRuk(self):
        self.info_ruk.load_pdf(QUrl("file:///ruk.pdf"))
        #self.info_signal.exec_() #QDialog
        self.info_ruk.show()    

    '''
    Функция
    Рисует график в виджете исходных данных сигнала
    '''
    def plot(self, x, y, desc, color): 
        p = self.GraphWidget.plot(x, y,pen=color, name=desc)
        return p
    
    '''
    Функция
    Очищает результаты вычислений кроме графика исходных данных
    '''
    def clear(self):
        if (self.calcPlot != None):
            self.GraphWidget.removeItem(self.calcPlot) # очистить график сглаженных данных в виджете исходных данных
            self.GraphWidgetResult.clear() # очистить графики в виджете рассчета сигнала
            self.calcPlot = None # график функции сглаженных данных не определен
            self.action_Clear.setEnabled(False) # запретить Очистить
            self.listResult.clear() # очистить результаты рассчета сигнала

    '''
    Функция
    Рассчет длительности и периода по уровню 0.5 сигнала
    ''' 
    def calcDlitelnostAndPeriodAndFreq(self, poitns):
        tmp = len(poitns)
        sig_id = 0 # счетчик номеров сигналов
        for i in range(tmp):
            self.GraphWidgetResult.addLine(x=poitns[i].x, y=None, pen={'color':'m', 'width':1}) # рисуем вертикальную линию в точке пересечения по уровню 0.5 сигнала
            if i==0:
                if ((i+1)<tmp):
                    self.listResult.addItem("Длительность сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i+1].x - poitns[i].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов

            else:
                if (i % 2)==0:
                    self.listResult.addItem("Период сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i].x - poitns[i-2].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов
                    self.listResult.addItem("Частота сигнала["+str(sig_id)+"]: "+"{:.2f}".format(1000000000 / (poitns[i].x - poitns[i-2].x))+" Гц")  # подсчет длистельности сигнала и вывод в поле результатов
                    sig_id = sig_id + 1
                    if ((i+1)<tmp):
                        self.listResult.addItem("Длительность сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i+1].x - poitns[i].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов

    def calcFronts(self, front_min, front_max):
        len_min = len(front_min)
        len_max = len(front_max)
        sig_id = 0 # счетчик номеров сигналов

        '''
        for i in range(tmp):
            self.GraphWidgetResult.addLine(x=poitns[i].x, y=None, pen={'color':'m', 'width':1}) # рисуем вертикальную линию в точке пересечения по уровню 0.5 сигнала
            if i==0:
                if ((i+1)<tmp):
                    self.listResult.addItem("Длительность сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i+1].x - poitns[i].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов

            else:
                if (i % 2)==0:
                    self.listResult.addItem("Период сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i].x - poitns[i-2].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов
                    self.listResult.addItem("Частота сигнала["+str(sig_id)+"]: "+"{:.2f}".format(1000000000 / (poitns[i].x - poitns[i-2].x))+" Гц")  # подсчет длистельности сигнала и вывод в поле результатов
                    sig_id = sig_id + 1
                    if ((i+1)<tmp):
                        self.listResult.addItem("Длительность сигнала["+str(sig_id)+"]: "+"{:.2f}".format(poitns[i+1].x - poitns[i].x)+" нс")  # подсчет длистельности сигнала и вывод в поле результатов
        '''

    '''
    Функция
    Рассчитывает параметры сигнала
    '''  
    def calc(self):
        global savgol_y
        global signal_y
        global signal_x

        if len(signal_y)>0: # проверка наличия входных данных
            savgol_y = []            

            if self.calcPlot != None: # удалить результаты предыдущего расчета
                self.GraphWidget.removeItem(self.calcPlot)
                self.GraphWidgetResult.clear()
                self.calcPlot = None
                self.action_Clear.setEnabled(False)
                self.listResult.clear() # очистить результаты вычислений


            dlg = SavGol_Dialog()
            dlg.exec_() #  открыть диалог параметров расчета

            if (dlg.get_result() == DLG_CLOSE_OK): # параметры были заданы
                win = dlg.get_win() # получить параметр окна
                poly = dlg.get_poly() # получить параметр полинома
                    
                savgol_y = savgol_filter(signal_y, win, poly) # сформировать данные массива функции сглаживания
                
#///////////////////////////////////////
                # Считаем максимальное значение сигнала
                level = np.amax(savgol_y)

                # Находим пики выше уровня 0.5 от максимального
                peaks, _ = find_peaks(savgol_y, height=0.5 * level)
                if peaks.size < 1:
                    print("ОШИБКА: некорректный сигнгал")
                    return
                sig_peaks = savgol_y[peaks[0]:peaks[-1]] # формируем массив пиковых значений сигнала
                
                mean_v = np.mean(sig_peaks) # Находим среднее значение пиков импульса                   
                sig_peaks = [sig for sig in sig_peaks if ( sig > 0.1*mean_v)] # удалить пиковые элементы меньше уровя 0.1 от среднего () 
                
                # Считаем результирующее среднее значение амплитуды сигнала
                magnitude =float(np.mean(sig_peaks))
                time.sleep(0.5)
                #print("MAGNITUDE: ", magnitude)

#////////////////////////////////////////

                data_magnitude = [] # амплитуда
                data_sigtime = [] # 0.5 уровня сигнала                
                data_front_max = [] # уровеню 0.9 амплитуды
                data_front_min = [] # уровеню 0.1 амплитуды
                for t in range(len(savgol_y)):
                    data_sigtime.append(magnitude / 2) # массив  для рассчета длительности и периода сигнала по уровню 0.5
                    data_magnitude.append(magnitude) # массив для рассчета амплитуды сигнала
                    data_front_max.append(magnitude*0.9) # массив для рассчета длительности фронта по уровню 0.9 амплитуда
                    data_front_min.append(magnitude*0.1) # массив для рассчета длительности фронта по уровню 0.1 амплитуда
                
                # отображение графиков расчетных линий сигнала
                legend_str = "Сглаженный сигнал: Par_win= " + str(win) + " Par_poly= " + str(poly)
                self.calcPlot = self.plot(signal_x, savgol_y, legend_str,'w') # отобразить функцию сглаживания
                
                self.GraphWidgetResult.clear()
                self.GraphWidgetResult.plot(signal_x, savgol_y, pen='r', name=legend_str) # отобразить функцию сглаживания для расчетов
                self.GraphWidgetResult.plot(signal_x, data_sigtime, pen='y', name="Сигнал, 0.5 уровня")
                self.GraphWidgetResult.plot(signal_x, data_magnitude, pen='g', name="Амплитуда сигнала")
                self.GraphWidgetResult.plot(signal_x, data_front_max, pen='b', name="Уровень 0.9")
                self.GraphWidgetResult.plot(signal_x, data_front_min, pen='c', name="Уровень 0.1")

                self.listResult.addItem("Амплитуда: "+"{:.2f}".format(magnitude)+" В")  # вывод значения амплитуды сигнала  
                
                # расчет длительности и периода сигнала по точкам пересечения линии 0.5 уровня сигнала и графика сигнала
                savgol_y_line = LineString(np.column_stack((signal_x, savgol_y))) # график сигнала
                sigtime_line = LineString(np.column_stack((signal_x, data_sigtime))) # график уровня 0.5
                p_intersection = savgol_y_line.intersection(sigtime_line) # формирование объекта точек пересечения 
                points_inters = [p for p in p_intersection.geoms] # преобразование объекта точек пересечения в массив объектов точек пересечения
                poitns_inters_sort = [item[1] for item in sorted([(pt.x,pt) for pt in points_inters])] # сортировка массива объектов точек пересечения по X по уровню 0.5 сигнала
                self.calcDlitelnostAndPeriodAndFreq(poitns_inters_sort)

                # расчет длительности фронтов сигнала
                data_front_max_line = LineString(np.column_stack((signal_x, data_front_max))) # график уровня 0.9
                p_intersection = savgol_y_line.intersection(data_front_max_line) # формирование объекта точек пересечения 
                front_inters_max = [p for p in p_intersection.geoms] # преобразование объекта точек пересечения в массив объектов точек пересечения
                front_inters_max_sort = [item[1] for item in sorted([(pt.x,pt) for pt in points_inters])] # сортировка массива объектов точек пересечения
                
                data_front_min_line = LineString(np.column_stack((signal_x, data_front_min))) # график уровня 0.9
                p_intersection = savgol_y_line.intersection(data_front_min_line) # формирование объекта точек пересечения 
                front_inters_min = [p for p in p_intersection.geoms] # преобразование объекта точек пересечения в массив объектов точек пересечения
                front_inters_min_sort = [item[1] for item in sorted([(pt.x,pt) for pt in points_inters])] # сортировка массива объектов точек пересечения
              
                self.calcFronts(front_inters_min_sort, front_inters_max_sort) # расчет длительности фронтов
                
                self.action_Calc.setEnabled(True)
                self.action_Clear.setEnabled(True)
                
                self.text_status = "Расчет выполнен"
                self.statLabel.setText(self.text_status)

    '''
    Функция
    Открывает файл исходных данных сигнала и отображает его в виджете исходного сигнала
    '''
    def get_file(self):

        global signal_x
        global signal_y

        is_open = False
        try:

            file_name, _ = QFileDialog.getOpenFileName(self, 'Выбор данных сигнала', r"", "") # открыть диалог выбора файла, по закрытию диалога в переменную file_name возвратится полное имя файла
            if os.path.exists(file_name):              
                file = open(file_name,'r', encoding="UTF-8")             
                # чтение файла в буфер и преобразование текстовых данных
                file_data = file.read().replace('[','').replace(']','').replace(' ','').split(",") 
                signal_y = np.asarray(file_data, dtype=float) # формирование массива numpy для входных данных сигнала из файла
                is_open = True
        except OSError:
            print("Ошибка OSError")
        except TypeError:
            print("Ошибка TypeError")
        except ValueError:
            print("Недопустимое значение. Невозможно считать данные из файла!")
        except IndexError:
            print("Ошибка IndexError")
        except FileNotFoundError:
            print("Файл не найден.")
        else:
            if is_open == True:
                # формирования массива временных отсчетов входного сигнала
                if len(signal_y) > 0:
                    time_value = 0 # рассчетное значение временных отсчетов входного сигнала (+50 нс)
                    signal_x = [] 
                    for t in range(len(signal_y)): 
                        signal_x.append(time_value) 
                        time_value = time_value + 50 
                    signal_x = np.array(signal_x) # преобразования массива в массива numpy

                    self.listResult.clear()  # очистка результатов расчета
                    self.GraphWidget.clear()  # очистка всех графиков исходных данных
                    self.GraphWidgetResult.clear()  # очистка всех графиков результатов
                    self.plot(signal_x, signal_y, file_name,'g') # отображение графика входного сигнала
                    self.calcPlot = None # график функции сглаживания не определен
            
                    self.action_Calc.setEnabled(True) # разрешение Рассчитать
                    self.action_Clear.setEnabled(False) # запрет Очистить
                    
                    self.text_status = "Данные загружены"
                    self.statLabel.setText(self.text_status)
                
         
'''
Функция:
Запуск программы
'''
if __name__ == '__main__': 
    app = QtWidgets.QApplication(sys.argv) # создать объект программы
    main = MainWindow() # создать объект окна программы
    main.show() # показать окно программы
    sys.exit(app.exec_())  # запустить программу и выдать код завершения по закрытию

