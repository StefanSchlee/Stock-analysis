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
        self.all_figs = []  # store all figures for finalize()

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
            self.all_figs.append(self.fig)

        ax = self.axes[self.plot_count]
        self.plot_count += 1
        if title:
            ax.set_title(title)
        ax.grid(True)
        return ax

    def finalize(self):
        """Hide unused axes, add legends, and show all figures."""
        for fig in self.all_figs:
            axes = fig.get_axes()
            for ax in axes:
                handles, labels = ax.get_legend_handles_labels()
                if handles:  # only add legend if there are labeled items
                    ax.legend()
            # Hide unused subplots in last window
            if fig is self.all_figs[-1] and self.plot_count < self.plots_per_window:
                for i in range(self.plot_count, self.plots_per_window):
                    try:
                        fig.delaxes(axes[i])
                    except IndexError:
                        pass
            fig.tight_layout(rect=[0, 0, 1, 0.95])
        plt.tight_layout()
        plt.show()
