from pathlib import Path
import numpy as np
import os
from analysissupport.dlc_support import auxiliaryfunctions

def setConfig_ContinueTraining(
    path_config_file,
    trainingsetindex=0,
    additionalIteration=1000000
):
    cfg = auxiliaryfunctions.read_config(path_config_file)
    trainFraction = cfg["TrainingFraction"][trainingsetindex]
    modelprefix = ""
    shuffle = 1
    snapshotindex = cfg["snapshotindex"]

    while True:
        modelfoldername = auxiliaryfunctions.GetModelFolder(
            trainFraction, shuffle, cfg, modelprefix=modelprefix
        )

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

        if len(Snapshots) is 0:
            cfg["iteration"] = cfg["iteration"] - 1
        else:
            print("Found snapshot in previous iteration #", cfg["iteration"])
            break

    increasing_indices = np.argsort([int(m.split("-")[1]) for m in Snapshots])
    Snapshots = Snapshots[increasing_indices]

    poseconfigfile = Path(
        os.path.join(
            cfg["project_path"], str(modelfoldername), "train", "pose_cfg.yaml"
        )
    )

    cfg_dlc = auxiliaryfunctions.read_plainconfig(poseconfigfile)
    cfg_dlc["init_weights"] = os.path.join(
        modelfolder, "train", Snapshots[snapshotindex]
    )

    cfg_dlc["project_path"] = cfg["project_path"]
    multi_step = cfg_dlc["multi_step"]
    cfg_dlc["multi_step"].append([0.001, multi_step[-1][1] + additionalIteration])

    auxiliaryfunctions.write_plainconfig(poseconfigfile, cfg_dlc)