# fantasy_lottery_two_tabs.py
import streamlit as st
import pandas as pd
import itertools
import random
import time
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Fantasy Draft Lottery Tool", page_icon="🎲", layout="wide")

# -----------------------
# Helper functions
# -----------------------

def generate_all_combinations():
    """Generate all 4-number combinations from 1–14."""
    numbers = list(range(1, 15))
    return [" ".join(map(str, sorted(c))) for c in itertools.combinations(numbers, 4)]


def assign_combinations_to_teams(teams_dict, seed=None):
    """
    Assign ALL 1000 unique combinations to teams according to their ticket share.
    Ensures that each team gets exactly 'tickets' combos, totaling 1000.
    """
    if seed is not None:
        random.seed(seed)

    all_combos = generate_all_combinations()  # 1001 total combos possible
    total_tickets = sum(teams_dict.values())

    if total_tickets != 1000:
        raise ValueError("Total tickets must equal 1000!")

    if total_tickets > len(all_combos):
        raise ValueError("Not enough unique 4-number combinations available!")

    random.shuffle(all_combos)

    assignments = []
    combo_index = 0
    for team, tickets in teams_dict.items():
        for _ in range(tickets):
            combo = all_combos[combo_index]
            assignments.append({"Combination": combo, "Team": team})
            combo_index += 1

    df = pd.DataFrame(assignments)
    return df


def simulate_lotteries(teams_dict, n_simulations=10000, seed=None):
    """Monte Carlo simulation to estimate draft odds for each pick."""
    if seed is not None:
        random.seed(seed)

    teams = list(teams_dict.keys())
    max_picks = len(teams)
    counts = {team: {pick: 0 for pick in range(1, max_picks + 1)} for team in teams}
    all_combos_master = generate_all_combinations()

    for sim in range(n_simulations):
        combos = all_combos_master.copy()
        random.shuffle(combos)
        combos = combos[:1000]
        assignments = []
        i = 0
        for team, n in teams_dict.items():
            block = combos[i:i + n]
            for c in block:
                assignments.append((c, team))
            i += n
        combo_to_team = dict(assignments)
        remaining_combos = list(combo_to_team.keys())

        for pick in range(1, max_picks + 1):
            choice = random.choice(remaining_combos)
            team = combo_to_team[choice]
            counts[team][pick] += 1
            remaining_combos = [c for c in remaining_combos if combo_to_team[c] != team]

    percents = {}
    for team in teams:
        percents[team] = {}
        for pick in range(1, max_picks + 1):
            percents[team][pick] = round(counts[team][pick] / n_simulations * 100, 4)

    df = pd.DataFrame.from_dict({team: percents[team] for team in teams}, orient="index")
    df.columns = [f"Pick {c}" for c in df.columns]
    return percents, df


def generate_draft_pdf(draft_order):
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, "Fantasy Draft Lottery - Draft Order")
    p.setFont("Helvetica", 12)
    y = h - 80
    for i, team in enumerate(draft_order, start=1):
        p.drawString(50, y, f"{i}. {team}")
        y -= 18
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = h - 50
    p.save()
    buf.seek(0)
    return buf
# -----------------------
# Session state defaults
# -----------------------
if "teams" not in st.session_state:
    st.session_state.teams = {}

if "assignment_df" not in st.session_state:
    st.session_state.assignment_df = pd.DataFrame(columns=["Combination", "Team"])

if "draft_order" not in st.session_state:
    st.session_state.draft_order = []

if "drawn_combos" not in st.session_state:
    st.session_state.drawn_combos = []

if "remaining_df" not in st.session_state:
    st.session_state.remaining_df = st.session_state.assignment_df.copy()

if "simulated_odds" not in st.session_state:
    st.session_state.simulated_odds = None

if "simulated_odds_df" not in st.session_state:
    st.session_state.simulated_odds_df = None

if "reset_inputs" not in st.session_state:
    st.session_state.reset_inputs = False
    
