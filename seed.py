from datetime import date, datetime, timedelta, timezone
import random

from werkzeug.security import generate_password_hash

from app import app
from database import db
from models import User, StaffProfile, Trek, Booking


PASSWORD = "Password@123"
PASSWORD_HASH = generate_password_hash(PASSWORD)


def random_phone():
    """10-digit Indian mobile number starting with 6–9."""
    return str(random.choice([6, 7, 8, 9])) + "".join(random.choices("0123456789", k=9))


def random_datetime_before(ref_date, min_days=1, max_days=60):
    """Timezone-aware UTC datetime a random number of days before ref_date."""
    delta = timedelta(days=random.randint(min_days, max_days))
    dt = datetime.combine(ref_date - delta, datetime.min.time())
    return dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 24 trekking enthusiasts from across India — mix of cities and backgrounds
# ---------------------------------------------------------------------------
USER_DATA = [
    ("Aarav Sharma",       "aarav.sharma"),        # Delhi — software engineer, weekend trekker
    ("Vivaan Gupta",       "vivaan.gupta"),        # Pune — MBA student, first-time trekker
    ("Aditya Verma",       "aditya.verma"),        # Bengaluru — fitness freak, 5+ treks done
    ("Vihaan Kapoor",      "vihaan.kapoor"),       # Mumbai — photographer, loves high-altitude
    ("Arjun Singh",        "arjun.singh"),         # Chandigarh — army background, experienced
    ("Krishna Nair",       "krishna.nair"),        # Kochi — nature lover, mostly South India
    ("Rohan Mehta",        "rohan.mehta"),         # Ahmedabad — trekking club member
    ("Rahul Joshi",        "rahul.joshi"),         # Dehradun — local to Uttarakhand, regular
    ("Karan Bansal",       "karan.bansal"),        # Jaipur — BLACKLISTED (payment fraud)
    ("Siddharth Rao",      "siddharth.rao"),       # Hyderabad — IT professional
    ("Neha Iyer",          "neha.iyer"),           # Chennai — school teacher, group organiser
    ("Ananya Das",         "ananya.das"),          # Kolkata — solo trekker, experienced
    ("Priya Kulkarni",     "priya.kulkarni"),      # Nashik — casual weekend trekker
    ("Sneha Patil",        "sneha.patil"),         # Nagpur — first Trek ever
    ("Pooja Reddy",        "pooja.reddy"),         # Vijayawada — adventure sports enthusiast
    ("Ishita Jain",        "ishita.jain"),         # Indore — yoga instructor, loves nature
    ("Aditi Menon",        "aditi.menon"),         # Bengaluru — startup founder, rare trekker
    ("Meera Chawla",       "meera.chawla"),        # Ludhiana — experienced, 10+ treks
    ("Ritika Arora",       "ritika.arora"),        # Gurugram — BLACKLISTED (no-show twice)
    ("Kavya Mishra",       "kavya.mishra"),        # Bhopal — college student, budget trekker
    ("Tanuj Bhatt",        "tanuj.bhatt"),         # Haridwar — frequent trekker, local guide
    ("Simran Kaur",        "simran.kaur"),         # Amritsar — adventure blogger
    ("Dev Malhotra",       "dev.malhotra"),        # Noida — corporate professional
    ("Riya Saxena",        "riya.saxena"),         # Lucknow — solo traveller, experienced
]

BLACKLISTED_USERS = {"karan.bansal", "ritika.arora"}


