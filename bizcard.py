import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import tempfile
import re
import PIL
from PIL import Image
import io
from io import BytesIO
import mysql.connector as msql
from mysql.connector import Error
import base64
from streamlit_lottie import st_lottie
import json


# ------------------- easyocr -----------------------------------------

reader = easyocr.Reader(['en'], gpu=True)

# ------------------- easyocr -----------------------------------------

# ------------- Functions to Image processing ---------------


# Function to convert image to base64 string
def pil_to_b64str(image):
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()
    b64str = base64.b64encode(img_bytes).decode()
    return b64str


# Function to convert base64 string to PIL image
def b64str_to_pil(b64str):
    img_bytes = base64.b64decode(b64str)
    image = Image.open(io.BytesIO(img_bytes))
    return image

# ------------- Functions to Image processing --------------------------------------------------------------------------

with st.sidebar:
    menu = option_menu(
        menu_title='Main Menu',
        options=['Home',
                 'Bizcard Extraction',
                 'MySQL Operations'],
        icons=['house', 'app', 'clipboard-data','pie-chart'],
        default_index=0)

if menu == 'Home':
    st.markdown("<h1 style='text-align:center; color:#Ff2f00; font-size: 60px; white-space: nowrap;'"
                "><u>Business Card Data Extraction</u></h1>",
                unsafe_allow_html=True)
    st.write('')
    # ----------------------------------------Lottie Animation----------------------------------------------------------
    # Here the lottie file
    with open("133736-interactive-digital-business-cards.json", "r") as f:
        data = json.load(f)
    st_lottie(data, height=600, width=780)
    # ----------------------------------------Lottie Animation----------------------------------------------------------


if menu == 'Bizcard Extraction':

    st.markdown("<h1 style='text-align:center; color:#00ff41; font-size: 45px; white-space: nowrap;'"
                "><u>Data Extraction from Business Card</u></h1>",
                unsafe_allow_html=True)
    st.write('')

    uploaded_file = st.file_uploader("Upload your file here...",
                                     type=['png', 'jpeg', 'jpg'])

    if uploaded_file is not None:
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write the contents of the uploaded file to the temporary file
            temp_file.write(uploaded_file.read())
            # Get the path of the temporary file
            file_path = temp_file.name

        img = st.image(uploaded_file)
        # Read the file object as bytes
        file_bytes = uploaded_file.read()
        # Convert the bytes to an image using PIL
        image = Image.open(io.BytesIO(file_bytes))
        # Display the image
        #st.image(image, caption="Uploaded Image")

    # -------------- Data Extraction portion ---------------------------------------------------------------

        # ------------ Using easyocr to read image text --------------------
        results = reader.readtext(file_path)
        card_info = [text[1] for text in results]

        # ------------ Finding Names ---------------------------------------
        name_pattern = r'^[A-Za-z]+ [A-Za-z]+$|^[A-Za-z]+$|^[A-Za-z]+ & [A-Za-z]+$'

        name_info = []
        for i in card_info:
            if re.findall(name_pattern, i):
                if i != 'WWW':
                    name_info.append(i)

        name = name_info[0]
        job_title = name_info[1]

        if len(name_info) == 3:
            company = name_info[2]
        else:
            company = name_info[2] + ' ' + name_info[3]
        # ------------ Finding Names ---------------------------------------------------------------

        # ------------ Finding Address -------------------------------------------------------------
        address_pattern = r'\d+\s+[a-zA-Z]+\s+\w+\s*,\s*[a-zA-Z]+\s*|\d [a-zA-Z]|^St |[A-Za-z],'

        address_info = []

        for i in card_info:
            if re.findall(address_pattern, i):
                address_info.append(i)

        if len(address_info) == 3:
            address_info = address_info
        else:
            for i in card_info:
                if re.findall(address_pattern, i):
                    address_info = re.split('[,;]+', i)
            address_info = [i for i in address_info if i != '']

        # ------------ Pincode finding -----------------------------------------------------------------
        pincode_pattern = r'\d{6}'

        for i in card_info:
            if re.findall(pincode_pattern, i):
                pincode = i.split(' ')
                print(pincode)

        address_new = address_info + pincode

        # ------------ Solving St.,(street) problem -------------------------
        for i in address_new:
            if i.startswith('St'):
                address_new.remove(i)
                address_new[0] = address_new[0] + ' ' + i

        # ------------ Finding Address ---------------------------------------

        # ------------ Finding Phone Number ---------------------------------------
        phone_no_pattern = r'^\+?\d{1,3}[- ]?\d{2,3}[- ]?\d{4}'

        phone_no = []
        for i in card_info:
            if re.findall(phone_no_pattern, i):
                phone_no.append(i)
        # ------------ Finding Phone Number ---------------------------------------

        # ------------ Finding Email Address ---------------------------------------
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        for i in card_info:
            if re.findall(email_pattern, i):
                email = i
        # ------------ Finding Email Address -----------------------------------

        # ------------ Finding Website URL ---------------------------------------
        website_pattern = r'\b(?<!@)(?:https?://|www\.)\S+\b|[wW][wW][wW]?\.\w+\.\w+|' \
                          '[Ww]{3}\s?[.a-zA-Z0-9]+\.com|^[A-Za-z]+\.com$'

        for i in card_info:
            if re.findall(website_pattern, i):
                website = i
                if website.startswith('www.') and website.endswith('.com'):
                    website = website
                elif website.endswith('com') and not website.endswith('.com'):
                    website = re.sub(r'com$', r'.com', website)
                elif not website.startswith('WWW'):
                    if website.startswith('wWW'):
                        website = website.replace('wWW', 'www')
                        break
                    elif website.startswith('www') and ' ' in website:
                        website = website.replace(' ', '.')
                    elif website.startswith('wwW') and ' ' in website:
                        website = website.replace('wwW', 'www').replace(' ', '.')
                    else:
                        website = "www." + website
                elif website.startswith('WWW') and ' ' in website:
                    website = website.replace(' ', '.')
                else:
                    website = website

        # ----------------- Finding Website URL -------------------------------------------------------------

    # --------------------- Data Extraction portion ----------------------------------------------------

        tab1, tab2 = st.tabs(['Extract the data from image', 'Load the Extracted data to MySQL'])

        with tab1:
            st.write('')
            btn1 = st.button('Extract Data from Image')
            if btn1:
                # ------------ Creating Business Card Dictionary ---------------------------
                business_card = {'Name': name_info[0],
                                 'Job Title': name_info[1],
                                 'Company': company,
                                 'Area': address_new[0],
                                 'City': address_new[1],
                                 'State': address_new[2],
                                 'Pincode': address_new[3],
                                 'Mobile Number': phone_no[0],
                                 'Email': email,
                                 'Website': website}

                # ------------ Creating Business Card Dictionary --------------------------------

                # ------------ Displaying Extracted data -------------------------------------------
                with st.expander('Expand this to view data'):
                    for key, val in business_card.items():
                        st.write(f'{key.upper()}: {val}')

        with tab2:
            st.write('')
            if st.button('Load data to MySQL'):

                # -------- Create a dataframe along with Image file ------------------------------
                business_card = {'Name': name_info[0],
                                 'Job_title': name_info[1],
                                 'Company': company,
                                 'Area': address_new[0],
                                 'City': address_new[1],
                                 'State': address_new[2],
                                 'Pincode': address_new[3],
                                 'Phone_Number': phone_no,
                                 'Email': email,
                                 'Website': website}
                df = pd.DataFrame(business_card)

                # Connect to the MySQL database
                cnx = msql.connect(user='root',
                                       password='sathesh123',
                                       host='localhost',
                                       database='biz_card')
                cursor = cnx.cursor()

                query = "INSERT INTO biz_card.business_card " \
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (file_bytes, name_info[0], name_info[1], company, address_new[0], address_new[1],
                           address_new[2], address_new[3], phone_no[0], email, website)
                cursor.execute(query, val)

                cnx.commit()

                # Close the database connection
                cursor.close()
                cnx.close()
                # Display a success message
                st.success("Data has been sent to MySQL database successfully", icon="👍")

