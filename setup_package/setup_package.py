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
    install("deeplabcut==2.2.0.3")
    print("Fixing opencv-python issues")
    uninstall("opencv-python")
    uninstall("opencv-contrib-python")
    install("opencv-contrib-python")
    print("Done!!")

def project_3d():
    print("Installing and uninstalling packages")
    print("Installing DeepLabCut")
    install("deeplabcut==2.2.0.3")
    print("Installing ffmpeg and app tools")
    install("ffmpeg")
    install_upgrade("apptools")
    print("Fixing opencv-python issues")
    uninstall("opencv-python")
    uninstall("opencv-contrib-python")
    install("opencv-contrib-python==3.4.17.63")
    print("Installing Anipose")
    install("anipose==1.0.1")
    install("aniposelib==0.4.2")
    print("Installing numba")
    install("numba==0.53.1")
    uninstall("mayavi")
    install("vtk==8.1.2")
    install("mayavi")
    print("Done!!")

if __name__ == '__main__':
    main()

