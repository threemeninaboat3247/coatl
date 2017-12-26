# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 04:16:37 2017

@author: Yuki
"""
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path

from PyQt5.QtCore import QRect,pyqtSignal,Qt,QTimer
from PyQt5.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QLabel,QTextEdit,QSizePolicy,QPushButton,\
                            QMainWindow,QAction,QApplication
from PyQt5.QtGui import QColor

import numpy as np

#Default graph setting
plt.rcParams['font.family'] ='sans-serif'
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.top']=True
plt.rcParams['ytick.right']=True
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams['font.size'] = 14 #フォントの大きさ
plt.rcParams['axes.linewidth'] = 1.0# 軸の線幅edge linewidth。囲みの太さ

##########################################################
#グラフウィンドウ
##########################################################
class MyPointer(QWidget):
    '''グラフにドロップできるポインタ　ドロップされると点にsnapしてx,yに点の座標を表示する'''
    COLOR='yellow'
    ALPHA=0.5
    SIZE=18
    def __init__(self):
        super().__init__()
        row=QHBoxLayout()
        xlabel=QLabel('X:')
        self.xEdit=QTextEdit()
        self.xEdit.setReadOnly(True)
        self.xEdit.setFixedHeight(30)
        self.xEdit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        ylabel=QLabel('Y:')
        self.yEdit=QTextEdit()
        self.yEdit.setReadOnly(True)
        self.yEdit.setFixedHeight(30)
        self.yEdit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button=QPushButton('✖')
        button.pressed.connect(self.reset)
        row.addWidget(xlabel)
        row.addWidget(self.xEdit)
        row.addWidget(ylabel)
        row.addWidget(self.yEdit)
        row.addWidget(button)
        row.addStretch(1)
        
        self.setLayout(row)
        
    def reset(self):
        try:
            self.point.remove()
            self.xEdit.setText(None)
            self.yEdit.setText(None)
            self.canvas.draw()
        except:
            pass
        
    def setXY(self,event):
        if not len(event.ind):
            return True
        self.ax=event.artist.axes
        try: #すでにpointがあるとき
            if self.point.axes==self.ax: #同じaxにpointがあるとき
                pass
            else: #前と違うaxでクリックされた時
                self.point.remove()
                self.point,=self.ax.plot([], [], 'o', ms=self.SIZE, alpha=self.ALPHA,color=self.COLOR, visible=False)
        except: #初めてクリックした時
            self.point,=self.ax.plot([], [], 'o', ms=self.SIZE, alpha=self.ALPHA,color=self.COLOR, visible=False)
        ind = event.ind[0]
        x = event.artist.get_xdata()[ind]
        y = event.artist.get_ydata()[ind]
        self.target=event.artist
        self.ind=ind
        clicked = (x, y)
        
        self.point.set_visible(True)
        self.point.set_data(clicked)
        self.canvas.draw()
        self.xEdit.setText(str(x))
        self.yEdit.setText(str(y))
        
    def startMove(self,event):
        try:
            self.timer.stop()
        except:
            pass
        self.timer=QTimer(self)
        if event.key == 'right':
            self.timer.timeout.connect(self.moveRight)
        elif event.key=='left':
            self.timer.timeout.connect(self.moveLeft)
        self.timer.start(70)
        
    def stopMove(self,event):
        self.timer.stop()
        
    def moveRight(self):
        try:
            self.ind+=1
            x=self.target.get_xdata()[self.ind]
            y=self.target.get_ydata()[self.ind]
            self.point.set_data(x,y)
            self.canvas.draw()
            self.xEdit.setText(str(x))
            self.yEdit.setText(str(y))
        except:
            pass
        
    def moveLeft(self):
        try:
            self.ind-=1
            x=self.target.get_xdata()[self.ind]
            y=self.target.get_ydata()[self.ind]
            self.point.set_data(x,y)
            self.canvas.draw()
            self.xEdit.setText(str(x))
            self.yEdit.setText(str(y))
        except:
            pass
        
    def activate(self,canvas):
        self.show()
        self.canvas=canvas
        self.pick=self.canvas.mpl_connect('pick_event',self.setXY)
        self.key_press=self.canvas.mpl_connect('key_press_event',self.startMove)
        self.key_release=self.canvas.mpl_connect('key_release_event',self.stopMove)
        self.canvas.setFocusPolicy(Qt.ClickFocus )
        self.canvas.setFocus()
        
    def deactivate(self):
        self.hide()
        self.reset()
        try:
            self.canvas.mpl_disconnect(self.pick)
            self.canvas.mpl_disconnect(self.key_press)
            self.canvas.mpl_disconnect(self.key_release)
        except:
            pass
        
def geneMyGraph(fig,geometry,title):
    return MyGraphWindow(fig,geometry,title)
    
class MyColors():
    '''Default color list for MyGraphWindow.'''
    def __init__(self):
        self.index=0
        self.colors=['r','g','b','c','m','y','k']
        self.length=len(self.colors)

    def get_color(self):
        color=self.colors[self.index]
        self._incre_index()
        return color

    def _incre_index(self):
        self.index=(self.index+1)%self.length
        
class MyGraphWindow(QMainWindow):
    ALPHA_OTHER=0.2 #lasso非選択データの透明度
    PICKER=5 #lineをクリックしたときに取得できるための領域
    mycolors=MyColors() #memory the color to use for self.plot method.
    def __init__(self,fig=None,geo=None,title='temp'):
        super().__init__()
        #mutableなオブジェクトをデフォルトに指定するとまずいのでこのように書く
        if fig==None:
            self.fig=Figure(figsize=(6,6), dpi=100)
        else:
            self.fig=fig
        if geo==None:
            self.geo=QRect(30,30,500, 500)
        else:
            self.geo=geo
            
        self.canvas=FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.lassoAction=QAction('lasso',self.canvas)
        self.pointerAction=QAction('pointer',self.canvas)
        self.lineAction=QAction('line',self.canvas)
        self.lassoAction.setCheckable(True)
        self.pointerAction.setCheckable(True)
        self.lineAction.setCheckable(True)
        self.navi_toolbar.addAction(self.lassoAction)
        self.navi_toolbar.addAction(self.pointerAction)
        self.navi_toolbar.addAction(self.lineAction)
        self.lassoAction.triggered.connect(self.lassoTriggered)
        self.pointerAction.triggered.connect(self.pointerTriggered)
        self.lineAction.triggered.connect(self.lineTriggered)
        
        self.lassoTarget=None #選択対象 lasso時はcilickでalphaを下げる
        self.selectedLine=None #選択中の点をself.lassoTargetの上にプロットする
        self.pre_alpha=1 #alphaを下げる前の値
        self.pre_settings=None #markerの色とサイズselectedLineをplotする時に使う
        
        #setTargetで指定したlineの点とそこからlassoで選ばれたindexを保存
        self.xys=None #numpy.array 列数2の行列
        self.selectedIndices=set()
        self.unselectedIndices=set()
        
        #クリックされたlineを記憶しておいてgetLineで参照を渡す
        self.line=None
        self.pre_width=0 #太くした後元に戻すのに使う
        
        #点の座標を表示する
        self.pointer=MyPointer()
        self.pointer.deactivate()
        
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.navi_toolbar)
        self.vbl.addWidget( self.canvas )
        self.vbl.addWidget(self.pointer)
        
        self.frontPanel=QWidget()
        self.frontPanel.setLayout(self.vbl)
        self.setCentralWidget(self.frontPanel)
        
        self.setGeometry(self.geo)
        self.setWindowTitle(title)
        self.show()
        
    def __reduce_ex__(self, proto):
        #pickleのためのメソッド QMainWindowはそのままpickleできないことに注意
        return geneMyGraph, (self.fig,self.geometry(),self.windowTitle())
        
    def getSelected(self):
        points=self.xys[list(self.selectedIndices)]
        return points
        
    def getUnSelected(self):
        points=self.xys[list(self.unselectedIndices)]
        return points
        
    def getLine(self):
        return self.line
        
    def plot(self,*args,**kwargs):
        #pickerはlineの選択に使うので必要
        kwargs=self._addPickerToValue(kwargs)
        kwargs=self._addColorToValue(kwargs)

        try: #axが指定されていたらそのaxに対して描画を行う axが無いまたはaxオブジェクト以外が指定されていると引数にaxが無い状態で次
            ax=kwargs.pop('ax')
            ax.plot(*args,**kwargs)
        except: #無ければself.figの最初のaxに描画　それもなければ新たにaxを追加して描画
            try:
                ax=self.fig.get_axes()[0]
                ax.plot(*args,**kwargs)
            except:
                ax=self.fig.add_subplot(111)
                ax.plot(*args,**kwargs)
        self.canvas.draw()
        
    def _addPickerToValue(self,kwargs):
        #pickerが無いとlassoで選択できないのでユーザーが引数にpickerを指定しなかった場合はpickerを加える
        if 'picker' in kwargs.keys():
            return kwargs
        else:
            kwargs['picker']=self.PICKER
            return kwargs
            
    def _addColorToValue(self,kwargs):
        #If color is in the kwargs use it. Otherwise get a color from self.mycolors and use it.
        if not 'color' in kwargs.keys():
            color=self.mycolors.get_color()
            kwargs['color']=color
        return kwargs
                
    def lassoTriggered(self):
        if self.lassoAction.isChecked()==True: #pointer Off lasso　On
            if self.pointerAction.isChecked()==True:
                self.pointerAction.setChecked(False)
                self.pointer.deactivate()
            if self.lineAction.isChecked()==True:
                self.lineAction.setChecked(False)
                self.removeLine()
            self.setLasso()
        else:
            self.removeLasso()
            
    def pointerTriggered(self):
        if self.pointerAction.isChecked()==True: #pointer on lasso　off
            if self.lassoAction.isChecked()==True:
                self.lassoAction.setChecked(False)
                self.removeLasso()
            if self.lineAction.isChecked()==True:
                self.lineAction.setChecked(False)
                self.removeLine()
            self.pointer.activate(self.canvas)
        else:
            self.pointer.deactivate()
            
    def lineTriggered(self):
        if self.lineAction.isChecked()==True: #他をoff
            if self.lassoAction.isChecked()==True:
                self.lassoAction.setChecked(False)
                self.removeLasso()
            if self.pointerAction.isChecked()==True:
                self.pointerAction.setChecked(False)
                self.pointer.deactivate()
            self.setLine()
        else:
            self.removeLine()
            
    def setLine(self):
        self.linepick=self.canvas.mpl_connect('pick_event',self.highlightLine)
        
    def removeLine(self):
        try:
            self.canvas.mpl_disconnect(self.linepick)
            if not self.line==None: #選択されていたものを元に戻す
                self.line.set_linewidth(self.pre_width)
                self.canvas.draw()
            self.line=None
            self.pre_width=0
        except:
            print('line is still not sellected')
        
    def highlightLine(self,event):
        #選択中のlineの輪郭を太くする
        if not len(event.ind):
            return True
        if not self.line==None: #初回のclickでない場合は先に選択されていたものを元に戻す
            self.line.set_linewidth(self.pre_width)
        #plotの設定を保存
        self.line=event.artist
        self.pre_width=self.line.get_linewidth()
        
        #alphaの調整とselectedLineの描画 まだinvisible　データの取得
        self.line.set_linewidth(self.pre_width*5)
        self.canvas.draw()
            
    def setLasso(self):
        self.pick=self.canvas.mpl_connect('pick_event',self.setTarget)
        
    def removeLasso(self):
        try:
            self.canvas.mpl_disconnect(self.pick)
            del self.lasso
            if not self.lassoTarget==None: #先に選択されていたものを元に戻す
                self.lassoTarget.set_alpha(self.pre_alpha)
                self.selectedLine.remove()
                self.canvas.draw()
            #多分必要ないが念のために初期化
            self.lassoTarget=None
            self.selectedLine=None
            self.pre_alpha=1
            self.pre_settings=None
            self.xys=None
            self.selectedIndices=set()
            self.unselectedIndices=set()
        except:
            print('Lasso is still not setted')
            
    def setTarget(self,event):
        #lassoの対象をclickから決定する
        if not len(event.ind):
            return True
        if not self.lassoTarget==None: #初回のclickでない場合は先に選択されていたものを元に戻す
            self.lassoTarget.set_alpha(self.pre_alpha)
            try: #あったら掃除 多分いつもある
                self.selectedLine.remove()
            except:
                pass
        self.selectedIndices=set()
        self.unselectedIndices=set()
        
        #plotの設定を保存
        self.lassoTarget=event.artist
        self.pre_alpha=self.lassoTarget.get_alpha()
        self.pre_settings=self.getSettings(self.lassoTarget)
        
        #alphaの調整とselectedLineの描画 まだinvisible　データの取得
        self.lassoTarget.set_alpha(self.ALPHA_OTHER)
        self.selectedLine,=self.lassoTarget.axes.plot([],[],visible=False,linestyle='None',**self.pre_settings)
        self.lasso=LassoSelector(self.lassoTarget.axes, onselect=self.onselect)
        self.xys=np.array([[x,y] for x,y in zip(self.lassoTarget.get_xdata(),self.lassoTarget.get_ydata())])
        self.canvas.draw()
        
    def getSettings(self,line):
        settings={'color':line.get_color(),'marker':line.get_marker(),'markersize':line.get_markersize()}
        return settings

    def onselect(self, verts):
        path = Path(verts)
        try:
            selected_ind = set(np.nonzero([path.contains_point(xy) for xy in self.xys])[0])
            all_ind=set(range(self.xys.shape[0]))
            unselected_ind=all_ind-selected_ind
        except:
            print('canot determin selected points')
        #選択される度にselcectedlineに追加
        self.selectedIndices=self.selectedIndices | selected_ind
        self.unselectedIndices=self.unselectedIndices | unselected_ind
        self.selectedLine.set_visible(True)
        points=self.xys[list(self.selectedIndices)]
        self.selectedLine.set_data(points[:,0],points[:,1])
        self.canvas.draw()
        
if __name__=='__main__':
    import sys
    app = QApplication( sys.argv )
    g=MyGraphWindow()
    x=np.arange(0,1000,0.1)
    y=np.random.rand(10000)
    z=np.random.rand(10000)+10
    g.plot(x,y,marker='o',markersize=20)
    g.plot(x,z,marker='o',picker=20)
    sys.exit(app.exec_())