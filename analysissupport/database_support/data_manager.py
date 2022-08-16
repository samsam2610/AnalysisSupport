

import sys
import os
from pathlib import Path

cwd = os.getcwd()
sys.path.append('analysissupport')

from sqlalchemy import create_engine, inspect, insert, MetaData, Table
from analysissupport.dlc_support import auxiliaryfunctions

from analysissupport.dlc_support import *
from analysissupport.dlc_support.auto_extraction import AutoFrameExtraction

config = '/Volumes/GoogleDrive/My Drive/Test Exchange/Spinal Implant-Sam-2021-10-05/config.yaml'

videofile_pathlist = ['/Volumes/GoogleDrive/My Drive/Test Exchange/combined_vids',]
videoListObject = ProcessVideoList(videofile_pathlist)
videoUnprocessList = videoListObject.getListofUnprocessedVideos()

autoExtract = AutoFrameExtraction(config=config,
                                  videoUnprocessList=videoUnprocessList)
videoPath = '/Volumes/GoogleDrive/My Drive/Test Exchange/combined_vids/cam2_D1-220603-142830_200f-11e100g.avi'
DataFiltered = autoExtract.getFilteredFrames(videoPath)

videoName = Path(videoPath).stem
Scorers = list(set(DataFiltered.columns.get_level_values('scorer')))
bodyparts = list(set(DataFiltered.columns.get_level_values('bodyparts')))
coords = list(set(DataFiltered.columns.get_level_values('coords')))
indexes = list(DataFiltered.index.values)

indexlength = int(np.ceil(np.log10(max(indexes))))
data_list = []
for listindex, index in enumerate(indexes):
    for scorerindex, loopscorer in enumerate(Scorers):
        for bpindex, bp in enumerate(bodyparts):
            
            if np.isfinite(
                DataFiltered[loopscorer][bp]["y"][index]
                + DataFiltered[loopscorer][bp]["x"][index]
            ):
                y, x = (
                    (DataFiltered[loopscorer][bp]["y"][index]),
                    (DataFiltered[loopscorer][bp]["x"][index]),
                )

                likelihood = DataFiltered[loopscorer][bp]["likelihood"][index]
                bodypart = bp
                frame_num = index
                frame_name = (
                        "/img"
                        + str(index).zfill(indexlength)
                        + ".png"
                )
                
                data_entry = {
                    "frame_num": str(frame_num),
                    "frame_name": frame_name,
                    "video_name": videoName,
                    "coord_x": x.astype(float),
                    "coord_y": y.astype(float),
                    "coord_z": 0,
                    "likelihood": likelihood.astype(float),
                    "bodypart": bodypart
                }
                
                data_list.append(data_entry.copy())

engine = create_engine('postgresql://localhost:5432/treschdeeplabcut')

metadata_obj = MetaData()
metadata_obj.reflect(bind=engine)

frame_data = metadata_obj.tables['frame_data']
#DataCombined[loopscorer][bp]["y"][imagenr]

with engine.connect() as conn:
    result = conn.execute(
            insert(frame_data), data_list[1:])


inspector = inspect(engine)
schemas = inspector.get_schema_names()

for schema in schemas:
    print("schema: %s" % schema)
    for table_name in inspector.get_table_names(schema=schema):
        for column in inspector.get_columns(table_name, schema=schema):
            print("Table: %s Column: %s" % (table_name, column))