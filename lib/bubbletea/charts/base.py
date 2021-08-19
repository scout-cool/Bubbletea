import streamlit as st
import altair as alt
from altair.utils.schemapi import Undefined
from pandas import DataFrame, set_option, melt

from .heuristics import guess_x_config, guess_y_config, DEFAULT_X, DEFAULT_Y_EXTRA
from .colors import PALETTE

# Suppress SettingWithCopyWarning from pandas
set_option("mode.chained_assignment", None)


def _process_legacy_ys(legacyYs):
    if type(legacyYs) is dict:
        legacyYs = {**legacyYs}

    if "data" in legacyYs:
        data = legacyYs.pop("data")
        yExtra = {**legacyYs}
    elif type(legacyYs) is list:
        data = legacyYs
        yExtra = DEFAULT_Y_EXTRA
    else:
        raise "Unable to process configuration for Y"

    if (not "title" in yExtra) or (yExtra["title"] == None):
        yExtra["title"] = ", ".join(list(map(lambda d: d["title"] or d["field"], data)))

    return data, yExtra


# WARNING: Mutates frames
def _calculate_x_config(frames: DataFrame, x: alt.X):
    guessed_x_config = guess_x_config(x, frames)
    x_config = guessed_x_config["config"]
    x_tooltip_config = {**x_config, "timeUnit": Undefined}
    x_axis_config = guessed_x_config["axis"]

    if "title" in x_config:
        frames[x_config["title"]] = frames[x_config["field"]]
        x_config["field"] = x_config["title"]
        del x_config["title"]

    return (x_config, x_tooltip_config, x_axis_config)


# WARNING: Mutates frames
def _calculate_ys_config(frames: DataFrame, ys):
    yExtra = {**ys}
    data = yExtra.pop("data")
    ys_config = list(map(lambda y: guess_y_config(y, frames), data))

    for yc in ys_config:
        if "title" in yc["config"]:
            frames[yc["config"]["title"]] = frames[yc["config"]["field"]]

    return ys_config, yExtra


def _get_annotations(
    frames: DataFrame,
    base: alt.Chart,
    color,
    x_config,
    x_axis_config,
    x_tooltip_config,
    ys_config,
    yExtra=DEFAULT_Y_EXTRA,
):
    stack = yExtra.pop("stack") if "stack" in yExtra else False

    hover_selection = alt.selection(
        type="single",
        nearest=True,
        on="mouseover",
        fields=[x_config["field"]],
        empty="none",
    )
    click_selection = alt.selection_multi(
        nearest=True,
        on="click",
        fields=[x_config["field"]],
        empty="none",
    )

    # Draw a rule at the location of the selection
    hover_rule = (
        alt.Chart(frames)
        .mark_rule(color=color)
        .encode(
            x=alt.X(
                **x_config,
                axis=alt.Axis(
                    **x_axis_config,
                ),
            ),
            opacity=alt.condition(hover_selection, alt.value(1), alt.value(0)),
            tooltip=[
                alt.StringFieldDefWithCondition(
                    **x_tooltip_config, format=x_axis_config["format"]
                ),
                *list(
                    map(
                        lambda y_config: y_config["config"]["title"]
                        or y_config["config"]["field"],
                        ys_config,
                    )
                ),
            ],
        )
        .add_selection(hover_selection)
        .add_selection(click_selection)
    )

    multi_rules = (
        alt.Chart(frames)
        .mark_rule(color=color, xOffset=0.5)
        .encode(
            x=alt.X(
                **x_config,
                axis=alt.Axis(
                    **x_axis_config,
                ),
            ),
            opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
        )
        .transform_filter(click_selection)
    )

    if base == None:
        return hover_rule, multi_rules

    hover_point = base.mark_point().encode(
        y=alt.Y("value:Q", stack=stack),
        opacity=alt.condition(hover_selection, alt.value(1), alt.value(0)),
    )

    sticky_points = base.mark_point().encode(
        y=alt.Y("value:Q", stack=stack),
        opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
    )

    return hover_rule, multi_rules, hover_point, sticky_points


def _get_all_config(frames, x, ys):

    x_config, x_tooltip_config, x_axis_config = _calculate_x_config(frames, x)
    ys_config_all, yExtra = _calculate_ys_config(frames, ys)
    return x_config, x_tooltip_config, x_axis_config, ys_config_all, yExtra


