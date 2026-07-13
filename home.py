import streamlit as st

from utils.branding import load_logo

# UP-2 — front-door rebuild (proposal, on branch `platform-home`, NOT merged).
#
# Old home.py (27 lines, still on main) was two logos, a giant link away to
# the FitzLab site, and ten undescribed page links — a first-time visitor had
# to guess what each tool did. This version groups the nine tools by what a
# student is actually trying to do (matching the "group" label each page
# already declares to itself on `platform-page-contract`'s page_header()),
# gives each one a real physics sentence instead of just its filename, and
# moves the FitzLab link to a normal footer line. No renames, no URL changes,
# no st.navigation — every existing bookmark still resolves to the same page.
TOOLS = {
    "Learn": [
        ("pages/Qubit_Simulator.py", "Qubit Simulator", "⚛",
         "Sweep a qubit's drive frequency and watch the Rabi chevron emerge from the Lindblad master equation."),
        ("pages/Quantum_Measurement_Tutorial.py", "Quantum Measurement Tutorial", "🎮",
         "Step through projective measurement and the Born rule, one interactive section at a time."),
        ("pages/IQ_mixer.py", "IQ Mixing", "〰️",
         "See how in-phase/quadrature mixing up-converts a baseband signal onto a microwave carrier."),
    ],
    "Play": [
        ("pages/QuBlitz_Arena.py", "QuBlitz Arena", "⚔️",
         "Command qubit armies in real time — charge, strike, and collapse with the same Lindblad physics engine the simulator pages use."),
        ("pages/Sonify.py", "Sonify Images", "🎵",
         "Turn an image's pixel rows into an audible signal — quantum data sonification, playfully."),
    ],
    "Research tools": [
        ("pages/Custom_Qubit_Query.py", "Custom Qubit Query (Local/VPN)", "🧪",
         "Run the simulator against a real lab qubit's assigned parameters over the lab network — VPN required."),
        ("pages/Dilution_Refrigerator_Noise_Explorer.py", "Dilution Refrigerator Noise Explorer", "❄️",
         "Model how line noise couples into a dilution fridge's coldest stage across frequency and bath temperature."),
        ("pages/EP_TPD_exploration.py", "Exceptional Point & Transmission Peak Degeneracy", "🎯",
         "Explore where exceptional points and transmission-peak degeneracies coincide in a tunable magnon-photon dimer."),
        ("pages/Laser_Heating_Calculator.py", "Laser Heating Calculator", "⚡",
         "Estimate a target's temperature rise under a fiber-delivered laser, from its heat capacity and thermal conductance to the bath."),
    ],
}

GROUP_BLURB = {
    "Learn": "Interactive explainers — start here if you're new to the physics.",
    "Play": "The games — same physics engine, no setup.",
    "Research tools": "Instruments used in the lab itself, exposed as pages.",
}


def main():
    st.set_page_config(page_title="QuBlitz — FitzLab", page_icon="⚛", layout="wide")

    col_logo, col_text = st.columns([1, 6])
    with col_logo:
        st.image(load_logo("images/logo.png"), width=72)
    with col_text:
        st.title("QuBlitz")
        st.subheader(
            "Simulate real quantum hardware in your browser — the same "
            "open-quantum-systems physics our lab runs, no install."
        )

    st.info("**New here?** Start with the Qubit Simulator → sweep a drive frequency and watch a Rabi chevron form in real time.", icon="👋")
    st.divider()

    for group, tools in TOOLS.items():
        st.markdown(f"#### {group}")
        st.caption(GROUP_BLURB[group])
        cols = st.columns(len(tools))
        for col, (path, title, icon, blurb) in zip(cols, tools):
            with col:
                with st.container(border=True):
                    st.markdown(f"##### {icon} {title}")
                    st.caption(blurb)
                    st.page_link(path, label="Open →")
        st.write("")

    st.divider()
    st.caption(
        'Built by the [FitzLab](https://sites.google.com/view/fitzlab/home) at Dartmouth. '
        '[QuBlitz on GitHub](https://github.com/mvwf/qublitz).'
    )


if __name__ == "__main__":
    main()