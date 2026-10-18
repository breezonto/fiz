"""
SalienTime-style layout template for Python Shiny.
Run:  pip install shiny shinywidgets plotly matplotlib numpy
      shiny run app.py
"""

import base64, io
import numpy as np
import matplotlib
import matplotlib.pyplot    as plt
import plotly.graph_objects as go


from shiny                  import App, reactive, render, ui
from shinywidgets           import output_widget, register_widget
from plotly.colors          import sequential

matplotlib.use("Agg")

# ---- mock data ----
LON    = np.linspace(-180, 180, 180)
LAT    = np.linspace(-75, 75, 90)
FRAMES = 40


_rng           = np.random.RandomState(42)
_lon2d, _lat2d = np.meshgrid(LON, LAT)


DATA = np.stack([
    0.5 * (1 + np.sin(_lat2d / 12)) * (0.6 + 0.4 * np.cos(_lon2d / 20 + t * 0.3))
    + 4 * np.exp(-((( (_lon2d - (-140 + 9 * t)) ** 2) / 220)
                   + ((_lat2d - 30 * np.sin(t / 6)) ** 2) / 100))
    + _rng.rand(*_lon2d.shape) * 0.15
    for t in range(FRAMES)
])                                    # (FRAMES, 90, 180) mock "wave height"

SAL = DATA.reshape(FRAMES, -1).max(axis=1)   # saliency curve per frame


MAP_LAYOUT = dict(
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
    geo=dict(
        projection_type="natural earth",
        bgcolor="#0e1117", landcolor="#3a4a2e",
        oceancolor="#173c63", showocean=True, showcountries=True,
        countrycolor="#666", coastlinecolor="#888",
        lataxis_range=[-75, 85], lonaxis_range=[-180, 180],
    ),
    coloraxis=dict(colorscale="Spectral", colorbar=dict(thickness=10,
                    len=0.6, x=0.01, y=0.45, title=dict(text="m"))),
)


def thumb_png(frame: int) -> str:
    """Render one frame to a base64 PNG for the filmstrip."""
    fig, ax = plt.subplots(figsize=(1.6, 0.9), dpi=60)
    ax.imshow(DATA[frame], cmap="Spectral", aspect="auto",
              extent=[-180, 180, -75, 75], origin="lower")
    ax.axis("off")
    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

THUMBS = [thumb_png(t) for t in range(FRAMES)]


def map_fig(frame: int) -> go.Figure:
    fig = go.Figure()
    if hasattr(go, "Heatmapgeo"):          # plotly >= 5.24: real geo projection
        fig.add_trace(go.Heatmapgeo(
            z=DATA[frame], lon=LON, lat=LAT, geo="geo", coloraxis="coloraxis",
            hovertemplate="%{lon:.1f}, %{lat:.1f}<br>%{z:.2f} m<extra></extra>"))
        fig.update_layout(**MAP_LAYOUT)
    else:                                  # any plotly: cartesian lon/lat raster
        fig.add_trace(go.Heatmap(
            x=LON, y=LAT, z=DATA[frame], coloraxis="coloraxis",
            hovertemplate="%{x:.1f}, %{y:.1f}<br>%{z:.2f} m<extra></extra>"))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            coloraxis=dict(colorscale="Spectral", colorbar=dict(
                thickness=10, len=0.6, x=1.0, y=0.45, title=dict(text="m"))),
            xaxis=dict(range=[-180, 180], title="longitude", color="#888"),
            yaxis=dict(range=[-75, 85], title="latitude", color="#888"))
    return fig


