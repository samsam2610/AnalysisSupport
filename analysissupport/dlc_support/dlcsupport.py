import os
import os.path
import yaml
import click
import json
from analysissupport.dlc_support import auxiliaryfunctions

def full_path(path):
    path_user = os.path.expanduser(path)
    path_full = os.path.abspath(path_user)
    path_norm = os.path.normpath(path_full)
    return path_norm

pass_config = click.make_pass_decorator(dict)

def load_config(fname):
    if fname is None:
        fname = 'config.yaml'

    if os.path.exists(fname):
        config = auxiliaryfunctions.read_config(fname)
    else:
        config = dict()

    # put in the defaults
    if 'path' not in config:
        if os.path.exists(fname) and os.path.dirname(fname) != '':
            config['path'] = os.path.dirname(fname)
        else:
            config['path'] = os.getcwd()

    config['path'] = full_path(config['path'])
    config['config-path'] = full_path(os.path.join(config['path'], 'config.yaml'))
    config['video-folder-list'] = []

    return config

@click.group(chain=True)
@click.version_option()
@click.option('--config',
              type=click.Path(exists=True, dir_okay=False),
              help='The config file to use instead of the default "config.yaml" .')
@click.pass_context
def cli(ctx, config):
    ctx.obj = load_config(config)
    click.echo('Current working directory of the config is ...')
    click.echo(ctx.obj['config-path'])

@cli.command()
@click.option("--likelihood",
              default=0.9999,
              help="The minimum likelihood of the frames to be extracted.")
@click.option("--video_folder",
              prompt=True,
              required=True,
              default="[]",
              help="List of folders containing the videos")
@click.option("--manual",
              default=False,
              help="Manual select videos to extract outliers")
@pass_config
def auto_extract_outlier(config, video_folder, likelihood, manual):
    video_folder = json.loads(video_folder)

    from analysissupport.dlc_support.processing_utils import ProcessVideoList
    videoListObject = ProcessVideoList(video_folder)

    videoUnprocessList = videoListObject.getListofUnprocessedVideos()
    click.echo('List of videos found is: ')
    click.echo(videoUnprocessList)

    if (manual is True):
        selected_videos = []
        for video in videoUnprocessList:
            if click.confirm('Do you want to extract the outlier of the {}?'.format(video)):
                selected_videos.append(video)
    else:
        selected_videos = videoUnprocessList
        
    if click.confirm('This will automatically extract outlier frames from your dataset. Do you want to continue?'):
        click.echo('Proceeding...')
        from analysissupport.dlc_support.auto_extraction import AutoFrameExtraction
        auto_frame_obj = AutoFrameExtraction(config=config['config-path'],
                                             videoUnprocessList=selected_videos)
        click.echo('Extracting frames ...')
        auto_frame_obj.extractFrameWithLikelihood(P=likelihood)
        click.echo('Done! Please go to the folders and check for extracted frames. Delete undersire frames from the folder before proceeding!!')

@cli.command()
@click.option("--video_folder",
              prompt=True,
              required=True,
              default="[]",
              help="List of folders containing the videos")
@click.option("--manual",
              default=False,
              help="Manual select videos to add outliers back")
@pass_config
def auto_add_outliers_back(config, video_folder, manual):
    video_folder = json.loads(video_folder)

    from analysissupport.dlc_support.processing_utils import ProcessVideoList
    videoListObject = ProcessVideoList(video_folder)

    videoUnprocessList = videoListObject.getListofUnprocessedVideos()
    click.echo('List of videos found is: ')
    click.echo(videoUnprocessList)

    if (manual is True):
        selected_videos = []
        for video in videoUnprocessList:
            if click.confirm('Do you want to extract the outlier of the {}?'.format(video)):
                selected_videos.append(video)
    else:
        selected_videos = videoUnprocessList
 
    if click.confirm('This will automatically add outlier frames from your the folders back to the labeled data folder. Do you want to continue?'):
        click.echo('Proceeding...')
        from analysissupport.dlc_support.auto_extraction import AutoFrameExtraction
        auto_frame_obj = AutoFrameExtraction(config=config['config-path'],
                                             videoUnprocessList=selected_videos)
        click.echo('Add new frames ...')
        auto_frame_obj.addFrameToLabeledData()

@cli.command()
@click.option("--add_iter",
              prompt=True,
              required=True,
              type=int,
              default=1000000,
              help="Additional iteration")
@pass_config
def set_config_continue(config, add_iter):
    from analysissupport.dlc_support.config_utils import setConfig_ContinueTraining
    setConfig_ContinueTraining(config['config-path'], additionalIteration=add_iter)

@cli.command()
@click.option("--video_folder",
              prompt=True,
              required=True,
              default="[]",
              help="List of folders containing the videos")
@click.option("--allow_growth",
              default=True,
              help="Allow the function to use all the GPU")
@click.option("--gputouse",
              default=None,
              help="Use nvidia-smi to specify which gpu number to user. Default is none.")
@click.option("--videotype",
              default=".avi",
              help="Set the type of videos that will be analyzed")
@click.option("--manual",
              default=False,
              help="Manual select videos to analyze")
@pass_config
def analyze_videos(config,
                   video_folder,
                   allow_growth,
                   manual,
                   gputouse,
                   videotype):

    video_folder = json.loads(video_folder)

    from analysissupport.dlc_support.processing_utils import ProcessVideoList
    videoListObject = ProcessVideoList(video_folder)

    videoUnprocessList = videoListObject.getListofUnprocessedVideos()
    click.echo('List of videos found is: ')
    click.echo(videoUnprocessList)

    if (manual is True):
        selected_videos = []
        for video in videoUnprocessList:
            if click.confirm('Do you want to extract the outlier of the {}?'.format(video)):
                selected_videos.append(video)
    else:
        selected_videos = videoUnprocessList

    if click.confirm('This will analyze all the videos found in the above folders. Do you want to continue?'):
        click.echo('Proceeding...')
        import deeplabcut
        deeplabcut.analyze_videos(config=config['config-path'],
                                  videos=selected_videos,
                                  videotype=videotype,
                                  allow_growth=allow_growth,
                                  gputouse=gputouse,
                                  save_as_csv=True,)

@cli.command()
@click.option("--net_type",
              default="resnet_101",
              help="Select the network type. Please put that in quote or double quotes. resnet_50, resnet_50")
@pass_config
def create_training_dataset(config, net_type):
    click.echo('Create new training dataset...')
    import deeplabcut
    deeplabcut.create_training_dataset(config=config['config-path'], net_type=net_type)

@cli.command()
@pass_config
def train_network(config):
    click.echo('Start training the network ...')
    import deeplabcut
    import tensorflow as tf
    deeplabcut.train_network(config=config['config-path'], shuffle=1, displayiters=10, saveiters=500)

@cli.command()
@pass_config
def hello_world(config):
    click.echo('The working config path is ')
    click.echo(config['config-path'])

if __name__ == '__main__':
    cli()