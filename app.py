import streamlit as st
import pandas as pd
import re
from db_utils import fetch_unannotated_doc, fetch_structured_drugs, save_annotation, init_db
from constants import FORM_OPTIONS, ROUTE_OPTIONS, FREQUENCY_OPTIONS, DOSAGE_UNITS

def split_dosage(dosage):
    if pd.isna(dosage):
        return '', ''
    match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', dosage)
    if match:
        return match.group(1), match.group(2)
    return dosage, ''

def normalize(form):
    if isinstance(form, str) and len(form) > 1:
        if form[0].isupper() and not form[1].isupper():
            return form[0].lower() + form[1:]
    return form

def main():
    st.set_page_config(layout="wide")
    st.title("Stroke Drugs Annotation Interface")

    # Initialize the database
    init_db()

    if "username" not in st.session_state:
        st.session_state.username = ""
    
    username = st.text_input("Username", value=st.session_state.username)

    if username:
        st.session_state.username = username

    if not st.session_state.username:
        st.warning("Please enter a username to start annotating.")
        st.stop()

    # Fetch unannotated document
    if 'current_doc' not in st.session_state:
        st.session_state.current_doc = fetch_unannotated_doc()

    if not st.session_state.current_doc:
        st.write("All documents have been annotated or are currently being processed.")
        return

    doc_id, drugs_text = st.session_state.current_doc

    # Display raw drugs text
    st.subheader("Raw Drugs Text")
    st.text_area("Raw drugs text", value=drugs_text, height=200, disabled=True)

    # Display editable table
    st.subheader("Structured Drugs Data")
    if 'df' not in st.session_state:
        st.session_state.df = fetch_structured_drugs(doc_id)
        # Split dosage into number and unit
        st.session_state.df[['dosage_num', 'dosage_unit']] = st.session_state.df['dosage'].apply(split_dosage).tolist()

    # Create table headers
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2,1,1,1,1,1,1,1,0.5])
    col1.write("Name")
    col2.write("Form")
    col3.write("Dosage")
    col4.write("Unit")
    col5.write("Concentration")
    col6.write("Frequency")
    col7.write("Duration")
    col8.write("Route")
    col9.write("Delete")

    # Create an editable table with dropdown menus for certain columns
    for index in range(len(st.session_state.df)):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2,1,1,1,1,1,1,1,0.5])
    
        with col1:
            st.session_state.df.at[index, 'name'] = st.text_input("Name", value=st.session_state.df.at[index, 'name'], key=f"name_{index}", label_visibility="collapsed")
        with col2:
            st.session_state.df.at[index, 'form'] = st.selectbox("Form", options=[''] + FORM_OPTIONS, index=0 if pd.isna(st.session_state.df.at[index, 'form']) or st.session_state.df.at[index, 'form'] == '' else FORM_OPTIONS.index(normalize(st.session_state.df.at[index, 'form']))+1, key=f"form_{index}", label_visibility="collapsed")
        with col3:
            st.session_state.df.at[index, 'dosage_num'] = st.text_input("Dosage", value=st.session_state.df.at[index, 'dosage_num'], key=f"dosage_num_{index}", label_visibility="collapsed")
        with col4:
            st.session_state.df.at[index, 'dosage_unit'] = st.selectbox("Unit", options=[''] + DOSAGE_UNITS, index=0 if pd.isna(st.session_state.df.at[index, 'dosage_unit']) or st.session_state.df.at[index, 'dosage_unit'] == '' or st.session_state.df.at[index, 'dosage_unit'] not in DOSAGE_UNITS else DOSAGE_UNITS.index(st.session_state.df.at[index, 'dosage_unit'])+1, key=f"dosage_unit_{index}", label_visibility="collapsed")
        with col5:
            st.session_state.df.at[index, 'concentration'] = st.text_input("Concentration", value=st.session_state.df.at[index, 'concentration'], key=f"concentration_{index}", label_visibility="collapsed")
        with col6:
            st.session_state.df.at[index, 'frequency'] = st.selectbox("Frequency", options=[''] + FREQUENCY_OPTIONS, index=0 if pd.isna(st.session_state.df.at[index, 'frequency']) or st.session_state.df.at[index, 'frequency'] == '' or st.session_state.df.at[index, 'frequency'] not in FREQUENCY_OPTIONS else FREQUENCY_OPTIONS.index(st.session_state.df.at[index, 'frequency'])+1, key=f"frequency_{index}", label_visibility="collapsed")
        with col7:
            st.session_state.df.at[index, 'duration'] = st.text_input("Duration", value=st.session_state.df.at[index, 'duration'], key=f"duration_{index}", label_visibility="collapsed")
        with col8:
            st.session_state.df.at[index, 'route'] = st.selectbox("Route", options=[''] + ROUTE_OPTIONS, index=0 if pd.isna(st.session_state.df.at[index, 'route']) or st.session_state.df.at[index, 'route'] == '' or st.session_state.df.at[index, 'route'] not in ROUTE_OPTIONS else ROUTE_OPTIONS.index(normalize(st.session_state.df.at[index, 'route']))+1, key=f"route_{index}", label_visibility="collapsed")
        with col9:
            if st.button("🗑️", key=f"delete_{index}", help="Delete this row"):
                st.session_state.df = st.session_state.df.drop(index)
                st.session_state.df = st.session_state.df.reset_index(drop=True)
                st.rerun()

    # Add new row button
    if st.button("Add New Row"):
        new_row = pd.DataFrame([[doc_id, '', '', '', '', '', '', '', '', '']], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

    # Create columns for buttons
    col1, col2, col3 = st.columns(3)

    # Save button
    with col1:
        if st.button("Save Annotation"):
            # Combine dosage_num and dosage_unit back into dosage
            st.session_state.df['dosage'] = st.session_state.df.apply(lambda row: f"{row['dosage_num']} {row['dosage_unit']}" if row['dosage_num'] and row['dosage_unit'] else '', axis=1)
            save_df = st.session_state.df.drop(columns=['dosage_num', 'dosage_unit'])
            print(f"Username saving - {st.session_state.username}")
            save_annotation(doc_id, st.session_state.username, save_df)
            st.success("Annotation saved successfully!")
            # Clear the session state to fetch a new document
            del st.session_state.current_doc
            del st.session_state.df
            st.rerun()

    # Next button
    with col2:
        if st.button("Next Document"):
            # Clear the session state to fetch a new document without saving
            del st.session_state.current_doc
            del st.session_state.df
            st.rerun()

    # Add a warning message when "Next" is clicked
    with col3:
        st.warning("Clicking 'Next Document' will discard unsaved changes.")

if __name__ == "__main__":
    main()