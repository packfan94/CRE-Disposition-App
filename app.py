import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="CRE Disposition Report Generator", layout="wide", page_icon="🏢")

# --- HELPER FUNCTIONS ---
def calculate_years(start_date, end_date):
    days = (end_date - start_date).days
    return days / 365.25

def format_currency(val):
    return f"${val:,.0f}"

def format_percent(val):
    return f"{val * 100:.1f}%"

# --- UI: APP TITLE ---
st.title("🏢 CRE Disposition Analysis & Distribution Report")
st.markdown("Fill out the deal metrics below to automatically generate your investor report. **Press Ctrl+P (or Cmd+P) to save the final report as a PDF.**")
st.divider()

# --- INPUT SECTION ---
with st.form("intake_form"):
    st.header("1. Property & Timeline")
    col1, col2, col3 = st.columns(3)
    with col1:
        address = st.text_input("Property Address", value="24018 Lyons Avenue, Newhall, CA")
        sqft = st.number_input("Building Square Footage", min_value=1, value=6475)
    with col2:
        start_date = st.date_input("Acquisition Date", value=datetime(2017, 5, 8))
        end_date = st.date_input("Target Closing Date", value=datetime(2026, 8, 28))
    with col3:
        gross_sale = st.number_input("Gross Sale Price ($)", min_value=0.0, value=2738000.0)

    st.header("2. Deal Economics & Deductions")
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        loan_payoff = st.number_input("Loan Payoff Amount ($)", value=1972072.0)
    with col5:
        commissions = st.number_input("Broker Commissions ($)", value=136900.0)
    with col6:
        closing_costs = st.number_input("Other Closing Costs ($)", value=27380.0)
    with col7:
        llc_cash = st.number_input("LLC Cash on Hand ($)", value=111752.0)

    st.header("3. Investor Cap Table")
    st.markdown("Enter the names, initial investments, ownership percentages, and past cash distributions. **Ensure ownership adds up to 100%.**")
    
    # Default data for Cap Table
    default_investors = pd.DataFrame({
        "Investor": ["Scott Akerley", "Jeff Russell", "Lynda Overton", "Joe Curtis"],
        "Initial Investment": [185120.0, 56960.0, 56960.0, 56960.0],
        "% Ownership": [52.0, 16.0, 16.0, 16.0],
        "Cash Distributions (Past)": [58583.0, 18105.0, 18105.0, 18105.0]
    })
    
    edited_investors = st.data_editor(default_investors, num_rows="dynamic", use_container_width=True)

    st.header("4. Scenarios & Context")
    col8, col9 = st.columns(2)
    with col8:
        st.markdown("Compare to other pricing scenarios:")
        default_scenarios = pd.DataFrame({
            "Scenario": ["Conservative Exit", "Broker High Range"],
            "Sale Price": [2500000.0, 2900000.0]
        })
        edited_scenarios = st.data_editor(default_scenarios, num_rows="dynamic", use_container_width=True)
    with col9:
        real_world_context = st.text_area("Real-World Context", value="We are successfully retiring the JLC loan prior to its September maturity date, eliminating the massive risk of refinancing a balloon payment in a high-interest-rate environment.", height=150)

    submitted = st.form_submit_button("Generate Report", type="primary")

