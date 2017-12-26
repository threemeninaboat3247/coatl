# -*- coding: utf-8 -*-
"""
Created on Sat Jan 21 02:40:20 2017

@author: Yuki
"""

import sys
import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import minimize
from coatl.Graph import MyGraphWindow

##############################################
#differential
##############################################

def differentiate(xs,ys,number=2):
    '''Neumerical diffferentiation by the linear regression.'''
    import numpy as np
    xs=np.array(xs)
    ys=np.array(ys)
    array=np.c_[xs,ys]
    array=array[array[:,0].argsort()] #xの昇順に並べ替え
    
    sort_xs=array[:,0]
    sort_ys=array[:,1]
    
    def least_square(sort_xs,sort_ys):
        #translate the coordinate system to avoid a cancellation of digits.
        n=len(sort_xs)
        xoffset=sort_xs[0]*np.ones(n)
        yoffset=sort_ys[0]*np.ones(n)
        sort_xs=sort_xs-xoffset
        sort_ys=sort_ys-yoffset

        x_ave=sort_xs.sum()/n
        y_ave=sort_ys.sum()/n
        xy_ave=np.dot(sort_xs,sort_ys)/n
        xx_ave=np.dot(sort_xs,sort_xs)/n

        a=(xy_ave-x_ave*y_ave)/(xx_ave-x_ave**2)
        #b=y_ave-a*x_ave
        #b=b+yoffset+a*xoffset #inverse to the original coordinate system
        return a
    
    df=np.ones(len(sort_xs))
    
    #左端number個の点は左側の点が不足するので処理を分ける
    for i in range(0,number):
        nearestx=sort_xs[0:i+number+1]
        nearesty=sort_ys[0:i+number+1]
        df[i]=least_square(nearestx,nearesty)
            
    for i in range(number,len(sort_xs)-number):
        nearestx=sort_xs[i-number:i+number+1]
        nearesty=sort_ys[i-number:i+number+1]
        df[i]=least_square(nearestx,nearesty)
        
    #右端number個の点は右側の点が不足するので処理を分ける
    for i in range(len(sort_xs)-number,len(sort_xs)):
        nearestx=sort_xs[i-number:]
        nearesty=sort_ys[i-number:]
        df[i]=least_square(nearestx,nearesty)
    
    return {'df':df,'sorted_xs':sort_xs,'sorted_ys':sort_ys}

##########################################################
#x,y方向にerrorが存在する場合の最小自乗法によるフィッティング関係
##########################################################    
class MyFitting():
    @classmethod
    def fit(cls,x,y,func,xlist,init_values,x_e=None,y_e=None):
        '''データ点にたいして指定された関数でfittingを行う グラフにデータ点とfitting結果をplotして結果をreturn'''
        #x,y:list
        #func:関数(params,x) params:関数パラメータ x:引数
        #xlist:定義域 list
        #init_values:関数パラメータの初期値
        #x_e,y_e標準偏差のlist
        if (x_e==None) or (y_e==None): #標準偏差が指定されない場合は全て同じ重みで計算
            print('use scipy.optimize.curve_fit')
        else:
            #MyDeviationPointsを作成
            points=[MyPoint(x,y) for x,y in zip(x,y)]
            dev_points=MyDeviationPoints(points,x_e,y_e)
            
            def handleFunc(params): #minimizeで最小化するべき評価値を返す
                ylist=[func(params,x) for x in xlist]
                points=[MyPoint(x,y) for x,y in zip(xlist,ylist)]
                curve=MyCurve(points)
                return dev_points.value(curve)
                
            result=minimize(handleFunc,init_values,method="nelder-mead")
            params_result=result.x
            
            def func_result(x): #fitting結果の関数
                return func(params_result,x)
                
            g=MyGraphWindow()
            g.plot(xlist,[func_result(x) for x in xlist])
            ax=g.fig.get_axes()[0]
            ax.errorbar(x,y,xerr=x_e,yerr=y_e,fmt='ro',markersize=4,ecolor='g')
            return {'params result':params_result,'function result':func_result,'graph':g}

class MyDeviationPoints():
    '''標準偏差付きのデータ点を保持するクラス'''
    def __init__(self,points,xerrors,yerrors):
        '''points:list of MyPoint ,xerrors:list,yerrors:list'''
        self.points=points
        self.xerrors=xerrors
        self.yerrors=yerrors
        self.weights=[1/(xerror**2+yerror**2) for xerror,yerror in zip(self.xerrors,self.yerrors)]
    
    @classmethod
    def distance(cls,point,curve):
        '''点とカーブを与えるとその距離を返す'''
        return curve.distance(point)
        
    def value(self,curve):
        '''カーブを与えると評価値を返す'''
        value=0.0
        for mypoint,weight in zip(self.points,self.weights):
            d=self.distance(mypoint,curve)
            value=value+weight*(d**2)
        return value    

class MyPoint():
    '''2Dの点を表すクラス'''
    def __init__(self,x,y):
        self.x=x
        self.y=y

    def distance(self,point):
        '''他点を与えるとそれとの距離を返す'''
        start=np.array([self.x,self.y])
        end=np.array([point.x,point.y])
        d=np.linalg.norm(end-start)
        return d
        
class MyCurve():
    '''曲線を表すクラス'''
    def __init__(self,points):
        self.points=points
        
    def distance(self,point):
        '''点を与えるとそれとの距離を返す　曲線が有限個の点で表現されていることに注意'''
        d=float('inf')
        for mypoint in self.points:
            temp=mypoint.distance(point)
            if temp<d:
                d=temp
        return d

