#!/usr/bin/env python3

import sys
import lib.net as net
from lib.mpd import MPD
from lib.util import Source
import pkgutil


def load_plugins(mpd):
    plugins_dir = "plugins"

    # import
    plugins = []
    for el in pkgutil.iter_modules([plugins_dir]):
        plugin = el[1]
        try:
            p = pkgutil.importlib.import_module("{}.{}".format(plugins_dir, plugin))
        except:
            print("Unable to load plugin: {} (Import failed)".format(plugin))  # TODO log
            continue
        else:
            plugins.append(p)

    # load
    failed = []
    for i in range(len(plugins)):
        module = plugins[i]
        try:
            plugin = module.Plugin(mpd)
        except AttributeError:
            failed.append(module)
            print("Unable to load plugin: {} (No Plugin class)".format(module))  # TODO log
        except TypeError:
            failed.append(module)
            print("Unable to load plugin: {} (Plugin class: too few or too many parameters)".format(module))
        except:
            failed.append(module)
            print("Unable to load plugin: {} (Unknown error)".format(module))
        else:
            plugins[i] = plugin

    for el in failed:
        plugins.remove(el)

    return plugins


def main(args):
    proxy = net.init()
    mpd = MPD()
    plugins = load_plugins(mpd)


if __name__ == "__main__":
    main(sys.argv)
