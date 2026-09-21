"""Shared Plotly layout defaults so every chart looks consistent."""

TRANSPARENT = "rgba(0,0,0,0)"

# Horizontal legend sitting above the plot, aligned to the right
TOP_RIGHT_LEGEND = dict(
    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
)


def apply_base_layout(fig, *, height: int, margin: dict, **layout):
    """Apply the shared transparent background plus chart-specific overrides."""

    fig.update_layout(
        height=height,
        margin=margin,
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        **layout,
    )
    return fig
