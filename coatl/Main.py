# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 22:16:39 2017

@author: Yuki
"""

from PyQt5.QtWidgets import QWidget,QApplication,QMainWindow,QMdiArea,QMdiSubWindow,QMenuBar,QAction
from jupyterhack import GraphWindow

class Manager():
    '''Manage graphs by holding them as attributes.'''
    
    def _add(self,graph,name):
        if name in self.__dict__.keys():
            raise Exception(name+' already exists.')
        else:
            setattr(self,name,graph)
        
    def _delete(self,name):
        if name in self.__dict__.keys():
            del self.__dict__[name]
        else:
            raise Exception(name+' does not exist.')
            
    def _get_all_graphs(self):
        import copy
        answer=copy.copy(self.__dict__)
        return answer
        
    def _check_name(self,name):
        ''' Check if 'name' exists in self attribute names and return a appropriately suffixed name if needed'''
        
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
        return check_and_get(name,self._get_all_graphs())
        
class MainWindow(QMainWindow):
    GRAPH=GraphWindow
    
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.graphs=Manager()
        self.browsers=Manager()
        self.show()
   
    def initUI(self):   
        #add Menubar
        menubar=MyMenuBar(self)
        self.setMenuBar(menubar)
        self.mdiArea=QMdiArea()
        self.setCentralWidget(self.mdiArea)
        self.show()
        
    def new_graph(self,name='Unnamed'):
        '''
        Description
            Create a new graph window and add it to self.
        Param
            name: the name of the graph
        Return
            Graph
        '''
        checked=self.graphs._check_name(name)
        graph=self.GRAPH()
        self.graphs._add(graph,checked)
        self.mdiArea.addSubWindow(graph)
        graph.show()
        return graph
        
    def new_browser(self,name='Unnamed'):
        '''
            Create a new browser and add it to self.
        '''
        checked=self.browsers._check_name(name)
        graph=self.()
        self.graphs._add(graph,checked)
        self.mdiArea.addSubWindow(graph)
        graph.show()
    
    def add_graph(self,graph,name='Unnamed'):
        '''
        Description
            Add a graph to self.
        Param
            graph: Graph
        Return
            Graph
        '''
        if isinstance(graph,self.GRAPH):
            checked=self._check_name(name)
            self.graphs._add(graph,checked)
            self.mdiArea.addSubWindow(graph)
            graph.show()
        else:
            raise Exception('A graph to be added must be an instance of' + str(self.GRAPH))
            
    def 
    
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
    
    
        
class MyMenuBar(QMenuBar):
    '''自作Menubar 状態を持ちその状態によって押せるボタンが変化する その状態としてはQMainWindowの状態を参照する QMainWindowのstateSignalと繋ぐことで状態をupdate'''
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
    import sys
    app = QApplication( sys.argv )
    gg=MainWindow()
    gg.new_graph()
    sys.exit(app.exec_())        