### How-to for Neptune the workstation
This tutorial shows steps to utilize the Deep Learning workstation (Neptune) in Dr.Tresch's lab for DEEPLABCUT (DLC) + Anipose tasks

#### 1. Overview - Notes
Since the DLC + Anipose (DLCA) pipeline is still being set up, we need to perform many steps manually. The guide will be updated promptly as the pipeline evolved. 

Here are some info + terminologies for future references:
- OS: Ubuntu 20.04
- GPU: 2x Nvidia RTX 3080 Ti
- You will need to create and set up your own conda environment to perform your tasks
- Need to be on Northwestern VPN to SSH into the workstation
- Most DLCA computing tasks can be done via SSH except for the hand-labeling step.
- Current IP address: 165.124.111.121
- The shell is `bash`

#### 2. Connect and setup the workstation
1. SSH into the computer using
    ```shell
    ssh <your username>@165.124.111.121
    ```
    When prompt, enter your user's password

2. Set up in the conda environment:
   1. Install DLC first by following the instruction here https://deeplabcut.github.io/DeepLabCut/docs/installation.html
   2. Specifically, clone the repo and create the environment using the conda file in the clone folder.
   3. Once done, activate the environment (`conda activate deeplabcut`)
   4. If there is issue in activate the conda environment, use `conda init bash` 
   5. Install anipose from pip - `pip install anipose`
   6. (Optional - Try if bug) Install aniposelib from pip - `pip install aniposelib`
   7. Uninstall opencv and their traces:
      1. `pip uninstall opencv-python`
      2. `pip uninstall opencv-python-headless`
      3. `pip uninstall opencv-contrib-pythonY`
   8. Re-install opencv-contrib
   ```shell
   pip install --no-deps --force-reinstall opencv-contrib-python==3.4.17.63
   ```
   9. (Optional - Try if bug) Install numba
        `pip install numba==0.53.1`
   10. Installation done!
   
3. Setup the FSM resfiles
   1. Note: To access the FSM resfile from SSH, we need to manually mount the server to the computer. After finish transferring the file, make it a good practice to unmount the directory using the command from the 4th step.
   2. Make mounting point directory - This can be anywhere, just remember to change it to the same directory in the 3rd step
    ```shell
    sudo mkdir -p /resfiles
    ```
   3. Mount the FSM Resfiles drive 
    ```shell
    sudo mount -t cifs -o "username=<netID>,password=<password>,domain=fsm" //fsmresfiles.fsm.northwestern.edu/fsmresfiles/Basic_Sciences/Phys/TreschLab /resfiles
    ```
   4. Unmount the file system
    ```shell
    sudo umount -l /resfiles
    ```
4. Transferring the files to and from the workstation
   1. Change the current directory to where the files are currently located
    ```shell
    cd <original directory>
    ```
   2.  Move files from the current directory to the destination
    ```shell
    cp <file> <destination's directory>
    ```
      1. Can use wild card (such as `*.csv`) to select all files with the same pattern in the current directory.
5. Setup the jupyter notebook
   1. Notes: Follow the documentation from Anaconda
   https://docs.anaconda.com/anaconda/user-guide/tasks/remote-jupyter-notebook/
   2. `cd` into the folder with the target notebook
   3. Launch the jupyter notebook server. The `PORT` number can typically be 8080.
   ```shell
   jupyter notebook --no-browser --port=<PORT>
   ```
   4. Access the notebook from your computer using the command
   ```shell
   ssh -L 8080:localhost:<PORT> <REMOTE_USER>@<REMOTE_HOST>
   ```
   PORT - The port from the above
   REMOTE_USER - Your computer username
   REMOTE_HOST - The IP of the computer
   5. Navigate your browser to http://localhost:8080/ to work on the notebook

#### 3. Pipeline notes