# ---------------------------------------------------------------------------
# 10 certified trek leaders/guides registered on the platform
# Statuses: 7 Approved, 1 Pending, 1 Rejected, 1 Blacklisted
# ---------------------------------------------------------------------------
STAFF_DATA = [
    (
        "Nikhil Rawat", "nikhil.rawat",
        "Certified Himalayan trek leader with 9 years of experience leading expeditions in Uttarakhand and Himachal Pradesh. NIMAS-certified and Wilderness First Responder trained.",
        "Active", "Approved",
    ),
    (
        "Saurabh Negi", "saurabh.negi",
        "Professional mountain guide with 7 years on Uttarakhand and Kumaon trails. Specialises in winter treks and high-altitude acclimatisation planning.",
        "Active", "Approved",
    ),
    (
        "Manish Bisht", "manish.bisht",
        "Outdoor educator and trek coordinator with 6 years of experience. Trained in swift-water rescue and alpine first aid.",
        "Active", "Approved",
    ),
    (
        "Ankit Thapa", "ankit.thapa",
        "High-altitude camping and navigation expert with 5 years leading expeditions in Sikkim and the Darjeeling Himalayas.",
        "Active", "Approved",
    ),
    (
        "Deepak Rana", "deepak.rana",
        "Trek logistics coordinator with 8 years managing group expeditions from permit procurement to campsite setup across Himachal Pradesh.",
        "Active", "Approved",
    ),
    (
        "Rahul Chauhan", "rahul.chauhan",
        "Seasoned trek leader with 6 years conducting beginner-to-advanced Himalayan treks. Known for his detailed pre-trek safety briefings.",
        "Active", "Approved",
    ),
    (
        "Vikas Joshi", "vikas.joshi",
        "Nature guide and eco-tourism specialist with 5 years experience in Uttarakhand. Holds a diploma in Wildlife and Environmental Studies.",
        "Active", "Approved",
    ),
    (
        "Akash Singh", "akash.singh",
        "Recently completed NIMAS Basic Mountaineering Course. Looking forward to leading beginner groups across Himachal and Uttarakhand routes.",
        "Active", "Pending",  # Application under review by admin
    ),
    (
        "Abhishek Mehra", "abhishek.mehra",
        "Outdoor trainer with 3 years experience in navigation and survival skills. Application rejected due to incomplete certification documents.",
        "Active", "Rejected",  # Rejected — incomplete certification
    ),
    (
        "Tarun Kapoor", "tarun.kapoor",
        "Former trek coordinator. Account blacklisted following a conduct complaint raised by participants during the Roopkund Trek.",
        "Blacklisted", "Rejected",  # Blacklisted — mirrors admin.py blacklist_staff()
    ),
]


