import tkinter as tk
import os
import cv2
import json
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from tkinter import font as tkfont
from dataclasses import dataclass
from functools import partial
from shutil import rmtree

import HumanPoseEstimation
import VirtualCoachMain


# Quit Function for closing the application
def QuitApp():
    quit()

# Base application class
class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # create title font
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")
        # set window title
        self.title("Virtual Coach")
        # store sport and technique and history file
        self.sport = tk.StringVar()
        self.technique = tk.StringVar()
        self.imageSet = tk.IntVar()
        self.historyFile = tk.StringVar()
        
        #container is used to stack the frames and only present the current one
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initiates and stacks all frames
        self.frames = {}
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback,historyGUI):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # starting frame
        self.show_frame("MenuGUI")

    # sets frame to the chosen
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    #refresh a page when a value needs to be changed
    def refresh(self,page_name,container,afterWindow,historyCheck):
        # set frame equal to chosen frame
        frame = self.frames[page_name]
        # if the next frame is not null then destroy it so that it can be refreshed
        if frame is not None:
            frame.destroy()
        # reload the chosen frame
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback,historyGUI):
            if F.__name__ == page_name:
                frame = F(parent=container, controller=self)
                self.frames[page_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
        # show the frame
        self.show_frame(page_name)
        # if the process will take time a loading screen is available
        if page_name == "Loading":
            frame.update()
            # update the frame to change to the loading screen (otherwise the functions will start and then change to loading after finish)
            if afterWindow == "chooseVideoInput":
                # once the user has chosen a technique then the reference frames are retrieved and pose estimated
                VirtualCoachMain.startUp(self.sport.get(),self.technique.get())
                # show choose video input
                self.show_frame(afterWindow)
            elif afterWindow == "presentFeedback":
                # after adding the video the frames are cropped and pose estimated, added to the user technique
                if historyCheck == False:
                    VirtualCoachMain.cropVideo(self.technique.get())
                    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(VirtualCoachMain.usersTechnique.frames)
                    VirtualCoachMain.usersTechnique.skeleton = HPEdImages
                    VirtualCoachMain.usersTechnique.points = pointsArray
                    # temporal analyse the frames
                    VirtualCoachMain.temporalAnalysis(self.technique.get())
                    # calculate the feedback on the hped frames
                    VirtualCoachMain.calculateFeedback(self.technique.get(),VirtualCoachMain.usersTechnique.points,self.sport.get())
                    # refresh the calc feedback window to show the feedback information
                    self.refresh(afterWindow,container,"",False)
                else:
                    # history feedback
                    # perpare program for feedback
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
                    # reference videos are prepared
                    VirtualCoachMain.startUp(self.sport.get(),self.technique.get())
                    #points and skeletons are fetched from file
                    fname = "storedFeedback"
                    fpath = fname + "\\" + self.historyFile.get() + "\\pointsData.json"
                    with open(os.path.abspath(fpath)) as file:
                        feedbackDict = json.loads(json.load(file))

                    fpath = fname + "\\" + self.historyFile.get() + "\\skeletonsList"
                    skelList = os.listdir(os.path.abspath(fpath))
                    skelIMGList = []
                    inim = 1
                    # read and change the skeletons for use with feedback
                    for x in skelList:
                        
                        skelImg = VirtualCoachMain.footageDecryption(os.path.abspath(fpath+"\\"+x))
                        skelImg = cv2.cvtColor(skelImg, cv2.COLOR_RGB2BGR)
                        inim+=1
                        skelIMGList.append(skelImg)

                    VirtualCoachMain.usersTechnique.skeleton = skelIMGList
                    VirtualCoachMain.usersTechnique.points = feedbackDict["points"]
                    # calculate feedback on stored points
                    VirtualCoachMain.calculateFeedback(technique,VirtualCoachMain.usersTechnique.points,chosenSport)
                    # refresh calc feedback window
                    self.refresh(afterWindow,container,"",False)
            
# menu user interface for startup
class MenuGUI(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent,width=850,height=500)
        self.pack_propagate(0)
        self.controller = controller
        menuFont = tkfont.Font(family='Helvetica', size=24, weight="bold")
        label = tk.Label(self, text="Virtual Coach", font=menuFont)
        label.pack(side="top", fill="x", pady=80)
        # button for adding video and providing feedback
        btnWidth = 20
        btnHeight = 2
        button1 = tk.Button(self, text="Track Technique",width=btnWidth,height=btnHeight,
                            command=lambda: controller.show_frame("chooseSportGUI"))
        #button for getting history
        button2 = tk.Button(self, text="Track History",width=btnWidth,height=btnHeight,
                            command=lambda: controller.refresh("historyGUI",parent,"",False))
        #quit button to stop program
        button3 = tk.Button(self, text="Quit",width=btnWidth,height=btnHeight,
                            command=QuitApp)
        button1.pack(pady=10)
        button2.pack(pady=10)
        button3.pack(pady=10)

# frame to show loading screen
class Loading(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent,width=850,height=500)
        self.pack_propagate(0)
        self.controller = controller
        label = tk.Label(self, text="Loading...", font=controller.title_font)
        label.pack(fill="none", expand=True)

# allow the user to choose a sport
class chooseSportGUI(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.frame = None
        self.grid(sticky="new")
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.rowconfigure(0,weight=0)
        label = tk.Label(self, text="", font=controller.title_font)
        label.grid(row=0,column=0,padx=20)
        label = tk.Label(self, text="Choose Sport", font=controller.title_font)
        label.grid(row=0,column=1,pady=20)
        # sports recieved from feedback areas folder
        fname = "FeedbackAreas"
        sportList = os.listdir(os.path.abspath(fname))
        # create a button for each sport to allow user to choose
        rowNum = 1
        for sport in sportList:
            self.rowconfigure(rowNum,weight=0)
            button = tk.Button(self, text=sport,height=2,width=20,
                            command=partial(self.partialButton,sport,controller,parent)).grid(row=rowNum,column=1,pady=10)
            rowNum+=1
        # back button to menu
        self.rowconfigure(rowNum,weight=1)
        backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI")).grid(row=rowNum,column=2,sticky="se",padx=5,pady=5)
    
    # sets the sport variable to whichever one the user chose
    def changeSport(self, sp):
        self.controller.sport.set(sp)
    
    # change sport and refrsh next window
    def partialButton(self,sport,controller,parent):
        self.changeSport(sport)
        controller.refresh("chooseTechniqueGUI",parent,"",False)
    
    
# allows the user to choose a technique from the chosen sport
class chooseTechniqueGUI(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.grid(sticky="new")
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.rowconfigure(0,weight=0)
        label = tk.Label(self, text="", font=controller.title_font)
        label.grid(row=0,column=0,padx=20)
        label = tk.Label(self, textvariable=controller.sport, font=controller.title_font)
        label.grid(row=0,column=1,pady=20)
        fname = "FeedbackAreas"
        rowNum=1
        try:
            # get technique from chosen sport folder
            techniqueList = (os.listdir(os.path.abspath(fname+"\\" + str(label["text"]))))
            for technique in techniqueList:
                self.rowconfigure(rowNum,weight=0)
                # techniques stored as json files and added as strings of file names
                technique=technique.replace(".json","")
                # add button of technique for user to select
                button = tk.Button(self, text=technique,height=2,width=20,
                                command=partial(self.setButton,technique,controller,parent)).grid(row=rowNum,column=1,pady=10)
                rowNum+=1
            # back button to go to choose sport
            self.rowconfigure(rowNum,weight=1)
            backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("chooseSportGUI")).grid(row=rowNum,column=2,sticky="se",padx=5,pady=5)
        except FileNotFoundError:
            print("")
    # set technique to chosen technique on button press
    def changeTechnique(self, tech):
        self.controller.technique.set(tech)
    
    # change technique and load next page
    def setButton(self,technique,controller,parent):
        self.changeTechnique(technique)
        controller.refresh("Loading",parent,"chooseVideoInput",False)

# allow the user to choose the method of inputting video
class chooseVideoInput(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.grid(sticky="new")
        self.columnconfigure((0,1,2),weight=1)
        self.rowconfigure((0,1,2,3,4,5,6),weight=1)
        label = tk.Label(self, text="", font=controller.title_font)
        label.grid(row=0,column=0,padx=20)
        label = tk.Label(self, text="Choose method of video input for", font=controller.title_font)
        label.grid(row=0,column=1)
        label2 = tk.Label(self, textvariable=controller.technique, font=controller.title_font)
        label2.grid(row=1,column=1)
        # input from file explorer
        fileButton = tk.Button(self, text="File Input",height=2,width=20,
                                command=partial(self.getVideo,label2,controller,parent)).grid(row=4,column=1,pady=10)
        # go to record video frame
        recordButton = tk.Button(self, text="Record Input",height=2,width=20,
                                command=lambda:controller.show_frame("recordInput")).grid(row=5,column=1,pady=10)
        
        # provide description of technique
        descButton = tk.Button(self, text="Technique Description",
                                command=partial(self.outputDescription)).grid(row=2,column=1,pady=1)
        # provide description of sport
        sportButton = tk.Button(self, text="Sport Description",
                                command=partial(self.outputSport)).grid(row=3,column=1,pady=1)
        # go back to choose technique
        backButton = tk.Button(self, text="Back",
                                command=lambda:self.backReset()).grid(row=6,column=2,padx=5,pady=5,sticky="se")

    # resets generated reference frames and goes back to choose technique
    def backReset(self):
        VirtualCoachMain.referenceTechniques = []
        self.controller.show_frame("chooseTechniqueGUI")

    #get a video from file explorer
    def getVideo(self,label2,controller,parent):
        # opens explorer window
        VirtualCoachMain.inputVideo(label2["text"])
        # if video file is chosen then calculate pose estimation and present feedback
        if VirtualCoachMain.usersTechnique.frames != []:
            controller.refresh("Loading",parent,"presentFeedback",False)
        else:
            # if none or an incorrect type of file is chosen then open toplevel window warning the user
            notice= tk.Toplevel(self.controller)
            notice.title("Error")
            fontlabel = tkfont.Font(family='Helvetica', size=11)
            label = tk.Label(notice, text= "File could not be openned", font=fontlabel,padx=10,pady=30)
            label.pack()
        
    # output the description of the technique and instructions to a seperate to the window
    def outputDescription(self):
        # get json file of technique
        fpath = "FeedbackAreas\\"+(str(self.controller.sport.get()))+"\\" + (str(self.controller.technique.get())) + ".json"
        feedbackDict = {}
        #load to dictionary
        try:
            with open(os.path.abspath(fpath)) as file:
                feedbackDict = json.load(file)
            desc = feedbackDict["description"]
        except:
            desc = "Error: No Description Found"
        # add new lines on full stops
        desc = desc.replace(". ",".\n")
        # open toplevel window of description
        notice= tk.Toplevel(self.controller)
        notice.title("Description")
        fontlabel = tkfont.Font(family='Helvetica', size=11)
        label = tk.Label(notice, text= desc, font=fontlabel,padx=10,pady=30,justify="left")
        label.pack()

    # output the description of the sport and instructions to a seperate to the window
    def outputSport(self):
        # get json file of technique
        fpath = "FeedbackAreas\\"+(str(self.controller.sport.get()))+"\\" + (str(self.controller.technique.get())) + ".json"
        feedbackDict = {}
        #load to dictionary
        try:
            with open(os.path.abspath(fpath)) as file:
                feedbackDict = json.load(file)
            desc = feedbackDict["sportdescription"]
        except:
            desc = "Error: No Description Found"
        # add new lines on full stops
        desc = desc.replace(". ",".\n")
        # open toplevel window of description
        notice= tk.Toplevel(self.controller)
        notice.title("Description")
        fontlabel = tkfont.Font(family='Helvetica', size=11)
        label = tk.Label(notice, text= desc, font=fontlabel,padx=10,pady=30,justify="left")
        label.pack()


# window to record user video
class recordInput(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        textFont = tkfont.Font(family='Helvetica', size=11)

        label = tk.Label(self, text="A timer will countdown and will start recording after reaching 0", font=textFont)
        label.pack(side="top", fill="x", pady=10)

        label2 = tk.Label(self, text="Another timer will then start to time the recording process", font=textFont)
        label2.pack(side="top", fill="x", pady=10)
        # scroll bar to allow the user to set a countdown to get in position (30 second limit)
        label3 = tk.Label(self, text="How many seconds for the countdown?", font=textFont)
        label3.pack(side="top", fill="x", pady=10)
        countdown = tk.Scale(self, from_=1, to=30, orient="horizontal",command=self.countdownValue)
        countdown.pack()
        # scroll bar to allow user to set length of video (30 second limit)
        label4 = tk.Label(self, text="How many seconds for the recording process ", font=textFont)
        label4.pack(side="top", fill="x", pady=10)
        record = tk.Scale(self, from_=5, to=30, orient="horizontal",command=self.recordValue)
        record.pack()
        # start button
        label5 = tk.Label(self, text="Press start when you are ready to start ", font=textFont)
        label5.pack(side="top", fill="x", pady=10)
        fileButton = tk.Button(self, text="START",
                                command=partial(self.recordGUI,controller,parent))
        fileButton.pack()

        backButton = tk.Button(self, text="Back",
                                command=lambda:self.backCheck())
        backButton.pack(anchor="se")

    # go back to choose technique frame and reset ref technique
    def backCheck(self):
        self.controller.show_frame("chooseVideoInput")
    # set countdown value
    def countdownValue(self,cd):
        global countdownVal
        countdownVal = cd
    # set record value
    def recordValue(self,re):
        global recordValue
        recordValue = re

    # send countdown and record values to record video, after recording moves to loading and presents feedback after hpe
    def recordGUI(self,controller,parent):
        VirtualCoachMain.recordVideo(self.controller.technique.get(),countdownVal,recordValue)
        controller.refresh("Loading",parent,"presentFeedback",False)



# present feedback to the user
class presentFeedback(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # grid for easy presenting
        self.grid(sticky="new")
        self.columnconfigure((0,1,2,3,4,5),weight=1)
        self.columnconfigure(6,weight=0)
        self.rowconfigure((0,1,2,3),weight=1)
        label = tk.Label(self, text="Feedback", font=controller.title_font)
        label.grid(row=0,column=3,sticky="N")
        # on start load there is no images so error is met. this prevents it until the user gets to the screen
        try:
            # set start image
            self.controller.imageSet.set(0)
            # resize and add first skeleton image to ui in grid
            img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
            im = Image.fromarray(img)
            im = im.resize((((im.width)//2),((im.height)//2)))
            imgtk = ImageTk.PhotoImage(image=im)
            photos = tk.Label(self,image=imgtk,padx=10,pady=10)
            photos.image = imgtk 
            photos.grid(row=1,column=0)
            
            # gets the reference technique object in list
            count=0
            xCheck = 0
            for x in VirtualCoachMain.referenceTechniques:
                if x.technique == self.controller.technique.get():
                        xCheck = count
                count+=1    
            
            # add first reference skeleton to ui in grid next to users
            refimg = VirtualCoachMain.referenceTechniques[xCheck].skeleton[self.controller.imageSet.get()]
            refim = Image.fromarray(refimg)
            refim = refim.resize(((refim.width//2),(refim.height//2)))
            refimgtk = ImageTk.PhotoImage(image=refim)
            refphotos = tk.Label(self,image=refimgtk,padx=10,pady=10)
            refphotos.image = refimgtk 
            refphotos.grid(row=1,column=1)

            # buttons for changing moving through the different photos in the list of reference and user simultaneously
            nextButton = tk.Button(self, text="NEXT",
                                command=lambda:self.next(photos,refphotos,xCheck)).grid(row=2,column=1)
            previousButton = tk.Button(self, text="PREVIOUS",
                                command=lambda:self.previous(photos,refphotos,xCheck)).grid(row=2,column=0)

            # ouput the feedback from the hpe and calculate feedback
            VirtualCoachMain.outputFeedback(VirtualCoachMain.feedbackList)
            improString = ""
            # for each each line in output feedback list add to string with new line
            for impro in VirtualCoachMain.provideFeedback:
                improString+=impro+f"\n"
                if "Area of Tracking:" in impro:
                    improString+=f"\n"
            # create new font
            improFont = tkfont.Font(family='Helvetica', size=11)
            # create text box to allow for resizing and scrollbar
            improvement = tk.Text(self,font=improFont,height=15,width=50)
            # add improvements string to text
            improvement.insert(index="end",chars=improString)
            # disable the box to prevent user typing in the box
            improvement.configure(state="disabled")
            improvement.grid(row=1,column=5,sticky="E")
            # add scrollbar attached to the text box's y scroll
            scrollbar = tk.Scrollbar(self, command=improvement.yview)
            scrollbar.grid(row=1,column=6,sticky="E")
            improvement['yscrollcommand'] = scrollbar.set

            # error message reasuring of any large percentage values
            errorFont = tkfont.Font(family='Helvetica', size=8,slant="italic")
            errorMSG = tk.Label(self,text="Large percentage differences may be due to the \ncamera unable to see certain body parts\n Please refer to images",justify="left",bd=2,font=errorFont)
            errorMSG.grid(row=2,column=5,sticky="E")

            # button to save the skeletons and points to history folders
            saveHistory = tk.Button(self, text="Save To History",
                                command=partial(self.History)).grid(row=3,column=5)
            # back to menu
            backButton = tk.Button(self, text="Back",
                                command=lambda:self.backReset()).grid(row=3,column=6)
        except TypeError as e:
            # error catch for no images on start of application
            photos = tk.Label(self,text="Image Error")
            photos.grid(row=1,column=0)
            
    # resets values used in process and goes to menu
    def backReset(self):
        VirtualCoachMain.usersTechnique.frames = []
        VirtualCoachMain.usersTechnique.points = []
        VirtualCoachMain.usersTechnique.skeleton = []
        VirtualCoachMain.referenceTechniques = []
        VirtualCoachMain.feedbackList = []
        VirtualCoachMain.provideFeedback = []
        self.controller.show_frame("MenuGUI")

    # send to history and alert user
    def History(self):
        VirtualCoachMain.sendToHistory(self.controller.technique.get())
        notice= tk.Toplevel(self.controller,width=100)
        notice.title("Notice")
        fontlabel = tkfont.Font(family='Helvetica', size=12)
        label = tk.Label(notice, text= "Saved to History", font=fontlabel,padx=10,pady=30)
        label.pack()

    # move to next image
    def next(self, canv,refphotos,xCheck):
        # checks index wont go over length of skeletons
        if (self.controller.imageSet.get()==len(VirtualCoachMain.usersTechnique.skeleton)-1):
            self.controller.imageSet.set(0)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()+1)
        # change images
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

    # goes to previous image
    def previous(self, canv,refphotos,xCheck):
        # check index wont go into negatives and go to end of list instead
        if (self.controller.imageSet.get()==0):
            self.controller.imageSet.set(len(VirtualCoachMain.usersTechnique.skeleton)-1)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()-1)
        # adds images
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
    
# view history user interface
class historyGUI(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        fname = "storedFeedback"
        btnList = []
        # grid interface
        self.grid(sticky="new")
        self.columnconfigure(0,weight=0)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(3,weight=1)
        self.rowconfigure(0,weight=0)
        label = tk.Label(self, text="Tracking History", font=controller.title_font)
        label.grid(row=0,column=1)
        rowNum = 1
        try:
            # get all history file names
            historyList = os.listdir(os.path.abspath(fname))
            for history in historyList:
                # add rows depending on number of folders
                self.rowconfigure(rowNum,weight=0,uniform="a",pad=10)
                # folder name
                label = tk.Label(self, text=history)
                label.grid(row=rowNum,column=0,padx=15)
                # button to regenerate feedback and go to ouput feedback
                button = tk.Button(self, text="Track Technique",
                                command=partial(self.setButton,history,controller,parent)).grid(row=rowNum,column=1)
                # allow user to delete folder including points and images
                button2 = tk.Button(self, text="Delete",
                                command=partial(self.deleteHistory,history,parent)).grid(row=rowNum,column=3,padx=5)
                btnList.append(button)
                rowNum+=1
            # back to menu
            self.rowconfigure(rowNum,weight=1)
            backButton = tk.Button(self, text="Back",
                                command=lambda:controller.show_frame("MenuGUI"))
            
            backButton.grid(row=rowNum,column=3,sticky="se",padx=10,pady=10)

        except FileNotFoundError:
            print("")
    
    # set the chosen history folder
    def changeHistory(self, history):
        self.controller.historyFile.set(history)

    #change history and regenerate feedback and present
    def setButton(self,history,controller,parent):
        self.changeHistory(history)
        controller.refresh("Loading",parent,"presentFeedback",True)

    # delete history folder
    def deleteHistory(self,fpath,parent):
        rmtree(os.path.abspath("storedFeedback\\"+fpath))
        self.controller.refresh("historyGUI",parent,"",False)

# start application and tkinter loop
if __name__ == "__main__":
    app = App()
    app.mainloop()
    