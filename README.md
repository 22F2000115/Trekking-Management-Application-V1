# Trekking Management Application - V1

A full-stack web application built using Flask, SQLite, SQLAlchemy, and Bootstrap for managing trekking expeditions from start to finish. The application supports three roles: Admin, Staff, and User (Trekker). Each role has its own dashboard and access permissions, with route-level access control to make sure users can only access the features available to them.

The system includes trek creation and approval, staff assignment and approval, slot-based booking with overbooking prevention, payment status tracking, and complete booking history management.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Concepts](#core-concepts)
- [Role-Based Functionality](#role-based-functionality)
  - [Admin](#admin)
  - [Staff](#staff)
  - [User (Trekker)](#user-trekker)
- [Trek Lifecycle](#trek-lifecycle)
- [Getting Started](#getting-started)
- [Default Admin Account](#default-admin-account)
- [Seeding Demo Data](#seeding-demo-data)
- [Resetting Data](#resetting-data)

## Tech Stack

- **Backend:** Python and Flask using the application factory pattern and Blueprints
- **Database:** SQLite with Flask-SQLAlchemy using SQLAlchemy 2.x syntax
- **Authentication:** Flask-Login for session-based authentication and Werkzeug for password hashing
- **Frontend:** Jinja2 templates, Bootstrap 5.3, and Bootstrap Icons
- **Fonts:** Google Fonts using Cormorant Garamond for headings and Inter for body text

## Project Structure

```
Trekking-Management-Application-V1/
├── app.py                              # Application factory, extension setup, and Admin auto-seed
├── database.py                         # SQLAlchemy database instance
├── models.py                           # User, StaffProfile, Trek, and Booking models
├── decorators.py                       # Role-based access control decorators
├── seed.py                             # Populates the database with realistic demo data
├── reset.py                            # Wipes all data except the Admin account
├── requirements.txt                    # Python project dependencies
├── controllers/
│   ├── auth.py                         # Registration, login, logout, and role-based redirects
│   ├── admin.py                        # Trek, Staff, User, and Booking management for Admin
│   ├── staff.py                        # Assigned trek, participant, and booking management for Staff
│   ├── user.py                         # Trek browsing, booking, and booking history for Users
│   └── main.py                         # Landing page and role-based routing
├── static/
│   └── css/
│       └── style.css                   # Application styling and reusable UI components
└── templates/                          # Jinja2 templates organized by role
    ├── 403.html                        # Unauthorized access page
    ├── base.html                       # Main shared base template
    ├── landing_page.html               # Public landing page
    ├── admin/
    │   ├── add_trek.html               # Create a new trek
    │   ├── admin_base.html             # Shared base layout for Admin pages
    │   ├── bookings.html               # View and search all platform bookings
    │   ├── dashboard.html              # Admin dashboard
    │   ├── edit_trek.html              # Edit existing trek details
    │   ├── staff.html                  # Staff approval and account management
    │   ├── treks.html                  # Trek management and search
    │   └── users.html                  # User account management
    ├── auth/
    │   ├── login.html                  # Shared login page
    │   ├── register_staff.html         # Staff registration page
    │   └── register_user.html          # User registration page
    ├── staff/
    │   ├── bookings.html               # View bookings for assigned treks
    │   ├── dashboard.html              # Staff dashboard and assigned treks
    │   ├── participants.html           # Participant management for an assigned trek
    │   ├── pending.html                # Staff approval status page
    │   ├── profile.html                # Staff profile and password management
    │   ├── staff_base.html             # Shared base layout for Staff pages
    │   └── trek_detail.html            # Assigned trek details and status management
    └── user/
        ├── bookings.html               # Personal booking history
        ├── dashboard.html              # User dashboard
        ├── profile.html                # User profile and password management
        ├── trek_detail.html            # Trek details and booking option
        ├── treks.html                  # Browse, search, and filter available treks
        └── user_base.html              # Shared base layout for User pages
```

## Core Concepts

**Roles**
Every account has one role: `Admin`, `Staff`, or `User`. The role determines which dashboard and routes the account can access.

**Account Status**
Every account also has a status of either `Active` or `Blacklisted`, regardless of its role. A blacklisted account cannot log in to the application.

**Staff Approval**
Staff accounts have an additional approval status of `Pending`, `Approved`, or `Rejected`. This is managed separately from the account status. Only `Active` and `Approved` staff members can access the staff dashboard or be assigned to treks.

**Slot Integrity**
Whenever a booking is created or cancelled, the trek's `available_slots` value is updated within the same database transaction. This prevents overbooking and makes sure a slot is correctly restored after a cancellation.

**Booking History**
Cancelled bookings are not deleted. Instead, they are marked as `Cancelled` and kept in the database, preserving a complete booking history for Staff and Admin.

## Role-Based Functionality

## Admin

The Admin account is automatically created when the application runs for the first time and has full administrative control over the platform.

**Dashboard**
- At-a-glance summary: total users, total staff, total treks, total bookings, and pending staff approvals
- View of the 5 most recent bookings across the platform

**Trek Management**
- Create new treks with name, location, difficulty, duration, price, total slots, start/end dates, and description
- Search and filter treks by name, location, or trek ID
- Edit existing trek details, including total and available slots (bounded by active bookings so slots can never be reduced below what is already booked)
- Assign, reassign, or unassign staff to a trek (restricted to Active, Approved staff only)
- Update a trek's status through its full lifecycle: Pending, Approved, Bookings Open, Bookings Closed, Ongoing, Completed, Cancelled (any of these statuses can be set directly at any time; the system does not enforce a strict sequential order)
- Delete a trek, blocked automatically if the trek has any booking history, to preserve records
- Staff reassignment is automatically blocked once a trek is Ongoing, Completed, or Cancelled

**Staff Management**
- View and search all staff accounts by name, email, ID, or approval status
- Approve or reject pending staff applications
- Blacklist a staff member, which simultaneously sets their approval status to Rejected and unassigns them from every trek not currently Ongoing, Completed, or Cancelled
- Reactivate a previously blacklisted staff member (returns to Pending, requiring re-approval)

**User Management**
- View and search all registered users (Trekkers) by name, email, or ID
- Blacklist a user to immediately block further login
- Reactivate a blacklisted user

**Booking Oversight**
- View every booking across the entire platform
- Search by user name, email, trek name, booking status, payment status, or booking ID

## Staff

Staff accounts represent trek guides. A newly registered Staff account starts with a Pending status and must be approved by an Admin before the Staff dashboard can be accessed.

**Dashboard**
- Search and filter across treks assigned specifically to the logged-in staff member, by trek name, location, status, or trek ID
- Summary statistics: number of assigned treks, total active bookings, treks with bookings open, and treks currently ongoing
- Live participant count per assigned trek

**Trek Detail and Status**
- View full detail for any trek assigned to them
- Update the status of an assigned trek (Bookings Open, Bookings Closed, Ongoing, Completed, Cancelled)
- Manually override available slots for an assigned trek, constrained so it can never exceed total slots minus active bookings
- Access to a trek's detail and status pages is restricted to the staff member it is assigned to; attempting to access another staff member's trek is blocked

**Participant Management**
- View and search all participants (bookings) for a specific assigned trek, by trekker name, email, or booking ID
- Cancel a booking on behalf of a participant, which restores the freed slot (blocked once the trek is Ongoing, Completed, or Cancelled)
- Update a booking's payment status (Pending, Paid, Refunded)

**All Bookings View**
- A flat, searchable list of every booking across all treks assigned to the staff member, searchable by trekker name, email, trek name, booking status, payment status, or booking ID

**Profile**
- Update name, contact number, and bio
- Optionally change password, requiring correct current password confirmation

## User (Trekker)

Users are the customer-facing role of the application. They can browse available treks and make bookings.

**Dashboard**
- Summary statistics: active bookings, treks currently open for booking, treks approved but not yet open, and completed treks the user has participated in
- Quick view of the 3 most recent active bookings and the 5 most recent bookings overall

**Trek Browsing**
- Browse all treks that are either Approved or have Bookings Open (treks in Pending, Bookings Closed, Ongoing, Completed, or Cancelled states are not shown)
- Search by trek name or location, and filter by difficulty (Easy, Moderate, Hard)
- View full trek detail, including a live indicator of whether the user already holds an active booking for that trek

**Booking**
- Book a trek that is currently in Bookings Open status
- Duplicate active bookings for the same trek are automatically prevented
- Booking is blocked once a trek has no available slots

**My Bookings**
- View and search personal booking history by trek name, booking status, payment status, or booking ID
- Cancel an active booking, which restores the freed slot back to the trek (blocked once the trek is Ongoing, Completed, or Cancelled)
- Payment status on a booking is managed exclusively by Staff and is not editable by the User

**Profile**
- Update name and contact number
- Optionally change password, requiring correct current password confirmation

## Trek Lifecycle

```
Pending -> Approved -> Bookings Open -> Bookings Closed -> Ongoing -> Completed
                                                                  \-> Cancelled
```

The diagram above shows the usual lifecycle of a trek. However, the Admin can directly change a trek to any of the seven available statuses at any time because the application does not enforce a strict sequence.

- **Pending:** Newly created by Admin, not visible to Users
- **Approved:** Visible to Users, but not yet bookable
- **Bookings Open:** Visible and bookable by Users
- **Bookings Closed:** No longer visible or bookable to Users, but still visible to Staff and Admin
- **Ongoing / Completed / Cancelled:** Staff reassignment is blocked and available slots are forced to zero for these statuses. Deletion is not tied to status, a trek can only be deleted if it has no booking history at all, regardless of its current status

## Getting Started

**Prerequisites**
- Python 3.10 or later

**Installation**

```bash
git clone <repository-url>
cd Trekking-Management-Application-V1
pip install -r requirements.txt
```

**Run the application**

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`. When the application runs for the first time, the database tables are automatically created and a default Admin account is added.

## Default Admin Account

When the application runs for the first time, a default Admin account is automatically created if an Admin account does not already exist:

| Field    | Value                  |
|----------|------------------------|
| Email    | admin@trekkapp.com     |
| Password | Admin@123              |

For a real deployment, the default password should be changed after the first login.

## Seeding Demo Data

To add realistic demo data for Users, Staff, Treks, and Bookings, run:

```bash
python seed.py
```

This creates 24 users, 10 staff accounts (spanning Approved, Pending, Rejected, and Blacklisted states), 18 treks across all seven lifecycle statuses, and a proportionate set of bookings with varied payment statuses. The password for every seeded account is `Password@123`. The existing Admin account is left untouched.

## Resetting Data

To remove all Users, Staff, Treks, and Bookings while keeping the Admin account, run:

```bash
python reset.py
```
