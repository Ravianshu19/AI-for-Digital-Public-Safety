"""
Labeled evaluation benchmark for the scam classifier.

A curated set of realistic messages modelled on documented fraud patterns
(MHA/I4C advisories, RBI/bank warnings, public scam reports) plus genuine
"hard-negative" messages that mention money/banking/urgency legitimately —
specifically to test the false-positive rate.

label: "scam" | "benign"   family: scam family or "legit"
All content is synthetic; no real personal data.
"""

BENCHMARK = [
    # ---------------- Digital arrest / impersonation ----------------
    ("I am Inspector Verma from CBI. A parcel in your name was seized at customs with illegal drugs. A case is registered against you. Do not tell anyone, you are under digital arrest, stay on this video call.", "scam", "digital_arrest"),
    ("This is the ED. Your Aadhaar was used for money laundering. Transfer all your money to an RBI verified account for verification or we will arrest you today.", "scam", "digital_arrest"),
    ("Customs officer here. Your courier has a fake passport and narcotics. Pay a verification deposit immediately to avoid a non-bailable warrant.", "scam", "digital_arrest"),
    ("Mumbai police cyber cell. Your number is linked to a money laundering case. Keep this confidential and do not disconnect the call or you will be arrested.", "scam", "digital_arrest"),
    ("Sir this is TRAI. Your SIM will be disconnected today as it is misused in illegal activity. Stay on the line for police verification.", "scam", "digital_arrest"),
    ("You are under investigation by the narcotics bureau. Switch on your camera for interrogation, this is a confidential digital custody.", "scam", "digital_arrest"),

    # ---------------- OTP / credential phishing ----------------
    ("Your account will be blocked. Please share the OTP you just received to keep it active.", "scam", "credential_phishing"),
    ("Dear customer, to complete verification enter your OTP, PIN and CVV now to avoid suspension.", "scam", "credential_phishing"),
    ("We detected unusual activity. Confirm your password and the one-time code sent to your phone immediately.", "scam", "credential_phishing"),
    ("Bank security: tell me the OTP received on your number to cancel the unauthorized transaction.", "scam", "credential_phishing"),

    # ---------------- KYC / account suspension ----------------
    ("Your KYC has expired. Update your KYC immediately or your account will be suspended within 24 hours.", "scam", "kyc_account"),
    ("Dear user, your PAN is not linked. Update your details now to avoid your wallet being deactivated.", "scam", "kyc_account"),
    ("Your bank account will be blocked today. Complete KYC verification by clicking the link to update now.", "scam", "kyc_account"),
    ("Paytm KYC pending. Your number will be deactivated unless you verify immediately.", "scam", "kyc_account"),

    # ---------------- Lottery / prize ----------------
    ("Congratulations! You have won 25 lakh in the KBC lottery. Claim your prize by paying the processing fee.", "scam", "prize_lottery"),
    ("You won an iPhone in our lucky draw! Click the link and pay registration to claim your reward.", "scam", "prize_lottery"),
    ("Lucky winner! Your number has won a brand new car. Contact us to claim your winnings now.", "scam", "prize_lottery"),

    # ---------------- Loan / refund / advance-fee ----------------
    ("Pre-approved instant loan of 5 lakh. Just pay a small processing fee to release the amount today.", "scam", "advance_fee"),
    ("Your income tax refund is pending. Click here to process the refund and pay the clearance fee.", "scam", "advance_fee"),
    ("To receive your parcel pay a customs fee. Deposit the charges to release your package.", "scam", "advance_fee"),

    # ---------------- Sextortion ----------------
    ("I have recorded a private video of you through your webcam. Pay money or I will leak it to your contacts.", "scam", "sextortion"),
    ("I captured your intimate video. Send money in bitcoin or we will share it publicly.", "scam", "sextortion"),

    # ---------------- Utility / payment pressure ----------------
    ("Your electricity connection will be disconnected tonight at 9pm. Pay immediately to avoid disconnection.", "scam", "payment_pressure"),
    ("Dear consumer your power will be cut off today due to pending bill. Pay now to the given number urgently.", "scam", "payment_pressure"),

    # ---------------- Subtle scams (hard positives — may slip) ----------------
    ("Hello, regarding your recent issue please call back on this number, it is important.", "scam", "subtle"),
    ("Sir, there is a problem with your account, kindly cooperate with the officer who will call you shortly.", "scam", "subtle"),

    # ================= BENIGN =================
    # Genuine bank / official (hard negatives)
    ("This is a recorded line for quality from your bank. We will never ask you for your OTP or to transfer money. If you did not request this, please visit your nearest branch in person.", "benign", "legit"),
    ("Your OTP for the transaction is 482913. Do not share it with anyone, including bank staff.", "benign", "legit"),
    ("Reminder: your electricity bill of Rs 1,240 is due on 30 June. Pay anytime via the official app or website.", "benign", "legit"),
    ("Your loan EMI of Rs 8,500 has been successfully debited from your account. Thank you.", "benign", "legit"),
    ("Dear customer, your KYC is complete and your account is active. No action is required.", "benign", "legit"),
    ("Your salary of Rs 65,000 has been credited to your account ending 4421.", "benign", "legit"),
    ("Income tax e-filing: your return has been processed. Refund, if any, will be credited to your registered bank account.", "benign", "legit"),
    # Delivery / commerce
    ("Your Amazon order has shipped and will arrive by Thursday. Track it in the app.", "benign", "legit"),
    ("Your Swiggy order is on the way and will reach you in 15 minutes.", "benign", "legit"),
    ("Flipkart: your refund of Rs 999 has been initiated to your original payment method.", "benign", "legit"),
    # Personal / work
    ("Hi mom, can we have dinner at 8 tonight?", "benign", "legit"),
    ("Meeting moved to 3pm tomorrow, please confirm if that works for you.", "benign", "legit"),
    ("Don't forget to pick up the groceries on your way home.", "benign", "legit"),
    ("Happy birthday! Wishing you a wonderful year ahead.", "benign", "legit"),
    ("The project report is ready for your review, I have shared it on the drive.", "benign", "legit"),
    # Promo / service (urgency but legitimate)
    ("Last day! Flat 40% off on all shoes. Shop now on our official store.", "benign", "legit"),
    ("Your Netflix subscription will renew on 1 July. Manage your plan in account settings.", "benign", "legit"),
    ("Your appointment with Dr. Rao is confirmed for Monday at 11am.", "benign", "legit"),
    ("Cricket score update: India needs 45 runs in 30 balls.", "benign", "legit"),
    ("Your cab is arriving in 2 minutes. Driver: Suresh, vehicle DL 1AB 1234.", "benign", "legit"),
]
