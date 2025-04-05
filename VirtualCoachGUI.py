import tkinter as tk
import os
import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from tkinter import font as tkfont
from dataclasses import dataclass
from functools import partial

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
class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")
        self.sport = tk.StringVar()
        self.technique = tk.StringVar()
        self.imageSet = tk.IntVar()
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback):
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

    def refresh(self,page_name,container,afterWindow):
        frame = self.frames[page_name]
        if frame is not None:
            frame.destroy()
        for F in (MenuGUI, chooseSportGUI, chooseTechniqueGUI, chooseVideoInput, recordInput, Loading, presentFeedback):
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
                pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(VirtualCoachMain.usersTechnique.frames)
                VirtualCoachMain.usersTechnique.skeleton = HPEdImages
                VirtualCoachMain.usersTechnique.points = pointsArray
                VirtualCoachMain.calculateFeedback(self.technique.get(),False,VirtualCoachMain.usersTechnique.points,self.sport.get())
                self.refresh(afterWindow,container,"")
            
        

    
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
                            command=lambda: controller.show_frame("chooseSportGUI"))
        button3 = tk.Button(self, text="Manage Techniques",
                            command=lambda: controller.show_frame("chooseSportGUI"))
        button4 = tk.Button(self, text="Quit",
                            command=QuitApp)
        button1.pack()
        button2.pack()
        button3.pack()
        button4.pack()

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
    
    def changeSport(self, sp):
        self.controller.sport.set(sp)
    
    def partialButton(self,sport,controller,parent):
        self.changeSport(sport)
        controller.refresh("chooseTechniqueGUI",parent,"")
    
    

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
        except FileNotFoundError:
            print("")
    def changeTechnique(self, tech):
        self.controller.technique.set(tech)
    def setButton(self,technique,controller,parent):
        self.changeTechnique(technique)
        controller.refresh("Loading",parent,"chooseVideoInput")

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
        fileButton.pack()
        recordButton.pack()

    def getVideo(self,label2,controller,parent):
        print(label2["text"])
        VirtualCoachMain.inputVideo(label2["text"])
        controller.refresh("Loading",parent,"presentFeedback")



class recordInput(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Choose method of Video input", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        fileButton = tk.Button(self, text="File Input",
                                command=lambda:controller.show_frame("fileInput"))
        recordButton = tk.Button(self, text="Record Input",
                                command=lambda:controller.show_frame("recordInput"))
        fileButton.pack()
        recordButton.pack()

class presentFeedback(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Feedback", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        try:
            self.controller.imageSet.set(0)
            img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
            im = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=im)
            photos = tk.Label(self,image=imgtk)
            photos.image = imgtk 
            photos.pack(side="left",padx=20,pady=20)

            nextButton = tk.Button(self, text="NEXT",
                                command=lambda:self.next(photos))
            previousButton = tk.Button(self, text="PREVIOUS",
                                command=lambda:self.previous(photos))
            nextButton.pack(side="left")
            previousButton.pack(side="left")
        except TypeError:
            print("TypeError")
            photos = tk.Label(self,text="Image Error")
            photos.pack(side="left",padx=20,pady=20)
        
    def next(self, canv):
        if (self.controller.imageSet.get()==len(VirtualCoachMain.usersTechnique.skeleton)-1):
            self.controller.imageSet.set(0)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()+1)
        img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im)
        canv.configure(image=imgtk)
        canv.image = imgtk
    def previous(self, canv):
        if (self.controller.imageSet.get()==0):
            self.controller.imageSet.set(len(VirtualCoachMain.usersTechnique.skeleton)-1)
        else:
            self.controller.imageSet.set(self.controller.imageSet.get()-1)
        img = VirtualCoachMain.usersTechnique.skeleton[self.controller.imageSet.get()]
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im)
        canv.configure(image=imgtk)
        canv.image = imgtk
    

if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
    