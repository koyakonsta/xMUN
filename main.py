import sys
from MUNApp import *
import io
from functools import partial

#(c) Konstantin O'Donnell-Dragović 2022

if __name__ == '__main__':

    munApp = QtWidgets.QApplication([sys.argv])
    munApp.setWindowIcon(QtGui.QIcon('logo.png')) #set logo
    munApp.setStyleSheet('QLineEdit{ width:0px; height:0px; border: 0px}') #make qlineedits invisible

    window = QtWidgets.QWidget()

    window.setFocus(); window.setWindowTitle("xMUN Debate Manager 0.9.9"); window.setGeometry(0,0,1920, 1080)

    Logo = QtWidgets.QLabel() #Labels beside editable committee names and topic, and 'present'
    CommitteeName, Topic = [QtWidgets.QLineEdit() for i in [...]*2] #editable invisible fields
    CommitteeNameText, TopicText = (open(r'headertext.txt','r').read().split('\n')[:2] + ['']*3)[:2] #read committee, topic info from previous session
    Logo.setPixmap(QtGui.QPixmap('logo.png').scaled(128,128)) #set logo

    CommitteeNameLabel=lLabel(CommitteeName, CommitteeNameText, '<h1><b>Committee: </b></h1><h2>')
    TopicLabel=lLabel(Topic, TopicText, '<h1><b>Topic: </b></h1><h2>')




    newcommittee=newCommittee(0,0)
    rollcall=rollCall(0,0)
    Present=PresentLabel('<h1>Present: ', newcommittee, rollcall)
    Present.updateRatio()
    newcommittee.__init__(rollcall, Present)
    rollcall.__init__(newcommittee, Present)
    GSL = generalSpeakersList(newcommittee)
    MC=caucusBase(0, newcommittee)
    UMC=caucusBase(1, newcommittee)

    superlayout=QtWidgets.QVBoxLayout(window)
    statuslayout=QtWidgets.QHBoxLayout(window); superlayout.addLayout(statuslayout, 0)
    statuslayout.addWidget(Logo, 1)
    statuslayout.addWidget(CommitteeNameLabel, 2); statuslayout.addWidget(CommitteeName, 2)
    statuslayout.addWidget(TopicLabel, 2); statuslayout.addWidget(Topic, 2)
    statuslayout.addWidget(Present, 2)

    maintab=QtWidgets.QTabWidget(); superlayout.addWidget(maintab, 1)

    maintab.currentChanged.connect(GSL.updateDGL)
    maintab.currentChanged.connect(MC.updateDGL)

    pv = proceduralVoting(newcommittee)



    maintab.addTab(newcommittee,'New Committee')
    maintab.addTab(rollcall, 'Roll call')
    # maintab.addTab(QtWidgets.QLabel('<h1><b><i><center> Not yet implemented'), 'Opening Speeches')
    maintab.addTab(GSL, "General Speakers' List")
    maintab.addTab(MC, 'Moderated Caucus')
    maintab.addTab(UMC, 'Unmoderated Caucus')
    maintab.addTab(pv, 'Procedural Voting')








    #CommitteeName.setText(CommitteeNameText)
    Topic.setText(TopicText)

    window.show()

    while 1:

        _=munApp.exec()
        open(r'headertext.txt', 'w').writelines([CommitteeNameLabel.lEditName.text(), '\n', TopicLabel.lEditName.text()])
        sys.exit(_)





