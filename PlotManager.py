###########################
# helper for grouped plotting
###########################
import itertools
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


class PlotManager:
    def __init__(self, rows=2, cols=2):
        self.rows = rows
        self.cols = cols
        self.plots_per_window = rows * cols
        self.fig = None
        self.axes = None
        self.plot_count = 0
        self.window_count = 0

    def next_axis(self, title=None) -> Axes:
        """Get the next subplot axis in the current window."""
        if self.fig is None or self.plot_count % self.plots_per_window == 0:
            # open new window
            self.window_count += 1
            self.fig, self.axes = plt.subplots(self.rows, self.cols, figsize=(10, 8))
            self.axes = list(itertools.chain.from_iterable(
                self.axes.reshape(-1, self.cols)
            )) if hasattr(self.axes, 'reshape') else self.axes.flatten()
            self.fig.suptitle(f"Stock Analysis – Window {self.window_count}")
            self.plot_count = 0
        ax = self.axes[self.plot_count]
        self.plot_count += 1
        if title:
            ax.set_title(title)
        ax.grid()
        ax.legend()
        return ax

    def finalize(self):
        """Hide any unused axes and show all figures."""
        if self.fig and self.plot_count < self.plots_per_window:
            for i in range(self.plot_count, self.plots_per_window):
                self.fig.delaxes(self.axes[i])
        plt.tight_layout()
        plt.show()