def timeline_fig(frame: int, window: int) -> go.Figure:
    fig = go.Figure()
    lo, hi = max(0, frame - window // 2), min(FRAMES - 1, frame + window // 2)
    fig.add_trace(go.Scatter(y=SAL, mode="lines", line=dict(color="#7fd4c1"),
                             fill="tozeroy", fillcolor="rgba(127,212,193,.15)",
                             hovertemplate="t=%{x}<br>saliency=%{y:.2f}<extra></extra>"))
    fig.add_shape(type="rect", x0=lo, x1=hi, y0=0, y1=SAL.max(),
                  fillcolor="rgba(255,255,255,.08)", line_width=0)
    fig.add_vline(x=frame, line_color="#ffb347", line_width=2)
    fig.update_layout(margin=dict(l=20, r=10, t=5, b=20),
                      paper_bgcolor="#111", plot_bgcolor="#111",
                      font_color="#ccc", height=110,
                      xaxis=dict(title="time step", range=[0, FRAMES - 1]),
                      yaxis=dict(title="salient variation"))
    return fig


def latent_fig() -> go.Figure:
    rng = np.random.RandomState(7)
    t = np.linspace(0, 4 * np.pi, 60)
    x = np.r_[np.cos(t) * 40 + rng.randn(60) * 5,
              np.cos(t) * 30 + 60 + rng.randn(60) * 5,
              np.sin(t) * 35 + 20 + rng.randn(60) * 5]
    y = np.r_[np.sin(t) * 25 + rng.randn(60) * 5,
              np.sin(t) * 20 + 40 + rng.randn(60) * 5,
              np.cos(t) * 30 + 70 + rng.randn(60) * 5]
    c = np.repeat([0, 1, 2], 60)
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="markers",
        marker=dict(size=6, color=c, colorscale="Spectral", opacity=0.8,
                    line=dict(color="#111", width=1)),
        hoverinfo="skip"))
    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5), height=180,
                      paper_bgcolor="#151b1f", plot_bgcolor="#151b1f",
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

# ---------------------------------------------------------------- UI

def _select_btn_(name, label):
    return ui.input_action_button(name, label, class_="btn-sm btn-secondary")


'''

The mock-up of the html and DOM

'''
app_ui = ui.page_fluid(
    ui.include_css("www/style.css"),
    ui.include_js("www/app.js"),

    ui.div(
        {"class": "grid"},

        # =========================================================
        # Main map / canvas
        # =========================================================

        ui.div(
            {"class": "mapwrap"},

            ui.div(
                {"class": "map-plot"},
                
                output_widget("map"),
            ),

            # -----------------------------------------------------
            # Floating inset preview
            # -----------------------------------------------------

            ui.div(
                {"class": "inset"},

                ui.div(
                    {"class": "lbl inset-toggle"},
                    "Preview Inset",
                    ui.tags.span("⌃", class_="inset-arrow"),
                ),

                ui.div(
                    {"class": "inset-content"},
                    ui.output_ui("inset"),
                ),
            ),

            # -----------------------------------------------------
            # Floating playback controls
            # -----------------------------------------------------

            ui.div(
                {"class": "play"},

                _select_btn_("prev10", "⏮"),
                _select_btn_("prev", "◀"),
                _select_btn_("next", "▶"),
                _select_btn_("next10", "⏭"),
                _select_btn_("mark", "🔖"),
            ),

            # -----------------------------------------------------
            # Floating filmstrip + timeline
            # -----------------------------------------------------

            ui.div(
                {"class": "bottom"},

                ui.div(
                    {"class": "strip"},
                    ui.output_ui("strip"),
                ),

                output_widget(
                    "timeline",
                    height="110px",
                ),
            ),
        ),

        # =========================================================
        # Sidebar
        #
        # IMPORTANT:
        # The button and panel are siblings inside this wrapper.
        # =========================================================
        ui.div(
            {"class": "sidebar-container"},

            # -----------------------------------------------------
            # Actual sidebar
            # -----------------------------------------------------

            ui.div(
                {"class": "side"},

                ui.div(
                    {"class": "side-content"},

                    ui.h4("SalienTime"),

                    ui.input_select(
                        "dataset",
                        "Select Dataset:",
                        {
                            "waves": (
                                "Significant Height of Wind and Swell Waves "
                                "(WAVEWATCH III)"
                            ),
                            "temp": "Sea Surface Temperature (mock)",
                            "wind": "Surface Wind Speed (mock)",
                        },
                    ),

                    ui.tags.p(
                        {"class": "description"},
                        "Mock dataset description. Saliency marks frames "
                        "whose spatial patterns are structurally or "
                        "statistically unusual.",
                    ),

                    ui.h5("Saliency Definition:"),

                    ui.input_slider(
                        "structural",
                        "Structural:",
                        0,
                        100,
                        90,
                    ),

                    ui.input_slider(
                        "statistical",
                        "Statistical:",
                        0,
                        100,
                        10,
                    ),

                    ui.input_radio_buttons(
                        "agg",
                        "Aggregation:",
                        {
                            "MAX": "MAX",
                            "MIN": "MIN",
                            "AVG": "AVG",
                        },
                        inline=True,
                    ),

                    ui.input_slider(
                        "steps",
                        "Time Steps:",
                        1,
                        20,
                        10,
                    ),

                    ui.h5("Latent Space:"),

                    output_widget(
                        "latent",
                        height="180px",
                    ),

                    ui.h5("Details:"),

                    ui.output_ui("details"),

                    ui.div(
                        {"class": "cbar"},
                    ),

                    ui.tags.div(
                        {"class": "colormap-label"},
                        "Colormap: Spectral · Mapping: Linear",
                    ),
                ),
            ),

            # -----------------------------------------------------
            # Toggle button
            #
            # This is NOT inside .side.
            # -----------------------------------------------------

            ui.tags.button(
                ">",
                id     = "toggle_sidebar",
                class_ = "sidebar-toggle",
                type   = "button",
            ),
        ),
    ),
)


