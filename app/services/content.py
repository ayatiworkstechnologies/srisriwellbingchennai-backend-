from sqlalchemy.orm import Session

from ..config import get_settings, is_safe_admin_password
from ..database import SessionLocal
from ..legacy import is_active_flag
from ..models import (
    AdminUser,
    AlternativeTreatment,
    ContentCategory,
    NadiCamp,
    PageMetaSetting,
    PanchakarmaCoreTherapy,
    PanchakarmaOtherTreatment,
    RelaxationTherapy,
    Service,
    Testimonial,
)
from ..schemas import (
    AdminUserResponse,
    AlternativeTreatmentResponse,
    ManagedContentCategoryRecord,
    NadiCampResponse,
    PageMetaSettingResponse,
    PanchakarmaCoreTherapyResponse,
    PanchakarmaOtherTreatmentResponse,
    RelaxationTherapyResponse,
    ServiceResponse,
    TestimonialResponse,
)
from ..security import get_password_hash

settings = get_settings()


def split_lines(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if not value:
        return []
    return [item.strip() for item in str(value).splitlines() if item.strip()]


def join_lines(items: list[str] | str | None) -> str:
    if isinstance(items, str):
        return "\n".join([item.strip() for item in items.splitlines() if item.strip()])
    if not items:
        return ""
    return "\n".join([item.strip() for item in items if isinstance(item, str) and item.strip()])


def seed_admin_user() -> None:
    db = SessionLocal()
    try:
        existing_admin = db.query(AdminUser).filter(AdminUser.email == settings.admin_email).first()
        safe_admin_password = is_safe_admin_password(settings.admin_password)
        if existing_admin:
            existing_admin.full_name = "Sri Sri Wellbeing Admin"
            existing_admin.role = "super_admin"
            existing_admin.is_active = "true"
            if safe_admin_password or not settings.is_production:
                existing_admin.hashed_password = get_password_hash(settings.admin_password)
        else:
            if settings.is_production and not safe_admin_password:
                raise ValueError(
                    "Unsafe ADMIN_PASSWORD for production. Set ADMIN_PASSWORD to a unique password "
                    "with at least 10 characters before creating the initial admin user."
                )
            db.add(
                AdminUser(
                    email=settings.admin_email,
                    full_name="Sri Sri Wellbeing Admin",
                    hashed_password=get_password_hash(settings.admin_password),
                    role="super_admin",
                    is_active="true",
                )
            )
        db.commit()
    finally:
        db.close()


def seed_default_content() -> None:
    db = SessionLocal()
    try:
        _seed_content_categories(db)
        _seed_services(db)
        _seed_testimonials(db)
        _seed_nadi_camps(db)
        _seed_alternative_treatments(db)
        _seed_relaxation_therapies(db)
        _sync_relaxation_services(db)
        _seed_page_meta_settings(db)
        db.commit()
    finally:
        db.close()


def _seed_services(db: Session) -> None:
    service_records = [
        {
            "category": "main",
            "title": "Nadi Pariksha",
            "description": "A non-invasive Ayurvedic pulse diagnosis technique used by our practitioners to assess your doshas and identify imbalances, serving as the starting point for your personalized wellness journey.",
            "benefits": [
                "Identifies dosha imbalance through pulse reading",
                "Supports personalized therapy and diet planning",
                "Helps detect early wellness patterns",
                "Non-invasive and comfortable assessment",
            ],
            "image": "/images/ser-1.jpg",
            "rating": 4.9,
            "sort_order": 1,
        },
        {
            "category": "main",
            "title": "Panchakarma Rituals",
            "description": "A comprehensive Ayurvedic detoxification and cleansing program designed to eliminate deep-seated toxins and effectively restore balance to the body and mind.",
            "benefits": [
                "Supports deep detoxification and cleansing",
                "Helps restore digestion and metabolic balance",
                "Promotes lightness, energy, and clarity",
                "Personalized rituals guided by Ayurvedic assessment",
            ],
            "image": "/images/ser-2.jpg",
            "rating": 4.9,
            "sort_order": 2,
        },
        {
            "category": "main",
            "title": "Marma Chikitsa",
            "description": "An Ayurvedic technique involving gentle stimulation of specific vital energy points on the body to improve energy flow, reduce stress, and support deep healing.",
            "benefits": [
                "Activates vital energy points",
                "Helps reduce stress and body tension",
                "Supports natural healing and energy flow",
                "Encourages relaxation and emotional balance",
            ],
            "image": "/images/ser-3.jpg",
            "rating": 4.8,
            "sort_order": 3,
        },
        {
            "category": "main",
            "title": "Osteopathic Therapy",
            "description": "A manual therapy focused on the body's musculoskeletal system, aiming to improve overall health by strengthening the framework of the body and managing pain.",
            "benefits": [
                "Improves musculoskeletal alignment",
                "Helps manage stiffness and chronic pain",
                "Supports posture, mobility, and flexibility",
                "Gentle hands-on care for whole-body function",
            ],
            "image": "/images/ser-4.jpg",
            "rating": 4.8,
            "sort_order": 4,
        },
        {
            "category": "main",
            "title": "Ozone Therapy",
            "description": "An advanced restorative treatment utilized to address various chronic conditions and enhance overall systemic vitality through the healing properties of ozone.",
            "benefits": [
                "Supports systemic vitality and recovery",
                "Helps improve oxygen utilization",
                "May assist chronic wellness concerns",
                "Complements integrative restorative care plans",
            ],
            "image": "/images/ser-5.jpg",
            "rating": 4.7,
            "sort_order": 5,
        },
        {
            "category": "main",
            "title": "Meru Therapy",
            "description": "A specialized therapy deeply focused on spinal health and alignment, aiming to restore harmony and balance to the body's structural and energetic systems.",
            "benefits": [
                "Supports spinal health and alignment",
                "Helps ease back, neck, and shoulder discomfort",
                "Encourages structural and energetic balance",
                "Promotes improved movement and body awareness",
            ],
            "image": "/images/ser-6.jpg",
            "rating": 4.8,
            "sort_order": 6,
        },
        {
            "category": "main",
            "title": "Craniosacral Therapy",
            "description": "A gentle, hands-on technique that monitors the rhythm of cerebrospinal fluid to release tensions deep in the body, relieving pain and dysfunction.",
            "benefits": [
                "Gently releases deep body tension",
                "Supports nervous system relaxation",
                "May help reduce pain and dysfunction",
                "Encourages calm, sleep, and inner ease",
            ],
            "image": "/images/ser-7.jpg",
            "rating": 4.8,
            "sort_order": 7,
        },
        {
            "category": "main",
            "title": "Pain Management Therapies",
            "description": "Integrative treatments combining classical and contemporary therapies, including L&B pain management, to address chronic discomfort and restore natural mobility.",
            "benefits": [
                "Targets chronic discomfort and stiffness",
                "Supports natural mobility and functional movement",
                "Combines classical and contemporary therapies",
                "Personalized approach for pain relief goals",
            ],
            "image": "/images/heal/manual.png",
            "rating": 4.9,
            "sort_order": 8,
        },
        {
            "category": "alternative",
            "title": "Osteopathy",
            "description": "A drug-free, non-invasive manual therapy that aims to improve health across all body systems by manipulating and strengthening the musculoskeletal framework.",
            "benefits": ["Supports whole-body alignment", "Helps improve mobility", "Encourages natural pain relief"],
            "image": "/images/heal/osteopathy.png",
            "rating": 4.8,
            "sort_order": 1,
        },
        {
            "category": "alternative",
            "title": "Ozone Therapy",
            "description": "A medical therapy that uses ozone gas to treat infections, wounds, and multiple diseases by inactivating bacteria, viruses, fungi, yeast, and protozoa.",
            "benefits": ["Supports oxygen utilization", "Complements restorative care", "Helps strengthen systemic vitality"],
            "image": "/images/heal/ozone.png",
            "rating": 4.7,
            "sort_order": 2,
        },
        {
            "category": "alternative",
            "title": "Meru Chikitsa",
            "description": "An ancient Ayurvedic spinal therapy involving specific manipulations of the vertebral column to realign the spine and restore the flow of prana through the body.",
            "benefits": ["Supports spinal alignment", "Encourages prana flow", "Helps ease structural discomfort"],
            "image": "/images/heal/meru.png",
            "rating": 4.8,
            "sort_order": 3,
        },
        {
            "category": "alternative",
            "title": "Rakkenho",
            "description": "A Japanese holistic healing system based on the correction of energy flow through the body's meridians, promoting natural self-healing and deep relaxation.",
            "benefits": ["Encourages energy balance", "Promotes deep relaxation", "Supports natural self-healing"],
            "image": "/images/heal/rakkenho.png",
            "rating": 4.8,
            "sort_order": 4,
        },
        {
            "category": "alternative",
            "title": "L&B Therapy",
            "description": "A transformative bodywork modality that integrates breath, movement, and touch to release deep-seated physical and emotional patterns held in the body.",
            "benefits": ["Integrates breath and movement", "Helps release stored tension", "Supports emotional ease"],
            "image": "/images/heal/l&b.png",
            "rating": 4.8,
            "sort_order": 5,
        },
        {
            "category": "alternative",
            "title": "Manual Lymphatic Drainage",
            "description": "A gentle rhythmic massage technique that stimulates the lymphatic system to drain excess fluid, reduce swelling, and support the body's natural detoxification process.",
            "benefits": ["Stimulates lymph flow", "Helps reduce fluid retention", "Supports natural detoxification"],
            "image": "/images/heal/manual.png",
            "rating": 4.8,
            "sort_order": 6,
        },
        {
            "category": "alternative",
            "title": "Marma Chikitsa",
            "description": "Marma Chikitsa involves the stimulation of vital energy points on the body to activate the body's innate healing intelligence and restore the flow of prana.",
            "benefits": ["Activates vital energy points", "Supports prana flow", "Encourages natural healing"],
            "image": "/images/heal/marma.png",
            "rating": 4.8,
            "sort_order": 7,
        },
        {
            "category": "alternative",
            "title": "Reflexology",
            "description": "A therapeutic method based on the principle that there are reflexes in the feet, hands, and ears that correspond to every part, organ, and gland in the body.",
            "benefits": ["Supports organ reflex points", "Promotes relaxation", "Helps improve circulation"],
            "image": "/images/heal/reflexology.png",
            "rating": 4.8,
            "sort_order": 8,
        },
        {
            "category": "alternative",
            "title": "Light & Sound Therapy",
            "description": "An innovative therapy that uses specific frequencies of light and sound to synchronise brain waves, reduce stress, and support mental and emotional wellness.",
            "benefits": ["Supports mental calm", "Uses light and sound frequencies", "Helps reduce stress"],
            "image": "/images/heal/light.png",
            "rating": 4.7,
            "sort_order": 9,
        },
    ]

    legacy_titles = {"Marma Therapy": "Marma Chikitsa"}
    for old_title, new_title in legacy_titles.items():
        existing = db.query(Service).filter(Service.title == old_title).first()
        if existing:
            existing.title = new_title

    for record in service_records:
        query = db.query(Service).filter(Service.title == record["title"])
        if record["category"] != "main":
            query = query.filter(Service.category == record["category"])
        item = query.first()
        if not item:
            item = Service(title=record["title"])
            db.add(item)

        item.category = record["category"]
        item.short_description = record["description"]
        item.description = record["description"]
        item.benefits = join_lines(record["benefits"])
        item.image = record["image"]
        item.duration = record.get("duration", "")
        item.rating = record.get("rating")
        item.sort_order = record["sort_order"]
        item.is_active = "true"


def _seed_content_categories(db: Session) -> None:
    category_records = [
        ("main", "Main", "Homepage and main therapy/service content.", 1),
        ("relax", "Relax", "Relaxation therapy and renewal content.", 2),
        ("relax-sub", "Relax Sub", "Head, hair, and facial renewal therapy content.", 3),
        ("alternative", "Alternative", "Alternative and integrative therapy content.", 4),
        ("panchakarma", "Panchakarma", "Panchakarma and detox-related content.", 5),
    ]

    for slug, label, description, sort_order in category_records:
        item = db.query(ContentCategory).filter(ContentCategory.slug == slug).first()
        if not item:
            item = ContentCategory(slug=slug)
            db.add(item)

        item.label = label
        item.description = description
        item.sort_order = sort_order
        item.is_active = "true"


def _seed_testimonials(db: Session) -> None:
    testimonial_records = [
        ("home", "Anusha Rajan", "A deeply soothing and authentic experience. Netra Tejas felt gentle yet remarkably effective, bringing clarity and comfort in the most natural way. A refined approach to non-invasive care that truly delivers.", 1),
        ("home", "Muthukrishnan Gopal", "An exceptional destination for authentic Ayurvedic care. The experience is thoughtfully curated, offering both depth and genuine healing in a calm, welcoming environment.", 2),
        ("home", "Meera Venkatesh", "What stood out was the level of personalisation. Beginning with Nadi Pariksha, every therapy felt aligned to my body's needs. The experience was unhurried, intuitive, and deeply restorative.", 3),
        ("home", "Rohit Subramanian", "From Abhyanga to relaxation therapies, each session brought a noticeable sense of lightness and ease. The care extended to every member of the family, making it a truly holistic experience.", 4),
        ("relax", "Priya S.", "The Nadi Pariksha consultation was eye-opening. The doctors accurately pinpointed my digestive issues and the tailored Ayurvedic diet transformed my health within weeks.", 1),
        ("relax", "Ramesh K.", "I've been to many spas and wellness centers, but the authenticity and serene ambiance here is unmatched. The stress relief therapies are truly a lifesaver for my corporate lifestyle.", 2),
        ("relax", "Anita M.", "Exceptional care and truly personalized treatments. The staff goes above and beyond to make you feel comfortable and understood. Highly recommend for chronic joint pain.", 3),
        ("nadi", "Ruban Kumar", "The Nadi Pariksha experience I had at Sri Sri Wellbeing was the best thing I've done for my health. The doctor immediately identified my issues and I got a customised set of treatments and supplements from my visits.", 1),
        ("nadi", "Priya Sharma", "I was suffering from chronic digestive issues for years. The Nadi Vaidya accurately identified the root cause through pulse diagnosis and recommended a personalised treatment plan.", 2),
        ("nadi", "Arjun Menon", "As someone dealing with stress-related health problems, Nadi Pariksha was a revelation. The Ayurvedic treatments and lifestyle changes suggested have transformed my sleep quality and mental clarity.", 3),
        ("netra", "Anusha Rajan", "Netra Tejas felt gentle yet remarkably effective, bringing clarity and comfort in the most natural way.", 1),
        ("netra", "Muthukrishnan Gopal", "An exceptional destination for authentic Ayurvedic care with a calm, welcoming environment.", 2),
    ]

    for category, name, review, sort_order in testimonial_records:
        item = (
            db.query(Testimonial)
            .filter(Testimonial.category == category, Testimonial.name == name)
            .first()
        )
        if not item:
            item = Testimonial(category=category, name=name)
            db.add(item)

        item.review = review
        item.sort_order = sort_order
        item.is_active = "true"


def _seed_nadi_camps(db: Session) -> None:
    camp_records = [
        ("Dr. K Aravindhan", "20/05/2026", "Chennai, Tamil Nadu", "Manickam M (9444004975)", "Gurukripa Agencies, No : 16, Aadhi Street , Villivakkam", 1),
        ("Dr. S Meenakshi", "15/05/2026", "Pondicherry", "Saravanan (9843210987)", "Sri Auro Wellness Hall, Heritage Town", 2),
        ("Dr. R Rajesh", "05/05/2026", "Coimbatore, Tamil Nadu", "Vijay (9765432109)", "Art of Living Center, Race Course", 3),
        ("Dr. N Lakshmi", "10/06/2026", "Salem, Tamil Nadu", "Prakash (9123456789)", "Shiva Temple Premise, Fairlands", 4),
        ("Dr. V Anitha", "22/05/2026", "Trichy, Tamil Nadu", "Ramesh (9876543210)", "Srirangam Community Hall", 5),
        ("Dr. M Karthik", "02/05/2026", "Tirunelveli, Tamil Nadu", "Gopal (9944332211)", "Nellai Wellness Hub", 6),
        ("Dr. P Swathi", "18/05/2026", "Vellore, Tamil Nadu", "Suresh (9000011122)", "Anna Salai Center", 7),
    ]

    for doctor, camp_date, location, contact, address, sort_order in camp_records:
        item = (
            db.query(NadiCamp)
            .filter(NadiCamp.doctor == doctor, NadiCamp.camp_date == camp_date)
            .first()
        )
        if not item:
            item = NadiCamp(doctor=doctor, camp_date=camp_date)
            db.add(item)

        item.location = location
        item.contact = contact
        item.address = address
        item.status = "active"
        item.sort_order = sort_order
        item.is_active = "true"


def _seed_alternative_treatments(db: Session) -> None:
    treatment_records = [
        ("osteopathy", "Osteopathy", "A drug-free, non-invasive manual therapy that aims to improve health across all body systems by manipulating and strengthening the musculoskeletal framework.", "/images/heal/osteopathy.png", 1),
        ("ozone", "Ozone Therapy", "A medical therapy that uses ozone gas to treat infections, wounds, and multiple diseases by inactivating bacteria, viruses, fungi, yeast, and protozoa.", "/images/heal/ozone.png", 2),
        ("meru-chikitsa", "Meru Chikitsa", "An ancient Ayurvedic spinal therapy involving specific manipulations of the vertebral column to realign the spine and restore the flow of prana through the body.", "/images/heal/meru.png", 3),
        ("rakkenho", "Rakkenho", "A Japanese holistic healing system based on the correction of energy flow through the body's meridians, promoting natural self-healing and deep relaxation.", "/images/heal/rakkenho.png", 4),
        ("lb-therapy", "L&B Therapy", "A transformative bodywork modality that integrates breath, movement, and touch to release deep-seated physical and emotional patterns held in the body.", "/images/heal/l&b.png", 5),
        ("lymphatic", "Manual Lymphatic Drainage", "A gentle rhythmic massage technique that stimulates the lymphatic system to drain excess fluid, reduce swelling, and support the body's natural detoxification process.", "/images/heal/manual.png", 6),
        ("marma", "Marma Chikitsa", "Marma Chikitsa involves the stimulation of vital energy points on the body to activate the body's innate healing intelligence and restore the flow of prana.", "/images/heal/marma.png", 7),
        ("reflexology", "Reflexology", "A therapeutic method based on the principle that there are reflexes in the feet, hands, and ears that correspond to every part, organ, and gland in the body.", "/images/heal/reflexology.png", 8),
        ("light-sound", "Light & Sound Therapy", "An innovative therapy that uses specific frequencies of light and sound to synchronise brain waves, reduce stress, and support mental and emotional wellness.", "/images/heal/light.png", 9),
    ]

    for item_id, name, short_desc, image, sort_order in treatment_records:
        item = db.query(AlternativeTreatment).filter(AlternativeTreatment.item_id == item_id).first()
        if not item:
            item = AlternativeTreatment(item_id=item_id)
            db.add(item)

        item.name = name
        item.category = "alternative"
        item.short_desc = short_desc
        item.image = image
        item.sort_order = sort_order
        item.is_active = "true"


def _seed_relaxation_therapies(db: Session) -> None:
    therapy_records = [
        {
            "title": "Abhyanga",
            "duration": "45 mins",
            "short_description": "An Ayurvedic massage that promotes wellbeing by applying warm oil on your entire body.",
            "details": "Experience the benefits of Abhyanga, an Ayurvedic massage that promotes wellbeing by applying warm oil on your entire body. The oil is the central component of Abhyanga. When combined with massage strokes, it promotes overall health and wellness. It can be done by a therapist or self-administered at home.",
            "benefits": ["Reduces the signs of aging", "Gives the body muscle tone & energy", "Gives the limbs a firmness", "Lubricates the joints", "Promotes blood circulation & detoxification", "Activates the body's internal organs", "Boosts endurance", "Calms the nerves", "Softens & smoothens skin"],
            "image": "/images/relax/abhyanga.png",
            "sort_order": 1,
        },
        {
            "title": "Uzhichil",
            "duration": "45 mins",
            "short_description": "Effective full-body, deep tissue ayurvedic massage therapy with specific oil pressure.",
            "details": "This is one of the most effective full-body, deep tissue ayurvedic massage therapy. Pressure is applied to the specific parts of the body with oil massage. This therapy is highly recommended for blood circulation as well as the nervous system.",
            "benefits": ["Reduces pressure on the heart", "Treats nervous disorders", "Calms anxiety", "Good for insomnia & hypertension", "Relieves stress & headaches"],
            "image": "/images/relax/uzhichil.png",
            "sort_order": 2,
        },
        {
            "title": "Reflexology",
            "duration": "30 mins",
            "short_description": "Pressure-point therapy for the feet to treat illnesses and strengthen body systems.",
            "details": "Your foot is rubbed, pressed and squeezed on certain locations to treat illnesses. And when the entire foot is massaged, all of the body's systems is strengthened.",
            "benefits": ["Provides deep relaxation", "Improves sleep quality", "Energizes all organs & body tissues", "Relieves anxiety & stress", "Enhances blood circulation in the lower half of the body", "Strengthens the feet", "Reduces stiffness & tiredness"],
            "image": "/images/relax/foot.png",
            "sort_order": 3,
        },
        {
            "category": "relax-sub",
            "title": "Shirolepa",
            "duration": "45 mins",
            "short_description": "Soothing application of medicinal pastes on the scalp for psychosomatic relief.",
            "details": "Medicinal pastes are applied over the entire scalp which is soothing and has relaxing properties. This time-tested Ayurveda therapy is an excellent treatment for a variety of psychosomatic ailments and boosting overall well-being.",
            "benefits": ["Improves sleep quality", "Helps the visionary abilities", "When combined with yoga, it helps with anxiety", "Improves hair health", "Brings the pita dosh back into equilibrium"],
            "image": "/images/relax/shirolepa.png",
            "sort_order": 4,
        },
        {
            "title": "Body Wrap",
            "duration": "90 mins",
            "short_description": "Natural aromatic body wrap enriched with Moringa for detoxification and nourishment.",
            "details": "Also called Haritaka Lepam, this beauty treatment is enriched with Moringa's goodness. This Ayurveda body wrap is a natural aromatic paste of freshly ground Moringa Oleifera leaves. It offers powerful antioxidants to skin cells to keep the skin cleansed, moisturized, nourished and revitalized naturally.",
            "benefits": ["Detoxifies the skin", "Improves circulation", "Rejuvenates & hydrates the skin", "Improves skin tone", "Is soothing, comforting & provides relaxation"],
            "image": "/images/relax/chlorophyll.png",
            "sort_order": 5,
        },
        {
            "title": "Shirodhara",
            "duration": "45 mins",
            "short_description": "Lukewarm oil stream over the forehead to enhance the central nervous system.",
            "details": "A deeply relaxing therapy during which the scalp and forehead are caressed by a thin stream of medicated lukewarm oil. Helps to enhance the functioning of the central nervous system. Prevents hair fall and premature greying. Good for insomnia, tension headaches, nervous disorders. Shirodhara is a more calm therapeutic head massage that has many positive effects on the body and the mind. Shirodhara is therefore superior than a head massage. After applying oil to the forehead, there is a brief massage performed in this procedure. And it really is as soothing as it sounds.",
            "benefits": ["Activates intuition", "Improves sleep", "Reduces stress", "Soothes eyes", "Pacifies elevated vata dosha", "Improves cognitive abilities"],
            "image": "/images/relax/shirodhara.png",
            "sort_order": 6,
        },
        {
            "title": "Head Massage",
            "duration": "45 mins",
            "short_description": "Holistic treatment targeting marma points to boost healing and sleep quality.",
            "details": "Ayurveda head massage is a holistic treatment that involves applying mild pressure to the head, which has 31 marma points where arteries and veins intersect. This massage also benefits the scalp. Besides, it boosts the body's natural healing abilities and enhances sleep quality.",
            "benefits": ["Boosts blood circulation", "Induces relaxation & deep sleep", "Stimulates hair growth", "Improves concentration", "Relieves stress, insomnia, depression & migraine pain"],
            "image": "/images/relax/head-massage.png",
            "sort_order": 7,
        },
        {
            "title": "Head & Foot Massage",
            "duration": "45 mins",
            "short_description": "Combined therapy for cerebral nourishment and reflex point activation.",
            "details": "Head massage helps to break down muscular knots and reduces chronic neck & shoulder discomfort. This procedure also promotes hair growth, nourishes cerebral arteries, and enhances blood circulation. Foot massage, on the other hand, concentrates on the reflex points in the feet to enhance blood circulation. This practice, in addition to giving relaxation, is beneficial to one's vision because foot massage nourishes our optic nerve.",
            "benefits": ["Advances hair growth", "Nourishes the brain's arteries", "Improves blood circulation", "Relaxes the body", "Nourishes the optic nerve"],
            "image": "/images/relax/head-foot.png",
            "sort_order": 8,
        },
        {
            "category": "relax-sub",
            "title": "Keshavarna",
            "duration": "45 mins",
            "short_description": "Hair care treatment with crushed herbs and oils to prevent dandruff and boost growth.",
            "details": "This hair care treatment involves an energizing head massage, which is enhanced with freshly crushed herbs, butter and olive oil. This treatment encourages healthy hair development and aids with dandruff prevention.",
            "benefits": ["Promotes healthy hair growth", "Helps in eradicating dandruff", "Releases stress & anxiety"],
            "image": "/images/relax/keshavarna.png",
            "sort_order": 9,
        },
        {
            "category": "relax-sub",
            "title": "Mukhalepa",
            "duration": "45 mins",
            "short_description": "Natural Ayurveda facial therapy for skin purity, glow, and rejuvenation.",
            "details": "An Ayurveda Facial Therapy which uses natural ingredients, freshly ground herbal blends & packs to maintain the purity of one's inner beauty. Besides - fruits, coconut extract and saffron - all form part of this herbal paste. This beauty therapy is relaxing due to the fragrant and aromatic oils used. This natural herbal beauty therapy is by far the best solution for our outer cosmetic skin requirements, bringing out our inner glow.",
            "benefits": ["Keeps skin soft, glowing & radiant", "Natural & chemical free", "Reduces acne & pimples", "Prevents aging of the skin", "Moisturises & hydrates", "Improves skin tone"],
            "image": "/images/relax/mukhalepa.png",
            "sort_order": 10,
        },
    ]

    for record in therapy_records:
        item = db.query(RelaxationTherapy).filter(RelaxationTherapy.title == record["title"]).first()
        if not item:
            item = RelaxationTherapy(title=record["title"])
            db.add(item)

        item.category = record.get("category", "relax")
        item.duration = record["duration"]
        item.short_description = record["short_description"]
        item.details = record["details"]
        item.benefits = join_lines(record["benefits"])
        item.image = record["image"]
        item.sort_order = record["sort_order"]
        item.is_active = "true"


def _sync_relaxation_services(db: Session) -> None:
    therapies = (
        db.query(RelaxationTherapy)
        .filter(RelaxationTherapy.category.in_(["relax", "relax-sub"]))
        .order_by(RelaxationTherapy.sort_order.asc(), RelaxationTherapy.id.asc())
        .all()
    )

    for therapy in therapies:
        item = (
            db.query(Service)
            .filter(Service.title == therapy.title)
            .first()
        )
        if not item:
            item = Service(category=therapy.category, title=therapy.title)
            db.add(item)

        item.category = therapy.category
        item.short_description = therapy.short_description
        item.description = therapy.details
        item.benefits = therapy.benefits
        item.image = therapy.image
        item.duration = therapy.duration
        if item.rating is None:
            item.rating = 4.8
        item.sort_order = therapy.sort_order
        item.is_active = "true"


def _seed_page_meta_settings(db: Session) -> None:
    if db.query(PageMetaSetting).first():
        return

    db.add_all(
        [
            PageMetaSetting(page_key="home", page_path="/", title="Sri Sri Wellbeing Chennai | Ayurveda, Panchakarma & Relaxation", description="Discover natural healing at Sri Sri Wellbeing Chennai with Ayurvedic treatments, Panchakarma therapies, relaxation rituals, and personalised wellness care."),
            PageMetaSetting(page_key="about", page_path="/about-us", title="About Sri Sri Wellbeing Chennai", description="Learn about Sri Sri Wellbeing Chennai, our Ayurvedic approach, wellness philosophy, and personalised healing experience."),
            PageMetaSetting(page_key="relax", page_path="/relaxationtherapy", title="Relaxation Therapy | Sri Sri Wellbeing Chennai", description="Explore Ayurvedic relaxation therapies, renewal rituals, and restorative wellbeing experiences at Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="facilities", page_path="/facilities", title="Facilities | Sri Sri Wellbeing Chennai", description="Explore the facilities, stay options, therapy spaces, and wellness environment at Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="products", page_path="/products", title="Products | Sri Sri Wellbeing Chennai", description="Browse wellness products and supportive Ayurvedic offerings from Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="contact", page_path="/contact", title="Contact Sri Sri Wellbeing Chennai", description="Reach Sri Sri Wellbeing Chennai for Ayurveda treatments, Panchakarma therapies, wellness appointments, and enquiries."),
            PageMetaSetting(page_key="nadi-pariksha", page_path="/heal/nadi-pariksha", title="Nadi Pariksha | Sri Sri Wellbeing Chennai", description="Book Nadi Pariksha consultations and upcoming camps with expert Ayurvedic guidance at Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="panchakarma", page_path="/heal/panchakarma", title="Panchakarma | Sri Sri Wellbeing Chennai", description="Discover Panchakarma detox, cleansing therapies, and Ayurvedic renewal programmes at Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="alternative-treatments", page_path="/heal/alternativetreatments", title="Alternative Treatments | Sri Sri Wellbeing Chennai", description="Explore complementary Ayurvedic and holistic treatments offered at Sri Sri Wellbeing Chennai."),
            PageMetaSetting(page_key="netra-tejas", page_path="/heal/netratejas", title="Netra Tejas | Sri Sri Wellbeing Chennai", description="Learn about Netra Tejas and supportive eye-focused wellness therapies at Sri Sri Wellbeing Chennai."),
        ]
    )


def as_service(item: Service) -> ServiceResponse:
    return ServiceResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        short_description=item.short_description,
        description=item.description,
        benefits=split_lines(item.benefits),
        image=item.image,
        duration=item.duration,
        rating=item.rating,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_testimonial(item: Testimonial) -> TestimonialResponse:
    return TestimonialResponse(
        id=item.id,
        category=item.category,
        name=item.name,
        review=item.review,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_nadi_camp(item: NadiCamp) -> NadiCampResponse:
    return NadiCampResponse(
        id=item.id,
        doctor=item.doctor,
        camp_date=item.camp_date,
        location=item.location,
        contact=item.contact,
        address=item.address,
        status=item.status,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_managed_content_category(item: ContentCategory) -> ManagedContentCategoryRecord:
    return ManagedContentCategoryRecord(
        id=item.id,
        slug=item.slug,
        label=item.label,
        description=item.description,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_relax(item: RelaxationTherapy) -> RelaxationTherapyResponse:
    return RelaxationTherapyResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        duration=item.duration,
        short_description=item.short_description,
        details=item.details,
        benefits=split_lines(item.benefits),
        image=item.image,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_alt(item: AlternativeTreatment) -> AlternativeTreatmentResponse:
    return AlternativeTreatmentResponse(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        category=item.category,
        short_desc=item.short_desc,
        image=item.image,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_pk_core(item: PanchakarmaCoreTherapy) -> PanchakarmaCoreTherapyResponse:
    return PanchakarmaCoreTherapyResponse(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        dosha=item.dosha,
        dosha_color=item.dosha_color,
        dosha_bg=item.dosha_bg,
        dosha_border=item.dosha_border,
        short_desc=item.short_desc,
        image=item.image,
        benefits=split_lines(item.benefits),
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_pk_other(item: PanchakarmaOtherTreatment) -> PanchakarmaOtherTreatmentResponse:
    return PanchakarmaOtherTreatmentResponse(
        id=item.id,
        name=item.name,
        category=item.category,
        desc=item.desc,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_admin_user(item: AdminUser) -> AdminUserResponse:
    return AdminUserResponse(
        id=item.id,
        email=item.email,
        full_name=item.full_name,
        role=item.role,
        therapist_id=item.therapist_id,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_page_meta_setting(item: PageMetaSetting) -> PageMetaSettingResponse:
    return PageMetaSettingResponse(
        id=item.id,
        page_key=item.page_key,
        page_path=item.page_path,
        title=item.title,
        description=item.description,
        is_active=is_active_flag(item.is_active),
        updated_at=item.updated_at,
        created_at=item.created_at,
    )