# ---------------------------------------------------------------------------
# 20 real Indian treks across lifecycle statuses
# Prices reflect actual market rates (INR) for 2024–25 season
# ---------------------------------------------------------------------------
TREK_DATA = [
    # --- Pending (invisible to users, not yet approved) ---
    {
        "name": "Kedarkantha Winter Trek",
        "location": "Uttarakhand",
        "difficulty": "Easy",
        "duration": 6,
        "price": 7999,
        "capacity": 30,
        "description": (
            "One of India's most beloved winter summit treks. The trail winds through dense oak and pine forests "
            "blanketed in snow, culminating at the Kedarkantha summit (3,800m) with sweeping 360° views of "
            "Swargarohini, Bandarpoonch, and the Gangotri range. Perfect for first-time winter trekkers."
        ),
    },
    {
        "name": "Triund Trek",
        "location": "Himachal Pradesh",
        "difficulty": "Easy",
        "duration": 2,
        "price": 3499,
        "capacity": 40,
        "description": (
            "A short, spectacular trek from McLeod Ganj to the Triund ridge (2,850m) with panoramic views of "
            "the Dhauladhar range. The campsite is one of the most scenic in Himachal — ideal for beginners "
            "and those doing their first Himalayan overnight camp."
        ),
    },
    # --- Approved (visible to users, not yet bookable) ---
    {
        "name": "Hampta Pass Trek",
        "location": "Himachal Pradesh",
        "difficulty": "Moderate",
        "duration": 5,
        "price": 10499,
        "capacity": 28,
        "description": (
            "A dramatic crossover trek connecting the lush Kullu Valley to the stark, barren landscapes of Lahaul. "
            "The Hampta Pass (4,270m) offers one of the most striking contrasts in the Himalayas — green meadows "
            "on one side and a lunar-like plateau on the other. Includes a day trip to Chandratal Lake."
        ),
    },
    {
        "name": "Sandakphu Trek",
        "location": "West Bengal",
        "difficulty": "Moderate",
        "duration": 7,
        "price": 11999,
        "capacity": 32,
        "description": (
            "The highest peak in West Bengal (3,636m), Sandakphu sits on the India-Nepal border and offers "
            "the only vantage point in the world where you can see four of the five highest peaks simultaneously — "
            "Everest, Kanchenjunga, Lhotse, and Makalu. The trail passes through Singalila National Park."
        ),
    },
    # --- Bookings Open (actively bookable) ---
    {
        "name": "Valley of Flowers Trek",
        "location": "Uttarakhand",
        "difficulty": "Easy",
        "duration": 6,
        "price": 9499,
        "capacity": 35,
        "description": (
            "A UNESCO World Heritage Site in the Nanda Devi Biosphere Reserve. Every monsoon, the high-altitude "
            "meadow (3,658m) transforms into a canvas of over 500 species of wildflowers. The trail from "
            "Govindghat to Ghangaria passes through dense rhododendron forests and glacial streams."
        ),
    },
    {
        "name": "Goecha La Trek",
        "location": "Sikkim",
        "difficulty": "Hard",
        "duration": 10,
        "price": 19999,
        "capacity": 20,
        "description": (
            "The premier high-altitude expedition in Sikkim (4,940m), offering the closest accessible views of "
            "Mt. Kanchenjunga (the world's third highest peak). The trail passes through Dzongri and Thangsing "
            "meadows with yak herders, glacial lakes, and rhododendron forests."
        ),
    },
    {
        "name": "Roopkund Trek",
        "location": "Uttarakhand",
        "difficulty": "Hard",
        "duration": 8,
        "price": 14999,
        "capacity": 25,
        "description": (
            "One of India's most dramatic and mysterious trails leading to the Skeleton Lake (4,778m) — a glacial "
            "lake containing ancient human skeletons. The route crosses the Ali Bugyal and Bedni Bugyal meadows, "
            "two of the largest high-altitude grasslands in Asia."
        ),
    },
    {
        "name": "Brahmatal Trek",
        "location": "Uttarakhand",
        "difficulty": "Moderate",
        "duration": 6,
        "price": 9499,
        "capacity": 30,
        "description": (
            "A hidden gem for winter trekking, Brahmatal (3,804m) offers frozen alpine lakes, snow-capped ridges, "
            "and stunning views of Mt. Trishul and Mt. Nanda Ghunti. Unlike crowded winter trails, this route "
            "through Wan village stays relatively off the beaten path."
        ),
    },
    {
        "name": "Chopta Chandrashila Trek",
        "location": "Uttarakhand",
        "difficulty": "Easy",
        "duration": 3,
        "price": 5499,
        "capacity": 40,
        "description": (
            "Known as the 'Mini Switzerland of Uttarakhand', Chopta offers a well-maintained trail through "
            "dense bugyal (alpine meadow) to the Chandrashila summit (4,130m). The path passes the ancient "
            "Tungnath temple — the highest Shiva temple in the world at 3,680m."
        ),
    },
    # --- Bookings Closed (fully booked / closed by staff) ---
    {
        "name": "Har Ki Dun Trek",
        "location": "Uttarakhand",
        "difficulty": "Moderate",
        "duration": 7,
        "price": 12499,
        "capacity": 30,
        "description": (
            "A cradle-shaped hanging valley (3,510m) in the Govind National Park, Har Ki Dun is surrounded by "
            "peaks like Swargarohini and Bandarpoonch. The valley is inhabited by the Jaunsari tribe and holds "
            "deep mythological significance in the Mahabharata."
        ),
    },
    {
        "name": "Nag Tibba Trek",
        "location": "Uttarakhand",
        "difficulty": "Easy",
        "duration": 2,
        "price": 2999,
        "capacity": 45,
        "description": (
            "The highest peak of the Lesser Himalayas in Garhwal (3,022m), Nag Tibba is the perfect weekend "
            "getaway from Delhi NCR. The trail through dense oak and rhododendron forests leads to a campsite "
            "with spectacular sunrise views over the Gangotri, Bandarpoonch, and Kedarnath ranges."
        ),
    },
    # --- Ongoing (currently in progress) ---
    {
        "name": "Kashmir Great Lakes Trek",
        "location": "Jammu & Kashmir",
        "difficulty": "Hard",
        "duration": 8,
        "price": 18999,
        "capacity": 22,
        "description": (
            "Often called the most beautiful trek in India, this circuit crosses seven high-altitude alpine lakes "
            "above 3,500m including Vishansar, Krishansar, and Gangabal. The route traverses the Sind valley "
            "and crosses three mountain passes with unmatched panoramic views of the Kashmir range."
        ),
    },
    {
        "name": "Dzongri Trek",
        "location": "Sikkim",
        "difficulty": "Moderate",
        "duration": 6,
        "price": 14499,
        "capacity": 24,
        "description": (
            "Dzongri (4,020m) is the definitive high-altitude trek in Sikkim offering sunrise views of "
            "Kanchenjunga that are considered among the finest in the world. The trail through Yuksom and "
            "Tsokha passes ancient Buddhist monasteries and yak pastures."
        ),
    },
    # --- Completed (historical data for analytics and booking history) ---
    {
        "name": "Tarsar Marsar Trek",
        "location": "Jammu & Kashmir",
        "difficulty": "Moderate",
        "duration": 7,
        "price": 16499,
        "capacity": 24,
        "description": (
            "Twin alpine lakes hidden in the heart of the Kashmir Himalayas. Tarsar and Marsar Lakes sit at "
            "over 3,800m surrounded by wildflower meadows, snow-capped peaks, and ancient shepherd paths. "
            "This trek is considered one of Kashmir's best-kept secrets."
        ),
    },
    {
        "name": "Beas Kund Trek",
        "location": "Himachal Pradesh",
        "difficulty": "Easy",
        "duration": 3,
        "price": 5999,
        "capacity": 35,
        "description": (
            "A short but rewarding trek to the glacial source of the Beas River (3,700m) near Solang Valley, "
            "Manali. The trail crosses rocky moraines, glacier streams, and high-altitude meadows. Popular "
            "with first-timers visiting Manali who want a genuine Himalayan experience."
        ),
    },
    {
        "name": "Kuari Pass Trek",
        "location": "Uttarakhand",
        "difficulty": "Moderate",
        "duration": 6,
        "price": 10499,
        "capacity": 30,
        "description": (
            "Historically known as the Curzon Trail (named after Lord Curzon who trekked it in 1905), the "
            "Kuari Pass (3,640m) offers a front-row view of some of the Garhwal Himalaya's most iconic peaks — "
            "Nanda Devi, Dronagiri, Kamet, and Bethartoli. The trail is accessible year-round."
        ),
    },
    # --- Cancelled (called off before starting) ---
    {
        "name": "Pin Parvati Pass Trek",
        "location": "Himachal Pradesh",
        "difficulty": "Hard",
        "duration": 11,
        "price": 26999,
        "capacity": 18,
        "description": (
            "One of India's toughest and most remote crossover expeditions connecting the lush Parvati Valley "
            "in Kullu to the stark, high-altitude Pin Valley in Spiti (5,319m). The route involves glacier "
            "crossings, moraines, and extreme weather. Cancelled this season due to early snowfall forecast."
        ),
    },
    {
        "name": "Rupin Pass Trek",
        "location": "Uttarakhand",
        "difficulty": "Hard",
        "duration": 8,
        "price": 14999,
        "capacity": 22,
        "description": (
            "Widely regarded as one of India's most scenic high-altitude passes (4,650m), the Rupin Pass "
            "route passes through the dramatic Rupin waterfall, hanging villages, and snow bridges. "
            "Cancelled this season due to landslide damage on the Dhaula approach trail."
        ),
    },
]

