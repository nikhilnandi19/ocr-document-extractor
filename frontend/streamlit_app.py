"""
OCR Document Extractor v2 — Streamlit frontend
Phase 4A: Polished pre-upload homepage

Design tokens and layout are adapted from the Google Stitch reference (DESIGN.md).
Post-upload results view will be redesigned in Phase 4B.
"""

import html
import io

import requests
import pandas as pd
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="OCR Document Extractor v2",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "result"   not in st.session_state: st.session_state.result   = None
if "filename" not in st.session_state: st.session_state.filename = None

FLASK_URL   = "http://localhost:5001"
EXTRACT_URL = f"{FLASK_URL}/api/extract-document"
HEALTH_URL  = f"{FLASK_URL}/api/health"
TIMEOUT     = 120

# ── Design tokens (Cognitive Clarity / DESIGN.md) ─────────────────────────────

P   = "#3525cd"      # primary
P2  = "#4f46e5"      # primary-container (used for buttons / interactive)
BG  = "#f9f9ff"      # background / surface
WH  = "#ffffff"      # surface-container-lowest
CL  = "#f0f3ff"      # surface-container-low
CM  = "#e7eefe"      # surface-container
CH  = "#e2e8f8"      # surface-container-high
TX  = "#151c27"      # on-surface
TV  = "#464555"      # on-surface-variant
OL  = "#777587"      # outline
OV  = "#c7c4d8"      # outline-variant
SC  = "#6cf8bb"      # secondary-container
OSC = "#00714d"      # on-secondary-container

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset Streamlit chrome ── */
#MainMenu,
header[data-testid="stHeader"],
.stDeployButton,
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] {{
    display: none !important;
}}
footer {{ visibility: hidden; }}

/* ── Page base ── */
html, body {{ scroll-behavior: smooth; }}
.stApp {{
    background-color: {BG} !important;
    font-family: 'Inter', sans-serif !important;
}}
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── Navigation ── */
.oc-nav {{
    background: {BG};
    border-bottom: 1px solid {OV};
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2.5rem;
    font-family: 'Inter', sans-serif;
    position: sticky;
    top: 0;
    z-index: 9999;
}}
.oc-nav-logo {{
    font-size: 18px;
    font-weight: 700;
    color: {P};
    display: flex;
    align-items: center;
    gap: 8px;
}}
.oc-nav-links {{
    display: flex;
    align-items: center;
    gap: 2rem;
}}
.oc-nav-link {{
    font-size: 14px;
    font-weight: 600;
    color: {TV};
    text-decoration: none;
    transition: color .15s;
    padding-bottom: 2px;
}}
.oc-nav-link:hover {{ color: {P}; }}
.oc-nav-link.active {{
    color: {P};
    border-bottom: 2px solid {P};
}}
.oc-nav-cta {{
    background: {P};
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: opacity .15s;
}}
.oc-nav-cta:hover {{ opacity: .88; }}

/* ── Hero ── */
.oc-hero {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 5rem 2.5rem 4rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3.5rem;
    align-items: center;
}}
.oc-hero-h1 {{
    font-size: 40px;
    font-weight: 700;
    color: {TX};
    line-height: 1.15;
    letter-spacing: -.02em;
    margin: 0 0 1rem;
    font-family: 'Inter', sans-serif;
}}
.oc-hero-sub {{
    font-size: 17px;
    color: {TV};
    line-height: 1.65;
    margin: 0 0 1.5rem;
    font-family: 'Inter', sans-serif;
}}
.oc-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 2rem;
}}
.oc-badge {{
    background: {CH};
    color: {TV};
    font-size: 12px;
    font-weight: 500;
    padding: 5px 14px;
    border-radius: 9999px;
    font-family: 'Inter', sans-serif;
}}
.oc-hero-btns {{
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
}}
.oc-btn-p {{
    background: {P2};
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    box-shadow: 0 2px 8px rgba(79,70,229,.3);
    transition: all .2s;
}}
.oc-btn-p:hover {{
    background: {P};
    box-shadow: 0 4px 16px rgba(79,70,229,.4);
}}
.oc-btn-s {{
    background: {BG};
    color: {P};
    border: 1.5px solid {P};
    border-radius: 8px;
    padding: 11px 24px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    transition: background .2s;
}}
.oc-btn-s:hover {{ background: {CL}; }}

/* ── Preview card ── */
.oc-preview {{
    background: {WH};
    border: 1px solid {CM};
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
}}
.oc-preview-hd {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
}}
.oc-preview-title {{
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Inter', sans-serif;
}}
.oc-conf {{
    background: {SC};
    color: {OSC};
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 9999px;
    font-family: 'Inter', sans-serif;
}}
.oc-pf {{
    background: {CL};
    border: 1px solid {CM};
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
}}
.oc-pf:last-child {{ margin-bottom: 0; }}
.oc-pf-lbl {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: {TV};
    margin-bottom: 4px;
    font-family: 'Inter', sans-serif;
}}
.oc-pf-val {{
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    font-family: 'Inter', sans-serif;
}}
.oc-pf-val.mono {{
    font-family: 'JetBrains Mono', monospace;
    color: {P};
}}
.oc-pf-ok {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 13px;
    font-weight: 500;
    color: {OSC};
    font-family: 'Inter', sans-serif;
}}