# --- PROCESSING & OUTPUT SECTION ---
if submitted:
    st.divider()
    
    # --- CALCULATIONS ---
    hold_years = calculate_years(start_date, end_date)
    psf = gross_sale / sqft if sqft > 0 else 0
    
    net_sale_proceeds = gross_sale - loan_payoff - commissions - closing_costs
    total_distributable_cash = net_sale_proceeds + llc_cash
    
    total_historical_distributions = edited_investors["Cash Distributions (Past)"].sum()
    total_value_generated = total_distributable_cash + total_historical_distributions
    
    total_initial_capital = edited_investors["Initial Investment"].sum()
    true_total_multiple = total_value_generated / total_initial_capital if total_initial_capital > 0 else 0
    
    # Annual Return (CAGR)
    cagr = (true_total_multiple ** (1 / hold_years)) - 1 if hold_years > 0 and true_total_multiple > 0 else 0

    # Individual Returns Dataframe Math
    investor_df = edited_investors.copy()
    investor_df["Capital Distribution (Est. Wire)"] = total_distributable_cash * (investor_df["% Ownership"] / 100)
    investor_df["Total Return"] = investor_df["Cash Distributions (Past)"] + investor_df["Capital Distribution (Est. Wire)"]
    investor_df["Total Multiple"] = investor_df["Total Return"] / investor_df["Initial Investment"]
    investor_df["Cash-on-Cash"] = investor_df["Total Return"] / investor_df["Initial Investment"] # Displayed as % later
    
    # --- REPORT RENDER ---
    # Hide UI elements for clean printing using CSS
    st.markdown("""
        <style>
        @media print {
            .stButton {display: none;}
            header {display: none;}
            .stForm {display: none;}
            #MainMenu {display: none;}
            footer {display: none;}
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown(f"## Final Deal Analysis - {address}")

    # 1. Deal Summary
    st.subheader("Deal Summary")
    st.markdown(f"""
    * **Final Sale Price:** {format_currency(gross_sale)}
    * **Price per Square Foot:** {format_currency(psf)}
    * **Closing Date:** {end_date.strftime('%B %d, %Y')}
    * **Investment Period:** {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')} ({hold_years:.2f} years)
    """)

    # 2. Sale Proceeds Calculation
    st.subheader("Sale Proceeds Calculation")
    proceeds_data = {
        "Item": ["Gross Sale Price", "Less: Loan Payoff", "Less: Commissions", "Less: Closing Costs", "Net Sale Proceeds", "Plus: LLC Cash on Hand", "Plus: Historical Cash Distributions", "TOTAL VALUE GENERATED (LIFECYCLE)"],
        "Amount": [format_currency(gross_sale), format_currency(-loan_payoff), format_currency(-commissions), format_currency(-closing_costs), format_currency(net_sale_proceeds), format_currency(llc_cash), format_currency(total_historical_distributions), format_currency(total_value_generated)]
    }
    st.table(pd.DataFrame(proceeds_data))

    # 3. Individual Investor Returns
    st.subheader("Individual Investor Returns")
    
    # Formatting for display
    display_investor_df = investor_df.copy()
    cols_to_currency = ["Initial Investment", "Cash Distributions (Past)", "Capital Distribution (Est. Wire)", "Total Return"]
    for col in cols_to_currency:
        display_investor_df[col] = display_investor_df[col].apply(format_currency)
    
    display_investor_df["% Ownership"] = display_investor_df["% Ownership"].apply(lambda x: f"{x:.1f}%")
    display_investor_df["Total Multiple"] = display_investor_df["Total Multiple"].apply(lambda x: f"{x:.2f}x")
    display_investor_df["Cash-on-Cash"] = display_investor_df["Cash-on-Cash"].apply(lambda x: f"{x * 100:.1f}%")
    
    st.dataframe(display_investor_df, hide_index=True, use_container_width=True)

    # 4. Key Performance Metrics
    st.subheader("Key Performance Metrics")
    st.markdown("**Returns Summary**")
    st.markdown(f"""
    * **Average Annual Return:** {format_percent(cagr)}
    * **Average Cash-on-Cash Return:** {format_percent(true_total_multiple)}
    * **Average Multiple:** {true_total_multiple:.2f}x
    * **Total Return per $1,000 Invested:** {format_currency(true_total_multiple * 1000)}
    """)

    # 5. Scenarios
    if not edited_scenarios.empty:
        st.subheader("Comparison to Original Scenarios")
        scen_df = edited_scenarios.copy()
        
        # Calculate mock returns for scenarios assuming identical debt/fees for simplicity
        scen_df["$/per square foot"] = scen_df["Sale Price"] / sqft
        scen_df["Mock Net Proceeds"] = scen_df["Sale Price"] - loan_payoff - commissions - closing_costs
        scen_df["Total distribution"] = scen_df["Mock Net Proceeds"] + llc_cash + total_historical_distributions
        scen_df["Multiple"] = scen_df["Total distribution"] / total_initial_capital
        scen_df["Annual Return"] = (scen_df["Multiple"] ** (1 / hold_years)) - 1
        
        # Format Scenario output
        display_scen_df = pd.DataFrame()
        display_scen_df["Scenario"] = scen_df["Scenario"]
        display_scen_df["Sale Price"] = scen_df["Sale Price"].apply(format_currency)
        display_scen_df["$/per square foot"] = scen_df["$/per square foot"].apply(format_currency)
        display_scen_df["Annual Return"] = scen_df["Annual Return"].apply(format_percent)
        display_scen_df["Cash on Cash"] = scen_df["Multiple"].apply(lambda x: f"{x * 100:.0f}%")
        display_scen_df["Total distribution"] = scen_df["Total distribution"].apply(format_currency)
        
        st.dataframe(display_scen_df, hide_index=True, use_container_width=True)

    # 6. Narrative
    st.subheader("Deal Assessment & Strategic Narrative")
    
    # Simple logic engine to grade the deal
    grade = ""
    if cagr >= 0.12:
        grade = "an exceptional, market-beating outcome"
    elif cagr >= 0.08:
        grade = "a solid, stable performance"
    elif cagr > 0:
        grade = "a capital-preservation outcome with marginal upside"
    else:
        grade = "an underperforming exit requiring capital loss realization"
        
    assessment = f"**Assessment:** Over the {hold_years:.1f}-year investment period, this deal generated a **{true_total_multiple:.2f}x multiple** and a **{format_percent(cagr)} annualized return**. Statistically, this represents {grade} for stabilized commercial assets in this holding period.\n\n"
    assessment += f"**Strategic Narrative:** {real_world_context}"
    
    st.info(assessment)