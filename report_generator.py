import os
from datetime import datetime
import base64
import json

def generate_report(profile: dict, cutout_png_path: str, output_html_path: str):
    """
    Generates a premium, self-contained HTML report for the galaxy profile.
    Embeds the cutout PNG image as base64.
    """
    # Base64 encode cutout
    cutout_base64 = ""
    if cutout_png_path and os.path.exists(cutout_png_path):
        try:
            with open(cutout_png_path, "rb") as img_file:
                cutout_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Failed to base64 encode cutout: {e}")
            
    # Load spectrum data from companion spectrum.json if available
    spectrum_data_json = "{}"
    if profile.get("has_spectrum"):
        # The spectrum.json is stored in the same folder
        spec_path = os.path.join(os.path.dirname(output_html_path), "spectrum.json")
        if os.path.exists(spec_path):
            try:
                with open(spec_path, "r") as sf:
                    # Parse and downsample for faster rendering in HTML if needed
                    spec_data = json.load(sf)
                    wavelengths = spec_data.get("wavelengths", [])
                    flux = spec_data.get("flux", [])
                    
                    # Downsample to maximum 500 points to keep HTML loading snappy
                    if len(wavelengths) > 500:
                        step = len(wavelengths) // 500
                        wavelengths = wavelengths[::step]
                        flux = flux[::step]
                        
                    spectrum_data_json = json.dumps({
                        "wavelengths": [round(w, 2) for w in wavelengths],
                        "flux": [round(f, 4) for f in flux]
                    })
            except Exception as e:
                print(f"Failed to read spectrum for HTML: {e}")

    # Build self-contained HTML page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galaxy Profile: {profile.get("name", "Unknown")}</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --font-heading: 'Space Grotesk', system-ui, sans-serif;
            --font-body: 'Outfit', system-ui, sans-serif;
            --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
            
            --bg-dark: #090a0f;
            --bg-card: #121420;
            --accent: #6c5ce7;
            --accent-glow: rgba(108, 92, 231, 0.15);
            --text-main: #f1f2f6;
            --text-muted: #a4b0be;
            --border: #2f3542;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-body);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}

        h1 {{
            font-family: var(--font-heading);
            font-size: 2.8rem;
            font-weight: 700;
            letter-spacing: -1px;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }}

        .tagline {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        .badge {{
            background: var(--accent-glow);
            border: 1px solid var(--accent);
            color: var(--text-main);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            font-family: var(--font-heading);
        }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }}

        @media (min-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        .card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.75rem;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        }}

        h2 {{
            font-family: var(--font-heading);
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            border-left: 4px solid var(--accent);
            padding-left: 0.75rem;
        }}

        .meta-list {{
            list-style: none;
        }}

        .meta-list li {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .meta-list li:last-child {{
            border-bottom: none;
        }}

        .meta-label {{
            color: var(--text-muted);
            font-weight: 500;
        }}

        .meta-value {{
            font-family: var(--font-mono);
            font-weight: 600;
        }}

        .image-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 256px;
            background-color: #040508;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .image-container img {{
            max-width: 100%;
            max-height: 380px;
            object-fit: contain;
            display: block;
        }}

        .spectrum-card {{
            grid-column: 1 / -1;
        }}

        .no-data {{
            color: var(--text-muted);
            text-align: center;
            padding: 3rem 1rem;
            font-style: italic;
        }}

        footer {{
            margin-top: 3rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{profile.get("name", "Unknown Galaxy")}</h1>
                <p class="tagline">Galaxy Intelligence Platform — Analysis Report</p>
            </div>
            <div>
                <span class="badge">{profile.get("source", "SIMULATION")} Source</span>
            </div>
        </header>

        <div class="grid">
            <!-- Parameters Card -->
            <div class="card">
                <h2>Galaxy Parameters</h2>
                <ul class="meta-list">
                    <li>
                        <span class="meta-label">Primary Name</span>
                        <span class="meta-value">{profile.get("name", "N/A")}</span>
                    </li>
                    <li>
                        <span class="meta-label">Right Ascension (RA)</span>
                        <span class="meta-value">{profile.get("ra", 0.0):.6f}°</span>
                    </li>
                    <li>
                        <span class="meta-label">Declination (DEC)</span>
                        <span class="meta-value">{profile.get("dec", 0.0):.6f}°</span>
                    </li>
                    <li>
                        <span class="meta-label">Object Type</span>
                        <span class="meta-value">{profile.get("type", "Unknown")}</span>
                    </li>
                    <li>
                        <span class="meta-label">Redshift (z)</span>
                        <span class="meta-value">{profile.get("redshift") if profile.get("redshift") is not None else "N/A"}</span>
                    </li>
                    <li>
                        <span class="meta-label">Redshift Error</span>
                        <span class="meta-value">{profile.get("redshift_err") if profile.get("redshift_err") is not None else "N/A"}</span>
                    </li>
                    <li>
                        <span class="meta-label">Apparent Magnitude</span>
                        <span class="meta-value">{profile.get("mag") if profile.get("mag") is not None else "N/A"}</span>
                    </li>
                    <li>
                        <span class="meta-label">Photometric Filter</span>
                        <span class="meta-value">{profile.get("filter", "N/A")}</span>
                    </li>
                    <li>
                        <span class="meta-label">Photometric Error</span>
                        <span class="meta-value">{profile.get("phot_error") if profile.get("phot_error") is not None else "N/A"}</span>
                    </li>
                    <li>
                        <span class="meta-label">Image Quality</span>
                        <span class="meta-value">{profile.get("image_quality", "N/A")}</span>
                    </li>
                </ul>
            </div>

            <!-- Cutout Card -->
            <div class="card">
                <h2>FITS Image Cutout</h2>
                <div class="image-container">
                    {f'<img src="data:image/png;base64,{cutout_base64}" alt="Galaxy Cutout">' if cutout_base64 else '<div class="no-data">No FITS image data found or generated</div>'}
                </div>
                <div style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted); display: flex; justify-content: space-between;">
                    <span>Telescope: {profile.get("telescope", "N/A")}</span>
                    <span>Instrument: {profile.get("instrument", "N/A")}</span>
                </div>
            </div>

            <!-- Gaia Astrometry Card -->
            <div class="card">
                <h2>Gaia Astrometry (DR3)</h2>
                <ul class="meta-list">
                    <li>
                        <span class="meta-label">Parallax</span>
                        <span class="meta-value">{profile.get("parallax") if profile.get("parallax") is not None else "N/A"} mas</span>
                    </li>
                    <li>
                        <span class="meta-label">Parallax Error</span>
                        <span class="meta-value">{profile.get("parallax_error") if profile.get("parallax_error") is not None else "N/A"} mas</span>
                    </li>
                    <li>
                        <span class="meta-label">PM RA (Proper Motion RA)</span>
                        <span class="meta-value">{profile.get("pmra") if profile.get("pmra") is not None else "N/A"} mas/yr</span>
                    </li>
                    <li>
                        <span class="meta-label">PM DEC (Proper Motion DEC)</span>
                        <span class="meta-value">{profile.get("pmdec") if profile.get("pmdec") is not None else "N/A"} mas/yr</span>
                    </li>
                    <li>
                        <span class="meta-label">Gaia G Mean Mag</span>
                        <span class="meta-value">{profile.get("phot_g_mean_mag") if profile.get("phot_g_mean_mag") is not None else "N/A"}</span>
                    </li>
                </ul>
            </div>

            <!-- Aliases Card -->
            <div class="card">
                <h2>Identified Aliases</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                    {(" ").join([f'<span style="background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 0.25rem 0.6rem; border-radius: 4px; font-family: var(--font-mono); font-size: 0.9rem;">{alias}</span>' for alias in profile.get("aliases", [])]) if profile.get("aliases") else '<span style="color: var(--text-muted); font-style: italic;">No aliases identified</span>'}
                </div>
            </div>

            <!-- Spectrum Chart Card -->
            <div class="card spectrum-card">
                <h2>Spectroscopic Data</h2>
                {f'<canvas id="spectrumChart" style="width: 100%; max-height: 400px; background-color: #0b0c13; border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.05);"></canvas>' if profile.get("has_spectrum") else '<div class="no-data">No spectroscopic FITS dataset found or simulated for this object.</div>'}
            </div>
        </div>

        <footer>
            <p>Generated by Galaxy Intelligence Platform on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </div>

    <script>
        // Load spectrum if available
        const specData = {spectrum_data_json};
        if (specData.wavelengths && specData.wavelengths.length > 0) {{
            const ctx = document.getElementById('spectrumChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: specData.wavelengths,
                    datasets: [{{
                        label: 'Flux (10^-17 erg/s/cm^2/Å)',
                        data: specData.flux,
                        borderColor: '#6c5ce7',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Observed Wavelength (Å)',
                                color: '#a4b0be'
                            }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }},
                            ticks: {{ color: '#a4b0be' }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Flux',
                                color: '#a4b0be'
                            }},
                            grid: {{ color: 'rgba(255,255,255,0.05)' }},
                            ticks: {{ color: '#a4b0be' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    with open(output_html_path, "w") as f:
        f.write(html_content)
