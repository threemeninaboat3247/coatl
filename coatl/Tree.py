# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 01:08:17 2017

@author: Yuki
"""
import sys
import inspect
import pandas as pd

from PyQt5.QtCore import pyqtSignal,QObject
from PyQt5.QtWidgets import QApplication,QWidget,QFileDialog

from coatl.Graph import MyGraphWindow

def transformMyTree(mytree,parent=None):
    #MyTreeをMyTreeRawに変換する pickleのため
    raw=MyTreeRaw(parent=parent,name=mytree.name)
    for key,value in mytree.getChildren().items():
        if isinstance(value,MyTree):
            raw[key]=transformMyTree(value,raw)
        else:
            raw[key]=value
    return raw

def transformMyRootTree(mytree,parent=None):
    #MyTreeをMyTreeRawに変換する pickleのため
    raw=MyTreeRaw(parent=parent,name=mytree.name)
    for key,value in mytree.getChildren().items():
        if isinstance(value,MyTree):
            raw[key]=transformMyTree(value,raw)
        else:
            raw[key]=value
    return raw
    
def transformMyTreeRaw(tree,parent=None):
    #MyTreeRawをMyTreeに変換する unpickleのため
    result=MyTree(parent=parent,name=tree.name)
    for key,value in tree.items():
        if isinstance(value,MyTreeRaw):
            result.add(ref=transformMyTreeRaw(value,result),label=key)
        else:
            result.add(ref=value,label=key)
    return result
    
def transformMyRootTreeRaw(tree,current_path,dependencies):
    #MyTreeRawをMyRootTreeに変換する unpickleのため
    try:
        result=MyRootTree(name=tree.name)
        for key,value in tree.items():
            if isinstance(value,MyTreeRaw):
                result.add(ref=transformMyTreeRaw(value,result),label=key)
            else:
                result.add(ref=value,label=key)
        result.setCurrent(current_path)
        return result
    except Exception as e:
        print(e)
        print(dependencies)
        raise Exception('Cannot unpickle the file.You may use a different environment from the one used when pickling. Use a environment satisfies the above requirements')
    
class MyTreeRaw(dict):
    '''Tree構造を実装するクラス　MyTreeをpickleする時にこれに変換する'''
    def __init__(self,parent,myobject=None,name='temp'):
        if myobject==None:
            super().__init__({})
        else:
            super().__init__(myobject)
        self.parent=parent #nodeはroot以外必ず親を持つ
        self.name=name #子の名前はdict型のkey
#        
#class MyRootTreeRaw(dict):
#    '''Convert MyRootTree to a dictionary to avoid recursive error when pickling. Also record package dependencies to show them up when the file is opened in a different environment'''
#    def __init__(self,parent,myobject=None,name='temp'):
#        if myobject==None:
#            super().__init__({})
#        else:
#            super().__init__(myobject)
#        self.parent=parent #nodeはroot以外必ず親を持つ
#        self.name=name #子の名前はdict型のkey
#        self.dependencies={}
    
class MyTree(QObject):
    '''
    A data folder class that has a tree structure. This class's instance holds children as its attributes and you can access them '.childname'. 
    Note that you must reimplement getChildren method when you add a new attribute to this class for the above reason.
    '''
    SPACE='  '
    INDENT='--'
    addSignal=pyqtSignal(list,str,list) #path,label,refの順 最後は参照を入れたいので[ref]とする
    deleSignal=pyqtSignal(list,str)
    renameSignal=pyqtSignal(list,str,str)
    
    def __init__(self,name='temp',parent=None,children=None):
        #childrenには子をdict型{'名前':参照}で渡す
        super().__init__()
        self.parent=parent #nodeはroot以外必ず親を持つ
        self.name=name
        if not children==None:
            for key,item in children.items():
                self.__dict__[key]=item
        
    def __reduce_ex__(self, proto):
        #pickleのためのメソッド 動的にインスタンス変数を追加するクラスはそのままpickleできない
        return transformMyTreeRaw,(transformMyTree(self),)
    
    def __str__(self, level=0,current=None,unfold=True):
        if self is current:
            ret = self.SPACE*level+self.INDENT+self.name+'<=='+"\n"
        else:
            ret = self.SPACE*level+self.INDENT+self.name+"\n"
        #MyTreeは先に展開それ以外のデータはunfoldがTrueならばkeyをprint   
        for key in sorted([key for key,value in self.getChildren().items() if isinstance(value,MyTree)]):
            ret += self.__dict__[key].__str__(level=level+1,current=current,unfold=unfold)
        if unfold:
            for key in sorted([key for key,value in self.getChildren().items() if not isinstance(value,MyTree)]):
                ret += self.SPACE*(level+1)+repr(key)+"\n"
        return ret
    
    def show(self,unfold=True):
        sys.stdout.write(self.__str__(unfold=unfold))
        
    def get(self,label):
        return self.__dict__[label]
    
    def getChildren(self):
        #子供を{'名前':参照}で返す
        children={k:v for k,v in self.__dict__.items() if not (k=='parent' or k=='name')}
        return children
    
    def add(self,ref,label=None,check=False,signal=True):
        #childrenにlabelと同一の名前が無ければchildとして加える checkは違う名前の同一オブジェクトが無いかチェックするオプション
        if label==None: #labelを指定していなければ呼び出し時の実引数をlabelとする
            frame = inspect.currentframe()
            stack = inspect.getouterframes(frame)
            val_name = stack[1].code_context[0].split('(')[1].split(')')[0] #これで実引数の名前を取得できるらしい ただし関数内やJupyterのcell内で連続してaddを呼び出すと最後のaddの実引数をlabelにするのでlabel重複のエラーがでる
            label=val_name
            
        if label in self.__dict__.keys():
            raise Exception('The same name already exists.Or you should call \'add\' method like this \'add(refference,\"name\")\' .')
        if check:
            result=self.checkChildren(ref)
            if result[0]:
                raise Exception('same object is registered as '+result[1])
            else:
                #フォルダの場合は親子関係を設定し、つけるラベルとフォルダの名前を一致させる addSignalは親に上げるためにtransmitAddSignalにconnect
                if isinstance(ref,MyTree):
                    ref.name=label
                    ref.parent=self
                    ref.addSignal.connect(self.transmitAddSignal)
                    ref.deleSignal.connect(self.transmitDeleSignal)
                    ref.renameSignal.connect(self.transmitRenameSignal)
                    self.__dict__[label]=ref
                else:
                    self.__dict__[label]=ref
        else:
            if isinstance(ref,MyTree):
                ref.name=label
                ref.parent=self
                ref.addSignal.connect(self.transmitAddSignal)
                ref.deleSignal.connect(self.transmitDeleSignal)
                ref.renameSignal.connect(self.transmitRenameSignal)
                self.__dict__[label]=ref
            else:
                self.__dict__[label]=ref

        #signalをemit
        if signal:
            self.addSignal.emit([self.name],label,[ref])
            
    def pop(self,label,signal=True):
        target=self.__dict__.pop(label)
        if isinstance(target,MyTree):
            target.disconnect()
        if signal:
            self.deleSignal.emit([self.name],label)
        return target
        
    def plot(self,x,y,xlabel='X',ylabel='Y',title='No name'):
        g=MyGraphWindow()
        g.plot(x,y)
        ax=g.fig.get_axes()[0]
        ax.set_title(title)
        g.setWindowTitle(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        def try_add(graph,label):
            self.add(graph,label)
            
        try:
            try_add(g,title)
        except:
            suffix=0
            while True:
                try:
                    try_add(g,title+str(suffix))
                    break
                except:
                    suffix+=1
        
        
    def rename(self,before,after,signal=True):
        if (not before==after) and (not after in self.getChildren().keys()): #beforeとafterが違って afterが子供にいない時
            ref=self.get(before)
            self.pop(before,signal=False) #ちなみにpopとaddを逆にすると挙動が変になる　popとaddでは同じオブジェクトを扱うがpopでシグナルをdisconnectしていることに注意
            self.add(ref,label=after,signal=False)
            if signal:
                self.renameSignal.emit([self.name],before,after)
            return True
        else:
            return False
        
    def checkChildren(self,ref):
        #子としてrefを持っていないかcheckする ref:オブジェクト参照
        result=[False,None]
        for key,child in self.getChildren().items():
            if id(child)==id(ref):
                result[0]=True
                result[1]=key
                break
        return result
        
    def ascend(self):
        #親を遡って一番上からのfull_pathを返す
        start=self
        full_path=[start.name]
        while not start.parent==None:
            start=start.parent
            full_path.append(start.name)
        full_path.reverse()
        return full_path
        
    def search(self,target):
        #カレントディレクトリ移動のためのサーチなのでディレクトリだけ調べる target:文字列
        if self.name==target:
            return {'result':True,'path':[self.name]}
        for child in self.getChildren().values():
            if isinstance(child,MyTree): #ディレクトリだけ調べる
                answer=child.search(target)
                if answer['result']:
                    return {'result':True,'path':([self.name]+answer['path'])}
        #ここまでくれば探索は解無し
        return {'result':False,'path':None}
    
    def runAll(self):
        #tree内を全ての参照のlistを返す
        mylist=[]
        mylist.append(self)
        for child in self.getChildren().values():
            if isinstance(child,MyTree):
                mylist=mylist+child.runAll()
            else:
                mylist.append(child)
        return mylist
    
    def loadFiles(self):
        def load_a_file(path):
            if not path=='':
                #1行だけ読み込んでみてstrが入っていればheaderとして使用してrootにもその名前で登録　そうでなければ'data0','data1',,,,としてrootに登録
                reader=pd.read_csv(path,sep='\t',comment='#',header=None,chunksize=1)
                data=reader.get_chunk(1)
                ndata=None
                if type(data.ix[0,0])==str:
                    ndata=pd.read_csv(path,sep='\t',comment='#')
                else:
                    ndata=pd.read_csv(path,sep='\t',comment='#',header=None)
                    ndata.columns=['data'+str(x) for x in range(len(ndata.columns))]
                    #自分の下にフォルダを作ってそこにデータを追加
                name=path.split('/')[-1]
                childFolder=MyTree()
                self.add(childFolder,label=name)
                for index in ndata.columns:
                    childFolder.add(ndata[index],label=index)           
                    
        paths = QFileDialog.getOpenFileNames(None, 'choose data files to load')[0]
        for path in paths:
            load_a_file(path)
            
    def transmitAddSignal(self,path,label,ref):
        #childのaddSignalのパスの先頭に自分の名前を付けくわえてemit
        path.insert(0,self.name)
        self.addSignal.emit(path,label,ref)
        
    def transmitDeleSignal(self,path,label):
        #childのdeleSignalのパスの先頭に自分の名前を付けくわえてemit
        path.insert(0,self.name)
        self.deleSignal.emit(path,label)
        
    def transmitRenameSignal(self,path,before,after):
        #childのrenameSignalのパスの先頭に自分の名前を付けくわえてemit
        path.insert(0,self.name)
        self.renameSignal.emit(path,before,after)
              
class MyRootTree(MyTree):
    '''カレントディレクトリを持つRootTree インスタンス変数を追加してはいけない'''
    #self.parent,self.name,self.current以外が子供なのでgetChildrenやpickle用の関数も上書きする
    DATA_PATH='.\\raw_data\\'
    currentSignal=pyqtSignal(list)
    def __init__(self,name='root',children=None):
        super().__init__(parent=None,name=name,children=children)
        self.current=self
        
    def __str__(self,unfold=True):
        return super().__str__(level=0,current=self.current,unfold=unfold)
        
    
    def __reduce_ex__(self, proto):
        #pickleのためのメソッド 動的にインスタンス変数を追加するクラスはそのままpickleできない
        return transformMyRootTreeRaw,(transformMyTree(self),self.current.ascend(),self.get_dependencies())
    
    def getChildren(self):
        #子供を{'名前':参照}で返す self.currentも子供以外の要素に加わったのでオーバーライド
        children={k:v for k,v in self.__dict__.items() if not (k=='parent' or k=='name' or k=='current')}
        return children 
        
    def add_this(self,path,label,ref,signal=False):
        #フルパスでの追加 path:['root',...] label:フォルダ名またはデータ名 ref:参照
        target=self
        for index,child in enumerate(path):
            if index>0:
                target=target.__dict__[child]
        target.add(ref,label=label,signal=signal)
            
    def dele_this(self,path,label,signal=False):
        #フルパスでの消去 path:['root',...]  label:フォルダ名またはデータ名
        target=self
        for index,child in enumerate(path):
            if index>0:
                target=target.__dict__[child]
        return target.pop(label,signal=signal)
        
    def rename_this(self,full_label,newname,signal=False):
        if full_label==['root']: #rootのrename
            self.name=newname
            return True
        elif len(full_label)>1:
            prename=full_label[-1]
            folder=self.get_this(full_label[:-1])
            return folder.rename(prename,newname,signal=signal)
        else:
            raise Exception('Canot rename')
            
    def setCurrent(self,full_label):
        self.current=self.get_this(full_label)
        self.currentSignal.emit([self.current])
        
    def setCurrentDirectly(self,mytree):
        if isinstance(mytree,MyTree):
            self.current=mytree
            self.currentSignal.emit([self.current])
        else:
            raise Exception('the current folder must be a MyTree')

    def get_this(self,full_label):
        #full_labelで指定されたrefを返す
        start=self
        for index,label in enumerate(full_label):
            if index>0:
                start=start.__dict__[label]
        return start
    
    def get_dependencies(self):
        from pkg_resources import get_distribution
        children=self.runAll()
        dependencies={}
        for child in children:
            try:
                m_name=child.__module__.split('.',1)[0]
                version=get_distribution(m_name).version
                dependencies[m_name]=version
            except:
                pass
        return dependencies
        
if __name__=='__main__':
    import sys
    import numpy as np
    import pandas as pd
    import sympy
    from coatl.Graph import MyGraphWindow
    app = QApplication([])
    g=MyGraphWindow()
    n=np.array([1,2,3])
    s=pd.Series()
    a=1
    b=[1,2,3]
    sym=sympy.Symbol('')
    mytree=MyRootTree()
    mytree.add(g)
    mytree.add(n)
    mytree.add(s)
    mytree.add(a)
    mytree.add(b)
    mytree.add(sym)
    print(mytree)
    print(mytree.get_dependencies())
    sys.exit(app.exec_())