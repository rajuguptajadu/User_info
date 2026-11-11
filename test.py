import os
import re
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import streamlit as st

DB_FILE = "user_info.db"

# --- EMAIL CONFIGURATION ---
# Replace these with your actual SMTP server details (e.g., Gmail, Outlook, Mailtrap)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "rajuguptajadu@gmail.com"
SENDER_PASSWORD = "qfja bvoc qphc bmhx"  # Use an App Password, not your regular password!

# --- ADMIN CREDENTIALS ---
ADMIN_PASSWORD = "admin123"  # Change this to your desired admin password


# Initialize database and table structure
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                designation TEXT NOT NULL,
                address TEXT NOT NULL,
                mobile TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """
        )
        conn.commit()


# Insert user details into database
def save_user_data(name, designation, address, mobile, email):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, designation, address, mobile, email)
            VALUES (?, ?, ?, ?, ?)
        """,
            (name, designation, address, mobile, email),
        )
        conn.commit()


# Fetch all entries for viewing (Admin only)
def view_all_data():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("SELECT * FROM users", conn)


# Send automated email notification to the user
def send_confirmation_email(user_name, user_email, designation, address, mobile):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email
        msg["Subject"] = "Registration Successful - User Information Directory"

        body = f"""
        Hello {user_name},

        Thank you for submitting your information. Here is a copy of the details we recorded:

        - Name: {user_name}
        - Designation: {designation}
        - Address: {address}
        - Mobile: {mobile}
        - Email: {user_email}

        Regards,
        System Directory Admin
        """
        msg.attach(MIMEText(body, "plain"))

        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade connection to secure
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)


# Initialize the DB structure at runtime
init_db()

# Page Styling
st.set_page_config(page_title="User Directory", layout="centered", page_icon="📝")
st.title("📝 User Information Portal")

# Create tabs for clean UI
tab1, tab2 = st.tabs(["➕ User Registration", "🔒 View Database (Admin Only)"])

# --- TAB 1: USER REGISTRATION ---
with tab1:
    st.subheader("Enter User Details")
    st.info("A confirmation copy of your details will be sent to your email address.")

    with st.form("user_form", clear_on_submit=True):
        name = st.text_input("Full Name", placeholder="John Doe")
        designation = st.text_input("Designation", placeholder="Software Engineer")
        address = st.text_area(
            "Address", placeholder="123 Main Street, Apartment 4B"
        )
        mobile = st.text_input("Mobile Number", placeholder="9876543210")
        email = st.text_input("Email Address", placeholder="johndoe@example.com")

        submit_btn = st.form_submit_button("Submit Details")

        if submit_btn:
            # Field Validation
            if not (name and designation and address and mobile and email):
                st.error("❌ Please fill out all fields before submitting.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("❌ Please enter a valid email address.")
            else:
                # 1. Save data to database
                save_user_data(name, designation, address, mobile, email)

                # 2. Trigger email to user
                email_success, email_msg = send_confirmation_email(
                    name, email, designation, address, mobile
                )

                if email_success:
                    st.success(
                        f"🎉 Data saved successfully! A confirmation email has been sent to {email}."
                    )
                else:
                    st.warning(
                        f"⚠️ Data saved to database, but confirmation email failed to send. (Error: {email_msg})"
                    )

# --- TAB 2: ADMINISTRATOR DATABASE VIEW ---
with tab2:
    st.subheader("🔐 Administrator Access")

    # Ask for password entry before displaying data
    input_password = st.text_input(
        "Enter Admin Password", type="password", key="admin_pwd_field"
    )

    if input_password:
        if input_password == ADMIN_PASSWORD:
            st.success("🔓 Access Granted.")
            df = view_all_data()

            if df.empty:
                st.info("No records found in the database yet.")
            else:
                # Render the master database table for the administrator
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Allow downloading data backup as CSV file
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Database Backup (CSV)",
                    data=csv_data,
                    file_name="admin_directory_export.csv",
                    mime="text/csv",
                )
        else:
            st.error("❌ Incorrect Password. Access Denied.")
