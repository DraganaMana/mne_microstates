"""
Functions to visualize microstates.
"""
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
import seaborn as sns

import mne

def plot_segmentation(segmentation, data, times, n_states=4):
    """Plot a microstate segmentation.

    Parameters
    ----------
    segmentation : list of int
        For each sample in time, the index of the state to which the sample has
        been assigned.
    times : list of float
        The time-stamp for each sample.
    n_states : int
        The number of unique microstates to find. Defaults to 4.
    """
    
    colors = ["mediumpurple","steelblue", "skyblue","mediumseagreen"]
    from matplotlib.colors import ListedColormap
    my_cmap = ListedColormap(sns.color_palette(colors).as_hex())
    
    
    gfp = np.std(data, axis=0)
    
#    n_states = len(np.unique(segmentation))
    # Removed because for the group clustering it's a problem
    # as all the states might not appear in all subjects. 
    
    plt.figure(figsize=(6 * np.ptp(times), 2))
    cmap = my_cmap # plt.cm.get_cmap('plasma', n_states) # 
    plt.plot(times, gfp, color='black', linewidth=1)
    for state, color in zip(range(n_states), cmap.colors):
        plt.fill_between(times, gfp, color=color,
                         where=(segmentation == state))
    norm = mpl.colors.Normalize(vmin=0, vmax=n_states)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm)
    plt.yticks([])
    plt.xlabel('Time (s)')
    plt.title('Segmentation into %d microstates' % n_states)
    plt.autoscale(tight=True)
    plt.tight_layout()


def plot_maps(maps, info, num=None):
    """Plot prototypical microstate maps.

    Parameters
    ----------
    maps : ndarray, shape (n_channels, n_maps)
        The prototypical microstate maps.
    info : instance of mne.io.Info
        The info structure of the dataset, containing the location of the
        sensors.
    num : int
        The number to be written above the topo.
    """
    plt.figure(figsize=(2 * len(maps), 2))
    for i, t_map in enumerate(maps):
        plt.subplot(1, len(maps), i + 1)
        mne.viz.plot_topomap(t_map, pos=info)
        if num is not None:
            plt.title('%d' % num)
        else:
            plt.title('%d' % i )
