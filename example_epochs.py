import mne
import microstates as mst
import seaborn as sb
import matplotlib.pyplot as plt
import numpy as np

from mne.datasets import sample
fname = sample.data_path() + '/MEG/sample/sample_audvis_filt-0-40_raw.fif'
raw = mne.io.read_raw_fif(fname, preload=True)

raw.info['bads'] = ['MEG 2443', 'EEG 053']
raw.set_eeg_reference('average')
raw.pick_types(meg='mag', eeg=True, eog=True, ecg=True, stim=True)
raw.filter(1, 40)

# Clean EOG with ICA
ica = mne.preprocessing.ICA(0.99).fit(raw)
bads_eog, _ = ica.find_bads_eog(raw)
bads_ecg, _ = ica.find_bads_ecg(raw)
ica.exclude = bads_eog[:2] + bads_ecg[:2]
raw = ica.apply(raw)

event_id = {'auditory/left': 1, 'auditory/right': 2, 'visual/left': 3,
            'visual/right': 4, 'smiley': 5, 'button': 32}
events = mne.find_events(raw)
epochs = mne.Epochs(raw, events, event_id=event_id, tmin=-0.2, tmax=.5,
                    preload=True)

# Select sensor type
# raw.pick_types(meg=False, eeg=True)
epochs.pick_types(meg=False, eeg=True)


#================ Microstates ================#
# Parameteres setting up
n_states = 4
n_inits = 5
EGI256 = False
sfreq = epochs.info['sfreq']

# Removing channels around the face and neck because of artefacts
if EGI256 == True:
    epochs.drop_channels(['E67',  'E73',  'E247', 'E251', 'E256', 'E243', 'E246', 'E250', 
                          'E255', 'E82',  'E91',  'E254', 'E249', 'E245', 'E242', 'E253',
                          'E252', 'E248', 'E244', 'E241', 'E92',  'E102', 'E103', 'E111', 
                          'E112', 'E120', 'E121', 'E133', 'E134', 'E145', 'E146', 'E156', 
                          'E165', 'E166', 'E174', 'E175', 'E187', 'E188', 'E199', 'E200', 
                          'E208', 'E209', 'E216', 'E217', 'E228', 'E229', 'E232', 'E233',  
                          'E236', 'E237', 'E240', 'E218', 'E227', 'E231', 'E235', 'E239', 
                          'E219', 'E225', 'E226', 'E230', 'E234', 'E238'])
n_epochs, n_chans, n_samples = epochs.get_data().shape


# Segment the data in microstates
maps, segmentation, gev, gfp_peaks = mst.segment(
        epochs.get_data(), n_states, n_inits, normalize=True, 
        min_peak_dist=10, max_n_peaks=10000)

# Smoothen the segmentation
segmentation_smooth = mst.seg_smoothing(data=epochs.get_data(), maps=maps)

# Mark each epoch at a beginning and at an end of an epoch w/ the value 88
seg_w_borders = mst.mark_border_msts(segmentation, n_epochs, n_samples, n_states) 
# Remove the values 88 of the segmentation
seg_wo_borders = seg_w_borders[seg_w_borders != 88]

# Plot the topographic maps of the microstates and the segmentation
mst.viz.plot_maps(maps, epochs.info)
# plot the whole segmentation
mst.viz.plot_segmentation(
    segmentation[:500], np.hstack(epochs.get_data())[:, :500], raw.times[:500])
# plot the segmentation of a single epoch
mst.viz.plot_segmentation(
    segmentation[99*106:100*106], epochs.get_data()[99], epochs.times)


#================ Analyses ================#
# Setup for the analyses and stats
epoched_data = True

# p_empirical 
p_hat = mst.analysis.p_empirical(segmentation, n_epochs, n_samples, n_states, 
                                 epoched_data)
print("\n\t Empirical symbol distribution (RTT):\n")
for i in range(n_states): 
    print("\n\t\t p", i, " = {0:.5f}".format(p_hat[i]))

# T_empirical
T_hat = mst.analysis.T_empirical(segmentation, n_states)
print("\n\t\tEmpirical transition matrix:\n")
mst.analysis.print_matrix(T_hat)
# Plot a heatmap of the mSt transitions
heat_map = sb.heatmap(T_hat, vmax= 0.15) #sum(T_hat)[0]/len(T_hat))
plt.show()

