import psycopg2
import psycopg2.extras # Needed for DictCursor in app.py
from werkzeug.security import generate_password_hash
import uuid 

# This reads the secret URL you put in the Render Dashboard
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    try:
        if DATABASE_URL:
            # Use this on Render
            return psycopg2.connect(DATABASE_URL)
        else:
            # Use this for local testing on your Mac
            return psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="karthi"
            )
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def ensure_uhid_column():
    """Adds the uhid column to the patients table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        print("Checking for missing 'uhid' column in patients table...")

        # Use PostgreSQL's DO block to safely check and add the column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='patients' AND column_name='uhid'
                ) THEN
                    ALTER TABLE patients ADD COLUMN uhid VARCHAR(50) UNIQUE;
                    -- After adding, update existing records to have a placeholder value
                    UPDATE patients SET uhid = 'TEMP-UHID-' || mrn WHERE uhid IS NULL OR uhid = '';
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_uhid ON patients(uhid);
                    RAISE NOTICE 'Added and populated UHID column to patients table.';
                ELSE
                    -- If the column exists, ensure existing NULLs are updated to allow redirection
                    UPDATE patients SET uhid = 'TEMP-UHID-' || mrn WHERE uhid IS NULL OR uhid = '';
                    RAISE NOTICE 'UHID column already exists, ensuring no NULL values.';
                END IF;
            END$$;
        """)
        conn.commit()
        print("✅ UHID column check and data population complete.")
    except Exception as e:
        print(f"❌ Error ensuring UHID column: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals(): cursor.close()
            conn.close()

def ensure_prescription_columns():
    """
    Adds necessary prescription-related columns to the patient_prescriptions table.
    This is vital for existing installations.
    """
    conn = get_db_connection()
    if not conn:
        return
    
    # Define columns to be added: (column_name, data_type)
    columns_to_add = [
        ('lens_type', 'VARCHAR(100)'),
        ('systemic_medication', 'TEXT'),
        ('iol_notes', 'TEXT'),
        ('patient_instructions', 'TEXT'),
        ('follow_up_date', 'DATE'),
    ]

    try:
        cursor = conn.cursor()
        print("Checking for missing columns in patient_prescriptions table...")

        for col_name, col_type in columns_to_add:
            print(f"Checking for column: {col_name}...")
            # Use PostgreSQL's DO block for safe, idempotent column addition
            cursor.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='patient_prescriptions' AND column_name='{col_name}'
                    ) THEN
                        ALTER TABLE patient_prescriptions ADD COLUMN {col_name} {col_type};
                        RAISE NOTICE 'Added column {col_name} to patient_prescriptions.';
                    END IF;
                END$$;
            """)
        
        conn.commit()
        print("✅ Prescription column checks and additions complete.")

    except Exception as e:
        print(f"❌ Error ensuring prescription columns: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals(): cursor.close()
            conn.close()



def ensure_columns():
    """Consolidated function to ensure all required columns exist."""
    print("Ensuring all required database columns...")
    ensure_uhid_column()
    ensure_prescription_columns()
    
    # Also ensure prescription_details in patient_medical_records as expected by app.py startup
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        print("Checking for missing 'prescription_details' column in patient_medical_records table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='patient_medical_records' AND column_name='prescription_details'
                ) THEN
                    ALTER TABLE patient_medical_records ADD COLUMN prescription_details JSONB;
                    RAISE NOTICE 'Added prescription_details column to patient_medical_records.';
                END IF;
            END$$;
        """)
        print("Checking for missing 'uhid' column in patient_edit_history table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='patient_edit_history' AND column_name='uhid'
                ) THEN
                    ALTER TABLE patient_edit_history ADD COLUMN uhid VARCHAR(50);
                    RAISE NOTICE 'Added uhid column to patient_edit_history.';
                END IF;
            END$$;
        """)
        print("Checking for missing 'uhid' column in patient_edit_history table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='patient_edit_history' AND column_name='uhid'
                ) THEN
                    ALTER TABLE patient_edit_history ADD COLUMN uhid VARCHAR(50);
                END IF;
            END$$;
        """)

        print("Checking for missing columns in patient_medical_records table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_medical_records' AND column_name='uhid') THEN
                    ALTER TABLE patient_medical_records ADD COLUMN uhid VARCHAR(50);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_medical_records' AND column_name='created_by') THEN
                    ALTER TABLE patient_medical_records ADD COLUMN created_by INTEGER;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_medical_records' AND column_name='created_at') THEN
                    ALTER TABLE patient_medical_records ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_medical_records' AND column_name='updated_at') THEN
                    ALTER TABLE patient_medical_records ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
                END IF;
            END$$;
        """)

        print("Checking for missing columns in patient_prescriptions table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_prescriptions' AND column_name='uhid') THEN
                    ALTER TABLE patient_prescriptions ADD COLUMN uhid VARCHAR(50);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='patient_prescriptions' AND column_name='visit_date') THEN
                    ALTER TABLE patient_prescriptions ADD COLUMN visit_date TIMESTAMP;
                END IF;
            END$$;
        """)

        print("Making MRN column nullable in patients table...")
        cursor.execute("ALTER TABLE patients ALTER COLUMN mrn DROP NOT NULL;")

        print("Checking for missing 'created_at' column in users table...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='created_at'
                ) THEN
                    ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    RAISE NOTICE 'Added created_at column to users table.';
                END IF;
            END$$;
        """)

        conn.commit()
        print("✅ Consolidated column checks complete.")
    except Exception as e:
        print(f"❌ Error in ensure_columns: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals(): cursor.close()
            conn.close()


def create_tables():
    """Connects to the database and creates necessary tables."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Table 'users' ensured.")

        # Patients table
        # IS THE FALLBACK FOR EXISTING DATABASES***)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                mrn VARCHAR(20) UNIQUE, -- Changed to nullable to match app.py logic
                uhid VARCHAR(50) UNIQUE, -- Defined here for NEW installations
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                dob DATE,
                gender VARCHAR(10),
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(100)
            );
        """)
        print("Table 'patients' ensured.")
        
        # Patient Medical Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_medical_records (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                uhid VARCHAR(50), -- Added to support lookups as expected by app.py
                visit_date TIMESTAMP NOT NULL DEFAULT NOW(),
                diagnosis TEXT NOT NULL,
                treatment TEXT,
                test_results JSONB,
                prescribed_drops JSONB,
                prescribed_medication JSONB,
                surgery_recommendation TEXT,
                risk_assessment_score INTEGER,
                risk_assessment_category VARCHAR(50),
                risk_assessment_implication TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("Table 'patient_medical_records' ensured.")

        # Audit Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                user_id INTEGER, 
                action TEXT NOT NULL,
                details TEXT
            );
        """)
        print("Table 'audit_logs' ensured.")

        # Patient Edit History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_edit_history (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                uhid VARCHAR(50), -- Added to support system logs as expected by app.py
                editor_id INTEGER NOT NULL, 
                field_name VARCHAR(100) NOT NULL,
                old_value TEXT,
                new_value TEXT,
                edited_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("Table 'patient_edit_history' ensured.")

        # Patient Prescriptions table (Updated to include all form fields)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_prescriptions (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                medical_record_id INTEGER REFERENCES patient_medical_records(id) ON DELETE CASCADE,
                uhid VARCHAR(50), -- Added as expected by app.py
                
                -- Refraction/Spectacle Data
                spectacle_lens JSONB,
                lens_type VARCHAR(100),          -- NEW
                
                -- Medication Data
                drops JSONB,
                medications JSONB,

                -- Notes and Follow-up
                systemic_medication TEXT,        -- NEW
                surgery_recommendation TEXT,
                iol_notes TEXT,                  -- NEW
                patient_instructions TEXT,       -- NEW
                follow_up_date DATE,             -- NEW
                visit_date TIMESTAMP,            -- NEW
                
                created_by INTEGER, 
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✅ patient_prescriptions table verified/created with full schema.")

        # Insert a default admin user if not exists
        admin_username = "admin"
        admin_password_hash = generate_password_hash("adminpass", method='pbkdf2:sha256')
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (admin_username,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (admin_username, admin_password_hash, 'admin')
            )
            print(f"Default admin user '{admin_username}' created.")
        
        conn.commit()
        print("Database tables created/ensured successfully!")

    except psycopg2.Error as e:
        print(f"Error creating tables or connecting to database: {e}")
        if conn:
            conn.rollback() # Rollback in case of error
    finally:
        if conn:
            if 'cursor' in locals(): cursor.close()
            conn.close()


if __name__ == '__main__':
    create_tables()
    ensure_uhid_column()
    ensure_prescription_columns() # CRITICAL: Ensure existing installations get the new columns



