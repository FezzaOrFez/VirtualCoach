import tkinter as tk
import os
import cv2
import json
import time
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from tkinter import font as tkfont
from dataclasses import dataclass
from functools import partial
from shutil import rmtree


import HumanPoseEstimation
import Reference
import UserTechnique
import feedbackArea
import VirtualCoachMain


chosenTechnique = ""
# quit
def QuitApp():
    quit()
global startLoad
startLoad = True
class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")
        self.title("Virtual Coach")
        self.sport = tk.StringVar()
        self.technique = tk.StringVar()
        self.imageSet = tk.IntVar()
        self.historyFile = tk.StringVar()
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback,historyGUI):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuGUI")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

    def refresh(self,page_name,container,afterWindow,historyCheck):
        frame = self.frames[page_name]
        if frame is not None:
            frame.destroy()
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback,historyGUI):
            if F.__name__ == page_name:
                frame = F(parent=container, controller=self)
                self.frames[page_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(page_name)
        if page_name == "Loading":
            frame.update()
            if afterWindow == "chooseVideoInput":
                VirtualCoachMain.main()
                self.show_frame(afterWindow)
            elif afterWindow == "presentFeedback":
                if historyCheck == False:
                    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(VirtualCoachMain.usersTechnique.frames)
                    VirtualCoachMain.usersTechnique.skeleton = HPEdImages
                    VirtualCoachMain.usersTechnique.points = pointsArray
                    VirtualCoachMain.temporalAnalysis(self.technique.get())
                    VirtualCoachMain.calculateFeedback(self.technique.get(),False,VirtualCoachMain.usersTechnique.points,self.sport.get())
                    self.refresh(afterWindow,container,"",False)
                else:
                    VirtualCoachMain.main()
                    fname = "storedFeedback"
                    fpath = fname + "\\" + self.historyFile.get() + "\\pointsData.json"
                    print(fpath)
                    with open(os.path.abspath(fpath)) as file:
                        feedbackDict = json.loads(json.load(file))

                    fpath = fname + "\\" + self.historyFile.get() + "\\skeletonsList"
                    skelList = os.listdir(os.path.abspath(fpath))
                    skelIMGList = []
                    inim = 1
                    for x in skelList:
                        skelImg = cv2.imread(os.path.abspath(fpath+ "\\" + x), 1)
                        plt.subplot(4,3,inim)
                        plt.axis("off")
                        skelImg = cv2.cvtColor(skelImg, cv2.COLOR_RGB2BGR)
                        inim+=1
                        skelIMGList.append(skelImg)

                    VirtualCoachMain.usersTechnique.skeleton = skelIMGList
                    VirtualCoachMain.usersTechnique.points = feedbackDict["points"]

                    techRecieve = self.historyFile.get()
                    techRecieve = techRecieve.split('-')
                    technique = techRecieve[0]
                    self.technique.set(technique)
                    chosenSport = ""
                    fname = "FeedbackAreas"
                    sportList = os.listdir(os.path.abspath(fname))
                    for sport in sportList:
                        techniqueList = (os.listdir(os.path.abspath(fname+"\\" + sport)))
                        if technique+".json" in techniqueList:
                            chosenSport = sport

                    self.sport.set(sport)

                    VirtualCoachMain.calculateFeedback(technique,False,VirtualCoachMain.usersTechnique.points,chosenSport)
                    self.refresh(afterWindow,container,"",False)
            
        

    
class MenuGUI(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent,width=850,height=500)
        self.pack_propagate(0)
        self.controller = controller
        label = tk.Label(self, text="Virtual Coach", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        button1 = tk.Button(self, text="Track Technique",
                            command=lambda: controller.show_frame("chooseSportGUI"))
        button2 = tk.Button(self, text="Track History",
                            command=lambda: controller.refresh("historyGUI",parent,"",False))
        button3 = tk.Button(self, text="Quit",
                            command=QuitApp)
        button1.pack()
        button2.pack()
        button3.pack()

class Loading(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent,width=850,height=500)
        self.pack_propagate(0)
        self.controller = controller
        label = tk.Label(self, text="Loading...", font=controller.title_font)
        label.pack(fill="none", expand=True)


class chooseSportGUI(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.frame = None
        label = tk.Label(self, text="Choose Sport", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        fname = "FeedbackAreas"
        sportList = os.listdir(os.path.abspath(fname))
        for sport in sportList:
            button = tk.Button(self, text=sport,
                            command=partial(self.partialButton,sport,controller,parent))
            button.pack()
        backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI"))
        backButton.pack(anchor="se")
    
    def changeSport(self, sp):
        self.controller.sport.set(sp)
    
    def partialButton(self,sport,controller,parent):
        self.changeSport(sport)
        controller.refresh("chooseTechniqueGUI",parent,"",False)
    
    

class chooseTechniqueGUI(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, textvariable=controller.sport, font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        fname = "FeedbackAreas"
        btnList = []
        try:
            techniqueList = (os.listdir(os.path.abspath(fname+"\\" + str(label["text"]))))
            for technique in techniqueList:
                technique=technique.replace(".json","")
                button = tk.Button(self, text=technique,
                                command=partial(self.setButton,technique,controller,parent))
                button.pack()
                btnList.append(button)
            backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("chooseSportGUI"))
            backButton.pack(anchor="se")
        except FileNotFoundError:
            print("")
    def changeTechnique(self, tech):
        self.controller.technique.set(tech)
    def setButton(self,technique,controller,parent):
        self.changeTechnique(technique)
        controller.refresh("Loading",parent,"chooseVideoInput",False)

class chooseVideoInput(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Choose method of Video input for", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        label2 = tk.Label(self, textvariable=controller.technique, font=controller.title_font)
        label2.pack(side="top", fill="x", pady=10)
        fileButton = tk.Button(self, text="File Input",
                                command=partial(self.getVideo,label2,controller,parent))
        recordButton = tk.Button(self, text="Record Input",
                                command=lambda:controller.show_frame("recordInput"))
        descButton = tk.Button(self, text="Technique Description",
                                command=partial(self.outputDescription))
        sportButton = tk.Button(self, text="Sport Description",
                                command=partial(self.outputSport))
        sportButton.pack()
        descButton.pack()
        fileButton.pack()
        recordButton.pack()

        backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("chooseTechniqueGUI"))
        backButton.pack(anchor="se")



    def getVideo(self,label2,controller,parent):
        print(label2["text"])
        VirtualCoachMain.inputVideo(label2["text"])
        controller.refresh("Loading",parent,"presentFeedback",False)
        
    def outputDescription(self):
        fpath = "FeedbackAreas\\"+(str(self.controller.sport.get()))+"\\" + (str(self.controller.technique.get())) + ".json"
        feedbackDict = {}
        with open(os.path.abspath(fpath)) as file:
            feedbackDict = json.load(file)
        desc = feedbackDict["description"]

        notice= tk.Toplevel(self.controller)
        notice.title("Description")
        fontlabel = tkfont.Font(family='Helvetica', size=11)
        label = tk.Label(notice, text= desc, font=fontlabel,padx=10,pady=30)
        label.pack()

    def outputSport(self):
        fpath = "FeedbackAreas\\"+(str(self.controller.sport.get()))+"\\" + (str(self.controller.technique.get())) + ".json"
        feedbackDict = {}
        with open(os.path.abspath(fpath)) as file:
            feedbackDict = json.load(file)
        desc = feedbackDict["sportdescription"]

        notice= tk.Toplevel(self.controller)
        notice.title("Description")
        fontlabel = tkfont.Font(family='Helvetica', size=11)
        label = tk.Label(notice, text= desc, font=fontlabel,padx=10,pady=30)
        label.pack()



class recordInput(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        textFont = tkfont.Font(family='Helvetica', size=11)

        label = tk.Label(self, text="A timer will countdown and will start recording after reaching 0", font=textFont)
        label.pack(side="top", fill="x", pady=10)

        label2 = tk.Label(self, text="Another timer will then start to time the recording process", font=textFont)
        label2.pack(side="top", fill="x", pady=10)

        label3 = tk.Label(self, text="How many seconds for the countdown?", font=textFont)
        label3.pack(side="top", fill="x", pady=10)
        countdown = tk.Scale(self, from_=0, to=30, orient="horizontal",command=self.countdownValue)
        countdown.pack()

        label4 = tk.Label(self, text="How many seconds for the recording process ", font=textFont)
        label4.pack(side="top", fill="x", pady=10)
        record = tk.Scale(self, from_=0, to=30, orient="horizontal",command=self.recordValue)
        record.pack()

        label5 = tk.Label(self, text="Press start when you are ready to start ", font=textFont)
        label5.pack(side="top", fill="x", pady=10)
        fileButton = tk.Button(self, text="START",
                                command=partial(self.recordGUI,controller,parent))
        fileButton.pack()

        backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI"))
        backButton.pack(anchor="se")

    def countdownValue(self,cd):
        global countdownVal
        countdownVal = cd
    def recordValue(self,re):
        global recordValue
        recordValue = re

    def recordGUI(self,controller,parent):
        VirtualCoachMain.recordVideo(self.controller.technique.get(),countdownVal,recordValue)
        controller.refresh("Loading",parent,"presentFeedback",False)




class presentFeedback(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.grid(sticky="new")
        self.columnconfigure((0,1,2,3,4,5),weight=1)
        self.columnconfigure(6,weight=0)
        self.rowconfigure((0,1,2,3),weight=1)
        label = tk.Label(self, text="Feedback", font=controller.title_font)
        label.grid(row=0,column=3,sticky="N")
        #label.pack(side="top", fill="x", pady=10)
        try:
            self.controller.imageSet.set(0)
            img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
            im = Image.fromarray(img)
            im = im.resize((((im.width)//2),((im.height)//2)))
            imgtk = ImageTk.PhotoImage(image=im)
            photos = tk.Label(self,image=imgtk,padx=10,pady=10)
            photos.image = imgtk 
            photos.grid(row=1,column=0)
            #photos.pack(side="left",padx=10,pady=10)
            count=0
            xCheck = 0
            for x in VirtualCoachMain.referenceTechniques:
                if x.technique == self.controller.technique.get():
                        xCheck = count
                count+=1    
            print(count)
            print(xCheck)
            refimg = VirtualCoachMain.referenceTechniques[xCheck].skeleton[self.controller.imageSet.get()]
            refim = Image.fromarray(refimg)
            refim = refim.resize(((refim.width//2),(refim.height//2)))
            refimgtk = ImageTk.PhotoImage(image=refim)
            refphotos = tk.Label(self,image=refimgtk,padx=10,pady=10)
            refphotos.image = refimgtk 
            refphotos.grid(row=1,column=1)
            #refphotos.pack(side="left",padx=10,pady=10)

            nextButton = tk.Button(self, text="NEXT",
                                command=lambda:self.next(photos,refphotos,xCheck)).grid(row=2,column=1)
            previousButton = tk.Button(self, text="PREVIOUS",
                                command=lambda:self.previous(photos,refphotos,xCheck)).grid(row=2,column=0)
            #nextButton.pack(side="left")
            #previousButton.pack(side="left")
            VirtualCoachMain.outputFeedback(VirtualCoachMain.feedbackList)
            improString = ""
            for impro in VirtualCoachMain.provideFeedback:
                improString+=impro+f"\n"
                if "Area of Tracking:" in impro:
                    improString+=f"\n"
            improFont = tkfont.Font(family='Helvetica', size=11)
            improvement = tk.Text(self,font=improFont,height=15,width=50)
            improvement.insert(index="end",chars=improString)
            improvement.configure(state="disabled")
            improvement.grid(row=1,column=5,sticky="E")

            scrollbar = tk.Scrollbar(self, command=improvement.yview)
            scrollbar.grid(row=1,column=6,sticky="E")
            improvement['yscrollcommand'] = scrollbar.set


            errorFont = tkfont.Font(family='Helvetica', size=8,slant="italic")
            errorMSG = tk.Label(self,text="Large percentage differences may be due to the \ncamera unable to see certain body parts\n Please refer to images",justify="left",bd=2,font=errorFont)
            errorMSG.grid(row=2,column=5,sticky="E")

            saveHistory = tk.Button(self, text="Save To History",
                                command=partial(self.History)).grid(row=3,column=5)
            backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI")).grid(row=3,column=6)
        except TypeError as e:
            print(e)
            photos = tk.Label(self,text="Image Error")
            photos.grid(row=1,column=0)
            #photos.pack(side="left",padx=20,pady=20)
        
    def History(self):
        VirtualCoachMain.sendToHistory(self.controller.technique.get())
        notice= tk.Toplevel(self.controller,width=100)
        notice.title("Notice")
        fontlabel = tkfont.Font(family='Helvetica', size=12)
        label = tk.Label(notice, text= "Saved to History", font=fontlabel,padx=10,pady=30)
        
        label.pack()


    def next(self, canv,refphotos,xCheck):
        if (self.controller.imageSet.get()==len(VirtualCoachMain.usersTechnique.skeleton)-1):
            self.controller.imageSet.set(0)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()+1)
        img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(img)
        im = im.resize(((im.width//2),(im.height//2)))
        imgtk = ImageTk.PhotoImage(image=im)
        canv.configure(image=imgtk)
        canv.image = imgtk

        refimg = VirtualCoachMain.referenceTechniques[xCheck].skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(refimg)
        im = im.resize(((im.width//2),(im.height//2)))
        imgtk = ImageTk.PhotoImage(image=im)
        refphotos.configure(image=imgtk)
        refphotos.image = imgtk

    def previous(self, canv,refphotos,xCheck):
        if (self.controller.imageSet.get()==0):
            self.controller.imageSet.set(len(VirtualCoachMain.usersTechnique.skeleton)-1)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()-1)
        img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(img)
        im = im.resize(((im.width//2),(im.height//2)))
        imgtk = ImageTk.PhotoImage(image=im)
        canv.configure(image=imgtk)
        canv.image = imgtk

        refimg = VirtualCoachMain.referenceTechniques[xCheck].skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(refimg)
        im = im.resize(((im.width//2),(im.height//2)))
        imgtk = ImageTk.PhotoImage(image=im)
        refphotos.configure(image=imgtk)
        refphotos.image = imgtk
    
class historyGUI(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        fname = "storedFeedback"
        btnList = []
        self.grid(sticky="new")
        self.columnconfigure(0,weight=0)
        self.columnconfigure((1,2),weight=1)
        self.columnconfigure(3,weight=0)
        self.rowconfigure(0,weight=0)
        label = tk.Label(self, text="Tracking History", font=controller.title_font)
        label.grid(row=0,column=1)
        rowNum = 1
        try:
            historyList = os.listdir(os.path.abspath(fname))
            for history in historyList:
                self.rowconfigure(rowNum,weight=0)
                label = tk.Label(self, text=history)
                label.grid(row=rowNum,column=0)
                button = tk.Button(self, text=history,
                                command=partial(self.setButton,history,controller,parent)).grid(row=rowNum,column=1)
                button2 = tk.Button(self, text="Delete",
                                command=partial(self.deleteHistory,history,parent)).grid(row=rowNum,column=2)
                btnList.append(button)
                rowNum+=1
            backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI"))
            backButton.grid(row=rowNum,column=3)


        except FileNotFoundError:
            print("")
    def changeHistory(self, history):
        self.controller.historyFile.set(history)

    def setButton(self,history,controller,parent):
        self.changeHistory(history)
        controller.refresh("Loading",parent,"presentFeedback",True)

    def deleteHistory(self,fpath,parent):
        rmtree(os.path.abspath("storedFeedback\\"+fpath))
        self.controller.refresh("historyGUI",parent,"",False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
    