if "league_name" not in st.session_state:
    st.session_state.league_name = "My League"

if "draft_year" not in st.session_state:
    st.session_state.draft_year = 2025
# -----------------------
# UI: two tabs
# -----------------------
tab1, tab2 = st.tabs(["⚙️ Custom League Setup", "🎯 Draft Lottery"])

# -----------------------
# TAB 1: Setup & Simulation
# -----------------------
with tab1:
    st.header("⚙️ 1) Setup league, teams & tickets")
    st.markdown(
            "Enter your fantasy league name and the year of your draft."
        )
    # --- League name + year ---
    if "league_name" not in st.session_state:
        st.session_state.league_name = "My League"
    if "league_year" not in st.session_state:
        st.session_state.league_year = 2025
    col_league = st.columns([2,1])
    with col_league[0]:
        league_name = st.text_input("League name", key="league_name")
        year = st.number_input("Year", min_value=2000, max_value=2100, step=1, key="league_year")
    st.info("Enter the number of teams in your league, team names and ticket counts. Total tickets must sum to 1000.")
    colA, colB = st.columns([2, 1])
    with colA:
        n = st.number_input(
            "Number of teams",
            min_value=2,
            max_value=30,
            value=max(2, len(st.session_state.teams) or 4),
            step=1
        )
        temp_names = []
        temp_tickets = []
        for i in range(int(n)):
            cols = st.columns([3,1])
            name = cols[0].text_input(
                f"Team #{i+1} name",
                key=f"name_{i}",
                value=(list(st.session_state.teams.keys())[i] if i < len(st.session_state.teams) else "")
            )
            tickets = cols[1].number_input(
                f"Tickets #{i+1}",
                min_value=1,
                key=f"tickets_{i}",
                value=(list(st.session_state.teams.values())[i] if i < len(st.session_state.teams) else 100)
            )
            temp_names.append(name.strip())
            temp_tickets.append(int(tickets))
    with colB:
        st.write("Current teams:")
        # Anzeige direkt aktualisieren, auch nach Apply
        current_teams = {}
        for name, tk in zip(temp_names, temp_tickets):
            if name:
                current_teams[name] = tk
        if current_teams:
            st.table(pd.DataFrame({"Team": list(current_teams.keys()), "Tickets": list(current_teams.values())}))
        else:
            st.write("No teams set yet.")
        st.write("---")

        if st.button("Apply team list"):
            # validate
            new_teams = {}
            for name, tk in zip(temp_names, temp_tickets):
                if name:
                    new_teams[name] = int(tk)
            if len(new_teams) < 2:
                st.error("Please provide at least two teams with names.")
            else:
                total = sum(new_teams.values())
                if total != 1000:
                    st.error(f"Total tickets = {total}. Please adjust so the sum is exactly 1000.")
                else:
                    st.session_state.teams = new_teams
                    st.session_state.assignment_df = assign_combinations_to_teams(st.session_state.teams)
                    st.session_state.remaining_df = st.session_state.assignment_df.copy()
                    st.session_state.draft_order = []
                    st.session_state.drawn_combos = []
                    st.success("Teams applied and 1000 combinations assigned.")
                    # Tabelle sofort anzeigen
                    st.table(pd.DataFrame({"Team": list(new_teams.keys()), "Tickets": list(new_teams.values())}))

        if st.button("Clear teams and assignments"):
            st.session_state.teams = {}
            st.session_state.assignment_df = pd.DataFrame(columns=["Combination", "Team"])
            st.session_state.remaining_df = st.session_state.assignment_df.copy()
            st.session_state.draft_order = []
            st.session_state.drawn_combos = []
            st.success("Cleared.")

    st.markdown("---")
    st.header("2) Assigned combinations")
    st.write("You can download the CSV with all teams and their assigned combinations.")
    if not st.session_state.assignment_df.empty:
        csv_bytes = st.session_state.assignment_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download initial assignment CSV", data=csv_bytes, file_name="assignment.csv", mime="text/csv")
        st.dataframe(st.session_state.assignment_df.sample(min(50, len(st.session_state.assignment_df))))
    else:
        st.write("No assignments yet. Define teams and click 'Apply team list' above.")

    st.markdown("---")
    st.header("3) Monte-Carlo simulation of lottery odds")
    st.write("Run a Monte-Carlo simulation (10,000 runs) to estimate the probability for each team to land each pick.")
    sim_col1, sim_col2 = st.columns([2,1])
    with sim_col2:
        runs = st.number_input("Simulations to run", min_value=1000, max_value=200000, step=1000, value=10000)
        if st.button("🔁 Run simulation"):
            if not st.session_state.teams or st.session_state.assignment_df.empty:
                st.error("Please apply teams first.")
            else:
                with st.spinner("Running simulations (this may take a moment)..."):
                    start = time.time()
                    percents_dict, df_odds = simulate_lotteries(st.session_state.teams, n_simulations=runs)
                    st.session_state.simulated_odds = percents_dict
                    st.session_state.simulated_odds_df = df_odds
                    took = time.time() - start
                    st.success(f"Simulation done ({runs} runs) in {took:.1f}s. Results stored.")
    with sim_col1:
        if st.session_state.simulated_odds_df is not None:
            st.subheader("Simulated odds (sample)")
            st.dataframe(st.session_state.simulated_odds_df)
            csv_sim = st.session_state.simulated_odds_df.to_csv().encode("utf-8")
            st.download_button("Download simulated odds CSV", data=csv_sim, file_name="simulated_odds.csv", mime="text/csv")
        else:
            st.info("No simulated odds yet. Run the simulation to compute per-pick probabilities.")