# Positional mapping to TREK_DATA above (one status per trek index)
TREK_STATUSES = [
    "Pending",          # 0  Kedarkantha
    "Pending",          # 1  Triund
    "Approved",         # 2  Hampta Pass
    "Approved",         # 3  Sandakphu
    "Bookings Open",    # 4  Valley of Flowers
    "Bookings Open",    # 5  Goecha La
    "Bookings Open",    # 6  Roopkund
    "Bookings Open",    # 7  Brahmatal
    "Bookings Open",    # 8  Chopta Chandrashila
    "Bookings Closed",  # 9  Har Ki Dun
    "Bookings Closed",  # 10 Nag Tibba
    "Ongoing",          # 11 Kashmir Great Lakes
    "Ongoing",          # 12 Dzongri
    "Completed",        # 13 Tarsar Marsar
    "Completed",        # 14 Beas Kund
    "Completed",        # 15 Kuari Pass
    "Cancelled",        # 16 Pin Parvati Pass
    "Cancelled",        # 17 Rupin Pass
]

# Only these statuses have booking history (Pending/Approved = not yet bookable)
BOOKABLE_STATUSES = {"Bookings Open", "Bookings Closed", "Ongoing", "Completed", "Cancelled"}


def create_users():
    """Creates 24 users: 22 Active, 2 Blacklisted."""
    users = []
    for name, username in USER_DATA:
        status = "Blacklisted" if username in BLACKLISTED_USERS else "Active"
        user = User(
            name=name,
            email=f"{username}@gmail.com",
            password_hash=PASSWORD_HASH,
            contact_no=random_phone(),
            role="User",
            status=status,
        )
        db.session.add(user)
        users.append(user)

    db.session.commit()

    active      = sum(1 for u in users if u.status == "Active")
    blacklisted = sum(1 for u in users if u.status == "Blacklisted")
    print(f"Created {len(users)} users  (Active: {active}, Blacklisted: {blacklisted}).")
    return users


