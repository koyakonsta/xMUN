from PyQt5 import QtCore, QtWidgets, QtGui
import requests as r
from functools import partial
import os
import time
import io

# (c) Konstantin O'Donnell-Dragović, 2022

## reads up-to-date country names if connected, else read saved list
if not os.system('ping pkgstore.datahub.io'):
    countryNames=[i.decode() for i in r.get(r'https://pkgstore.datahub.io/core/country-list/data_csv/data/d7c9d7cfb42cb69f4422dec222dbbaa8/data_csv.csv').content.splitlines()][1:]
else:
    countryNames=open(r'data.csv', 'r', encoding='utf-8').read().splitlines()[1:]
flagMode = os.system('ping countryflagsapi.com') #determines method to use to retrieve flags: from cfAPI if 0 (online) else from local store

class proceduralVoting(QtWidgets.QWidget):
        def __init__(self, dgListObj=0):
            super().__init__()
            self.dgListObj=dgListObj

            self.votingtopic=QtWidgets.QLabel('')
            self.hlayout = QtWidgets.QHBoxLayout(self)
            self.lvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.lvlayout, 1)
            self.rvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.rvlayout, 1)
            self.topic_speakerLayout = QtWidgets.QGridLayout(); self.rvlayout.addLayout(self.topic_speakerLayout)
            self.speakerProgress = QtWidgets.QProgressBar()
            self.votingon = QtWidgets.QLabel('Voting on: ')

            self.votingcombo = QtWidgets.QComboBox();
            self.votingcombo.addItems(
                ['Agenda', 'Closure of Debate', 'Postponement of Debate', 'Resumption of Debate', 'Amendment',
                 'Division of the Question', 'Reconsideration', 'Resolution', 'Other']);
            self.votingcombo.currentTextChanged.connect(self.changeTopic);

            self.speakermSpinbox = QtWidgets.QSpinBox(); self.speakermSpinbox.setMaximum(60)
            self.speakersSpinbox=QtWidgets.QSpinBox(); self.speakersSpinbox.setMaximum(60)
            self.setspeakertime=QtWidgets.QLabel('Set speaker time: ')
            self.speakermSpinbox.valueChanged.connect(self.timeChanged);
            self.speakersSpinbox.valueChanged.connect(self.timeChanged);

            self.countryFlag=QtWidgets.QLabel()
            self.countryName=QtWidgets.QLabel('')
            self.progressLabel=QtWidgets.QLabel()
            self.votingresult = QtWidgets.QLabel()
            self.side = QtWidgets.QLabel()
            self.sB = QtWidgets.QPushButton('Stop'); self.sB.adjustSize()
            self.sB.clicked.connect(self.stopTimer)
            self.topic_speakerLayout.addWidget(self.votingon,0,0);self.topic_speakerLayout.addWidget(self.votingcombo,0,1,1,2);
            self.topic_speakerLayout.addWidget(self.setspeakertime,1,0);
            self.topic_speakerLayout.addWidget(self.speakermSpinbox,1,1);self.topic_speakerLayout.addWidget(self.speakersSpinbox,1,2);

            for w in [self.votingtopic, self.side, self.countryFlag, self.countryName, self.speakerProgress, self.progressLabel, self.sB]:
                self.lvlayout.addWidget(w, 1)

            class votingBox(QtWidgets.QListWidget):
                def __init__(self, title : str, dgListObj=0, countervoteObj=0):
                    super().__init__()

                    self.title = title
                    self.dgListObj=dgListObj
                    self.countervoteObj = countervoteObj
                    self.vlayout = QtWidgets.QVBoxLayout(self)
                    self.box = QtWidgets.QGroupBox(title); self.box.setLayout(self.vlayout)
                    self.hlayout = QtWidgets.QHBoxLayout();
                    self.dgcombo = QtWidgets.QComboBox();
                    if self.dgListObj!=0:
                        self.dgcombo.addItems(self.dgListObj.delegateList)
                        self.dgListObj.delegateCombo.currentTextChanged.connect(self.updateDGL)
                        self.dgListObj.delegateCombo.currentTextChanged.connect(self.updateDGL)
                    self.dgcombo.currentTextChanged.connect(self.addDelegate)
                    self.dglist = QtWidgets.QListWidget();
                    self.delButton = QtWidgets.QPushButton('Delete'); self.delButton.clicked.connect(self.delDelegate)
                    self.clrButton = QtWidgets.QPushButton('Clear'); self.clrButton.clicked.connect(self.dglist.clear)
                    for w in [self.delButton, self.clrButton]: self.hlayout.addWidget(w)
                    for w in [self.dgcombo, self.dglist]: self.vlayout.addWidget(w)
                    self.vlayout.addLayout(self.hlayout)
                def delDelegate(self): self.dglist.takeItem(self.dglist.currentRow())
                def updateDGL(self):
                    self.dgcombo.clear()
                    self.dgcombo.addItems(self.dgListObj.delegateList)
                    self.dglist.clear()
                def addDelegate(self, event):
                    if (not self.dglist.findItems(event, QtCore.Qt.MatchExactly)) and (not self.countervoteObj.dglist.findItems(event, QtCore.Qt.MatchExactly)):
                        self.dglist.addItem(event)
            self.infavour = votingBox('')
            self.against = votingBox('')
            self.infavour.__init__('In Favour', self.dgListObj, self.against)
            self.against.__init__('Against', self.dgListObj, self.infavour)
            self.infavour.dglist.itemDoubleClicked.connect(self.startTimer)
            self.against.dglist.itemDoubleClicked.connect(self.startTimer)

            self.rvlayout.addWidget(self.infavour.box)
            self.rvlayout.addWidget(self.against.box)

            self.on=False
            self.timelimit=0
            self.timer=QtCore.QTimer(self)
            self.timer.timeout.connect(self.timer_tick)

        def timeChanged(self, event):
            self.timelimit=self.speakermSpinbox.value()*60 + self.speakersSpinbox.value()
            self.speakerProgress.setMaximum(self.timelimit)
        def updateDGL(self, event):
            self.votingcombo.clear()
            self.votingcombo.addItems(self.dgListObj.delegateList)
        def changeTopic(self, event): self.votingtopic.setText('<center><h1><i>'+event)
        def startTimer(self, event):
            self.on=True
            self.countryName.setText('<h2>' + event.text())

            self.timeelapsed=0
            self.speakerProgress.setFormat('\n%vs / {}s'.format(self.timelimit))
            self.timer.start(1000)

            if flagMode:
                p=QtGui.QPixmap(r'flags\{}.png'.format(event.text().split(',')[-1])).scaledToHeight(180, QtCore.Qt.SmoothTransformation)
            else:
                (p:=QtGui.QPixmap().scaledToHeight(180, QtCore.Qt.SmoothTransformation)).loadFromData( r.get(r'http://countryflagsapi.com/png/%s'%event.text().split(',')[-1]).content)
            self.countryFlag.setPixmap(p)
        def timer_tick(self):
            if (self.timeelapsed < self.timelimit):
                if self.on:
                    self.timeelapsed+=1
                    self.setprogress(self.timeelapsed)
                    self.progressLabel.setText('<h1><center>%d:%d/%d:%d'%(
                    self.timeelapsed//60, self.timeelapsed%60, self.timelimit//60, self.timelimit%60))
            else:
                self.stopTimer(...)
        def setprogress(self, value):
            self.speakerProgress.setValue(value)
            self.progressLabel.setText('<h1><center>%d:%d/%d:%d'%(self.timeelapsed//60, self.timeelapsed%60, self.speakermSpinbox.value(), self.speakersSpinbox.value()))
        def stopTimer(self, event):
            if self.on: self.timer.stop()
            self.setprogress(0)
            self.countryName.setText('')
            self.countryFlag.setPixmap(QtGui.QPixmap(r'flags\ZZ.png'))
            self.on=False

class caucusBase(QtWidgets.QWidget):
    def __init__(self, mode : bool, dgListObj):
        super().__init__()
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.dgListObj = dgListObj
        self.mode      = True if mode else False
        self.SAMClabel = QtWidgets.QLabel('<center><b>Start a new %smoderated caucus' % (self.mode*'un'))
        self.SAMClabel.setAlignment(QtCore.Qt.AlignTop)
        self.hlayout   = QtWidgets.QHBoxLayout(self) #overall horizontal layout of widgets
        self.lvlayout  = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.lvlayout, 1) #overall vertical layout of left widgets
        self.rvlayout  = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.rvlayout, 1) #overall vertical layout of right widgets
        self.durationLayout = QtWidgets.QHBoxLayout() #overall horizontal layout of right widgets
        self.durationLayout.setAlignment(QtCore.Qt.AlignTop)
        self.durationlabel = QtWidgets.QLabel('Duration: ')
        self.durationhSpinbox = QtWidgets.QSpinBox(); self.durationmSpinbox = QtWidgets.QSpinBox(); self.durationsSpinbox = QtWidgets.QSpinBox();
        self.durationLayout.addWidget(self.durationlabel, 1)
        for w in [self.durationhSpinbox, self.durationmSpinbox, self.durationsSpinbox]:
            self.durationLayout.addWidget(w, 1)
            w.valueChanged.connect(self.caucustimeChanged)

        self.rvlayout.addWidget(self.SAMClabel, 0)
        self.rvlayout.addLayout(self.durationLayout, 0)
        #===============#
        self.topicledit = QtWidgets.QLineEdit()
        self.topiclabel = lLabel(self.topicledit, '', 'Topic: ')
        self.topic = lLabel(self.topicledit, '', '<h2><center>')
        self.rvlayout.addWidget(self.topiclabel, self.mode); self.rvlayout.addWidget(self.topicledit,0);
        self.topiclabel.setAlignment(QtCore.Qt.AlignTop)
        ##
        self.caucustimelimit = 0
        self.caucusProgress = QtWidgets.QProgressBar(); self.caucusProgress.setMinimum(0); self.caucusProgress.setMaximum(self.caucustimelimit)
        self.caucusProgress.setAlignment(QtCore.Qt.AlignCenter); self.caucusProgress.setValue(0)
        self.caucusProgressLabel = QtWidgets.QLabel('')
        self.caucusProgress.setFormat('\n%vs / {}s'.format(self.caucustimelimit))
        self.caucustimer = QtCore.QTimer(self)
        self.caucustimer.timeout.connect(self.caucus_timer_tick)
        self.lsmallhlayout=QtWidgets.QHBoxLayout();
        ##
        self.countryName=QtWidgets.QLabel();
        self.countryName.setAlignment(QtCore.Qt.AlignCenter)
        self.countryFlag=QtWidgets.QLabel();
        self.countryFlag.setAlignment(QtCore.Qt.AlignCenter)
        self.countryFlag.setPixmap(QtGui.QPixmap(r'\flags\ZZ.png'))
        ##
        self.lvlayout.addWidget(self.countryFlag, 4); self.lvlayout.addWidget(self.countryName, 0);
        self.lvlayout.addWidget(self.topic, 1)
        self.rB, self.pB, self.sB = [QtWidgets.QPushButton(i) for i in ['Resume', 'Pause', 'Stop']]
        for i in [self.rB, self.pB, self.sB]: self.lsmallhlayout.addWidget(i)
        self.sB.clicked.connect(self.stopTimers)
        self.rB.clicked.connect(self.resumeTimers)
        self.pB.clicked.connect(self.pauseTimers)


        if not self.mode:
            self.speakerPrompt = QtWidgets.QLabel('Set speaker time: ')
            self.speakermSpinbox = QtWidgets.QSpinBox(); self.speakersSpinbox = QtWidgets.QSpinBox();
            self.speakertimer = QtCore.QTimer(self)
            self.speakertimelimit=0
            self.speakertimer.timeout.connect(self.speaker_timer_tick)
            self.speakerList = QtWidgets.QListWidget()
            self.speakerList.itemDoubleClicked.connect(self.startTimers)
            self.speakerLayout = QtWidgets.QHBoxLayout();
            self.speakerProgress=QtWidgets.QProgressBar(); self.speakerProgress.setMinimum(0); self.speakerProgress.setMaximum(self.speakertimelimit)
            self.speakerProgress.setAlignment(QtCore.Qt.AlignCenter); self.speakerProgress.setValue(0)
            self.speakerProgressLabel=QtWidgets.QLabel('')
            self.speakerProgress.setFormat('\n%vs / {}s'.format(self.speakertimelimit))
            self.speakerLayout.addWidget(self.speakerPrompt)
            for w in [self.speakermSpinbox, self.speakersSpinbox]: self.speakerLayout.addWidget(w); w.valueChanged.connect(self.speakertimeChanged)
            self.rvlayout.addLayout(self.speakerLayout, 0)
            self.rvlayout.addWidget(self.speakerList, 1); self.speakerList.addItems(self.dgListObj.delegateList)
            self.lvlayout.addWidget(self.speakerProgress, 1)
            self.lvlayout.addWidget(self.speakerProgressLabel,1)
        self.startB=QtWidgets.QPushButton('Start');
        self.startB.clicked.connect(self.startTimers)
        self.rvlayout.addWidget(self.startB, 0)

        self.lvlayout.addWidget(self.caucusProgress, 1)
        self.lvlayout.addWidget(self.caucusProgressLabel, 1)
        self.lvlayout.addLayout(self.lsmallhlayout, 0)

        self.on = False
        self.speakertimeelapsed = 0
        self.caucustimeelapsed = 0

    def updateDGL(self, event):
        if not self.mode:
            self.speakerList.clear()
            self.speakerList.addItems(self.dgListObj.delegateList)
    def caucustimeChanged(self, event):
        self.caucustimelimit = self.durationhSpinbox.value()*3600+self.durationmSpinbox.value()*60+self.durationsSpinbox.value()
        self.caucusProgress.setMaximum(self.caucustimelimit)
    def speakertimeChanged(self, event):
        self.speakertimelimit = self.speakermSpinbox.value()*60+self.speakersSpinbox.value()
        self.speakerProgress.setMaximum(self.speakertimelimit)
    def pauseTimers(self): self.on = False
    def resumeTimers(self): self.on = True
    def startTimers(self, event=...):
        self.caucusProgress.setFormat('\n%vs / {}s'.format(self.caucustimelimit))
        if hasattr(event, 'text'): #only set up flag & speakerprogress if activated from delegates list, otherwise started w/ 'start' button
            if event == '': return
            self.speakertimeelapsed=0
            self.speakerProgress.setFormat('\n%vs / {}s'.format(self.speakertimelimit))
            self.countryName.setText('<h2>' + event.text())
            self.speakertimer.start(1000)
            if flagMode:
                p=QtGui.QPixmap(r'flags\{}.png'.format(event.text().split(',')[-1])).scaledToHeight(180, QtCore.Qt.SmoothTransformation)
            else:
                (p:=QtGui.QPixmap().scaledToHeight(180, QtCore.Qt.SmoothTransformation)).loadFromData(r.get(r'http://countryflagsapi.com/png/%s'%event.text().split(',')[-1]).content)
        else:
            p=QtGui.QPixmap()
        self.on = True

        if self.caucusProgress.value()==0:
            self.caucustimeelapsed = 0
            self.caucustimer.start(1000)


        self.countryFlag.setPixmap(p)

    def caucus_timer_tick(self):
        if (self.caucustimeelapsed < self.caucustimelimit):
            if self.on:
                self.caucustimeelapsed+=1
                self.setcaucusprogress(self.caucustimeelapsed)
        else:
            self.stopTimers(...)
            self.caucusProgress.setValue(0)
    def speaker_timer_tick(self):
        if (self.speakertimeelapsed < self.speakertimelimit):
            if self.on:
                self.speakertimeelapsed+=1
                self.setspeakerprogress(self.speakertimeelapsed)
        else:
            self.stopspeakerTimer(...)
            self.speakerProgress.setValue(0)
    def setspeakerprogress(self, value):
        self.speakerProgress.setValue(value)
        elapsed = self.speakertimeelapsed//60, self.speakertimeelapsed%60
        self.speakerProgressLabel.setText('<h1><center>%d:%d/%d:%d'%(*elapsed, self.speakermSpinbox.value(), self.speakersSpinbox.value()))
    def setcaucusprogress(self, value):
        self.caucusProgress.setValue(value)
        elapsed = self.caucustimeelapsed//3600, (self.caucustimeelapsed%3600)//60, self.caucustimeelapsed%60
        self.caucusProgressLabel.setText('<h1><center>%d:%d:%d/%d:%d:%d'%(*elapsed, self.durationhSpinbox.value(), self.durationmSpinbox.value(), self.durationsSpinbox.value()))
    def stopspeakerTimer(self, event): self.speakertimer.stop()
    def stopcaucusTimer(self, event):
        self.caucustimer.stop();
        if not self.mode:
            self.speakertimer.stop()

    def stopTimers(self, event):
        if self.on:
            self.caucustimer.stop()
            if not self.mode: self.speakertimer.stop()
        if not self.mode: self.setspeakerprogress(0)
        self.setcaucusprogress(0);
        self.countryName.setText('')
        self.countryFlag.setPixmap(QtGui.QPixmap(r'flags\ZZ.png'))
        self.on = False

class generalSpeakersList(QtWidgets.QWidget):
    def __init__(self, dgListObj):
        super().__init__()

        self.dgListObj=dgListObj

        self.hlayout = QtWidgets.QHBoxLayout(self)
        self.rsmallhlayout = QtWidgets.QHBoxLayout()
        self.lsmallhlayout = QtWidgets.QHBoxLayout()
        self.hSpinbox = QtWidgets.QSpinBox(); self.sSpinbox = QtWidgets.QSpinBox()
        self.lvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.lvlayout)
        self.rvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.rvlayout)
        self.countryName = QtWidgets.QLabel(); self.countryName.setAlignment(QtCore.Qt.AlignCenter)
        self.countryFlag = QtWidgets.QLabel(); self.countryFlag.setAlignment(QtCore.Qt.AlignCenter)
        self.countryFlag.setPixmap(QtGui.QPixmap(r'\flags\ZZ.png'))
        self.progressBar = QtWidgets.QProgressBar(self); self.progressBar.setMinimum(0)
        self.progressLabel = QtWidgets.QLabel('')
        self.speakerTimePrompt = QtWidgets.QLabel("Set speaker time: ")
        self.countryCombo = QtWidgets.QComboBox(); self.countryCombo.addItems(self.dgListObj.delegateList)
        self.speakerList = QtWidgets.QListWidget()
        self.cB, self.yB, self.nB, self.rB, self.pB, self.sB = [QtWidgets.QPushButton(i) for i in ['Clear','Yield OFF','Next Spk.','Resume','Pause','Stop']]
        self.addAllB = QtWidgets.QPushButton('Add all Delegates')
        self.addAllB.clicked.connect(self.addSpeakers)
        self.lvlayout.addWidget(self.countryFlag, 4); self.lvlayout.addWidget(self.countryName, 1);
        self.lvlayout.addWidget(self.progressBar,1); self.lvlayout.addWidget(self.progressLabel,1)
        self.rvlayout.addLayout(self.rsmallhlayout, 0)
        self.lvlayout.addLayout(self.lsmallhlayout, 0)
        for w in [self.yB, self.nB, self.rB, self.pB, self.sB]: self.lsmallhlayout.addWidget(w)
        for w in [self.speakerTimePrompt, self.hSpinbox, self.sSpinbox]: self.rsmallhlayout.addWidget(w)
        for w in [self.countryCombo, self.speakerList, self.cB, self.addAllB]: self.rvlayout.addWidget(w)
        #==================================#
        self.current = ''
        self.timelimit = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timer_tick)
        # ==================================#
        self.countryCombo.currentTextChanged.connect(self.addSpeaker)
        self.cB.clicked.connect(self.speakerList.clear)
        self.hSpinbox.valueChanged.connect(self.timeChanged); self.sSpinbox.valueChanged.connect(self.timeChanged);
        self.speakerList.itemDoubleClicked.connect(self.startTimer)
        self.nB.clicked.connect( self.nextSpeaker )
        self.sB.clicked.connect(self.stopTimer)
        self.pB.clicked.connect(self.pauseTimer)
        self.rB.clicked.connect(self.resumeTimer)
        self.rB.clicked.connect(partial(self.pB.setEnabled, 1)); #when resume but. pressed, pause button should reenable
        self.sB.clicked.connect(partial(self.pB.setEnabled, 1)); #when stop button pressed, pause button should reenable
        self.pB.clicked.connect(self.pB.setEnabled)

        self.yB.clicked.connect(self.yieldToggle)
        self.yieldMode = 0
        self.on = False
    def yieldToggle(self, event):
        self.yieldMode^=1
        self.yB.setText('Yield %s' % ('ON' if self.yieldMode else 'OFF'))
    def addSpeaker(self, event):
        if not self.speakerList.findItems(event, QtCore.Qt.MatchExactly):
            self.speakerList.addItem(event)
    def addSpeakers(self, event):
        for i in self.dgListObj.delegateList:
            if not self.speakerList.findItems(i, QtCore.Qt.MatchExactly):
                self.speakerList.addItem(i)
    def updateDGL(self, event):
        self.countryCombo.clear()
        self.countryCombo.addItems(self.dgListObj.delegateList)
        self.speakerList.clear()
    def nextSpeaker(self):
        self.startTimer(self.speakerList.item(0))
    def timeChanged(self, event):
        self.timelimit = self.hSpinbox.value()*60+self.sSpinbox.value()
        self.progressBar.setMaximum(self.timelimit)
    def pauseTimer(self): self.on = False
    def resumeTimer(self): self.on = True
    def startTimer(self, event):
        self.on = True
        if not hasattr(event, 'text'): return
        self.countryName.setText('<h2>'+event.text())
        if not self.yieldMode:
            self.timeelapsed = 0
            self.progressBar.setFormat('\n%vs / {}s'.format(self.timelimit))
            self.timer.start(1000)
            self.speakerList.takeItem(self.speakerList.row(event))
        else: self.yieldToggle(...)
        if flagMode:
            p=QtGui.QPixmap(r'flags\{}.png'.format(event.text().split(',')[-1])).scaledToHeight(180, QtCore.Qt.SmoothTransformation)
        else:
            (p:=QtGui.QPixmap().scaledToHeight(180, QtCore.Qt.SmoothTransformation)).loadFromData(r.get(r'http://countryflagsapi.com/png/%s'%event.text().split(',')[-1]).content)
        self.countryFlag.setPixmap(p)
    def continueTimer(self): ...
    def timer_tick(self):
        if (self.timeelapsed < self.timelimit):
            if self.on:
                self.timeelapsed+=1
                self.setprogress(self.timeelapsed)
                self.progressLabel.setText('<h1><center>%d:%d/%d:%d' % (self.timeelapsed//60,self.timeelapsed%60, self.timelimit//60,self.timelimit%60) )
        else:
            self.stopTimer(...)
    def setprogress(self, value):
        self.progressBar.setValue(value)
    def stopTimer(self, event):
        if self.on: self.timer.stop()
        self.setprogress(0)
        self.countryName.setText('')
        self.countryFlag.setPixmap(QtGui.QPixmap(r'flags\ZZ.png'))
        self.on = False

class lLabel(QtWidgets.QLabel):  # dynamic editable label class, using proxy invisible qlineedit for entry
    def __init__(self, lEditName, LabelText,Heading):  # pass in associated lineedit to connect with, previous session text and intended lLabel Heading
        super().__init__()
        self.lEditName=lEditName
        self.LabelText=LabelText
        self.Heading=Heading
        self.lEditName.setText(self.LabelText)
        self.lEditName.textEdited.connect(self.mousePressEvent)
        self.setText(self.Heading + self.lEditName.text())

    def mousePressEvent(self, event):
        self.lEditName.setFocus()
        self.setText(self.Heading + self.lEditName.text())

class PresentLabel(QtWidgets.QLabel): #dynamically updating present label
    def __init__(self, header, dgListObj, rollCallObj):
        super().__init__()
        self.header = header
        self.dgListObj = dgListObj
        self.rollCallObj = rollCallObj
        self.numDelegates = len(dgListObj.delegateList)
        self.numPresent = rollCallObj.votes.count('P')+rollCallObj.votes.count('PV')
        self.setText(self.header +'\n{}/{}</h1><h2>(1/2 = {}; 2/3={})'.format(self.numPresent, self.numDelegates, round(self.numPresent/2),round(2*self.numPresent/3)))
    def updateRatio(self):
        self.numDelegates=len(self.dgListObj.delegateList)
        self.numPresent=self.rollCallObj.votes.count('P') + self.rollCallObj.votes.count('PV')
        self.setText(self.header +'\n{}/{}</h1><h2>(1/2 = {}; 2/3={})'.format(self.numPresent, self.numDelegates, round(self.numPresent/2),round(2*self.numPresent/3)))

class newCommittee(QtWidgets.QWidget):
    def __init__(self, rollCallObj=0, presentLabelObj=...):
        super().__init__()
        self.rollCallObj=rollCallObj
        self.presentLabelObj = presentLabelObj
        self.hlayout = QtWidgets.QHBoxLayout(self) #overall horiz. layout separating delegates combo box from list and clear button
        self.lvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.lvlayout) #left vbox for delegates label and combo box
        self.rvlayout = QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.rvlayout) #right vbox for delegates list and clear button
        self.lvlayout.addWidget(QtWidgets.QLabel('<h2>New Committee: '),0)
        self.delegateCombo = QtWidgets.QComboBox(); self.delegateCombo.addItems(countryNames)
        self.resetButton=QtWidgets.QPushButton('Reset')
        self.delegateCombo.currentTextChanged.connect(self.addDelegate)
        if self.rollCallObj!=0:
            try:
                self.delegateCombo.currentTextChanged.connect(self.rollCallObj.updateDelegateList)
                self.resetButton.clicked.connect(self.rollCallObj.updateDelegateList)
            except: ...
        self.resetButton.clicked.connect(self.resetDelegates)
        self.lvlayout.addWidget(self.delegateCombo,100)
        self.delegateList = []
        self.delegateDisplay = QtWidgets.QLabel('')
        self.rvlayout.addWidget(self.delegateDisplay)
        self.rvlayout.addWidget(self.resetButton)
        self.resetButton.clicked.connect(self.resetDelegates)
    def addDelegate(self, dgName):
        if dgName not in self.delegateList:
            self.delegateList = sorted(self.delegateList+[dgName])
            i=self.delegateList.index(dgName)
            if i<len(self.delegateList):
                self.rollCallObj.delegateList.insertItem(i, dgName)
                self.rollCallObj.votes.insert(i, '?')
                self.rollCallObj.votingList.insertItem(i, '?')
            else:
                self.rollCallObj.delegateList.insertItem(-1, dgName)
                self.rollCallObj.votes.insert(-1, '?')
                self.rollCallObj.votingList.insertItem(-1, '?')
        self.delegateDisplay.setText('\n'.join([', '.join(i.split(',')[:-1]) for i in self.delegateList]))
        #####################
        if self.presentLabelObj != ...:
            try: self.presentLabelObj.updateRatio()
            except: ...
    def resetDelegates(self):
        self.delegateList = []
        self.delegateDisplay.setText('')
        self.rollCallObj.resetDelegateList()
        #####################
        if self.presentLabelObj != ...:
            try: self.presentLabelObj.updateRatio()
            except: ...

