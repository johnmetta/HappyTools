import HappyTools.gui.progress_bar as progressbar
import HappyTools.gui.debug as debug
from HappyTools.gui.tooltip import ToolTip
from HappyTools.util.pdf import Pdf
from HappyTools.util.output import Output
from HappyTools.bin.chromatogram import Chromatogram
from HappyTools.bin.peak import Peak

from datetime import datetime
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.signal import argrelextrema
from numpy import greater, less, linspace, poly1d, polyfit
from bisect import bisect_left, bisect_right
from os import path, W_OK, access
from glob import glob

class Functions(object):
    def __init__(self, master):
        self.master = master

    def apply_calibration_function(self, master, data):
        """ TODO
        """
        time, intensity = zip(*data.data)
        data.data = zip(master.function(time), intensity)
        return data

    def batch_process(self, master):
        if master.batch_folder.get():

            self.abs_int = master.abs_int
            self.rel_int = master.rel_int
            self.gauss_int = master.gauss_int
            self.bck_sub = master.rel_int
            self.bck_noise = master.rel_int
            self.peak_qual = master.rel_int
            self.settings = master.settings
            self.batch_folder = master.batch_folder
            bar = progressbar.ProgressBar(self)

            if master.cal_file.get():

                self.reference = self.read_peak_list(master.cal_file.get())
                files = self.get_calibration_files(self)

                for index, file in enumerate(files):
                    data = Chromatogram(file)
                    self.calibrate_chrom(self, data)
                    bar.update_progress_bar(bar.progressbar,
                        bar.calibration_percentage, index, len(files))

            bar.update_progress_bar(bar.progressbar,
                bar.calibration_percentage, 1, 1)

            if master.anal_file.get():

                self.results = []
                self.reference = self.read_peak_list(master.anal_file.get())
                files = self.get_quantitation_files(self)

                for index, file in enumerate(files):
                    data = Chromatogram(file)
                    self.results.append({'file': path.basename(file),
                        'results': self.quantify_chrom(self, data)})
                    bar.update_progress_bar(bar.progressbar2,
                        bar.quantitation_percentage, index, len(files))

                self.output = Output(self)
                self.output.init_output_file(self)
                self.output.build_output_file(self)

                bar.update_progress_bar(bar.progressbar2,
                    bar.quantitation_percentage, 1, 1)

    def calibrate_chrom(self, master, data):
        self.time_pairs = self.find_peak(master, data)
        if len(self.time_pairs) >= master.settings.min_peaks:
            self.function = self.determine_calibration_function(self)
            data = self.apply_calibration_function(self, data)
            data.filename = path.join(master.batch_folder.get(),
                "calibrated_"+path.basename(data.filename))
        else:
            data.filename = path.join(master.batch_folder.get(),
                "uncalibrated_"+path.basename(data.filename))
        self.write_data(master, data)

    def create_tooltip(self, master, widget, text):
        """Create a tooltip.

        This function will create a tooltip and assign it to the widget that
        was handed to this function. The widget will then show the provided
        text upon a mouseover.

        Keyword arguments:
        widget -- tkinter object
        text -- string
        """
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def check_disk_access(self, master):
        disk_access = True
        for directory in master.directories:
            if not access(directory, W_OK):
                disk_access = False
        return disk_access

    def determine_breakpoints(self, master):
        time, intensity = zip(*master.data.data)
        low = bisect_left(time, master.time-master.window)
        high = bisect_right(time, master.time+master.window)

        f = InterpolatedUnivariateSpline(time[low:high], intensity[low:high])
        f_prime = f.derivative()

        new_x = linspace(time[low], time[high], 2500*(time[high]-time[low]))
        new_prime_y = f_prime(new_x)

        maxm = argrelextrema(new_prime_y, greater)
        minm = argrelextrema(new_prime_y, less)

        breaks = maxm[0].tolist() + minm[0].tolist()
        breaks = sorted(breaks)

        return breaks

    def determine_calibration_function(self, master):
        expected, observed = zip(*master.time_pairs)
        if master.settings.use_UPC == "False":
            z = polyfit(observed, expected, 2)
            function = poly1d(z)
        elif master.settings.use_UPC == "True":
            raise NotImplementedError("Ultra performance calibration has not "+
                "been implemented in the refactoring yet.")
        return function

    def find_peak(self, master, data):
        """ TODO
        """
        self.settings = master.settings
        self.data = data
        time_pairs = []

        time, intensity = zip(*data.data)

        for i in master.reference:

            self.peak = i[0]
            self.time = i[1]
            self.window = i[2]

            self.peak = Peak(self)
            self.peak.determine_background_and_noise(self)
            self.peak.determine_signal_noise(self)

            max_value = max(intensity[self.peak.low:self.peak.high])
            max_index = intensity[self.peak.low:self.peak.high].index(max_value)

            if self.peak.signal_noise >= master.settings.min_peak_SN:
                time_pairs.append((i[1], time[self.peak.low+max_index]))

        return time_pairs

    def get_calibration_files(self, master):
        """ TODO
        """
        calibration_files = []
        for files in master.settings.calibration_filetypes:
            for file in glob(path.join(master.batch_folder.get(), files)):
                if file not in master.settings.exclusion_files:
                    calibration_files.append(path.join(
                        master.batch_folder.get(), file))
        return calibration_files

    def get_quantitation_files(self, master):
        """ TODO
        """
        quantitation_files = []
        for files in master.settings.quantitation_filetypes:
            for file in glob(path.join(master.batch_folder.get(), files)):
                if file not in master.settings.exclusion_files:
                    quantitation_files.append(path.join(
                        master.batch_folder.get(), file))
        return quantitation_files

    def log(self, message):
        """ TODO
        """
        if debug.logging is True and debug.logLevel >= 1:
            with open(debug.logFile, 'a') as fw:
                fw.write(str(datetime.now().replace(microsecond=0))+"\t"+
                    str(message)+"\n")

    def peak_detection(self, master):
        raise NotImplementedError("This feature is not implemented in the " +
                                  "refactor yet.")

    def quantify_chrom(self, master, data):
        """ TODO
        """

        self.master = master
        self.reference = master.reference
        self.data = data
        self.settings = master.settings

        results = []

        time, intensity = zip(*data.data)

        # Initialize PDF and plot overview
        if master.settings.create_figure == "True" and bisect_left(
            time, master.settings.start) and bisect_right(time,
            master.settings.end):

                self.pdf = Pdf(self)
                self.pdf.plot_overview(self)

        # Iterate over peaks
        for i in self.reference:

            self.peak = i[0]
            self.time = i[1]
            self.window = i[2]

            self.peak = Peak(self)

            # Background correct
            self.peak.determine_background_and_noise(self)
            if self.peak.background < 0.:
                self.peak.background_correct(self)
                self.peak.determine_background_and_noise(self)

            # Determine Areas, background and noise
            self.peak.determine_peak_area(self)
            self.peak.determine_background_area(self)
            self.peak.determine_peak_noise(self)
            self.peak.determine_signal_noise(self)
            self.peak.determine_total_area(self)

            # Data Subset (based on second derivative)
            self.breaks = self.determine_breakpoints(self)
            self.data_subset = self.subset_data(self)

            # Gaussian fit
            self.peak.determine_gaussian_coefficients(self)
            if self.peak.coeff.any():
                self.peak.determine_gaussian_area(self)
                self.peak.determine_gaussian_parameters(self)
                self.peak.determine_height(self)
            self.peak.determine_residual(self)

            # Add individual peak to PDF
            if master.settings.create_figure == "True":
                self.pdf.plot_individual(self)

            # Results
            results.append({'peak': self.peak.peak,
                'time': self.peak.time,
                'peak_area': self.peak.peak_area,
                'gaussian_area': self.peak.gaussian_area,
                'signal_noise': self.peak.signal_noise,
                'background_area': self.peak.background_area,
                'peak_noise': self.peak.peak_noise,
                'residual': self.peak.residual,
                'background': self.peak.background,
                'noise': self.peak.noise,
                'fwhm': self.peak.fwhm,
                'actual_time': self.peak.actual_time})

        # Close PDF
        if master.settings.create_figure == "True":
            self.pdf.close(self)

        return results

    def read_peak_list(self, file_name):
        """Read and parse the peak file and return a list of peaks.

        This function opens the file that is specified in 'fileName', and
        reads it on a line per line basis. The function will split each
        line on '\t' prior to trying to append the parts to the 'peaks'
        list. The function will write a message to the logFile if logging
        is enabled if the previous mentioned try goes to the except clause.

        Keyword argments:
        fileName -- string
        """
        peaks = []
        try:
            with open(file_name, 'r') as fr:
                for line in fr:
                    line = line.rstrip("\n").split("\t")
                    try:
                        peaks.append((str(line[0]), float(line[1]),
                            float(line[2])))
                    except ValueError:
                        self.log("Ignoring line: "+str(line)+" from file: "+
                            str(file_name))
        except IOError:
            self.log("The selected reference file "+str(file)+" could not "+
                "be opened.")
        return peaks

    def save_calibrants(self, master):
        raise NotImplementedError("This feature is not implemented in the " +
                                  "refactor yet.")

    def save_annotation(self, master):
        raise NotImplementedError("This feature is not implemented in the " +
                                  "refactor yet.")

    def subset_data(self, master):

        max_point = 0
        time, intensity = zip(*master.data.data)
        low = bisect_left(time, master.time-master.window)
        high = bisect_right(time, master.time+master.window)

        f = InterpolatedUnivariateSpline(time[low:high], intensity[low:high])
        new_x = linspace(time[low], time[high], 2500*(time[high]-time[low]))
        new_y = f(new_x)

        x_data = new_x
        y_data = new_y

        # Subset the data
        # Region from newY[0] to breaks[0]
        try:
            if max(new_y[0:master.breaks[0]]) > max_point:
                max_point = max(new_y[0:master.breaks[0]])
                x_data = new_x[0:master.breaks[0]]
                y_data = new_y[0:master.breaks[0]]
        except IndexError:
            pass

        # Regions between breaks[x] and breaks[x+1]
        try:
            for index, j in enumerate(master.breaks):
                if max(new_y[master.breaks[index]:master.breaks[index+1]]) > max_point:
                    max_point = max(new_y[master.breaks[index]:
                        master.breaks[index+1]])
                    x_data = new_x[master.breaks[index]:master.breaks[index+1]]
                    y_data = new_y[master.breaks[index]:master.breaks[index+1]]
        except IndexError:
            pass

        # Region from break[-1] to newY[-1]
        try:
            if max(new_y[master.breaks[-1]:-1]) > max_point:
                max_point = max(new_y[master.breaks[-1]:-1])
                x_data = new_x[master.breaks[-1]:-1]
                y_data = new_y[master.breaks[-1]:-1]
        except IndexError:
            pass

        return zip(x_data, y_data)

    def write_data(self, master, data):
        """ TODO
        """
        try:
            with open(data.filename, 'w') as fw:
                for data_point in data.data:
                    fw.write(str(format(data_point[0], '0.'+str(
                        master.settings.decimal_numbers)+'f'))+"\t"+str(
                        format(data_point[1], '0.'+str(
                        master.settings.decimal_numbers)+'f'))+"\n")
        except IOError:
            self.log("File: "+str(path.basename(data.filename))+" could not "+
                "be opened.")