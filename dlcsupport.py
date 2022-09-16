import os
import os.path
import yaml
import click
from analysissupport.dlc_support import auxiliaryfunctions

pass_config = click.make_pass_decorator(dict)


def full_path(path):
    path_user = os.path.expanduser(path)
    path_full = os.path.abspath(path_user)
    path_norm = os.path.normpath(path_full)
    return path_norm

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

    return config

@click.group()
@click.version_option()
@click.option('--config', type=click.Path(exists=True, dir_okay=False),
              help='The config file to use instead of the default "config.yaml" .')
@click.pass_context
def cli(ctx, config):
    ctx.obj = load_config(config)

@cli.command()
@pass_config
def hello_world(config):
    click.echo('The working config path is ')
    click.echo(config['config-path'])

@cli.command()
@click.option('--repeat', default=1, help='Number of template .')
@pass_config
def generate_template_folder(config):
    from analysissupport.anipose_support.config_utils import generate_template
    click.echo('Creating template of folders ...')
    generate_template(config)