def _plot_single(
    marker: str,
    df: DataFrame,
    x: alt.X = DEFAULT_X,
    y: "list[alt.Y]" = [],
    palette: list[str] = PALETTE,
    legend="right",  # could be 'left', 'right', 'none',
    orient="left",  # or 'right'
):
    frames = df.reset_index()

    x_config, x_tooltip_config, x_axis_config, ys_config_all, yExtra = _get_all_config(
        frames, x, y
    )

    legend_selection = alt.selection_multi(fields=["variable"], bind="legend")

    melted = melt(
        frames,
        id_vars=[x_config["field"]],
        value_vars=map(
            lambda y_config: y_config["config"]["title"]
            if "title" in y_config["config"]
            else y_config["config"]["field"],
            ys_config_all,
        ),
    )

    base = alt.Chart(melted).encode(
        alt.X(
            title="",
            **x_config,
            axis=alt.Axis(
                domain=False,
                grid=False,
                **x_axis_config,
            ),
        ),
        alt.Y(
            "value:Q",
            **yExtra,
            axis=alt.Axis(
                grid=False,
                orient=orient,
                **ys_config_all[0]["axis"],
            ),
        ),
        color=(
            alt.Color(
                "variable:N",
                legend=(
                    None if legend == "none" else alt.Legend(title="", orient=legend)
                ),
                scale=alt.Scale(range=palette[1:]),
            )
        ),
        # column=(
        #     alt.Column("variable:N", spacing=5, header=alt.Header(labelOrient="bottom"))
        # ),
        opacity=alt.condition(legend_selection, alt.value(0.75), alt.value(0.3)),
    )

    main = getattr(base, marker)(
        strokeJoin="round",
    ).add_selection(legend_selection)

    return main, base


def _plot_annotations(
    df: DataFrame,
    base: alt.Chart,
    x: alt.X = DEFAULT_X,
    y: "list[alt.Y]" = [],
    palette: list[str] = PALETTE,
):
    frames = df.reset_index()

    x_config, x_tooltip_config, x_axis_config, ys_config_all, yExtra = _get_all_config(
        frames, x, y
    )
    return _get_annotations(
        frames,
        base,
        palette[0],
        x_config,
        x_axis_config,
        x_tooltip_config,
        ys_config_all,
        yExtra,
    )


def _plot_simple(
    marker: str,
    df: DataFrame,
    x: alt.X = DEFAULT_X,
    y=None,
    palette=PALETTE,
    title: str = None,
    height: int = 400,
    legend="right",  # could be 'left', 'right', 'none',
):
    if title != None:
        st.subheader(title)

    chart, base = _plot_single(marker, df, y=y, x=x, palette=palette, legend=legend)
    annotations = _plot_annotations(df=df, base=base, y=y, x=x, palette=palette)

    st.altair_chart(
        alt.layer(chart, *annotations).properties(height=height),
        use_container_width=True,
    )


def _plot_combo(
    df: DataFrame,
    x: alt.X = DEFAULT_X,
    yLeft={},
    yRight={},
    palette=PALETTE,
    title: str = None,
    height: int = 400,
    legend="right",  # could be 'left', 'right', 'none',
    defaultMarker="mark_line",
):

    if title != None:
        st.subheader(title)

    leftData = yLeft.pop("data")
    rightData = yRight.pop("data")

    leftMarker = yLeft.pop("marker") if "marker" in yLeft else defaultMarker
    rightMarker = yRight.pop("marker") if "marker" in yRight else defaultMarker

    left, _ = _plot_single(
        leftMarker,
        df,
        x=x,
        y={"data": leftData, **yLeft},
        palette=palette,
        legend=legend,
        orient="left",
    )

    right, _ = _plot_single(
        rightMarker,
        df,
        x=x,
        y={"data": rightData, **yRight},
        palette=palette,
        legend=legend,
        orient="right",
    )

    annotations = _plot_annotations(
        df=df,
        base=None,
        y={"title": "", "data": leftData + rightData},
        x=x,
        palette=palette,
    )

    st.altair_chart(
        alt.layer(
            left,
            right,
            *annotations,
        )
        .properties(height=height)
        .resolve_scale(y="independent"),
        use_container_width=True,
    )


def legacy_plot(
    marker: str,
    df: DataFrame,
    x: alt.X = DEFAULT_X,
    ys: "list[alt.Y]" = None,
    yLeft: "list[alt.Y]" = None,
    yRight: "list[alt.Y]" = None,
    palette=PALETTE,
    height: int = 400,
    title: str = None,
    legend="right",  # could be 'left', 'right', 'none',
):
    if ys:
        data, yExtra = _process_legacy_ys(ys)

        _plot_simple(
            marker=marker,
            df=df,
            title=title,
            x=x,
            y={**yExtra, "data": data},
            palette=palette,
            height=height,
            legend=legend,
        )

    if yLeft != None and yRight != None:

        leftData, leftExtra = _process_legacy_ys(yLeft)
        rightData, rightExtra = _process_legacy_ys(yRight)

        _plot_combo(
            df=df,
            x=x,
            title=title,
            yLeft={**leftExtra, "data": leftData},
            yRight={**rightExtra, "data": rightData},
            palette=palette,
            height=height,
            legend=legend,
            defaultMarker=marker,
        )


# def _plot_dual(
#     marker: str,
#     df: DataFrame,
#     x: alt.X = DEFAULT_X,
#     ys: "list[alt.Y]" = None,
#     yLeft: "list[alt.Y]" = [],
#     yRight: "list[alt.Y]" = [],
#     palette=PALETTE,
#     height: int = 400,
#     title: str = None,
#     legend="right",  # could be 'left', 'right', 'none',
# ):
#     """Plot a line chart for the given data frame.

#     Parameters
#     ----------
#     df : pd.DataFrame (required)
#         The data frame to plot a line chart with.

#     x : altair.X (optional)
#         Configuration for altair X encoding. Default to {"field": "time", "type": "temporal"}

