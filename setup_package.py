import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package , "--quiet"])

def uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package, "-y"])

def install_upgrade(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package, "--quiet"])

if __name__ == '__setup_package__':
    install("deeplabcut")
    install("aniposelib")
    install("anipose")
    install("ffmpeg")
    install_upgrade("apptools")
    uninstall("opencv-python")
    uninstall("opencv-contrib-python")
    install("opencv-contrib-python")

    uninstall("mayavi")
    install("vtk==8.1.2")
    install("mayavi")