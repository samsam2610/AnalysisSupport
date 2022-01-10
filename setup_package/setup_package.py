#!/usr/bin/env python3

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package , "--quiet"])

def uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package, "-y"])

def install_upgrade(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package, "--quiet"])

def project_2d():
    print("Installing and uninstalling packages")
    print("Installing DeepLabCut")
    install("deeplabcut")
    print("Fixing opencv-python issues")
    uninstall("opencv-python")
    uninstall("opencv-contrib-python")
    install("opencv-contrib-python")
    print("Done!!")

def project_3d():
    print("Installing and uninstalling packages")
    print("Installing DeepLabCut")
    install("deeplabcut")
    print("Installing Anipose")
    install("aniposelib==0.3.9")
    install("anipose==0.8.1")
    print("Installing ffmpeg and app tools")
    install("ffmpeg")
    install_upgrade("apptools")
    print("Fixing opencv-python issues")
    uninstall("opencv-python")
    uninstall("opencv-contrib-python")
    install("opencv-contrib-python")

    uninstall("mayavi")
    install("vtk==8.1.2")
    install("mayavi")
    print("Done!!")

if __name__ == '__main__':
    main()

