# -*- coding: utf-8 -*-

"""
This file is part of eyelinkparser.

eyelinkparser is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

eyelinkparser is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with datamatrix.  If not, see <http://www.gnu.org/licenses/>.
"""


from datamatrix import operations as ops
from matplotlib import pyplot as plt
import seaborn as sns


def data_quality (data, signal, baseline, group, 
                  z_threshold=2, downsample=10, 
                  xlabel_trace='Time (ms)', ylabel_trace='Pupil size (mm)',
                  ylim_trace=None, xlabel_hist='Baseline pupil size (mm)', 
                  ylabel_hist='Density',  xlim_hist=(-1.5, 1.5)):
    """
    desc:
        This function checks data quality by plotting raw baseline pupil sizes,
        z-scored baseline pupil sizes, and prints the number of trials before
        and after outlier trials exclusion.

    arguments:
        data:
            desc: Indicates to-be-analyzed dataset
            type: datamatrix
        signal: Indicates the signal whose quality is to be checked (usually pupil traces).
         type: SeriesColum
        baseline:
            desc: The column with baseline values.
            type: BaseColumn
        group:
            desc:   The column according to which data should be split          (usually subjects id)
            type: BaseColumn
        z_threshold:
            desc:   The cut-off z-score value for outliers exclusion. 
            Default is 2.
            type: integer
        downsample:
            desc:   The value according to which data is downsampled. 
            Used to convert x-axis of plots to original units. Default is 10.
            type: integer
        xlabel_trace:
            desc:   The label of the x-axis of the trace plot (left panel). 
            Default is 'Time (ms)'.
            type: string
        ylabel_trace:
            desc:   The label of the y-axis of the trace plot (left panel). 
            Default is 'Pupil size (mm)'.
            type: string
        ylim_trace:
            desc:   The limit of the y-axis of the trace plot (left panel). 
            type: float/tuple
        xlabel_hist:
            desc:   The label of the x-axis of the histogram plot (right panel). 
            Default is 'Baseline pupil size (mm)'.
            type: string
        ylabel_hist:
            desc:   The label of the y-axis of the histogram plot (right panel). 
            Default is 'Density'.
            type: string
        xlim_hist:
            desc: The limit of the x-axis of the histogram plot (right panel).
            Default is ±1.5 from cut-off z-value (calculated based on determined     z-threshold).
            type: float/tuple
    """
    if group is None:
        _data_quality_group_plot(signal,baseline,z_threshold,
                                 downsample, xlabel_trace, ylabel_trace,
                                 ylim_trace, xlabel_hist, 
                                 ylabel_hist, xlim_hist)
    else:
        for group, sdata in ops.split(group):
            print('Subject {}'.format(group))
            _data_quality_group_plot(signal[sdata], 
                                     baseline[sdata], z_threshold,
                                     downsample, xlabel_trace, ylabel_trace, 
                                     ylim_trace, xlabel_hist, ylabel_hist, xlim_hist)
    data.z_baseline = ops.z(baseline)
    print('Number of trials before removing outliers: N(trial) = {}'.format(len(data)))
    data = data.z_baseline >= -z_threshold 
    data = data.z_baseline <= z_threshold 
    print('Number of trials after removing outliers: N(trial) = {}'.format(len(data)))


def _data_quality_group_plot(signal, baseline, 
                             z_threshold,downsample,
                             xlabel_trace, ylabel_trace, 
                             ylim_trace, xlabel_hist, 
                             ylabel_hist, xlim_hist):
    plt.figure(figsize=(12, 6))
    plt.subplot(121)
    plt.title(r"$\bf{" + 'a) ' + "}$" + ' Pupil traces', fontsize=14, loc='left')
    plt.plot(signal.plottable, alpha=.2)
    plt.xlim(0, signal.depth)
    plt.xticks(range(0,signal.depth, 50), range(0*downsample,(signal.depth*downsample), 50*downsample))
    plt.xlabel(xlabel_trace)
    plt.ylabel(ylabel_trace)
    plt.ylim(ylim_trace)
    plt.subplot(122)
    plt.title(r"$\bf{" + 'b) ' + "}$" + ' Baseline pupil sizes', fontsize=14, loc='left')
    baseline_mean = baseline.mean
    baseline_std = baseline.std
    cutoff1 = baseline_mean -z_threshold*baseline_std
    cutoff2 = baseline_mean +z_threshold*baseline_std
    plt.axvline(cutoff1,color='black',linestyle=':')
    plt.axvline(cutoff2,color='black',linestyle=':')
    plt.xlabel(xlabel_hist) 
    plt.ylabel(ylabel_hist)
    sns.distplot(baseline)
    plt.xlim(cutoff1+xlim_hist[0], cutoff2+xlim_hist[1])
    plt.show()