class rollCall(QtWidgets.QTabWidget):
    def __init__(self, dgListObj=0, presentLabelObj=0):
        super().__init__()

        self.dgListObj = dgListObj
        self.presentLabelObj = presentLabelObj
        self.hlayout=QtWidgets.QHBoxLayout(self)  # overall horiz. layout separating delegates list from voting list, legend and clear button
        self.lvlayout=QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.lvlayout)  # left vbox for delegates label and combo box
        self.rvlayout=QtWidgets.QVBoxLayout(); self.hlayout.addLayout(self.rvlayout)  # right vbox for delegates list and clear button
        self.resetButton=QtWidgets.QPushButton('Reset Votes')
        self.resetButton.clicked.connect(self.resetVote)

        self.lvlayout.addWidget(QtWidgets.QLabel('<h2>Delegates: '), 0)
        self.delegateList=QtWidgets.QListWidget()
        self.lvlayout.addWidget(self.delegateList)

        class votingList(QtWidgets.QListWidget):
            def __init__(self, superobj):
                super().__init__()
                self.superobj=superobj
                self.setFocusPolicy(QtCore.Qt.ClickFocus)
                self.setFocus()
            def keyPressEvent(self, event):
                if type(event) == QtGui.QKeyEvent:
                    if event.key() == QtCore.Qt.Key_P:
                        i=self.currentRow()
                        self.superobj.votes[i]='P'
                        self.superobj.listVote(i)
                    if event.key() == QtCore.Qt.Key_V:
                        i=self.currentRow()
                        self.superobj.votes[i]='PV'
                        self.superobj.listVote(i)
                    event.accept()
                else:
                    event.ignore()

        self.votes=[]

        self.votingList=votingList(self)
        self.votingList.itemDoubleClicked.connect(self.listVote)
        self.rvlayout.addWidget(QtWidgets.QLabel('<h2>Present/Voting'))
        self.rvlayout.addWidget(self.votingList)

        self.rvlayout.addWidget(self.resetButton)
        if self.dgListObj!=0:
            try:
                self.delegateList.addItems(self.dgListObj.delegateList)
            except : ...

    def resetVote(self):
        self.votes=['?']*len(self.delegateList)
        self.votingList.clear()
        self.votingList.addItems(self.votes)
        #####################
        if self.presentLabelObj!=...:
            try: self.presentLabelObj.updateRatio()
            except: ...
    def listVote(self, index):
        if type(index) != int:
            index=self.votingList.indexFromItem(index).row()
            self.votes[index]={'?':'P','P':'PV','PV':'?'}[self.votes[index]]
        self.votingList.takeItem(index)
        self.votingList.insertItem(index, self.votes[index])
        self.votingList.setFocus()
        self.votingList.setCurrentRow((index+1)%len(self.votes))
        #####################
        if self.presentLabelObj != 0:
            try: self.presentLabelObj.updateRatio()
            except: ...
    def resetDelegateList(self):
        self.delegateList.clear()
        self.votingList.clear()
        self.votes=[]
