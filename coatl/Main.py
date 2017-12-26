# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 22:16:39 2017

@author: Yuki
"""

from PyQt5.QtWidgets import QWidget,QApplication,QMainWindow,QMdiArea,QMdiSubWindow,QMenuBar,QAction,QFileDialog,QDesktopWidget,\
                            QStatusBar
from PyQt5.QtCore import pyqtSignal                    
import pickle,os

import coatl
from coatl.Graph import MyGraphWindow
from coatl.Browser import MyTreeWidget
from coatl.Logger import logger

MAIN_EXTENSION='cl'
DEPEND_EXTENSION='cld'

MAXIMIZED=0
MINIMIZED=1
NORMAL=2

def open_windows():
    pathes=QFileDialog.getOpenFileNames(None,'Choose files to open','','{0} file (*{1})'.format(coatl.COATL,MAIN_EXTENSION))
    
    def try_pickle(path):
        if os.path.isfile(path):
            depend_path=path.rstrip(MAIN_EXTENSION)+DEPEND_EXTENSION
            try:
                answer=pickle.load(open(path,'rb'))
                answer.set_path(path,depend_path)
                return answer
            except Exception as e:
                print(e)
                try:
                    with open(depend_path,'rb') as df:
                        depend=pickle.load(df)
                        print('This {} file depends on the packages below. Check your environment meets these requirements.'.format(coatl.COATL))
                        print(depend)
                except Exception as e2:
                    print(e2)
                    print('Cannot find the dependencies file with extension (.{}). \
                          This file may depend on packages which do not match your environment'.format(DEPEND_EXTENSION))
        else:
            raise FileNotFoundError
            
    if len(pathes[0])==1:
        answer=try_pickle(pathes[0][0])
        return answer
    elif len(pathes[0])>1:
        answer=[try_pickle(path) for path in pathes[0]]
        return answer

class Manager():
    '''Manage widgets by holding them as attributes.'''
    
    
    def __init__(self,mdi,target_class):
        '''
        Params:
            mdi: QMdiArea
                the QMdiArea to which widgets are added
            target_class: class
                the class of widgets
        '''
        self.__mdi=mdi
        self.__target_class=target_class
        self.__prefix='_{}__'.format(self.__class__.__name__)
    
    def _add(self,widget,name,state=None,geometry=None):
        '''
        Add a widget to self.__mdi and holds it as an atrribute of itself
        
        Paramters:
            widget: QWidget
                the widget to be added (must be able to be pickled)
            name: str
                the widget's name
        '''
        if isinstance(widget,self.__target_class):
            subwindow=SubWindow()
            subwindow.setWidget(widget)
            subwindow.deleteSignal.connect(self._delete)
            self.__mdi.addSubWindow(subwindow)
            widget.objectNameChanged.connect(subwindow.setWindowTitle)
            checked=self._check_name(name)
            widget.setObjectName(checked)
            if state==MAXIMIZED:
                subwindow.showMaximized()
            elif state==MINIMIZED:
                subwindow.showMinimized()
            elif state==NORMAL:
                if not geometry==None:
                    subwindow.showNormal()
                    subwindow.setGeometry(geometry)
            widget.show()
            setattr(self,checked,widget)
        else:
            raise Exception('A widget to be added to this instance must be an instance of {}'.format(self.__target_class))
        
    def _delete(self,name):
        '''
        Delete a widget specified by the name from self.__mdi and the attributes
        
        Parameters:
            name: str
                the widget's name
        '''
        widgets=self._get_all_widgets()
        if name in widgets.keys():
            self.__mdi.removeSubWindow(widgets[name].parent())
            delattr(self,name)
        else:
            raise Exception('{} does not exist.'.format(name))
            
    def _get_all_widgets(self):
        '''
        Return All the widgets as dict
        
        Returns:
            dict
                key: the widget's name value: the widget
        '''
        answer={}
        for key,value in vars(self).items():
            if not key.startswith(self.__prefix):
                answer[key]=value
        return answer
        
    def _check_name(self,name):
        '''
        Check if 'name' already exists in self attributes' names  and return an appropriately suffixed name if needed.
        If the name starts with self.__prefix, raise Exception.
        
        Parameters:
            name: str
                the widget's name
        Returns:
            str
                an appropriate name suffixed if needed
        '''
        def check_and_get(name,mydict):
            '''
            Check the keys of 'mydict' and return an appropriate, suffixed if needed, string near 'name'.
            '''
            keys=mydict.keys()
            suffix=0
            answer=name
            while True:
                if not answer in keys:
                    return answer
                else:
                    answer=name+str(suffix)
                    suffix=suffix+1
            return answer
            
        if name.startswith(self.__prefix):
            raise Exception('\'{}\' is not an available name'.format(name))
        else:
            return check_and_get(name,self._get_all_widgets())
        
    def _rename(self,old,new):
        '''
        Rename a widget
        
        Params:
            old: str
                the old name
            new: str
                a new name
        '''
        widgets=self._get_all_widgets()
        if old in widgets.keys():
            widget=widgets[old]
            checked=self._check_name(new)
            delattr(self,old)
            setattr(self,checked,widget)
            widget.setObjectName(checked)
        else:
            raise Exception('{} does not exist.'.format(old))

class SubWindow(QMdiSubWindow):
    deleteSignal=pyqtSignal(str)
    
    def closeEvent(self, event):
        self.deleteSignal.emit(self.widget().objectName())
        event.accept()
            
def unpickle_mainwindow(main_geometry,g_geometries,b_geometries):
    '''
    Unpickle a MainWindow, keeping all the geometries when pickled
    
    Params:
        main_geometry: QRect
        g_geometries: dict {str: (MyGraphWindow,int,QRect)}
            {the name of widget: (the widget (can be pickled),the state,geometry of the parent subwindow)}
        b_geometries: dict {str: (MyTreeWidget,int,QRect)}
            same as above
    Returns:
        MainWindow
    '''
    
    main=MainWindow()
    
    def place_widgets(geometries,add_method):
        for key,value in geometries.items():
            widget=value[0]
            state=value[1]
            geometry=value[2]
            add_method(widget,key,state,geometry)
            
    place_widgets(g_geometries,main.add_graph)
    place_widgets(b_geometries,main.add_browser)
    
    return main
    
class MainWindow(QMainWindow):
    '''The main window of this application which contains subwindows'''
    def __init__(self):
        super().__init__()
        self.initUI()
        self.graphs=Manager(self.mdiArea,MyGraphWindow) #holds graph windows
        self.browsers=Manager(self.mdiArea,MyTreeWidget) #holds browser windows
        self._path=None
        self._depend_path=None
        
        #place the window to the left of the screen
        screen=QDesktopWidget().availableGeometry()
        height=int(0.9*screen.height())
        width=int(0.9*screen.width()/2)
        self.setGeometry(0,40,width,height)
        self.setWindowTitle(coatl.COATL)
        self.show()
        
    def __reduce_ex__(self,protocol):
        '''
        For pickle
        '''
        def get_states(manager):
            '''
            Get the states and geometris of widgets
            
            Params:
                manager: Manager
            Returns:
                dict {str: (QWidget,int,QRect)}
                    {the name of widget: (the widget (can be pickled),the state,geometry of the parent subwindow)}
            '''
            
            widgets=manager._get_all_widgets()
            geometries={}
            for key,widget in widgets.items():
                subwindow=widget.parent()
                if subwindow.isMaximized():
                    state=MAXIMIZED
                elif subwindow.isMinimized():
                    state=MINIMIZED
                else:
                    state=NORMAL
                geo=subwindow.geometry()
                geometries[key]=(widget,state,geo)
            return geometries
        
        graph_geometries=get_states(self.graphs)
        browser_geometries=get_states(self.browsers)
                
        return unpickle_mainwindow,(self.geometry(),graph_geometries,browser_geometries)

    def initUI(self):   
        #add Menubar
        menubar=MyMenuBar(self)
        self.setMenuBar(menubar)
        menubar.saveAction.triggered.connect(self.save)
        menubar.saveAsAction.triggered.connect(self.save_as)
        self.mdiArea=QMdiArea()
        self.setCentralWidget(self.mdiArea)
        self.status=QStatusBar(self)
        self.setStatusBar(self.status)
        
    def new_graph(self,name='Unnamed'):
        '''
        Create a new graph window and add it to self.graphs
        
        Parameters
            name: the name of the graph
        Returns
            MyGraphWindow
        '''
        graph=MyGraphWindow()
        self.graphs._add(graph,name)
        return graph
        
    def new_browser(self,name='Unnamed'):
        '''
        Create a new browser and add it to self.browsers
        
        Parameters
            name: the name of the browser
        Returns
            MyTreeWidget
        '''
        browser=MyTreeWidget()
        self.browsers._add(browser,name)
        return browser
    
    def add_graph(self,graph,name='Unnamed',state=None,geometry=None):
        '''
        Add a graph to self.graphs
        
        Parameters
            graph: MyGraphWindow
            name: str
        '''
        self.graphs._add(graph,name,state,geometry)
            
    def add_browser(self,browser,name='Unnamed',state=None,geometry=None):
        '''
        Add a browser to self.browsers
        
        Parameters
            graph: MyTreeWidget
            name: str
        '''
        self.browsers._add(browser,name,state,geometry)
    
    def set_active(self,graph):
        '''
            Set the active graph for 'graph'
        '''
        pass
    
    def get_active(self):
        '''
            Get the active graph
        '''
        
    def get_graphs(self):
        '''
            Get all the graphs which this instance has.
        '''
        return self.graphs
        
    def save(self):
        '''
        Save itself to the file in self._path if set
        '''
        if self._path:
            self.pickle_self(self._path,self._depend_path)
        else:
            self.save_as()
    
    def save_as(self):
        '''
        Accept a file path via a file dialog and try to save itself to it
        '''
        path = QFileDialog.getSaveFileName(None, 'Choose a save file','temp.{}'.format(MAIN_EXTENSION),
                                           '{0} file (*{1})'.format(coatl.COATL,MAIN_EXTENSION))[0] #pyqt5ではtapleの一個めにpathが入っている
        if path:
            #Enforce the extension
            if not path.endswith('.{}'.format(MAIN_EXTENSION)):
                path=path+'.{}'.format(MAIN_EXTENSION)
            depend_path=path.rstrip(MAIN_EXTENSION)+DEPEND_EXTENSION
            self.pickle_self(path,depend_path)
                    
    def pickle_self(self,path,depend_path):
        '''
        Actual pickling
        
        Params:
            path: str
                the path of the file to which itself is writen
            depend_path: str
                the path of the file to which the dependencies are writen
        '''
        with open(path,'wb') as f:
            with open(depend_path,'wb') as df:
                #! must call self.set_path before pickling because pathes are needed when pickling
                self.set_path(path,depend_path)
                pickle.dump(self,f)
                #get all the dependent packages' version as dict and pickle it
                versions=[browser.get_dependencies() for browser in self.browsers._get_all_widgets().values()]
                merged_version={}
                for version in versions:
                    merged_version.update(version)
                from pkg_resources import get_distribution
                merged_version[coatl.GRAPH_PACKAGE]=get_distribution(coatl.GRAPH_PACKAGE).version
                pickle.dump(merged_version,df)

                self.status.showMessage('Saved to: {}'.format(path))    
    
    def set_path(self,path,depend_path):
        '''
        Set the file path to which itself is pickled
        
        Params:
            path: str
            depend_path: str
                the path of the file to which the dependencies are writen
        '''
        self._path=path
        self._depend_path=depend_path
        self.setWindowTitle('{0}--{1}'.format(coatl.COATL,path))
        
class MyMenuBar(QMenuBar):
    '''Menubar'''
    def __init__(self,ref):
        super().__init__()
        self.saveAction=QAction('save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAsAction = QAction('save as', self)
        self.saveAsAction.setShortcut('Ctrl+A')
        
        self.fileMenu =self.addMenu('File')
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveAsAction)
        
        self.helpAction = QAction('About this program', self)
        self.helpAction.setShortcut('Ctrl+H')
        helpMenu=self.addMenu('Help')
        helpMenu.addAction(self.helpAction)
        
#        self.setState(ref.state)
#        ref.stateSignal.connect(self.setState)
        
#    def setState(self,end):
#        '''状態の遷移はこの関数を通して行われる'''
#        if end==RUNNING:
#            self.loadAction.setEnabled(False)
#        else:
#            self.loadAction.setEnabled(True)

if __name__=='__main__':
    import sys,pickle
    app = QApplication( sys.argv )
#    m=MainWindow()
#    m.new_graph()
#    m.new_graph()
#    m.new_browser()
#    m.new_browser()
#    g=MyGraphWindow()
#    m.add_graph(g,state=MINIMIZED)
    m=MainWindow()
#    sys.exit(app.exec_())        