from pathlib import Path
import numpy as np
import os
from deeplabcut.utils import auxiliaryfunctions

def setConfig_ContinueTraining(path_config_file, trainingsetindex=0):
    cfg = auxiliaryfunctions.read_config(path_config_file)
    trainFraction = cfg["TrainingFraction"][trainingsetindex]
    trainingsetindex = 0
    modelprefix = ""
    shuffle = 1
    snapshotindex = cfg["snapshotindex"]

    modelfoldername = auxiliaryfunctions.GetModelFolder(
        trainFraction, shuffle, cfg, modelprefix=modelprefix
    )
    poseconfigfile = Path(
        os.path.join(
            cfg["project_path"], str(modelfoldername), "train", "pose_cfg.yaml"
        )
    )
    cfg_dlc = auxiliaryfuctions.read_plainconfig(poseconfigfile)

    modelfolder = os.path.join(
        cfg["project_path"],
        str(modelfoldername),
    )

    Snapshots = np.array(
        [
            fn.split(".")[0]
            for fn in os.listdir(os.path.join(modelfolder, "train"))
            if "index" in fn
        ]
    )
    increasing_indices = np.argsort([int(m.split("-")[1]) for m in Snapshots])
    Snapshots = Snapshots[increasing_indices]
    cfg_dlc["init_weights"] = os.path.join(
        modelfolder, "train", Snapshots[snapshotindex]
    )
    auxiliaryfunctions.write_plainconfig(poseconfigfile, cfg_dlc)