# Symmetry test for T_empirical
# alpha is the significance level
prob, T, df = mst.analysis.symmetryTest(X=segmentation, ns=n_states, alpha=0.01)

# Peaks Per Second (PPS)
fs = epochs.info['sfreq']
pps = len(gfp_peaks) / (len(segmentation)/fs)  # peaks per second
print("\n\t\tGFP peaks per sec.: {:.2f}".format(pps))

# Global Explained Variance (GEV)
print("\n\t\tGlobal explained variance (GEV):")
print ("\t\t" + str(gev))

#%% Mean durations of states 
mean_durs, all_durs = mst.analysis.mean_dur(segmentation, sfreq, n_states)
print("\n\t Mean microstate durations in ms:\n")
for i in range(n_states): 
    print("\t\tp_{:d} = {:.3f}".format(i, mean_durs[i]*1000))
# Histograms of durations per mst
bin_size = np.arange(1,84,4)
for i in range(n_states):
    # durations in ms
    all_dur = [(j/250)*1000 for j in all_durs[i]]
    plt.figure()
    plt.hist(all_dur, bins=bin_size)
    plt.xticks(bin_size)
    plt.yticks(np.arange(0, 1100, 100))
    plt.grid(True)
    plt.xlabel('Duration of mSts in ms')
    plt.ylabel('Number of mSts')
    
    
# Histograms of durations - all mSts together
labls = ['Microstate1', 'Microstate2', 'Microstate3', 'Microstate4']
bin_size = np.arange(0,22,1)
plt.figure()
plt.hist(all_durs, bins=bin_size, label=labls)
plt.xticks(bin_size)
plt.yticks(np.arange(0, 1300, 100))
plt.grid(True)
plt.legend(prop={'size': 10})
plt.xlabel('Duration of mSts in samples')
plt.ylabel('Number of mSts')

#%% Topo plots
# Path where to save the images/gifs:
path = '.../'

# Plot all topos of a single epoch
eps = epochs.get_data()
ep = eps[99]
# Transpose the epoch data from (ch_num, epo_length) to (epo_length, ch_num)
ep_T = np.transpose(ep)
for i in range(106):
    mst.viz.plot_maps(ep_T[i:i+1], epochs.info, i)
    plt.savefig(path + 'img' + str(i) + '.png')
    plt.close()

# Creating a gif of all the single topos
import imageio
filenames = [path + 'img'+str(i)+'.png' for i in range(106)]
with imageio.get_writer(path + 'movie.gif', mode='I') as writer:
    for filename in filenames:
        image = imageio.imread(filename)
        writer.append_data(image)
        
# Plot all topos in one figure
plt.figure(figsize=(2 * 10, 2 * 11)) # 11 rows, 10 col
for i, t_map in enumerate(ep_T):
    plt.subplot(11, 10, i + 1)
    mne.viz.plot_topomap(t_map, pos=epochs.info)
    plt.title('%d' % i )
plt.savefig(path + 'imgs.png')

########################################################################
# Plotting the original topo per epoch and next to it the topo of the attributed mst
eps = epochs.get_data()
ep_num = 99
ep = eps[ep_num]
num_chan, epo_len = ep.shape
ep_T = np.transpose(ep)
info = mne.pick_info(epochs[ep_num].info, 
                     mne.pick_types(epochs[ep_num].info, eeg=True))
seg = segmentation[ep_num*epo_len:(ep_num+1)*epo_len]

for i, t_map in enumerate(ep_T):
    mst_map = maps[seg[i]]
    topo_mst = np.concatenate([[t_map], [mst_map]])
    mst.viz.plot_maps(topo_mst[0:2], info, i)
    plt.savefig(path + 'topos'+ str(i) +'.png')
    plt.close()

from fpdf import FPDF
pdf = FPDF()
# imagelist is the list with all image filenames
imagelist = [path + 'topos'+str(i)+'.png' for i in range(epo_len)]
pdf.add_page()
for image in imagelist:
    pdf.image(image)
pdf.output(path +"topo_mst.pdf", "F")
########################################################################