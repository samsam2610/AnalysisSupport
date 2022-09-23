import os
from pathlib import Path
from skimage import io
from skimage.util import img_as_ubyte
import numpy as np
import pandas as pd
from analysissupport.dlc_support import auxiliaryfunctions, conversioncode
from analysissupport.dlc_support.auxfun_videos import VideoReader
from analysissupport.dlc_support.visualization import Plotting

class AutoFrameExtraction:
    def __init__(self,
                 config,
                 videoUnprocessList,
                 modelprefix="",
                 shuffle=1,
                 track_method="",
                 trainingsetindex=0,
                 crop=False,
                 scale=1,
                 comparisonbodyparts="all",
                 color_by="bodypart") -> None:
        self.config = config
        self.videoUnprocessList = videoUnprocessList
        self.modelprefix = modelprefix
        self.shuffle = shuffle
        self.track_method = track_method
        self.trainingsetindex = trainingsetindex
        self.crop = crop
        self.scale = scale
        self.color_by = color_by
        self.cfg = auxiliaryfunctions.read_config(config)
        
        self.DLCscorer, DLCscorerlegacy = auxiliaryfunctions.GetScorerName(
            self.cfg,
            self.shuffle,
            trainFraction=self.cfg["TrainingFraction"][trainingsetindex],
            modelprefix=modelprefix,
        )
        self.videos = self.cfg["video_sets"].keys()
        self.HUMANscorer = self.cfg["scorer"]

        self.video_names = [Path(i).stem for i in self.videos]
        alldatafolders = [
            fn
            for fn in os.listdir(Path(config).parent / "labeled-data")
            if "_labeled" not in fn
        ]

        self.comparisonbodyparts = auxiliaryfunctions.IntersectionofBodyPartsandOnesGivenbyUser(
            self.cfg, comparisonbodyparts
        )

    def getFilteredFrames(self,
                          videoPath,
                          P=0.999):
        videoName = Path(videoPath).stem

        output_path = Path(videoPath).parent.joinpath(videoName)
        output_path.mkdir(parents=True, exist_ok=True)

        destfolder = str(Path(videoPath).parents[0])

        df, filepath, _, _ = auxiliaryfunctions.load_analyzed_data(
            destfolder, videoName, self.DLCscorer, track_method=self.track_method
        )

        return df


    def extractFrameWithLikelihood(self,
                                   P=0.999):
        for video in self.videoUnprocessList:
            videoName = Path(video).stem

            output_path = Path(video).parent.joinpath(videoName)
            output_path.mkdir(parents=True, exist_ok=True)

            destfolder = str(Path(video).parents[0])

            df, filepath, _, _ = auxiliaryfunctions.load_analyzed_data(
                destfolder, videoName, self.DLCscorer, track_method=self.track_method
            )
            conversioncode.guarantee_multiindex_rows(df)

            dfnew = df.filter(regex='likelihood', axis=1)
            df_filt = dfnew[dfnew>P]
            df_filt.dropna(inplace=True)
            frames2pick = df_filt.index
            frames2pick = frames2pick[0::100]
            
            # Extracting and saving the frames
            cap = VideoReader(video)
            nframes = len(cap)
            indexlength = int(np.ceil(np.log10(nframes)))
            is_valid = []
            for index in frames2pick:
                cap.set_to_frame(index)  # extract a particular frame
                frame = cap.read_frame()
                if frame is not None:
                    image = img_as_ubyte(frame)
                    img_name = (
                        str(output_path)
                        + "/img"
                        + str(index).zfill(indexlength)
                        + ".png"
                    )

                    io.imsave(img_name, image)
                    is_valid.append(True)
                else:
                    print("Frame", index, " not found!")
                    is_valid.append(False)
            cap.close()


            self.DataCombined = df
            Plotting(self.cfg,
                self.comparisonbodyparts,
                self.DLCscorer,
                self.DataCombined * 1.0 / self.scale,
                frames2pick,
                indexlength,
                folderInput=str(output_path),
                foldername=str(output_path))

    def addFrameToLabeledData(self):
        for video in self.videoUnprocessList:
            videoName = Path(video).stem
            cap = VideoReader(video)
            nframes = len(cap)
            indexlength = int(np.ceil(np.log10(nframes)))

            # Retrive list of frames in the folder
            frames_folder = Path(video).parent.joinpath(videoName)
            if not frames_folder.is_dir():
                continue
            frames2pick = [int(p.stem.split('img')[1])
                        for p in frames_folder.glob('*.png')]
            print(frames2pick)

            # Set output path
            destfolder = str(Path(video).parents[0])
            df, filepath, _, _ = auxiliaryfunctions.load_analyzed_data(
                destfolder, videoName, self.DLCscorer, track_method=self.track_method
            )
            conversioncode.guarantee_multiindex_rows(df)

            df_selected = df.iloc[frames2pick]
            df_selected = df_selected.drop(list(self.DataCombined.filter(regex = 'likelihood')), axis=1)
            df_selected.columns = df_selected.columns.set_levels([self.HUMANscorer], level='scorer')
            index = pd.Index([os.path.join("labeled-data", videoName, "img" + str(fn).zfill(indexlength) + ".png") for fn in frames2pick])
            df_selected = df_selected.set_index(index)

            output_path = (
                Path(self.config).parents[0] / "labeled-data" / Path(video).stem
            )
            output_path.mkdir(parents=True, exist_ok=True)

            # Transfer the label data to the labeled data folder
            name_file = "CollectedData_" + self.HUMANscorer + ".h5"
            output_file = (
                output_path / name_file
            )
            if output_file.is_file():
                df_labeled = pd.read_hdf(
                    output_file
                )
                
                df_selected = pd.concat([df_selected, df_labeled])

            conversioncode.guarantee_multiindex_rows(df_selected)
            df_selected = df_selected[~df_selected.index.duplicated(keep="first")]
            df_selected.to_csv(
                os.path.join(
                    self.cfg["project_path"],
                    "labeled-data",
                    videoName,
                    "CollectedData_" + self.HUMANscorer + ".csv",
                )
            )
            df_selected.to_hdf(
                os.path.join(
                    self.cfg["project_path"],
                    "labeled-data",
                    videoName,
                    "CollectedData_" + self.HUMANscorer + ".h5",
                ),
                key="df_with_missing",
                mode="w",
            )

            # Extract and save the frames from the frame index list
            is_valid = []
            for index in frames2pick:
                cap.set_to_frame(index)  # extract a particular frame
                frame = cap.read_frame()
                if frame is not None:
                    image = img_as_ubyte(frame)
                    img_name = (
                        str(output_path)
                        + "/img"
                        + str(index).zfill(indexlength)
                        + ".png"
                    )
                    
                    io.imsave(img_name, image)
                    is_valid.append(True)
                else:
                    print("Frame", index, " not found!")
                    is_valid.append(False)
            cap.close()


