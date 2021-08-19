from pandas import DataFrame
from .base import legacy_plot, _plot_simple

MARKER = "mark_bar"


def legacy_plot_bar(df: DataFrame, **args):
    return legacy_plot(MARKER, df, **args)


def plot(df: DataFrame, **args):
    return _plot_simple(MARKER, df, **args)