/* ── Section divider ── */
.oc-divider {{
    border: none;
    border-top: 1px solid {OV};
    margin: 0 2.5rem;
}}

/* ── Upload section ── */
.oc-upload-section {{
    padding: 3rem 2.5rem 0.5rem;
    background: {BG};
}}
.oc-upload-hd {{
    text-align: center;
    margin-bottom: 1.5rem;
}}
.oc-upload-title {{
    font-size: 26px;
    font-weight: 600;
    color: {TX};
    letter-spacing: -.01em;
    margin-bottom: .5rem;
    font-family: 'Inter', sans-serif;
}}
.oc-upload-sub {{
    font-size: 14px;
    color: {TV};
    font-family: 'Inter', sans-serif;
}}
.oc-privacy {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: {CM};
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 12px;
    color: {TV};
    max-width: 540px;
    margin: 0.75rem auto 3rem;
    font-family: 'Inter', sans-serif;
}}

/* ── Streamlit widget overrides ── */

/* Upload card container (st.container border=True) */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {WH} !important;
    border: 1px solid {CM} !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,.06) !important;
    padding: 0.5rem !important;
}}

/* File uploader drop zone */
[data-testid="stFileUploaderDropzone"] {{
    background: {BG} !important;
    border: 2px dashed {OV} !important;
    border-radius: 12px !important;
    padding: 2.5rem 1.5rem !important;
    transition: border-color .2s, background .2s !important;
    cursor: pointer !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {P2} !important;
    background: {CL} !important;
}}
[data-testid="stFileUploader"] label {{ display: none !important; }}

/* Spinner */
[data-testid="stSpinner"] {{ font-family: 'Inter', sans-serif !important; }}

/* Primary button */
.stButton > button[kind="primary"] {{
    background: {P2} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.8rem 1.5rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    box-shadow: 0 2px 8px rgba(79,70,229,.25) !important;
    transition: all .2s !important;
    letter-spacing: 0 !important;
    width: 100% !important;
}}
.stButton > button[kind="primary"]:hover:not(:disabled) {{
    background: {P} !important;
    box-shadow: 0 4px 16px rgba(79,70,229,.4) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"]:disabled {{
    background: {CH} !important;
    color: {OL} !important;
    box-shadow: none !important;
    transform: none !important;
    cursor: not-allowed !important;
}}

/* Secondary button */
.stButton > button[kind="secondary"] {{
    background: {WH} !important;
    color: {P} !important;
    border: 1.5px solid {P} !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: background .2s !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background: {CL} !important;
}}

/* Alerts */
[data-testid="stAlert"] {{
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}}

/* ── Process section ── */
.oc-process {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 4rem 2.5rem;
}}
.oc-section-h {{
    font-size: 24px;
    font-weight: 600;
    color: {TX};
    margin: 0 0 2rem;
    letter-spacing: -.01em;
    font-family: 'Inter', sans-serif;
}}
.oc-pgrid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
}}
.oc-pcard {{
    background: {WH};
    border: 1px solid {CM};
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}}
.oc-pnum {{
    font-size: 18px;
    font-weight: 700;
    color: {P2};
    margin-bottom: .875rem;
    font-family: 'Inter', sans-serif;
}}
.oc-ptitle {{
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    margin-bottom: .375rem;
    font-family: 'Inter', sans-serif;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.oc-pbody {{
    font-size: 14px;
    color: {TV};
    line-height: 1.55;
    font-family: 'Inter', sans-serif;
}}

/* ── Outputs section ── */
.oc-outputs {{
    background: {CL};
    padding: 4rem 2.5rem;
}}
.oc-out-inner {{
    max-width: 1200px;
    margin: 0 auto;
}}
.oc-ogrid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
}}
.oc-ocard {{
    background: {WH};
    border: 1px solid {CM};
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    transition: border-color .2s;
}}
.oc-ocard:hover {{ border-color: {P2}; }}
.oc-oico {{ font-size: 26px; margin-bottom: 12px; display: block; }}
.oc-otitle {{
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    margin-bottom: .375rem;
    font-family: 'Inter', sans-serif;
}}
.oc-obody {{
    font-size: 14px;
    color: {TV};
    line-height: 1.55;
    font-family: 'Inter', sans-serif;
}}