# hidden slider backing the frame state (drives filmstrip highlight too)
app_ui = ui.page_fluid(
    ui.div({"style": "display:none"},
           ui.input_slider("frame", None, 1, FRAMES, 1, ticks=False)),
    app_ui)


def server(input, output, session):

    @reactive.calc
    def frame():
        return int(np.clip(input.frame() - 1, 0, FRAMES - 1))

    # filmstrip click -> sets input.frame
    ui.insert_ui(ui.tags.script("""
        $(document).on('click', '.strip img', function(){
          Shiny.setInputValue('frame', parseInt(this.dataset.f)+1,
                              {priority:'event'});
        });"""), selector="head")

    map_w = register_widget("map", go.FigureWidget(map_fig(0)))
    
    register_widget("latent", latent_fig())
    tl_w = register_widget("timeline", go.FigureWidget(timeline_fig(0, 10)))

    @reactive.effect
    @reactive.event(input.next)
    def _next():
        ui.update_slider("frame", value=min(FRAMES, input.frame() + 1))
    
    @reactive.effect
    @reactive.event(input.prev)
    def _prev():
        ui.update_slider("frame", value=max(1, input.frame() - 1))
    
    @reactive.effect
    @reactive.event(input.next10)
    def _next10():
        ui.update_slider("frame", value=min(FRAMES, input.frame() + 10))
    
    @reactive.effect
    @reactive.event(input.prev10)
    def _prev10():
        ui.update_slider("frame", value=max(1, input.frame() - 10))

    @render.ui
    def strip():
        f = frame()
        return [
            ui.tags.img({
                "src"    : f"data:image/png;base64,{THUMBS[t]}",
                "data-f" : t,
                "class"  : "sel" if t == f else ""
            })
            for t in range(FRAMES)
        ]

    @render.ui
    def inset():
        f = frame()
        return ui.tags.img({
            "src"   : f"data:image/png;base64,{THUMBS[f]}",
            "style" : "width:100%;display:block;"
        })

    @render.ui
    def details():
        f = frame(); d = DATA[f]
        return ui.tags.div(
            { 
                "class": "kv"
            },

            f"Frame: {f+1}/{FRAMES}<br>",
            f"Unit: Meter (M)<br>",
            f"Value @ center: {d[45,90]:.3f} (M)<br>",
            f"Global Max: {d.max():.2f} (M)<br>",
            f"Global Min: {d.min():.2f} (M)<br>",
            f"Frame Avg: {d.mean():.2f} (M)<br>",
            f"Saliency (MAX): {SAL[f]:.2f}"
        )

    @reactive.effect
    def _update():
        f = frame()

        with reactive.isolate():
            map_w.data[0].z = DATA[f]

            new_tl = timeline_fig(f, input.steps())
            tl_w.data[0].y = new_tl.data[0].y
            tl_w.layout.shapes = new_tl.layout.shapes


app = App(app_ui, server)