#     ys : List of altair.Y (required)
#         Configurations for altair Y encoding. E.g. {"field": "amount", "type": "quantitative"}

#         "field" is required, "type" and other formatting options will be inferred from the data on the best-effort basis.

#         `ys` will overwrite `yLeft` if both are defined.

#     yLeft : List of altair.Y (optional)
#         Configurations for left-side altair Y encoding.

#     yRight : List of altair.Y (optional)
#         Configurations for right-side altair Y encoding.

#     palette: List of colors (optional)
#         Color palette for data series, wil be used in order.

#     height: int (optional, default to 400)
#         Chart height in pixels.

#     title: str (optional)
#         Chart title.

#     legend: enum[left, right, none] (optional, default to left)
#         Chart legend setting.

#     Returns
#     -------
#     line_chart: altair.Chart
#         The line chart plotted.
#     """
#     if ys == None and len(yLeft) == 0 and len(yRight) == 0:
#         raise "Must define ys, yLeft, or yRight"

#     if ys != None and len(ys) != 0:
#         yLeft = ys

#     is_dual_y = len(yLeft) > 0 and len(yRight) > 0

#     frames = df.reset_index()

#     x_config, x_tooltip_config, x_axis_config = _calculate_x_config(frames, x)

#     ys_config_left, _ = _calculate_ys_config(frames, yLeft)
#     ys_config_right, _ = _calculate_ys_config(frames, yRight)
#     ys_config_all = ys_config_left + ys_config_right

#     if title != None:
#         st.subheader(title)

#     hover_rule, multi_rules = _get_annotations(
#         frames,
#         None,
#         palette[0],
#         x_config,
#         x_axis_config,
#         x_tooltip_config,
#         ys_config_all,
#         {},
#     )

#     def _get_base_chart(columnDef: alt.Y, axisDef: alt.Axis, index: int, orient="left"):

#         column_label = columnDef["field"] + "-label"
#         frames[column_label] = columnDef["title"] or columnDef["field"]
#         color = palette[index + 1]

#         base = alt.Chart(frames).encode(
#             alt.X(
#                 title="",
#                 # scale=alt.Scale(nice={"interval": "day", "step": 1}),
#                 **x_config,
#                 axis=alt.Axis(
#                     # values=frames[x_config["field"]].tolist(),
#                     domain=False,
#                     grid=False,
#                     **x_axis_config,
#                 ),
#             ),
#             alt.Y(
#                 axis=alt.Axis(
#                     titleColor=alt.Value(color),
#                     grid=(not is_dual_y),
#                     orient=orient,
#                     **axisDef,
#                 ),
#                 **columnDef,
#             ),
#             color=(
#                 alt.Color(
#                     field=column_label,
#                     type="ordinal",
#                     legend=(
#                         None
#                         if legend == "none"
#                         else alt.Legend(title="", orient=legend)
#                     ),
#                     scale=alt.Scale(range=palette[1:]),
#                 )
#             ),
#         )
#         main = getattr(base, marker)(
#             color=color,
#             strokeJoin="round",
#             opacity=(0.75 if len(ys_config_all) > 1 else 1.0),
#         )

#         # hover annotations
#         hover_point = base.mark_point(color=color).encode(
#             y=alt.Y(
#                 axis=alt.Axis(title=""),
#                 **columnDef,
#             ),
#             opacity=alt.condition(hover_selection, alt.value(1), alt.value(0)),
#         )

#         # sticky annotations
#         sticky_points = base.mark_point(color=color).encode(
#             y=alt.Y(
#                 axis=alt.Axis(title=""),
#                 **columnDef,
#             ),
#             opacity=alt.condition(click_selection, alt.value(1), alt.value(0)),
#         )

#         return {
#             "main": main,
#             "annotations": [] if marker == "mark_bar" else [hover_point, sticky_points],
#         }

#     charts = {"yLeft": [], "yRight": []}
#     annotations = {"yLeft": [], "yRight": []}
#     combined_charts = []

#     if len(yLeft) > 0:
#         for i, y in enumerate(ys_config_left):
#             chart_result = _get_base_chart(y["config"], y["axis"], i)
#             charts["yLeft"].append(chart_result["main"])
#             annotations["yLeft"] += chart_result["annotations"]

#         combined_charts.append(
#             alt.layer(*charts["yLeft"], *annotations["yLeft"]).properties(height=height)
#         )

#     if len(yRight) > 0:
#         for i, y in enumerate(ys_config_right):
#             chart_result = _get_base_chart(
#                 y["config"], y["axis"], i + len(ys_config_left), "right"
#             )
#             charts["yRight"].append(chart_result["main"])
#             annotations["yRight"] += chart_result["annotations"]

#         combined_charts.append(
#             alt.layer(*charts["yRight"], *annotations["yRight"]).properties(
#                 height=height
#             )
#         )

#     combined = (
#         alt.layer(*combined_charts, hover_rule, multi_rules)
#         .resolve_scale(y="independent")
#         .properties(height=height)
#     )

#     st.altair_chart(
#         combined,
#         use_container_width=True,
#     )