/* ── Footer ── */
.oc-footer {{
    background: {BG};
    border-top: 1px solid {OV};
    padding: 3rem 2.5rem;
    font-family: 'Inter', sans-serif;
}}
.oc-footer-inner {{
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1.5rem;
}}
.oc-footer-brand {{
    font-size: 14px;
    font-weight: 700;
    color: {P};
    margin-bottom: 4px;
}}
.oc-footer-copy {{
    font-size: 13px;
    color: {TV};
}}
.oc-footer-links {{
    display: flex;
    gap: 2rem;
}}
.oc-footer-link {{
    font-size: 14px;
    color: {TV};
    text-decoration: none;
    transition: color .15s;
}}
.oc-footer-link:hover {{ color: {P}; }}

/* ── Results page Phase 4B ── */

/* Section wrapper: centers + constrains width */
.oc-rs {{
    max-width: 1280px;
    margin: 0 auto 1.5rem;
    padding: 0 1.5rem;
}}

/* Nav results extra buttons */
.oc-nav-sec-btn {{
    background: {WH};
    color: {TX};
    border: 1px solid {OV};
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: background .15s;
    white-space: nowrap;
}}
.oc-nav-sec-btn:hover {{ background: {CL}; }}
.oc-nav-pri-btn {{
    background: {P};
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: opacity .15s;
    white-space: nowrap;
}}
.oc-nav-pri-btn:hover {{ opacity: .88; }}

/* Results header card */
.oc-res-header {{
    background: {WH};
    border: 1px solid {OV};
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
}}
.oc-res-icon-row {{
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    flex: 1;
}}
.oc-res-icon-wrap {{
    background: {SC};
    color: {OSC};
    width: 56px;
    height: 56px;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
}}
.oc-res-h1 {{
    font-size: 24px;
    font-weight: 600;
    color: {TX};
    line-height: 32px;
    letter-spacing: -0.01em;
    margin: 0;
    font-family: 'Inter', sans-serif;
}}
.oc-res-sub {{
    font-size: 16px;
    color: {TV};
    margin: 4px 0 0;
    font-family: 'Inter', sans-serif;
}}
.oc-res-fname {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: {CL};
    color: {TV};
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 8px;
    margin-top: 12px;
}}
.oc-res-btns {{
    display: flex;
    gap: 12px;
    align-items: center;
    flex-shrink: 0;
    flex-wrap: wrap;
}}

/* Metrics grid */
.oc-metrics {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
}}
.oc-metric-card {{
    background: {WH};
    border: 1px solid {OV};
    padding: 1.25rem;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}}
