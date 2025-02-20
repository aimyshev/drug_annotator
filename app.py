import streamlit as st
import pandas as pd
import re
from db_utils import fetch_constants, add_constant, fetch_unannotated_doc, fetch_structured_drugs, save_annotation, init_db

FORM_OPTIONS = fetch_constants("form_options")
ROUTE_OPTIONS = fetch_constants("route_options")
FREQUENCY_OPTIONS = fetch_constants("frequency_options")
DOSAGE_UNITS = fetch_constants("dosage_units")

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

@st.fragment
def render_table_row(index):
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2,1,1,1,1,1,1,1,0.5])
    
    # Name
    with col1:
        name = st.text_input(
            "Name", 
            value=st.session_state.df.at[index, 'name'], 
            key=f"name_{index}", 
            label_visibility="collapsed"
        )
        if name != st.session_state.df.at[index, 'name']:
            st.session_state.df.at[index, 'name'] = name

    # Form
    with col2:
        form_options = FORM_OPTIONS + ['Other']
        current_form = normalize(st.session_state.df.at[index, 'form'])
        form_index = 0
        if not pd.isna(current_form) and current_form != '':
            try:
                form_index = form_options.index(current_form) + 1
            except ValueError:
                form_index = 0
                
        form_selected = st.selectbox(
            "Form", 
            options=[''] + form_options, 
            index=form_index,
            key=f"form_{index}", 
            label_visibility="collapsed"
        )
        if form_selected == 'Other':
            new_form = st.text_input("", key=f"new_form_{index}", label_visibility="collapsed")
            if new_form:
                add_constant("form_options", new_form)
                FORM_OPTIONS.append(new_form)
                st.success(f"Added '{new_form}' to Form options.")
        elif form_selected != st.session_state.df.at[index, 'form']:
            st.session_state.df.at[index, 'form'] = form_selected

    # Dosage
    with col3:
        dosage_num = st.text_input(
            "Dosage", 
            value=st.session_state.df.at[index, 'dosage_num'], 
            key=f"dosage_num_{index}", 
            label_visibility="collapsed"
        )
        if dosage_num != st.session_state.df.at[index, 'dosage_num']:
            st.session_state.df.at[index, 'dosage_num'] = dosage_num

    # Unit
    with col4:
        unit_options = DOSAGE_UNITS + ['Other']
        current_unit = st.session_state.df.at[index, 'dosage_unit']
        unit_index = 0
        if not pd.isna(current_unit) and current_unit != '':
            try:
                unit_index = unit_options.index(current_unit) + 1
            except ValueError:
                unit_index = 0
                
        unit_selected = st.selectbox(
            "Unit", 
            options=[''] + unit_options, 
            index=unit_index,
            key=f"unit_{index}", 
            label_visibility="collapsed"
        )
        if unit_selected == 'Other':
            new_unit = st.text_input("", key=f"new_unit_{index}", label_visibility="collapsed")
            if new_unit and st.button(f"Add New Unit", key=f"add_unit_{index}"):
                add_constant("dosage_units", new_unit)
                DOSAGE_UNITS.append(new_unit)
                st.success(f"Added '{new_unit}' to Unit options.")
        elif unit_selected != st.session_state.df.at[index, 'dosage_unit']:
            st.session_state.df.at[index, 'dosage_unit'] = unit_selected

    # Concentration
    with col5:
        concentration = st.text_input(
            "Concentration", 
            value=st.session_state.df.at[index, 'concentration'], 
            key=f"concentration_{index}", 
            label_visibility="collapsed"
        )
        if concentration != st.session_state.df.at[index, 'concentration']:
            st.session_state.df.at[index, 'concentration'] = concentration

    # Frequency
    with col6:
        frequency_options = FREQUENCY_OPTIONS + ['Other']
        current_freq = st.session_state.df.at[index, 'frequency']
        freq_index = 0
        if not pd.isna(current_freq) and current_freq != '':
            try:
                freq_index = frequency_options.index(current_freq) + 1
            except ValueError:
                freq_index = 0
                
        frequency_selected = st.selectbox(
            "Frequency", 
            options=[''] + frequency_options, 
            index=freq_index,
            key=f"frequency_{index}", 
            label_visibility="collapsed"
        )
        if frequency_selected == 'Other':
            new_frequency = st.text_input("", key=f"new_frequency_{index}", label_visibility="collapsed")
            if new_frequency:
                add_constant("frequency_options", new_frequency)
                FREQUENCY_OPTIONS.append(new_frequency)
                st.success(f"Added '{new_frequency}' to Frequency options.")
        elif frequency_selected != st.session_state.df.at[index, 'frequency']:
            st.session_state.df.at[index, 'frequency'] = frequency_selected

    # Duration
    with col7:
        duration = st.text_input(
            "Duration", 
            value=st.session_state.df.at[index, 'duration'], 
            key=f"duration_{index}", 
            label_visibility="collapsed"
        )
        if duration != st.session_state.df.at[index, 'duration']:
            st.session_state.df.at[index, 'duration'] = duration

    # Route
    with col8:
        route_options = ROUTE_OPTIONS + ['Other']
        current_route = normalize(st.session_state.df.at[index, 'route'])
        route_index = 0
        if not pd.isna(current_route) and current_route != '':
            try:
                route_index = route_options.index(current_route) + 1
            except ValueError:
                route_index = 0
                
        route_selected = st.selectbox(
            "Route", 
            options=[''] + route_options, 
            index=route_index,
            key=f"route_{index}", 
            label_visibility="collapsed"
        )
        if route_selected == 'Other':
            new_route = st.text_input("", key=f"new_route_{index}", label_visibility="collapsed")
            if new_route and st.button(f"Add New Route", key=f"add_route_{index}"):
                add_constant("route_options", new_route)
                ROUTE_OPTIONS.append(new_route)
                st.success(f"Added '{new_route}' to Route options.")
        elif route_selected != st.session_state.df.at[index, 'route']:
            st.session_state.df.at[index, 'route'] = route_selected

    # Delete button
    with col9:
        if st.button("🗑️", key=f"delete_{index}", help="Delete this row"):
            st.session_state.df = st.session_state.df.drop(index)
            st.session_state.df = st.session_state.df.reset_index(drop=True)
            st.rerun()

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
        #st.session_state.df[['dosage_num', 'dosage_unit']] = st.session_state.df['dosage'].apply(split_dosage).tolist()

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

    # Render table rows
    for index in range(len(st.session_state.df)):
        render_table_row(index)

    # Add new row button
    if st.button("Add New Row"):
        new_row = pd.DataFrame([[doc_id, '', '', '', '', '', '', '', '']], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

    # Create columns for buttons
    col1, col2, col3 = st.columns(3)

    # Save button
    with col1:
        if st.button("Save Annotation"):
            # Combine dosage_num and dosage_unit back into dosage
            save_df = st.session_state.df
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