import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from skimage import io, color
from tqdm import trange, tqdm
import pandas as pd


from analysissupport.dlc_support.auxiliaryfunctions import attempttomakefolder

def get_cmap(n, name="hsv"):
    """Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name."""
    return plt.cm.get_cmap(name, n)

def make_labeled_image(
    frame,
    DataCombined,
    imagenr,
    pcutoff,
    Scorers,
    bodyparts,
    colors,
    cfg,
    labels=["+", ".", "x"],
    scaling=1,
    ax=None,
):
    """Creating a labeled image with the original human labels, as well as the DeepLabCut's! """

    alphavalue = cfg["alphavalue"]  # .5
    dotsize = cfg["dotsize"]  # =15

    if ax is None:
        if np.ndim(frame) > 2:  # color image!
            h, w, numcolors = np.shape(frame)
        else:
            h, w = np.shape(frame)
        _, ax = prepare_figure_axes(w, h, scaling)
    ax.imshow(frame, "gray")
    for scorerindex, loopscorer in enumerate(Scorers):
        for bpindex, bp in enumerate(bodyparts):
            if np.isfinite(
                DataCombined[loopscorer][bp]["y"][imagenr]
                + DataCombined[loopscorer][bp]["x"][imagenr]
            ):
                y, x = (
                    int(DataCombined[loopscorer][bp]["y"][imagenr]),
                    int(DataCombined[loopscorer][bp]["x"][imagenr]),
                )
                if cfg["scorer"] not in loopscorer:
                    p = DataCombined[loopscorer][bp]["likelihood"][imagenr]
                    if p > pcutoff:
                        ax.plot(
                            x,
                            y,
                            labels[1],
                            ms=dotsize,
                            alpha=alphavalue,
                            color=colors(int(bpindex)),
                        )
                    else:
                        ax.plot(
                            x,
                            y,
                            labels[2],
                            ms=dotsize,
                            alpha=alphavalue,
                            color=colors(int(bpindex)),
                        )
                else:  # this is the human labeler
                    ax.plot(
                        x,
                        y,
                        labels[0],
                        ms=dotsize,
                        alpha=alphavalue,
                        color=colors(int(bpindex)),
                    )
    return ax


def create_minimal_figure(dpi=100):
    fig, ax = plt.subplots(frameon=False, dpi=dpi)
    ax.axis("off")
    ax.invert_yaxis()
    return fig, ax


def erase_artists(ax):
    for artist in ax.lines + ax.collections + ax.artists + ax.patches + ax.images:
        artist.remove()
    ax.figure.canvas.draw_idle()


def prepare_figure_axes(width, height, scale=1.0, dpi=100):
    fig = plt.figure(
        frameon=False, figsize=(width * scale / dpi, height * scale / dpi), dpi=dpi
    )
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.invert_yaxis()
    return fig, ax

def plot_and_save_labeled_frame(
    DataCombined,
    ind,
    frames2pick,
    indexlength,
    cfg,
    colors,
    comparisonbodyparts,
    DLCscorer,
    foldername,
    folderInput,
    fig,
    ax,
    scaling=1,
):
    image_path = os.path.join(folderInput, "img" + str(DataCombined.index[ind]).zfill(indexlength) + ".png")

    frame = io.imread(image_path)
    if np.ndim(frame) > 2:  # color image!
        h, w, numcolors = np.shape(frame)
    else:
        h, w = np.shape(frame)
    fig.set_size_inches(w / 100, h / 100)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.invert_yaxis()
    ax = make_labeled_image(
        frame,
        DataCombined,
        ind,
        cfg["pcutoff"],
        [DLCscorer],
        comparisonbodyparts,
        colors,
        cfg,
        scaling=scaling,
        ax=ax,
    )
    save_labeled_frame(fig, image_path, foldername)
    return ax


def save_labeled_frame(fig, image_path, dest_folder):
    path = Path(image_path)
    imagename = path.parts[-1]
    imfoldername = path.parts[-2]

    full_path = os.path.join(dest_folder, imagename)

    if len(full_path) >= 260 and os.name == "nt":
        full_path = "\\\\?\\" + full_path
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
    fig.savefig(full_path)


def Plotting(
    cfg, comparisonbodyparts, DLCscorer, DataCombined, frames2pick, indexlength, foldername, folderInput
):
    """ Function used for plotting GT and predictions """
    colors = get_cmap(len(comparisonbodyparts), name=cfg["colormap"])
    NumFrames = np.size(frames2pick)
    fig, ax = create_minimal_figure()
    for ind in tqdm(np.arange(NumFrames)):
        ax = plot_and_save_labeled_frame(
            DataCombined,
            frames2pick[ind],
            frames2pick,
            indexlength,
            cfg,
            colors,
            comparisonbodyparts,
            DLCscorer,
            foldername,
            folderInput,
            fig,
            ax,
        )
        erase_artists(ax)