# -----------------------
# TAB 2: Draft-Lottery
# -----------------------

with tab2:

    
    # --- League + year headline ---
    league_title = st.session_state.get("league_name", "Fantasy League")
    draft_year = st.session_state.get("draft_year", 2026)
    st.markdown(f"## 🎉 {league_title} Fantasy Draft Lottery Ceremony {draft_year}")

    # --- Intro commentary only once ---
    if "intro_shown" not in st.session_state:
        st.session_state.intro_shown = False

    if not st.session_state.intro_shown:
        st.markdown("""
        Welcome to the official **Fantasy Draft Lottery!**
        The ping-pong balls are loaded, the tension is rising… and the future of your franchise is about to change forever.
        """)
        if st.button("🔥 Start the lottery show"):
            st.session_state.intro_shown = True
            st.session_state.pick_commentary = []
            st.session_state.draft_order = []
            st.session_state.drawn_combos = []
            st.session_state.remaining_df = st.session_state.assignment_df.copy()
            st.success("Let’s begin! The first ball is about to drop…")
    st.subheader("Manual or Auto Draw")

    if not st.session_state.teams:
        st.warning("No teams configured. Go to 'Setup & Simulation' and define teams first.")
    else:
        st.markdown(
            "You can either manually enter the drawn numbers **or** let the app randomly generate a combination from the remaining pool."
        )

        # --- Choose draw mode ---
        draw_mode = st.radio(
            "Select draw mode:",
            ["🎯 Manual Input", "🎲 Auto Generate"],
            horizontal=True
        )

        # --- MANUAL MODE ---
        if draw_mode == "🎯 Manual Input":
            st.markdown(
                "Enter the 4 numbers you physically drew (each between 1–14). Order doesn’t matter. "
                "The app will lookup the assigned combination and award that team."
            )
            c1, c2, c3, c4 = st.columns(4)
            z1 = c1.number_input("Number 1", min_value=1, max_value=14, step=1, key="z1_draw", value=1)
            z2 = c2.number_input("Number 2", min_value=1, max_value=14, step=1, key="z2_draw", value=2)
            z3 = c3.number_input("Number 3", min_value=1, max_value=14, step=1, key="z3_draw", value=3)
            z4 = c4.number_input("Number 4", min_value=1, max_value=14, step=1, key="z4_draw", value=4)

            if st.button("🔀 Check combination & award pick"):
                combo_str = " ".join(map(str, sorted([int(z1), int(z2), int(z3), int(z4)])))
                row = st.session_state.remaining_df.loc[st.session_state.remaining_df["Combination"] == combo_str]

                if row.empty:
                    st.error(
                        "Combination not found or already removed. Double-check the numbers or download the initial assignment CSV."
                    )
                else:
                    team = row.iloc[0]["Team"]
                    if team in st.session_state.draft_order:
                        st.warning(f"{team} already has a pick assigned.")
                    else:
                        # Original tickets %
                        total_tickets = sum(st.session_state.teams.values())
                        original_tickets = st.session_state.teams.get(team, 0)
                        original_pct = round(original_tickets / total_tickets * 100, 2)

                        # Award pick
                        st.session_state.draft_order.append(team)
                        pick_number = len(st.session_state.draft_order)

                        # Fetch simulated odds if available
                        pre_pct = None
                        if st.session_state.simulated_odds:
                            pre_pct = st.session_state.simulated_odds.get(team, {}).get(pick_number, None)

                        # Compute seed position
                        sorted_by_tickets = sorted(st.session_state.teams.items(), key=lambda x: x[1], reverse=True)
                        seed_map = {t: idx + 1 for idx, (t, _) in enumerate(sorted_by_tickets)}
                        original_seed = seed_map.get(team, None)
                        delta = original_seed - pick_number if original_seed is not None else None

                        st.success(
                            f"🏆 {team} awarded Pick {pick_number} (original tickets: {original_tickets}, {original_pct}%)"
                        )
                        if pre_pct is not None:
                            st.info(f"📊 Simulated chance for this pick: {pre_pct:.4f}%")
                        else:
                            st.info("📊 Simulated odds not available (run simulation in Setup tab).")

                        if delta is not None:
                            if delta > 0:
                                st.success(f"⬆️ Improvement vs seed: +{delta}")
                            elif delta < 0:
                                st.error(f"⬇️ Drop vs seed: {delta}")
                            else:
                                st.warning("⏺️ No change vs seed")

                        # Remove all combos of this team
                        st.session_state.remaining_df = st.session_state.remaining_df[
                            st.session_state.remaining_df["Team"] != team
                        ]
                        st.session_state.reset_inputs = True
                        st.session_state.drawn_combos.append(
                            {
                                "Combination": combo_str,
                                "Team": team,
                                "Original_Tickets": original_tickets,
                                "Pick": pick_number
                            }
                        )

        # --- AUTO MODE ---
        elif draw_mode == "🎲 Auto Generate":
            st.markdown(
                "Click the button below to automatically generate a random 4-number combination from the remaining pool."
            )

            if st.button("🔀 Generate random combination"):
                if st.session_state.remaining_df.empty:
                    st.error("No combinations left! Restart the lottery.")
                else:
                    # Randomly pick one combination from remaining
                    chosen_row = st.session_state.remaining_df.sample(1).iloc[0]
                    combo_str = chosen_row["Combination"]
                    team = chosen_row["Team"]

                    # Award pick
                    st.session_state.draft_order.append(team)
                    pick_number = len(st.session_state.draft_order)

                    # Compute original seed & delta
                    sorted_by_tickets = sorted(st.session_state.teams.items(), key=lambda x: x[1], reverse=True)
                    seed_map = {t: idx + 1 for idx, (t, _) in enumerate(sorted_by_tickets)}
                    original_seed = seed_map.get(team, None)
                    delta = original_seed - pick_number if original_seed is not None else None

                    st.session_state.remaining_df = st.session_state.remaining_df[
                        st.session_state.remaining_df["Team"] != team
                    ]
                    st.session_state.drawn_combos.append(
                        {"Combination": combo_str, "Team": team, "Pick": pick_number}
                    )

                    # Display results
                    st.success(f"🎲 Auto-generated combination: **{combo_str}**")
                    st.success(f"🏆 {team} wins Pick {pick_number}")
                    if delta is not None:
                        if delta > 0:
                            st.success(f"⬆️ Improvement vs seed: +{delta}")
                        elif delta < 0:
                            st.error(f"⬇️ Drop vs seed: {delta}")
                        else:
                            st.warning("⏺️ No change vs seed")


        # --- Status + Results (shared between both modes) ---
        st.divider()
        st.subheader("📊 Current Draft Order")
        if st.session_state.draft_order:
            for i, t in enumerate(st.session_state.draft_order, start=1):
                pre = ""
                if st.session_state.simulated_odds:
                    v = st.session_state.simulated_odds.get(t, {}).get(i, None)
                    pre = f"{v:.4f}%" if v is not None else "N/A"
                # compute delta text
                sorted_by_tickets = sorted(st.session_state.teams.items(), key=lambda x: x[1], reverse=True)
                seed_map = {team: idx+1 for idx,(team,_) in enumerate(sorted_by_tickets)}
                orig = seed_map.get(t)
                delta = orig - i if orig is not None else None
                delta_txt = f"+{delta}" if delta and delta>0 else (f"{delta}" if delta else "0")
                st.write(f"Pick {i}: {t} ({pre}, Δ {delta_txt})")
        else:
            st.write("No picks assigned yet.")
        st.divider()
        
        st.subheader("Live status")
        st.markdown(f"Remaining combinations: **{len(st.session_state.remaining_df)}**")
        total_remaining = len(st.session_state.remaining_df)
        team_counts = st.session_state.remaining_df["Team"].value_counts().to_dict()
        rows = []
        for t, tk in st.session_state.teams.items():
            cnt = team_counts.get(t, 0)
            pct = round((cnt / total_remaining * 100), 4) if total_remaining>0 else 0.0
            rows.append({"Team": t, "Remaining combos": cnt, "Current chance (%)": pct})
        st.table(pd.DataFrame(rows).sort_values("Current chance (%)", ascending=False))
        st.bar_chart(pd.DataFrame(rows).set_index("Team")["Current chance (%)"])


        st.divider()
        st.subheader("Drawn combinations")
        if st.session_state.drawn_combos:
            st.table(pd.DataFrame(st.session_state.drawn_combos))
        else:
            st.write("No combinations drawn yet.")

        st.markdown("---")
        st.subheader("Downloads & tables")
        if st.session_state.drawn_combos:
            st.download_button("Download drawn combos CSV", data=pd.DataFrame(st.session_state.drawn_combos).to_csv(index=False).encode("utf-8"), file_name="drawn_combos.csv", mime="text/csv")
        # always allow current draft PDF
        pdf_buf = generate_draft_pdf(st.session_state.draft_order)
        st.download_button("Download draft order as PDF", data=pdf_buf, file_name="draft_order.pdf", mime="application/pdf")

        st.divider()
        if st.button("Restart lottery (keep teams)"):
            # regenerate combos and reset draws
            st.session_state.assignment_df = assign_combinations_to_teams(st.session_state.teams)
            st.session_state.remaining_df = st.session_state.assignment_df.copy()
            st.session_state.draft_order = []
            st.session_state.drawn_combos = []
            st.session_state.simulated_odds = None
            st.session_state.simulated_odds_df = None
            st.session_state.reset_inputs = True
            st.success("Lottery restarted (teams preserved).")
        if st.button("Reset everything (clear teams)"):
            st.session_state.teams = {}
            st.session_state.assignment_df = pd.DataFrame(columns=["Combination","Team"])
            st.session_state.remaining_df = st.session_state.assignment_df.copy()
            st.session_state.draft_order = []
            st.session_state.drawn_combos = []
            st.session_state.simulated_odds = None
            st.session_state.simulated_odds_df = None
            st.session_state.reset_inputs = True
            st.success("All cleared.")