def create_staff():
    """Creates 10 staff accounts with StaffProfile rows."""
    staff_users = []
    for name, username, bio, user_status, approval_status in STAFF_DATA:
        staff = User(
            name=name,
            email=f"{username}@gmail.com",
            password_hash=PASSWORD_HASH,
            contact_no=random_phone(),
            role="Staff",
            status=user_status,
        )
        db.session.add(staff)
        db.session.flush()  # Needed to get staff.id for the StaffProfile FK

        profile = StaffProfile(
            user_id=staff.id,
            bio=bio,
            approval_status=approval_status,
        )
        db.session.add(profile)
        staff_users.append(staff)

    db.session.commit()

    approved    = sum(1 for s in staff_users if s.staff_profile.approval_status == "Approved" and s.status == "Active")
    pending     = sum(1 for s in staff_users if s.staff_profile.approval_status == "Pending")
    rejected    = sum(1 for s in staff_users if s.staff_profile.approval_status == "Rejected" and s.status == "Active")
    blacklisted = sum(1 for s in staff_users if s.status == "Blacklisted")
    print(
        f"Created {len(staff_users)} staff  "
        f"(Approved: {approved}, Pending: {pending}, "
        f"Rejected: {rejected}, Blacklisted: {blacklisted})."
    )
    return staff_users


def create_treks(staff_users):
    """
    Creates 18 treks with realistic dates and staff assignments.
    Only Active+Approved staff are eligible for assignment (mirrors admin.py get_approved_staff()).
    ~25% of treks are left unassigned — realistic for a live platform.
    """
    approved_staff = [
        s for s in staff_users
        if s.role == "Staff" and s.status == "Active" and s.staff_profile.approval_status == "Approved"
    ]

    treks = []
    for index, data in enumerate(TREK_DATA):
        status   = TREK_STATUSES[index]
        duration = data["duration"]

        if status == "Completed":
            end_date   = date.today() - timedelta(days=random.randint(10, 60))
            start_date = end_date - timedelta(days=duration)

        elif status == "Ongoing":
            started_days_ago = random.randint(1, max(1, duration - 1))
            start_date = date.today() - timedelta(days=started_days_ago)
            end_date   = start_date + timedelta(days=duration)

        elif status == "Cancelled":
            # Cancelled before departure — dates are still in the future
            start_date = date.today() + timedelta(days=random.randint(5, 45))
            end_date   = start_date + timedelta(days=duration)

        elif status in ("Pending", "Approved"):
            start_date = date.today() + timedelta(days=random.randint(30, 150))
            end_date   = start_date + timedelta(days=duration)

        else:
            # Bookings Open / Bookings Closed
            start_date = date.today() + timedelta(days=random.randint(10, 90))
            end_date   = start_date + timedelta(days=duration)

        assigned_staff = None
        if approved_staff and random.random() > 0.25:
            assigned_staff = random.choice(approved_staff)

        trek = Trek(
            name=data["name"],
            location=data["location"],
            difficulty=data["difficulty"],
            duration=duration,
            price=data["price"],
            total_slots=data["capacity"],
            available_slots=data["capacity"],   # Recalculated after bookings are inserted
            assigned_staff_id=assigned_staff.id if assigned_staff else None,
            status=status,
            start_date=start_date,
            end_date=end_date,
            description=data["description"],
        )
        db.session.add(trek)
        treks.append(trek)

    db.session.commit()

    assigned   = sum(1 for t in treks if t.assigned_staff_id is not None)
    unassigned = len(treks) - assigned
    print(f"Created {len(treks)} treks  (Assigned: {assigned}, Unassigned: {unassigned}).")
    return treks


