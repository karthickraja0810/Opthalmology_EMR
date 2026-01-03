import asyncio
from playwright.async_api import async_playwright
import random
import time
import os

# Create screenshots directory
os.makedirs("test_results", exist_ok=True)

async def run_comprehensive_test():
    async with async_playwright() as p:
        print("🚀 Starting Comprehensive Automation Test...")
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        base_url = "http://127.0.0.1:5001"
        uhid = f"AUTO-FULL-{int(time.time())}"
        doc_username = f"doc_auto_{random.randint(100, 999)}"
        doc_password = "password123"
        
        try:
            # --- 1. ADMIN FLOW: Create Doctor ---
            print("\n--- [1] Admin Flow: Creating Doctor ---")
            await page.goto(f"{base_url}/login")
            await page.fill("#username", "admin")
            await page.fill("#password", "adminpass")
            await page.click("button[type='submit']")
            await page.wait_for_url(f"{base_url}/dashboard")
            print("Logged in as Admin.")
            
            await page.fill("#new_username", doc_username)
            await page.fill("#new_password", doc_password)
            await page.select_option("#new_role", "doctor")
            await page.click("button:has-text('Create User')")
            await page.wait_for_selector(".flash-success")
            print(f"Doctor '{doc_username}' created successfully.")
            
            # Logout
            await page.goto(f"{base_url}/logout")
            print("Logged out from Admin.")
            
            # --- 2. DOCTOR FLOW: Register Patient ---
            print("\n--- [2] Doctor Flow: Registering Patient ---")
            await page.goto(f"{base_url}/login")
            await page.fill("#username", doc_username)
            await page.fill("#password", doc_password)
            await page.click("button[type='submit']")
            await page.wait_for_url(f"{base_url}/dashboard")
            print(f"Logged in as Doctor: {doc_username}")
            
            # Click Add Patient to show form
            await page.click("#showAddPatientFormBtn")
            await page.wait_for_selector("#addPatientForm", state="visible")
            
            await page.fill("input[name='uhid']", uhid)
            await page.fill("input[name='first_name']", "Automation")
            await page.fill("input[name='last_name']", "UserFull")
            await page.fill("input[name='dob']", "1990-01-01")
            await page.select_option("select[name='gender']", "male")
            await page.fill("input[name='address']", "456 Automation Ave")
            await page.fill("input[name='phone']", "1234567890")
            await page.fill("input[name='email']", "auto@test.com")
            
            await page.click("#addPatientForm button[type='submit']")
            await page.wait_for_selector(".flash-success")

            print(f"Patient registered: {uhid}")
            
            # --- 3. PATIENT VIEW: Add Medical Record & DR Risk ---
            print("\n--- [3] Patient View: Adding Medical Record ---")
            # Find the patient in the list and click View Details
            # Use a more specific selector to find the View Details link for OUR patient
            await page.click(f"tr:has-text('{uhid}') a:has-text('View Details')")
            # Alternatively, navigate directly if we know the URL pattern but it's better to test UI
            # await page.goto(f"{base_url}/patient/{uhid}")
            
            await page.wait_for_url(f"**/patient/{uhid}")
            print(f"Reached patient view for {uhid}")
            
            # Fill Medical Record
            await page.fill("#diagnosis", "Automation Test Diagnosis - Diabetic Retinopathy with Mild NPDR")
            await page.fill("#treatment", "Strict glycemic control, regular monitoring, consider anti-VEGF if progression.")
            
            # Fill detailed Eye Exam results - Visual Acuity
            await page.fill("#va_od", "20/30")
            await page.fill("#va_os", "20/40")
            await page.fill("#va_od_corrected", "20/20")
            await page.fill("#va_os_corrected", "20/25")
            
            # Intraocular Pressure
            await page.fill("#iop_od", "15")
            await page.fill("#iop_os", "16")
            
            # Refraction OD
            await page.fill("#ref_od_sph", "-2.00")
            await page.fill("#ref_od_cyl", "-0.75")
            await page.fill("#ref_od_ax", "180")
            
            # Refraction OS
            await page.fill("#ref_os_sph", "-1.75")
            await page.fill("#ref_os_cyl", "-0.50")
            await page.fill("#ref_os_ax", "10")
            
            # Slit Lamp Exam
            await page.fill("#sle_od_cornea", "Clear, no infiltrates or edema")
            await page.fill("#sle_os_cornea", "Clear, intact epithelium")
            await page.fill("#sle_od_lens", "Early nuclear sclerosis, Grade 1")
            await page.fill("#sle_os_lens", "Early cortical cataract changes")
            
            # Fundus Exam
            await page.fill("#fundus_od", "Optic disc: healthy C/D ratio 0.3, Macula: few microaneurysms, no hemorrhages")
            await page.fill("#fundus_os", "Optic disc: normal, Macula: scattered microaneurysms and dot hemorrhages, mild NPDR")
            
            # DR Risk Assessment
            print("Running DR Risk Assessment...")
            await page.fill("#dr_duration_diabetes_years", "10")
            await page.fill("#dr_hba1c", "7.5")
            await page.click("#assess-dr-risk")
            await page.wait_for_selector("#dr-risk-result:not(.hidden)")
            dr_result = await page.inner_text("#dr-risk-category")
            print(f"DR Risk Assessment Result: {dr_result}")
            
            # Submit Medical Record
            # Since the form is large, scroll to button
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.click("#submit-medical-record-btn")
            await page.wait_for_selector(".flash-success")

            print("Medical record added successfully.")
            
            # --- 4. PRESCRIPTION FLOW ---
            print("\n--- [4] Prescription Flow ---")
            # Use the "New Prescription" button in the patient view header
            await page.click("a:has-text('New Prescription')")
            await page.wait_for_url(f"**/prescription/{uhid}")
            print("Reached prescription page.")
            
            # 0. Visit Date
            await page.fill("#visit_date", "2025-12-23")
            
            # 1. Spectacle Prescription - Complete OD (Right Eye)
            await page.fill("input[name='spectacle_od_sph']", "-2.00")
            await page.fill("input[name='spectacle_od_cyl']", "-0.75")
            await page.fill("input[name='spectacle_od_axis']", "180")
            await page.fill("input[name='spectacle_od_add']", "+2.50")
            await page.fill("input[name='spectacle_od_prism']", "1 Base Up")
            await page.fill("input[name='spectacle_od_va']", "6/6")
            
            # Spectacle Prescription - Complete OS (Left Eye)
            await page.fill("input[name='spectacle_os_sph']", "-1.75")
            await page.fill("input[name='spectacle_os_cyl']", "-0.50")
            await page.fill("input[name='spectacle_os_axis']", "10")
            await page.fill("input[name='spectacle_os_add']", "+2.50")
            await page.fill("input[name='spectacle_os_prism']", "1 Base Down")
            await page.fill("input[name='spectacle_os_va']", "6/6")
            
            # Lens Type
            await page.select_option("select[name='lens_type']", "Progressive")
            
            # 2. Medication - Complete with duration
            await page.fill("input[name='medication_name_1']", "Timolol 0.5% Eye Drops")
            await page.fill("input[name='medication_dose_1']", "1 drop")
            await page.fill("input[name='medication_frequency_1']", "Twice Daily (BD)")
            await page.select_option("select[name='medication_eye_1']", "OU")
            await page.fill("input[name='medication_duration_value_1']", "30")
            await page.select_option("select[name='medication_duration_unit_1']", "Days")
            
            # 3. Complete Clinical Notes
            await page.fill("textarea[name='systemic_medication']", "Continue Metformin 500mg BD for Diabetes. Monitor HbA1c quarterly. Refer to physician for BP management.")
            await page.fill("textarea[name='surgery_recommendation']", "Cataract surgery advised for OD when vision deteriorates further. Patient counseled about procedure.")
            await page.fill("textarea[name='iol_notes']", "IOL Power: +21.0D (OD), Target: -0.50D myopia for near work. Consider toric IOL if astigmatism persists.")
            await page.fill("textarea[name='patient_instructions']", "Use eye drops regularly as prescribed. Avoid rubbing eyes. Wear UV protection sunglasses outdoors. Monitor blood sugar levels daily.")
            await page.fill("input[name='follow_up_date']", "2026-03-23")
            

            await page.click("button:has-text('Save Prescription')")
            
            # Wait for redirect back or success message
            await page.wait_for_selector(".flash-success")
            print("Prescription saved successfully.")
            
            print("\n✅ COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")

        finally:
            await browser.close()
            print("\n--- Test Environment Cleanup ---")
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
