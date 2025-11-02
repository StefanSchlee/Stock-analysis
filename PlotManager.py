###########################
# helper for grouped plotting
###########################
import itertools
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path


class PlotManager:
    def __init__(self, rows=2, cols=2):
        self._rows = rows
        self._cols = cols
        self._plots_per_window = rows * cols
        self._fig = None
        self._axes = None
        self._plot_count = 0
        self._window_count = 0
        self._all_figs = []  # store all figures for finalize() or save_pdf()

    def next_axis(self, title: str | None = None, full: bool = False) -> Axes:
        """
        Get the next subplot axis in the current window.
        If full=True, create a new full-size figure instead of using the grid.
        """
        if full:
            # create a new full-size figure
            self._window_count += 1
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.suptitle(f"Stock Analysis – Full View {self._window_count}")
            if title:
                ax.set_title(title)
            ax.grid(True)
            self._all_figs.append(fig)
            return ax

        # grid-based small plot
        if self._fig is None or self._plot_count % self._plots_per_window == 0:
            # open new window
            self._window_count += 1
            self._fig, self._axes = plt.subplots(
                self._rows, self._cols, figsize=(10, 8)
            )
            self._axes = (
                list(itertools.chain.from_iterable(self._axes.reshape(-1, self._cols)))
                if hasattr(self._axes, "reshape")
                else self._axes.flatten()
            )
            self._fig.suptitle(f"Stock Analysis – Grid {self._window_count}")
            self._plot_count = 0
            self._all_figs.append(self._fig)

        ax = self._axes[self._plot_count]
        self._plot_count += 1
        if title:
            ax.set_title(title)
        ax.grid(True)
        return ax

    def finalize(self):
        """Hide unused axes, add legends, and show all figures."""
        for fig in self._all_figs:
            axes = fig.get_axes()
            for ax in axes:
                handles, labels = ax.get_legend_handles_labels()
                if handles:  # only add legend if there are labeled items
                    ax.legend()
            # Hide unused subplots in last window (for grid figures only)
            if (
                fig is self._all_figs[-1]
                and fig is self._fig
                and self._plot_count < self._plots_per_window
            ):
                for i in range(self._plot_count, self._plots_per_window):
                    try:
                        fig.delaxes(axes[i])
                    except IndexError:
                        pass
            fig.tight_layout(rect=[0, 0, 1, 0.95])
        plt.tight_layout()
        plt.show()

    def save_pdf(self, filename: str | Path):
        """Save all stored figures to a single multi-page PDF."""
        if not self._all_figs:
            print("No figures to save.")
            return

        # ensure folder exists
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure file ends with .pdf
        path = path.with_suffix(".pdf")

        with PdfPages(path) as pdf:
            for fig in self._all_figs:
                pdf.savefig(fig)

        print(f"Saved {len(self._all_figs)} figure(s) to '{path}'")