def create_bookings(users, treks):
    """
    Creates contextually realistic bookings per trek.

    Fill rates by status:
        Bookings Open   → 25–65% (active season, still filling up)
        Bookings Closed → 85–100% (near-full; that's why bookings were closed)
        Ongoing         → 65–90% (all Booked; cancellation blocked once Ongoing)
        Completed       → 55–100% (historical; mix of Booked + some Cancelled)
        Cancelled       → 3–8 bookings; ALL booking.status = 'Cancelled'

    Payment status logic:
        Booked + Bookings Open/Closed → 65% Paid, 35% Pending (many pay closer to trek date)
        Booked + Ongoing              → 95% Paid, 5% Pending (live trek; almost all settled)
        Booked + Completed            → 100% Paid (historical; fully settled)
        booking.status = Cancelled    → 65% Refunded, 25% Paid (refund pending), 10% Pending

    Only Active users book (Blacklisted users are blocked at login — auth.py).
    """
    active_users   = [u for u in users if u.status == "Active"]
    bookable_treks = [t for t in treks if t.status in BOOKABLE_STATUSES]

    bookings      = []
    active_counts = {t.id: 0 for t in treks}
    used_pairs    = set()  # Prevents duplicate (user, trek) booking pairs

    for trek in bookable_treks:
        status = trek.status

        if status == "Cancelled":
            target = random.randint(3, min(8, trek.total_slots))
        elif status == "Ongoing":
            target = int(trek.total_slots * random.uniform(0.65, 0.90))
        elif status == "Completed":
            target = int(trek.total_slots * random.uniform(0.55, 1.0))
        elif status == "Bookings Closed":
            target = int(trek.total_slots * random.uniform(0.85, 1.0))
        else:
            # Bookings Open
            target = int(trek.total_slots * random.uniform(0.25, 0.65))

        target = max(1, target)

        pool = list(active_users)
        random.shuffle(pool)

        created   = 0
        attempts  = 0
        max_tries = len(pool) * 3

        while created < target and attempts < max_tries and pool:
            attempts += 1
            user = pool.pop()
            pair = (user.id, trek.id)

            if pair in used_pairs:
                continue

            # Determine booking + payment status
            if status == "Cancelled":
                booking_status = "Cancelled"
                payment_status = random.choices(
                    ["Refunded", "Paid", "Pending"], weights=[65, 25, 10]
                )[0]

            elif status == "Ongoing":
                booking_status = "Booked"  # Cancellation blocked once Ongoing (staff.py)
                payment_status = random.choices(["Paid", "Pending"], weights=[95, 5])[0]

            elif status == "Completed":
                booking_status = random.choices(["Booked", "Cancelled"], weights=[80, 20])[0]
                payment_status = "Paid" if booking_status == "Booked" else random.choices(
                    ["Refunded", "Paid", "Pending"], weights=[70, 20, 10]
                )[0]

            elif status == "Bookings Closed":
                booking_status = random.choices(["Booked", "Cancelled"], weights=[88, 12])[0]
                if booking_status == "Booked":
                    payment_status = random.choices(["Paid", "Pending"], weights=[70, 30])[0]
                else:
                    payment_status = random.choices(
                        ["Refunded", "Paid", "Pending"], weights=[65, 25, 10]
                    )[0]

            else:
                # Bookings Open
                booking_status = random.choices(["Booked", "Cancelled"], weights=[82, 18])[0]
                if booking_status == "Booked":
                    payment_status = random.choices(["Paid", "Pending"], weights=[65, 35])[0]
                else:
                    payment_status = random.choices(
                        ["Refunded", "Paid", "Pending"], weights=[60, 25, 15]
                    )[0]

            # Capacity guard — only Booked status consumes a slot
            if booking_status == "Booked" and active_counts[trek.id] >= trek.total_slots:
                continue

            # Booking timestamps are always before the trek start date
            if status in ("Completed", "Ongoing"):
                booked_at = random_datetime_before(trek.start_date, min_days=5, max_days=60)
            else:
                booked_at = random_datetime_before(date.today(), min_days=1, max_days=45)

            booking = Booking(
                user_id=user.id,
                trek_id=trek.id,
                booked_at=booked_at,
                status=booking_status,
                payment_status=payment_status,
            )
            db.session.add(booking)

            if booking_status == "Booked":
                active_counts[trek.id] += 1

            bookings.append(booking)
            used_pairs.add(pair)
            created += 1

    db.session.commit()

    total_booked    = sum(1 for b in bookings if b.status == "Booked")
    total_cancelled = sum(1 for b in bookings if b.status == "Cancelled")
    print(
        f"Created {len(bookings)} bookings  "
        f"(Booked: {total_booked}, Cancelled: {total_cancelled})."
    )
    return bookings


