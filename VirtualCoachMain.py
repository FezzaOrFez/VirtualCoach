import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

from zipfile import ZipFile
from urllib.request import urlretrieve

from IPython.display import YouTubeVideo, display, Image

protoFile   = os.path.abspath("pose_deploy_linevec_faster_4_stages.prototxt")
weightsFile = os.path.join("model", "pose_iter_160000.caffemodel")

nPoints = 15
POSE_PAIRS = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [1, 5],
    [5, 6],
    [6, 7],
    [1, 14],
    [14, 8],
    [8, 9],
    [9, 10],
    [14, 11],
    [11, 12],
    [12, 13],
]

def loadImages(folderName):
    setOfImages = []
    for files in os.listdir(folderName):
        im = cv2.imread(os.path.join(folderName,files))
        if im is not None:
            setOfImages.append(im)
    return setOfImages

def processImages(exerciseName):
    processedImages = []

    setImages = loadImages(exerciseName.lower())

    for im in setImages:
        if exerciseName.lower() == "deadlift":
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[0:400,175:500]
            processedImages.append(im)
        if exerciseName.lower() == "bench_press":
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[75:400,75:400]
            processedImages.append(im)
        if exerciseName.lower() == "squat":
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[0:400,0:180]
            processedImages.append(im)
    return processedImages

            
images = processImages("squat")
# Display probability maps
for im in images:
    plt.figure(figsize=(10, 5))
    plt.imshow(im)

    plt.show()