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
##### 2.1. SSH into the computer using
```shell
# The IP address might change over time, so you might want to use the hostname u124289
ssh <your username>@165.124.111.121 # OR
ssh <your username>u124289.fsm.northwestern.edu
```
When prompt, enter your user's password

##### 2.2. Set up in the conda environment:
1. Install DLC first by following the instruction here https://deeplabcut.github.io/DeepLabCut/docs/installation.html
2. Specifically, clone the repo and create the environment using the conda file in the clone folder.
3. Once done, activate the environment (`conda activate deeplabcut`)
4. If there is issue in activating the conda environment, use `conda init bash` 
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
9. (Optional - But pretty sure you'll need this) Install CUDA supporting packages for conda. Make sure that the environment is activated
```shell
conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/' > $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
```
10. (Optional - Try if bug) Install numba
     `pip install numba==0.53.1`
11. Installation done!
12. TODO
    - [ ] Create .yml file to consolidate the installation process

##### 2.3. Setup the FSM resfiles
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
##### 2.4. Transferring the files to and from the workstation
1. Change the current directory to where the files are currently located
```shell
cd <original directory>
```
2.  Move files from the current directory to the destination
 ```shell
 cp <file> <destination directory>
 ```
   We can use wild card (such as `*.csv`) to select all files with the same pattern in the current directory.
##### 2.5. Transferring between personal computer and the workstation
There are many ways to achieve this. The first and 'primitive' way is to use `scp`. The second way involves installing 3rd party software on the personal computer. We will cover both methods in this section.
1. `scp` is the easier method (**PuTTY** and `pscp` for Windows folks)
```shell
# from your computer to the workstation
scp /PathToSourceFile/file <your username>u124289.fsm.northwestern.edu:/PathToTargetDir/file # for single file
scp -r /Directory <your username>u124289.fsm.northwestern.edu:/PathToTargetDir/TargetDir # for directory/folders

# from the workstation to your computer current working directory
scp <your username>u124289.fsm.northwestern.edu:/PathToTargetDir/file . # for file
scp -r <your username>u124289.fsm.northwestern.edu:/PathToTargetDir/TargetDir . # for directory
```

2. `sftp` is another option for transferring files and folder. On Windows, you can download `WinSCP` or `FileZilla` for free and use their `sftp` function. Those also come with the GUI to make the browsing and transferring processes easier. On Macos, `forklift` and `transmission` can do the same things, but they are not free.

##### 2.6. Setup the Jupyter notebook
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

#### 3. Pipeline notes instructions
Progress checklist for things tested and can do on the workstation without needing the GUI or notebook:
- [ ] DLC - Add labeled data
- [x] DLC - Create training set
- [x] DLC - Train model - Using IPython or notebook
  - [ ] DLC - Training from CLI
  - [ ] DLC - Auto add labeled data to train
- [x] DLC - Analyze videos
- [x] DLC - Label videos
- [ ] Anipose - Create template folder and config file
- [x] Anipose - Label 2d-videos
- [x] Anipose - Calibration
- [x] Anipose - Triangulate
- [ ] Analysis Support - Testing and updating ability
1. Optional setup
    Install this package (it is this repo!) to use some helper functions that will make our lives easier. 
    ```shell
    pip install --force-reinstall git+https://github.com/samsam2610/AnalysisSupport
    ```
2. Create and label video (DLC)
    1. Create the project and hand labels the videos on your computer
    2. Use `scp` or `rsync` to transfer the project to the workstation
3. Create the training set (DLC)
    1. This is the tricky part. The problem is that the training directory is based on where the training set is created. If the training set was created on one machine and going to be trained on another, we must manually modify the directory of the training set.
    2. To simplify the process, it is advised that we create the training set on the same machine that is going to be used for training.
    - [ ] Test training set creation
    1. Code snippet for creating the training set
    ```python
    import os
    import sys
    import deeplabcut

    os.environ["DLClight"]="True"

    # Specify project info
    ProjectFolderName = 'Spinal Implant-Sam-2021-10-05'
    VideoType = 'avi' 
    path_config_file = '/<path to config file/config.yaml'

    # Create the training set
    deeplabcut.create_training_dataset(path_config_file, net_type='resnes_101', augmenter_type='imgaug')
    ```
    This code snippet can be used either in IPython or Notebook.
4. Train the model (DLC)
   1. (Optional) If we are going to re-train a trained model with updated dataset/labels, assuming the optional package is installed, we can quickly resume the training on the said model by running this snippet
    ```python
    from analysissupport.dlc_support import *
    setConfig_ContinueTraining(path_config_file, additionalIteration=1000000)
    ```

   2. The model can be trained using this snippet
    (Assuming that the library is import and `path_config_file` is specified)
    (For the `gputouse` flag, we can properly test using multiple gpu by setting it to 2)

    ```python
    deeplabcut.train_network(path_config_file, shuffle=1, displayiters=10, saveiters=500, gputouse=None
    ```
    
5. Analyze the videos (DLC **_OR_** Anipose)
We have many options for this step:
   1. Do it through Anipose's CLI to label the video. It requires some setups, but once done, the files are neatly organized for triangulation. Here are the steps:
       1. Create the folder following the instruction on the website (https://anipose.readthedocs.io/en/latest/start2d.html)
       2. Have your `config.toml` ready with the appropriate directory of the DLC project.
       3. Move the raw videos to videos-raw
       4. Use Anipose's CLI to analyze the videos. Specifically: 
        ```bash
        anipose analyze
        ```
   2. Use the DLC function with some helpers (required Analysis-Support installed, or it will be a pain). Here are the steps:
        1. Create a list of videos to be analyzed using this snippet:
        ```python
        from analysissupport.dlc_support import *
        videofile_pathlist = [ 
            'path to folder containing videos 1',
            'path to folder containing videos 2',
            ]
        videoListObject = ProcessVideoList(videofile_pathlist)
        videoUnprocessList = videoListObject.getListofUnprocessedVideos()
        ```

        The `videoUnprocessList` contains the paths to individual videos found in the above folders. If you don't use this function, you will have to create the list by yourself (Yes, that's true!!). It would be some like this:

        ```python
        videoUnprocessList = [
            'path to video 1 in folder 1',
            'path to video 2 in folder 1',
            'path to video 1 in folder 2',
            'path to video 2 in folder 2',
        ]
        ```
        2. Analyze the videos with this snippet
        ```python
        deeplabcut.analyze_videos(path_config_file, videoUnprocessList, videotype=VideoType, save_as_csv=True)
        deeplabcut.create_labeled_video(path_config_file, videoUnprocessList, videotype=VideoType)
        ```
6. Calibration (Anipose)
    1. `cd` to the folder containing the `config.toml` file.
    2. Have the calibration videos in the `calibration` folder. It should be in the same folder as the `videos-raw``
    3. Run the CLI
    ```bash
    anipose calibration
    ```
   1. If the calibration is successful, the `calibration` folder should have the `calibration.toml` file.
7. Triangulation (Anipose)
    1. To use this step, it would be easier to run the `anipose analyze` function to analyze the `videos-raw` (going 4.1 route). Make sure the `calibration/calibration.toml` exists
    2. Run the CLI `anipose triangulate`
8. Additional steps - follow instructions on Anipose documentation.

#### 4. Tips and tricks
1. `tmux`
    `tmux` can be used to create multiple independent sessions. This allows us to safely detach from a running process in one session and exit the remote connection.
2. Helpful unix commands:
   1. 