.oc-metric-lbl {{
    font-size: 14px;
    color: {TV};
    margin-bottom: 4px;
    font-family: 'Inter', sans-serif;
}}
.oc-metric-val {{
    font-size: 20px;
    font-weight: 700;
    color: {TX};
    line-height: 28px;
    font-family: 'Inter', sans-serif;
}}
.oc-metric-val.green {{ color: #006c49; }}
.oc-metric-val.amber {{ color: #b45309; }}
.oc-metric-val.red   {{ color: #ba1a1a; }}

/* Main 2-col grid */
.oc-main-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    align-items: start;
}}
.oc-fields-card, .oc-val-card {{
    background: {WH};
    border: 1px solid {OV};
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}
.oc-card-hd {{
    padding: 1rem 1.5rem;
    border-bottom: 1px solid {OV};
    background: {CL};
}}
.oc-card-title {{
    font-size: 20px;
    font-weight: 600;
    color: {TX};
    line-height: 28px;
    margin: 0;
    font-family: 'Inter', sans-serif;
}}
.oc-card-body {{ padding: 1.5rem; flex: 1; }}

/* Field rows */
.oc-field-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid {CH};
}}
.oc-field-row:last-child {{ border-bottom: none; }}
.oc-field-lbl {{
    font-size: 14px;
    font-weight: 600;
    color: {TV};
    font-family: 'Inter', sans-serif;
}}
.oc-field-rhs {{ display: flex; align-items: center; gap: 8px; }}
.oc-field-val {{ font-size: 16px; color: {TX}; font-family: 'Inter', sans-serif; }}
.oc-field-val.mono {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    background: {CH};
    padding: 2px 8px;
    border-radius: 4px;
    color: {P};
}}

/* Validation items */
.oc-val-items {{ display: flex; flex-direction: column; gap: 1rem; }}
.oc-val-item {{ display: flex; align-items: flex-start; gap: 1rem; }}
.oc-val-icon {{
    width: 30px;
    height: 30px;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 2px;
}}
.oc-val-icon.pass {{ background: rgba(108,248,187,0.25); color: #006c49; }}
.oc-val-icon.fail {{ background: rgba(186,26,26,0.10);  color: #ba1a1a; }}
.oc-val-title {{
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    margin: 0;
    font-family: 'Inter', sans-serif;
}}
.oc-val-desc {{
    font-size: 14px;
    color: {TV};
    margin: 2px 0 0;
    font-family: 'Inter', sans-serif;
}}
.oc-val-btn-row {{
    display: flex;
    gap: 12px;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}}

/* Tabs section */
.oc-tabs-wrap {{
    background: {WH};
    border: 1px solid {OV};
    border-radius: 12px;
    overflow: hidden;
}}
.oc-tab-bar {{
    display: flex;
    border-bottom: 1px solid {OV};
}}
.oc-tab-btn {{
    padding: 1rem 1.5rem;
    font-size: 14px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    border: none;
    background: transparent;
    transition: color .15s;
    color: {TV};
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}}
.oc-tab-btn.active {{ color: {P}; border-bottom-color: {P}; }}
.oc-tab-content {{ padding: 1.5rem; }}
.oc-raw-block {{
    background: {CM};
    border: 1px solid {OV};
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: {TX};
    height: 240px;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.7;
}}

/* Diagnostics table */
.oc-diag-wrap {{ overflow-x: auto; }}
.oc-diag-table {{
    width: 100%;
    border: 1px solid {OV};
    border-radius: 8px;
    border-collapse: collapse;
    overflow: hidden;
}}
.oc-diag-table th {{
    background: {CL};
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 700;
    color: {TV};
    border-bottom: 1px solid {OV};
    text-align: left;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: .04em;
}}
.oc-diag-table td {{
    padding: 10px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: {TX};
    border-bottom: 1px solid {CH};
}}
.oc-diag-table tr:last-child td {{ border-bottom: none; }}
.oc-diag-table td.conf {{ color: #006c49; }}

/* Developer section */
.oc-dev-wrap {{ border-top: 1px solid {OV}; padding-top: 1.5rem; }}
details.oc-dev {{ border: 1px solid {OV}; border-radius: 8px; overflow: hidden; }}
details.oc-dev summary {{
    list-style: none;
    padding: 1rem;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    font-weight: 600;
    color: {TX};
    user-select: none;
    font-family: 'Inter', sans-serif;
    transition: background .15s;
}}
details.oc-dev summary:hover {{ background: {CL}; }}
details.oc-dev summary::-webkit-details-marker {{ display: none; }}
details.oc-dev summary::after {{ content: '▾'; font-size: 14px; color: {TV}; }}
details.oc-dev[open] summary {{ border-bottom: 1px solid {OV}; }}
details.oc-dev[open] summary::after {{ content: '▴'; }}
.oc-dev-content {{
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: {TV};
    line-height: 1.8;
}}
.oc-dev-file {{ display: flex; align-items: flex-start; gap: 6px; margin-bottom: 4px; }}

/* Results footer */
.oc-res-footer {{
    background: {CL};
    border-top: 1px solid {OV};
    padding: 1.5rem;
    margin-top: 1.5rem;
}}
.oc-res-footer-inner {{
    max-width: 1280px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}}

/* Bottom action button styling (Streamlit secondary overrides for results) */
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {{
    width: auto !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
}}
div[data-testid="stHorizontalBlock"] .stDownloadButton > button {{
    background: {P} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: none !important;
    width: auto !important;
}}
</style>
""", unsafe_allow_html=True)


# ── HTML blocks ───────────────────────────────────────────────────────────────

NAV = f"""
<nav class="oc-nav" id="top">
  <div class="oc-nav-logo">
    <span>📄</span> OCR Extractor
  </div>
  <div class="oc-nav-links">
    <a class="oc-nav-link active" href="#how-it-works">How it works</a>
    <a class="oc-nav-link"        href="#outputs">Outputs</a>
    <a class="oc-nav-link"        href="#">GitHub ↗</a>
  </div>
  <button class="oc-nav-cta"
    onclick="document.getElementById('upload-section').scrollIntoView({{behavior:'smooth'}})">
    Get Started
  </button>
</nav>
"""

HERO = f"""
<section class="oc-hero">

  <!-- Left: copy -->
  <div>
    <h1 class="oc-hero-h1">
      Extract structured data from documents using OCR
    </h1>
    <p class="oc-hero-sub">
      Upload a PDF or image and get OCR text, validated fields, JSON, CSV,
      confidence scores, and line-level OCR details.
    </p>
    <div class="oc-badges">
      <span class="oc-badge">📄 PDF &amp; Image support</span>
      <span class="oc-badge">🔍 PaddleOCR pipeline</span>
      <span class="oc-badge">✅ Regex validation</span>
      <span class="oc-badge">📊 JSON / CSV export</span>
    </div>
    <div class="oc-hero-btns">
      <a class="oc-btn-p" href="#upload-section"
        onclick="document.getElementById('upload-section').scrollIntoView({{behavior:'smooth'}});return false;">
        Get started
      </a>
      <a class="oc-btn-s" href="#how-it-works"
        onclick="document.getElementById('how-it-works').scrollIntoView({{behavior:'smooth'}});return false;">
        How it works
      </a>
    </div>
  </div>

  <!-- Right: live-preview card -->
  <div class="oc-preview">
    <div class="oc-preview-hd">
      <div class="oc-preview-title">
        <span>📊</span> Live Preview
      </div>
      <span class="oc-conf">98% Confidence</span>
    </div>
    <div class="oc-pf">
      <div class="oc-pf-lbl">Extracted Name</div>
      <div class="oc-pf-val">Johnathan Doe</div>
    </div>
    <div class="oc-pf">
      <div class="oc-pf-lbl">Document ID</div>
      <div class="oc-pf-val mono">ABC-123-XYZ</div>
    </div>
    <div class="oc-pf">
      <div class="oc-pf-lbl">Status</div>
      <div class="oc-pf-ok">✅ Validated against regex</div>
    </div>
  </div>

</section>
<hr class="oc-divider">
"""

UPLOAD_HDR = f"""
<div class="oc-upload-section" id="upload-section">
  <div class="oc-upload-hd">
    <div class="oc-upload-title">Upload a document</div>
    <div class="oc-upload-sub">
      Use a dummy PAN-style PDF or image to test the extraction workflow.
    </div>
  </div>
</div>
"""

PRIVACY = f"""
<div class="oc-privacy">
  🔒 This prototype is designed for dummy documents and OCR workflow testing.
  Avoid uploading real sensitive identity documents.
</div>
"""

PROCESS = f"""
<section id="how-it-works">
  <div class="oc-process">
    <h3 class="oc-section-h">Process Overview</h3>
    <div class="oc-pgrid">
      <div class="oc-pcard">
        <div class="oc-pnum">01</div>
        <div class="oc-ptitle">⬆️ Data Input</div>
        <p class="oc-pbody">Upload image or multi-page PDF.</p>
      </div>
      <div class="oc-pcard">
        <div class="oc-pnum">02</div>
        <div class="oc-ptitle">👁️ OCR Detection</div>
        <p class="oc-pbody">PaddleOCR locates and reads all text lines.</p>
      </div>
      <div class="oc-pcard">
        <div class="oc-pnum">03</div>
        <div class="oc-ptitle">🔍 Regex Engine</div>
        <p class="oc-pbody">Patterns map raw text to specific fields.</p>
      </div>
      <div class="oc-pcard">
        <div class="oc-pnum">04</div>
        <div class="oc-ptitle">⬇️ Structured Output</div>
        <p class="oc-pbody">Export validated data to JSON/CSV.</p>
      </div>
    </div>
  </div>
</section>
"""

OUTPUTS = f"""
<section id="outputs">
  <div class="oc-outputs">
    <div class="oc-out-inner">
      <h3 class="oc-section-h">Available Outputs</h3>
      <div class="oc-ogrid">
        <div class="oc-ocard">
          <span class="oc-oico">📋</span>
          <div class="oc-otitle">Key-Value Pairs</div>
          <p class="oc-obody">Clean structured fields ready for database entry.</p>
        </div>
        <div class="oc-ocard">
          <span class="oc-oico">📝</span>
          <div class="oc-otitle">Raw Text Lines</div>
          <p class="oc-obody">Unfiltered list of all OCR-detected text regions.</p>
        </div>
        <div class="oc-ocard">
          <span class="oc-oico">✅</span>
          <div class="oc-otitle">Validation Report</div>
          <p class="oc-obody">Confidence scores and regex match status per field.</p>
        </div>
      </div>
    </div>
  </div>
</section>
"""

FOOTER = f"""
<footer class="oc-footer">
  <div class="oc-footer-inner">
    <div>
      <div class="oc-footer-brand">OCR Document Extractor v2</div>
      <div class="oc-footer-copy">
        © 2024. Prototype for testing purposes. Do not upload sensitive PII.
      </div>
    </div>
    <div class="oc-footer-links">
      <a class="oc-footer-link" href="#">Privacy</a>
      <a class="oc-footer-link" href="#">Terms</a>
      <a class="oc-footer-link" href="#">Docs</a>
    </div>
  </div>
</footer>
"""

NAV_RESULTS = f"""
<nav class="oc-nav" id="top">
  <div class="oc-nav-logo">
    <span>📄</span> DeepExtract OCR
  </div>
  <div class="oc-nav-links">
    <a class="oc-nav-link" href="#">How it works</a>
    <a class="oc-nav-link active" href="#">Outputs</a>
    <a class="oc-nav-link" href="#">GitHub ↗</a>
  </div>
  <div style="display:flex;gap:12px;align-items:center;">
    <button class="oc-nav-sec-btn">Upload another document</button>
    <button class="oc-nav-pri-btn">Download CSV</button>
  </div>
</nav>
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_backend() -> bool:
    try:
        return requests.get(HEALTH_URL, timeout=3).status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def _bool_icon(v: bool) -> str:
    return "✅ Yes" if v else "❌ No"


# ══════════════════════════════════════════════════════════════════════════════
# PRE-UPLOAD HOMEPAGE
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.result is None:

    st.markdown(NAV, unsafe_allow_html=True)

    # Hero
    st.markdown(HERO, unsafe_allow_html=True)

    # Upload section header
    st.markdown(UPLOAD_HDR, unsafe_allow_html=True)

    # Upload card — centered column + bordered container
    _, upload_col, _ = st.columns([0.15, 0.7, 0.15])
    with upload_col:
        with st.container(border=True):

            # Card inner padding via spacer + file uploader
            st.markdown(
                f"""
                <div style="text-align:center; padding: 0.25rem 0 0.5rem;
                            font-family:'Inter',sans-serif;">
                    <p style="font-size:13px; color:{TV}; margin:0;">
                        Drag and drop your file below, or click to browse.
                        &nbsp;Accepted: <strong>PDF, PNG, JPG, JPEG</strong>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_file = st.file_uploader(
                "Upload",
                type=["pdf", "png", "jpg", "jpeg"],
                label_visibility="collapsed",
            )

            if uploaded_file:
                sz = len(uploaded_file.getvalue()) / 1024
                st.markdown(
                    f'<p style="text-align:center; font-size:13px; color:{TV}; '
                    f'font-family:Inter,sans-serif; margin:.25rem 0 .5rem;">'
                    f'📎 <strong>{uploaded_file.name}</strong>&nbsp;·&nbsp;{sz:.1f} KB</p>',
                    unsafe_allow_html=True,
                )

            extract_clicked = st.button(
                "🔍  Extract Information",
                disabled=(uploaded_file is None),
                type="primary",
                use_container_width=True,
                key="extract_btn",
            )

    # Privacy note
    st.markdown(PRIVACY, unsafe_allow_html=True)

    # Remaining homepage sections
    st.markdown(PROCESS,  unsafe_allow_html=True)
    st.markdown(OUTPUTS,  unsafe_allow_html=True)
    st.markdown(FOOTER,   unsafe_allow_html=True)

    # ── Extraction logic ──────────────────────────────────────────────────────

    if extract_clicked and uploaded_file is not None:

        if not _check_backend():
            st.error(
                "**Cannot reach the Flask backend.**\n\n"
                "Start it with:\n```\nsource venv/bin/activate\npython backend/app.py\n```"
            )
            st.stop()

        with st.spinner("Running PaddleOCR and parsing fields… first run may take ~30 s to load models."):
            try:
                resp = requests.post(
                    EXTRACT_URL,
                    files={"file": (uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    uploaded_file.type)},
                    timeout=TIMEOUT,
                )
            except requests.exceptions.ConnectionError:
                st.error("Connection lost mid-upload. Restart the Flask server and try again.")
                st.stop()
            except requests.exceptions.Timeout:
                st.error(f"Request timed out after {TIMEOUT} s. Check the Flask terminal.")
                st.stop()

        if resp.status_code != 200:
            try:
                msg = resp.json().get("message", resp.text)
            except Exception:
                msg = resp.text
            st.error(f"API error {resp.status_code}: {msg}")
            st.stop()

        data = resp.json()
        if data.get("status") != "success":
            st.error(f"Extraction failed: {data.get('message', 'Unknown error')}")
            st.stop()

        st.session_state.result   = data
        st.session_state.filename = uploaded_file.name
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# POST-EXTRACTION RESULTS  (Phase 4B)
# ══════════════════════════════════════════════════════════════════════════════

else:
    data       = st.session_state.result
    fields     = data["extracted_fields"]
    validation = data["validation_summary"]
    ocr_lines  = data["ocr_lines"]
    raw_text   = data["raw_text"]
    avg_conf   = data["average_confidence"]
    fname      = st.session_state.filename

    # ── Computed display values ───────────────────────────────────────────────
    status       = validation["extraction_status"]
    fields_found = validation["fields_found"]
    total_fields = validation["total_required_fields"]
    avg_conf_pct = f"{avg_conf * 100:.1f}%"
    ext          = fname.rsplit(".", 1)[-1].upper() if "." in fname else "FILE"
    stem         = fname.rsplit(".", 1)[0]          if "." in fname else fname

    status_map = {
        "complete":    ("Complete",    "green"),
        "partial":     ("Partial",     "amber"),
        "low_quality": ("Low Quality", "red"),
    }
    status_label, status_color = status_map.get(status, (status.title(), "amber"))

    # ── CSV bytes ─────────────────────────────────────────────────────────────
    csv_bytes = (
        pd.DataFrame({k: [v] for k, v in fields.items()})
        .to_csv(index=False)
        .encode()
    )

    # ── HTML helpers ──────────────────────────────────────────────────────────

    def _esc(s) -> str:
        return html.escape(str(s)) if s else ""

    def _fval(val, mono=False) -> str:
        if val in (None, "", "Unavailable"):
            return '<span style="font-size:14px;color:#777587;font-style:italic;">Unavailable</span>'
        cls = "oc-field-val mono" if mono else "oc-field-val"
        return f'<span class="{cls}">{_esc(val)}</span>'

    def _fcheck(val) -> str:
        if val in (None, "", "Unavailable"):
            return '<span style="color:#777587;font-size:16px;">—</span>'
        return '<span style="color:#006c49;font-size:18px;font-weight:700;">✓</span>'

    # Validation items
    checks = [
        ("PAN format valid",
         "Standard pattern: 5 letters, 4 digits, 1 letter.",
         validation.get("pan_format_valid", False)),
        ("DOB format valid",
         "Matches DD/MM/YYYY sequence and is logically consistent.",
         validation.get("dob_format_valid", False)),
        ("Name quality valid",
         "High confidence characters, no numeric interference.",
         validation.get("name_quality_valid", False)),
        ("Father name quality valid",
         "High confidence characters, no numeric interference.",
         validation.get("father_name_quality_valid", False)),
    ]
    val_items_html = ""
    for _title, _desc, _ok in checks:
        _ic  = "✓" if _ok else "✗"
        _cls = "pass" if _ok else "fail"
        val_items_html += f"""
          <div class="oc-val-item">
            <div class="oc-val-icon {_cls}">{_ic}</div>
            <div>
              <p class="oc-val-title">{_title}</p>
              <p class="oc-val-desc">{_desc}</p>
            </div>
          </div>"""

    # Diagnostics table rows
    diag_rows = ""
    for _ln in ocr_lines:
        _txt  = _esc(_ln.get("text", ""))
        _conf = f"{_ln.get('confidence', 0):.4f}"
        _box  = _ln.get("box", [])
        if _box:
            _xs   = [p[0] for p in _box]
            _ys   = [p[1] for p in _box]
            _bs   = f"{min(_xs)}, {min(_ys)}, {max(_xs)-min(_xs)}, {max(_ys)-min(_ys)}"
        else:
            _bs = "—"
        diag_rows += f"""
          <tr><td>{_txt}</td><td class="conf">{_conf}</td><td>{_bs}</td></tr>"""

    # Developer saved paths
    saved    = data.get("saved_paths", {})
    dev_html = ""
    for _key, _lbl in [
        ("uploaded_file",   "Uploaded file"),
        ("converted_image", "Converted image"),
        ("raw_text",        "Raw OCR text"),
        ("json_output",     "JSON output"),
        ("csv_output",      "CSV output"),
    ]:
        _p = saved.get(_key)
        if _p:
            dev_html += f'<div class="oc-dev-file">📂&nbsp;<strong>{_lbl}</strong> — {_esc(str(_p))}</div>'

    # ── Nav ───────────────────────────────────────────────────────────────────
    st.markdown(NAV_RESULTS, unsafe_allow_html=True)

    # ── Results header card ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-res-header">
        <div class="oc-res-icon-row">
          <div class="oc-res-icon-wrap">✅</div>
          <div>
            <h1 class="oc-res-h1">Extraction complete</h1>
            <p class="oc-res-sub">Review extracted fields, OCR quality, validation checks, and generated outputs.</p>
            <div class="oc-res-fname">📄 {_esc(fname)} [{ext}]</div>
          </div>
        </div>
        <div class="oc-res-btns">
          <button class="oc-nav-sec-btn">Upload another document</button>
          <button class="oc-nav-pri-btn">Download CSV</button>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics row ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-metrics">
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Extraction Status</div>
          <span class="oc-metric-val {status_color}">{status_label}</span>
        </div>
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Fields Found</div>
          <span class="oc-metric-val">{fields_found}/{total_fields}</span>
        </div>
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Avg. OCR Confidence</div>
          <span class="oc-metric-val">{avg_conf_pct}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main 2-col: Extracted Fields + Validation Summary ─────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-main-grid">

        <div class="oc-fields-card">
          <div class="oc-card-hd"><h2 class="oc-card-title">Extracted Fields</h2></div>
          <div class="oc-card-body">
            <div class="oc-field-row">
              <span class="oc-field-lbl">Document Type</span>
              <div class="oc-field-rhs">{_fval(fields.get("document_type"))}<span style="color:#006c49;font-size:18px;font-weight:700;">✓</span></div>
            </div>
            <div class="oc-field-row">
              <span class="oc-field-lbl">Name</span>
              <div class="oc-field-rhs">{_fval(fields.get("name"))}{_fcheck(fields.get("name"))}</div>
            </div>
            <div class="oc-field-row">
              <span class="oc-field-lbl">Father Name</span>
              <div class="oc-field-rhs">{_fval(fields.get("father_name"))}{_fcheck(fields.get("father_name"))}</div>
            </div>
            <div class="oc-field-row">
              <span class="oc-field-lbl">Date of Birth</span>
              <div class="oc-field-rhs">{_fval(fields.get("date_of_birth"))}{_fcheck(fields.get("date_of_birth"))}</div>
            </div>
            <div class="oc-field-row">
              <span class="oc-field-lbl">PAN Number</span>
              <div class="oc-field-rhs">{_fval(fields.get("pan_number"), mono=True)}{_fcheck(fields.get("pan_number"))}</div>
            </div>
          </div>
        </div>

        <div class="oc-val-card">
          <div class="oc-card-hd"><h2 class="oc-card-title">Validation Summary</h2></div>
          <div class="oc-card-body">
            <div class="oc-val-items">{val_items_html}</div>
            <div class="oc-val-btn-row">
              <button class="oc-nav-sec-btn">Upload another document</button>
              <button class="oc-nav-pri-btn">Download CSV</button>
            </div>
          </div>
        </div>

      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs: Raw OCR Text / Advanced Diagnostics ─────────────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-tabs-wrap">
        <div class="oc-tab-bar">
          <button class="oc-tab-btn active" id="ocr-raw-btn"  onclick="ocTab('raw')">Raw OCR Text</button>
          <button class="oc-tab-btn"        id="ocr-diag-btn" onclick="ocTab('diag')">Advanced Diagnostics</button>
        </div>
        <div class="oc-tab-content" id="ocr-raw-pane">
          <div class="oc-raw-block">{html.escape(raw_text)}</div>
        </div>
        <div class="oc-tab-content" id="ocr-diag-pane" style="display:none;">
          <div class="oc-diag-wrap">
            <table class="oc-diag-table">
              <thead>
                <tr>
                  <th>Text Segment</th>
                  <th>Confidence</th>
                  <th>Bounding Box (x, y, w, h)</th>
                </tr>
              </thead>
              <tbody>{diag_rows}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <script>
    function ocTab(t) {{
      var rb=document.getElementById('ocr-raw-btn'),  db=document.getElementById('ocr-diag-btn');
      var rp=document.getElementById('ocr-raw-pane'), dp=document.getElementById('ocr-diag-pane');
      if(t==='raw'){{
        rb.className='oc-tab-btn active'; db.className='oc-tab-btn';
        rp.style.display=''; dp.style.display='none';
      }}else{{
        db.className='oc-tab-btn active'; rb.className='oc-tab-btn';
        dp.style.display=''; rp.style.display='none';
      }}
    }}
    </script>
    """, unsafe_allow_html=True)

    # ── Export metrics (repeated, per Stitch design) ──────────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-metrics">
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Extraction Status</div>
          <span class="oc-metric-val {status_color}">{status_label}</span>
        </div>
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Fields Found</div>
          <span class="oc-metric-val">{fields_found}/{total_fields}</span>
        </div>
        <div class="oc-metric-card">
          <div class="oc-metric-lbl">Avg. OCR Confidence</div>
          <span class="oc-metric-val">{avg_conf_pct}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Developer: Saved Output Files ─────────────────────────────────────────
    st.markdown(f"""
    <div class="oc-rs">
      <div class="oc-dev-wrap">
        <details class="oc-dev">
          <summary>
            <span style="display:flex;align-items:center;gap:8px;">
              <span style="font-size:16px;">🖥️</span>
              <span>Developer: Saved Output Files</span>
            </span>
          </summary>
          <div class="oc-dev-content">
            {dev_html if dev_html else "<em>No saved paths returned.</em>"}
          </div>
        </details>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bottom actions (functional Streamlit buttons) ─────────────────────────
    st.markdown(f'<div class="oc-rs"><div style="height:1px;background:{OV};margin-bottom:1.5rem;"></div></div>',
                unsafe_allow_html=True)

    _c1, _c2, _c3, _c4 = st.columns([0.18, 0.42, 0.25, 0.15])
    with _c1:
        if st.button("← Back to upload", key="back_btn", type="secondary"):
            st.session_state.result   = None
            st.session_state.filename = None
            st.rerun()
    with _c3:
        if st.button("Upload another document", key="bottom_upload_btn", type="secondary"):
            st.session_state.result   = None
            st.session_state.filename = None
            st.rerun()
    with _c4:
        st.download_button(
            "Download CSV",
            csv_bytes,
            f"{stem}_extracted.csv",
            "text/csv",
            key="bottom_csv_btn",
        )

    # ── Results footer ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="oc-res-footer">
      <div class="oc-res-footer-inner">
        <button class="oc-nav-sec-btn">Upload another document</button>
        <button class="oc-nav-pri-btn">Download CSV</button>
      </div>
    </div>
    """, unsafe_allow_html=True)