if menu == 'MySQL Operations':

    st.markdown(
        """
        <style>
        .fullScreenFrame > div:first-child {
            padding-left: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h1 style='text-align:left; color:#Ff009c; white-space: nowrap; font-size: 46px;'"
                "><u>Access the stored data from MySQL</u></h1>",
                unsafe_allow_html=True)

    st.write('')
    read_btn = st.button('Show Database')

    if not st.session_state.get('button'):
        st.session_state['button'] = read_btn  # Saved the state

    if st.session_state['button']:

        try:
            conn = msql.connect(host='localhost',
                                database='biz_card', user='root',
                                password='sathesh123')
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM business_card")
                records = cursor.fetchall()
                data = pd.DataFrame(records,
                                    columns=[i[0] for i in cursor.description])

                conn.commit()
                cursor.close()
                conn.close()
        except Error as e:
            print("Error while connecting to MySQL", e)

        st.dataframe(data)

        #st.write(data['image_data'][2])

        tab1, tab2, tab3 = st.tabs(["Read image from MySQL",
                                    "Update Information to MySQL",
                                    "Delete information from MySQL"])

        with tab1:

            name = st.text_input('Enter name:')
            job = st.text_input('Enter job:')

            if st.button('Show Image'):
                # Convert the image data to a PIL image
                image_data = data['image_data'][(data['name'] == name) & (data['job_title'] == job)]

                image_from_db = Image.open(BytesIO(image_data[image_data.index[0]]))

                # Display the image and text data
                st.image(image_from_db, caption="Image from MySQL database")

        with tab2:

            name2 = st.text_input('Enter the name:')
            job2 = st.text_input('Enter the job:')

            select_option = ('name', 'job_title', 'company', 'area', 'city', 'state',
                             'pincode', 'phone_number', 'email', 'website')

            change_option = st.selectbox('What do you want to change?', select_option)
            new_info = st.text_input(f'Enter the new {change_option}:')

            if st.button('Update Information'):
                try:
                    conn = msql.connect(host='localhost',
                                        database='biz_card', user='root',
                                        password='sathesh123')
                    if conn.is_connected():
                        cursor = conn.cursor()

                        # update query
                        update_query = f"UPDATE business_card " \
                                       f"SET {change_option} = '{new_info}' " \
                                       f"WHERE name = '{name2}' " \
                                       f"AND job_title = '{job2}'"

                        # execute query
                        cursor.execute(update_query)

                        conn.commit()
                        cursor.close()
                        conn.close()

                        st.success('You have successfully updated your information... ', icon="✅")

                except Error as e:
                    print("Error while connecting to MySQL", e)

        with tab3:

            name = st.text_input('Enter the Name:')
            job = st.text_input('Enter the Job:')

            if st.button('Delete Information'):
                try:
                    conn = msql.connect(host='localhost',
                                        database='biz_card', user='root',
                                        password='sathesh123')
                    if conn.is_connected():
                        cursor = conn.cursor()

                        # update query
                        delete_query = f"DELETE from business_card " \
                                       f"WHERE name = '{name}' " \
                                       f"AND job_title = '{job}'"

                        # execute query
                        cursor.execute(delete_query)

                        conn.commit()
                        cursor.close()
                        conn.close()

                        st.success('You have successfully Deleted the information... ', icon="👍")

                except Error as e:
                    print("Error while connecting to MySQL", e)