def recalculate_available_slots():
    """
    Recalculates available_slots for every trek after all bookings are inserted.
    Ongoing/Completed/Cancelled → 0 (mirrors admin.py and staff.py update_trek_status).
    All others → total_slots minus count of active (Booked) bookings.
    """
    treks = db.session.execute(db.select(Trek)).scalars().all()

    for trek in treks:
        if trek.status in ("Ongoing", "Completed", "Cancelled"):
            trek.available_slots = 0
            continue

        active_count = db.session.scalar(
            db.select(db.func.count(Booking.id)).where(
                Booking.trek_id == trek.id,
                Booking.status == "Booked",
            )
        )
        trek.available_slots = max(0, trek.total_slots - active_count)

    db.session.commit()
    print("Available slots recalculated.")


def clear_existing_data():
    """Wipes all non-admin seeded data in FK-safe order."""
    print("Removing existing dummy data...")
    db.session.query(Booking).delete()
    db.session.query(Trek).delete()
    db.session.query(StaffProfile).delete()
    db.session.query(User).filter(User.role != "Admin").delete()
    db.session.commit()
    print("Cleanup complete.")


def main():
    with app.app_context():
        random.seed()  # Non-deterministic — different data on every run

        print("=" * 60)
        print("TREKKING MANAGEMENT SYSTEM — Database Seeder")
        print("=" * 60)

        # 1. Wipe old seed data (preserves the Admin account created by app.py)
        clear_existing_data()

        # 2. 24 users (22 Active, 2 Blacklisted)
        users = create_users()

        # 3. 10 staff (7 Approved, 1 Pending, 1 Rejected, 1 Blacklisted)
        staff = create_staff()

        # 4. 18 treks across all 7 lifecycle statuses
        treks = create_treks(staff)

        # 5. Bookings for all treks that logically have booking history
        create_bookings(users, treks)

        # 6. Fix available_slots to reflect actual active booking counts
        recalculate_available_slots()

        db.session.commit()

        print()
        print("=" * 60)
        print("Seeding completed successfully.")
        print()
        print(f"Password for ALL seeded accounts : {PASSWORD}")
        print()
        print("Example accounts:")
        print("  Admin  : admin@trekkapp.com          (created by app.py on startup)")
        print("  Staff  : nikhil.rawat@gmail.com      (Approved — full dashboard access)")
        print("  Staff  : akash.singh@gmail.com       (Pending  — awaiting admin approval)")
        print("  Staff  : abhishek.mehra@gmail.com    (Rejected — blocked on login)")
        print("  Staff  : tarun.kapoor@gmail.com      (Blacklisted — blocked on login)")
        print("  User   : aarav.sharma@gmail.com      (Active)")
        print("  User   : karan.bansal@gmail.com      (Blacklisted — blocked on login)")
        print("=" * 60)


if __name__ == "__main__":
    main()
