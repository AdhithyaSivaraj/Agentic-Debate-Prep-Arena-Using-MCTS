"""
topic_knowledge.py — Pre-packaged and Dynamic Domain Knowledge Base

Provides grounded factual claims and argument pools for debate topics.
Includes:
  - Domain Knowledge for prepackaged demo topics ("hostel", "dex", "data centre", "exam", "ai regulation", "ro", "phone")
  - Universal Dynamic Topic Synthesizer for arbitrary custom topics with zero repetitive administrative boilerplate
  - Direct targeted rebuttal map for cross-agent counters
"""
from __future__ import annotations

import re
from typing import Any

from core.fact_generation import FactRecord
from tools.tool_executor import parse_propositional_form

                                                                             
PREPACKAGED_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "hostel": {
        "pro_facts": [
            "Living in a college hostel fosters self-reliance, independence, and essential life management skills away from parental supervision.",
            "Hostel residence provides 24/7 proximity to campus research libraries, laboratories, and peer study groups.",
            "Campus hostel life immerses students in rich extracurricular activities, student leadership roles, and social networking.",
            "Eliminating daily commuting saves significant travel time that students redirect toward academic studies and rest.",
        ],
        "con_facts": [
            "Dayscholars commuting from home enjoy a supportive family environment, home-cooked nutritious meals, and emotional stability.",
            "Commuting from home saves substantial room-and-board expenses, reducing the overall financial burden of higher education.",
            "Living at home provides a quiet, distraction-free study environment away from noisy dormitory environments.",
            "Dayscholars maintain strong family bonds and local community connections throughout their college degree.",
        ],
        "pro_arguments": [
            "Living in a college hostel fosters independence, self-reliance, and essential life management skills away from parental supervision.",
            "Hostel residence provides 24/7 access to campus libraries, research laboratories, study groups, and peer academic collaboration.",
            "Campus hostel life immerses students in rich extracurricular activities, leadership opportunities, and lifelong professional networking.",
            "Eliminating long daily commutes saves hours of travel time that can be redirected toward academic studies and adequate sleep.",
            "Hostel living exposes students to diverse cultural backgrounds, developing interpersonal empathy and adaptability.",
            "Peer study environments in hostels encourage spontaneous academic discussion and group problem-solving before exams.",
            "Living on campus allows full participation in evening sports, cultural events, workshops, and student organizational meetings.",
            "Managing personal budgets, laundry, and daily schedules in a hostel prepares students for independent adult life.",
            "Hostel residents develop strong bonds of camaraderie and peer support networks that last throughout their professional careers.",
            "On-campus living eliminates commute-related stress, traffic delays, and transportation hazards during exam seasons.",
            "Hostel environments offer quick access to faculty office hours, academic tutoring, and campus mentoring resources.",
            "Living with peers encourages collaborative project work and peer-to-peer skill sharing in technical disciplines.",
            "Campus residence facilities provide structured access to gymnasiums, sports fields, and campus wellness centers.",
            "Hostel life teaches conflict resolution and shared responsibility through shared living spaces with roommates.",
            "Students living on campus report higher involvement in undergraduate research projects and campus initiatives.",
            "Hostel residence removes geographic barriers for students attending prestigious universities far from their hometowns.",
            "Late-night study sessions in hostel common rooms foster intensive exam preparation and academic discipline.",
            "Living on campus allows students to utilize specialized high-speed university network infrastructure for research.",
            "Hostel governance committees provide hands-on experience in leadership, budgeting, and event management.",
            "Immersive campus living creates memorable university experiences and deep institutional connection.",
        ],
        "con_arguments": [
            "Dayscholars enjoy a supportive home environment with home-cooked nutritious meals, emotional stability, and family comfort.",
            "Commuting from home saves substantial room-and-board expenses, reducing the overall financial burden of higher education.",
            "Living at home eliminates common hostel drawbacks like noisy dormitories, lack of privacy, and unsatisfactory mess food.",
            "Dayscholars maintain strong family bonds, moral support systems, and local community connections throughout their degree.",
            "Quiet home study environments provide distraction-free spaces for focused academic reading and exam preparation.",
            "Living at home avoids exposure to negative peer pressure, late-night distractions, and dormitory politics.",
            "Day commuting allows students to stay connected with hometown mentors, local internships, and part-time jobs.",
            "Home living offers personalized health care, hygiene, and parental guidance during stressful academic periods.",
            "Saving hostel fee expenditures allows families to invest in supplementary online certifications and learning resources.",
            "Commuting daily teaches time management, navigation skills, and real-world urban routine discipline.",
            "Dayscholars experience less homesickness and emotional strain during the transition to university education.",
            "Home environments allow students to maintain personal hobbies, pets, and quiet personal routines without roommate friction.",
            "Living at home protects students from poor hygiene conditions and infectious illnesses common in crowded hostels.",
            "Dayscholars can balance academic responsibilities with family commitments and domestic contributions.",
            "Home living provides reliable, high-speed private internet and personal study desks tailored to individual comfort.",
            "Avoiding hostel mess food reduces gastrointestinal health issues and ensures balanced nutritional intake.",
            "Dayscholars develop strong boundaries separating academic campus life from relaxing home environments.",
            "Living at home avoids mandatory hostel curfews and restrictive dormitory regulations.",
            "Students commuting from home can maintain long-standing friendships in their local neighborhood.",
            "Day scholarship offers a stable, familiar environment ideal for students who thrive under structured routine.",
        ],
        "pro_rebuttals": {
            "cost": "Scholarships and financial aid options often subsidize hostel fees, making immersive campus living accessible.",
            "food": "Modern campus hostels offer diverse food courts and managed catering standards to ensure proper nutrition.",
        },
        "con_rebuttals": {
            "cost": "Saving thousands of dollars annually on hostel fees significantly reduces student loan debt upon graduation.",
            "food": "Home-cooked food provides superior nutritional balance and hygiene compared to large-scale institutional mess catering.",
        },
    },
    "dex": {
        "pro_facts": [
            "Samsung DeX transforms flagship smartphones into portable desktop environments by connecting to external monitors and peripherals.",
            "DeX eliminates the need to carry separate laptops by centralizing file storage, cellular connectivity, and processing power in one device.",
            "Modern DeX interfaces support multi-window desktop workflows, full keyboard-and-mouse navigation, and mobile productivity suites.",
            "Carrying a single DeX-compatible phone reduces travel luggage weight, device management overhead, and charging cable clutter.",
        ],
        "con_facts": [
            "Travel laptops feature full x86 desktop operating systems that run complex native software without mobile app limitations.",
            "Samsung DeX requires external displays, HDMI dongles, and power sources, making desktop setups inconvenient on planes and trains.",
            "Heavy DeX desktop usage drains smartphone battery rapidly and can cause device thermal throttling under intense workloads.",
            "Laptops offer integrated keyboards, trackpads, and larger high-resolution displays designed for standalone mobile productivity.",
        ],
        "pro_arguments": [
            "Samsung DeX delivers a lightweight, unified desktop environment powered directly by your smartphone, eliminating the need for a secondary laptop.",
            "Centralizing all work files, messaging, and applications on one DeX-enabled smartphone simplifies data security and device synchronization during travel.",
            "DeX allows travelers to connect to hotel TVs and external displays, creating high-resolution desktop workstations on demand.",
            "Using Samsung DeX significantly reduces travel bag weight and eliminates carrying heavy laptop power bricks through airport security.",
            "DeX leverages 5G cellular connectivity built into the phone, providing uninterrupted internet access without relying on risky public Wi-Fi hotspots.",
            "Modern mobile productivity suites in DeX support full multi-window multitasking, drag-and-drop file management, and desktop-class web browsing.",
            "Consolidation into a single DeX smartphone lowers overall hardware expenditure by removing separate laptop purchase and replacement cycles.",
            "DeX features dedicated Samsung Knox security, protecting confidential enterprise documents on a single encrypted mobile hardware root.",
            "Wireless DeX protocols enable instant screen mirroring to smart TVs and monitors without needing physical cables or adapters.",
            "Using a phone with DeX ensures all personal settings, credentials, and app states remain identical whether working on mobile or desktop.",
            "Integrated USB-C docking hubs allow DeX users to connect external storage drives, SD card readers, and Ethernet cables seamlessly.",
            "Mobile cloud desktop clients on DeX run full Windows environments for high-end enterprise software access on the go.",
            "Smartphone camera hardware connected via DeX functions as a high-definition webcam for video conference calls.",
            "Passive cooling pads for DeX docking stations sustain peak processor performance during extended desktop productivity sessions.",
            "DeX eliminates cloud sync latency between separate mobile and desktop file structures.",
            "Single-device productivity with DeX minimizes corporate hardware management costs and e-waste generation.",
            "Modern flagship mobile processors running DeX match traditional ultra-portable laptop benchmark performance.",
            "DeX enables dual-screen productivity by allowing the phone screen to function as a touchpad or secondary display.",
            "Fast-charging power delivery ports on DeX docks keep smartphones charged while powering high-resolution 4K monitors.",
            "Samsung DeX simplifies digital nomad travel logistics by reducing core technology gear to a phone and compact dock.",
        ],
        "con_arguments": [
            "Laptops provide complete standalone productivity with integrated keyboards, precision trackpads, and displays for work anywhere without external monitors.",
            "Native laptop operating systems like Windows and macOS run specialized professional software that mobile DeX applications cannot replicate.",
            "Setting up Samsung DeX during travel requires external monitors, HDMI adapters, and peripheral power, making usage impossible on flights or in transit.",
            "Sustained DeX desktop usage leads to rapid phone battery drain and potential thermal throttling during heavy multitasking.",
            "Mobile Android apps in DeX mode often lack advanced desktop features, macro capabilities, and full browser extension support.",
            "Laptops feature superior thermal cooling and multi-core processing designed for prolonged heavy workloads like video editing or compiling.",
            "Relying solely on a smartphone for work creates a single-point failure risk where losing or damaging the phone halts all productivity.",
            "Laptop displays offer superior color accuracy, higher refresh rates, and ergonomic anti-glare screen treatments for long work sessions.",
            "Frequent plugging and unplugging of DeX display cables accelerates USB-C port wear on primary mobile devices.",
            "Laptops offer expansive physical storage capacities and high-speed thunderbolt ports for external drive connectivity.",
            "In-flight tray tables lack the physical space needed to deploy an external monitor, keyboard, mouse, and DeX dongle setup.",
            "High-end CAD software, IDEs, and local virtual machines require full x86 operating systems not supported on ARM Android DeX.",
            "Touchpad emulation on smartphones lacks the tactile precision and gesture support of dedicated laptop glass trackpads.",
            "Unplugging a DeX phone during incoming calls can interrupt active desktop sessions and unsaved application states.",
            "Laptops provide long built-in battery runtimes for 8 to 12 hours of continuous work without requiring external power outlets.",
            "Ergonomic laptop form factors allow comfortable lap usage in airport lounges, waiting rooms, and vehicles.",
            "Enterprise software licensing often restricts full feature access to desktop OS installations rather than mobile Android apps.",
            "Secondary external displays for DeX add extra weight and fragility to travel luggage, offsetting phone weight savings.",
            "Thermal heat build-up during long DeX sessions can degrade smartphone lithium-ion battery health over time.",
            "Standalone laptops allow users to maintain separation between personal smartphone communications and sensitive corporate work data.",
        ],
        "pro_rebuttals": {
            "monitors": "Modern wireless DeX and portable USB-C monitors enable lightweight, high-resolution dual-screen setups anywhere.",
            "software": "Cloud desktop services like Azure Virtual Desktop run seamlessly on DeX, providing full Windows access on mobile hardware.",
        },
        "con_rebuttals": {
            "monitors": "Laptops feature built-in displays and physical keyboards that allow immediate productivity on flights, trains, and coffee shops without extra gear.",
            "software": "Native desktop operating systems execute complex local software without relying on continuous high-speed internet connections.",
        },
    },
    "phone": {
        "pro_facts": [
            "Smartphones enable instant access to digital research libraries, academic portals, and educational collaboration apps in college classrooms.",
            "Integrating mobile technology into higher education prepares students for modern digital workplace environments.",
            "Personal mobile devices provide essential accessibility support and customized learning tools for diverse student populations.",
            "Digital classroom applications allow instructors to conduct real-time comprehension polling and distribute immediate lecture notes.",
        ],
        "con_facts": [
            "Unrestricted smartphone usage during college lectures causes cognitive distraction, impairing information retention and academic performance.",
            "Constant phone access in lecture halls facilitates real-time academic dishonesty and exam misconduct.",
            "Excessive device reliance in academic settings reduces face-to-face interpersonal communication and collaborative seminar discussion.",
            "Digital notifications during instruction disrupt classroom focus and increase cognitive fatigue among students.",
        ],
        "pro_arguments": [
            "Smartphones provide students with instantaneous access to digital research libraries, academic databases, and real-time educational tools during lectures.",
            "Integrating mobile technology into higher education prepares students for modern workforce environments where digital literacy is essential.",
            "Digital classroom tools allow instructors to run interactive polls, distribute immediate course materials, and engage students dynamically.",
            "Allowing personal devices ensures equitable access to assistive learning technologies for students with diverse learning needs.",
            "Modern educational platforms leverage mobile accessibility to foster self-directed learning and continuous academic engagement.",
            "Smartphones enable rapid group communication and seamless document sharing during in-class collaborative workshops.",
            "Digital note-taking applications on mobile devices allow students to organize, search, and annotate lecture materials efficiently.",
            "Mobile access to campus safety alerts and emergency notification systems protects student well-being across university grounds.",
            "Cloud-connected mobile applications allow students to record audio lectures and review complex academic concepts at their own pace.",
            "Treating college students as autonomous adults responsible for managing their own digital engagement promotes personal accountability.",
            "Mobile calculators and domain-specific educational software enhance problem-solving capabilities in advanced STEM coursework.",
            "Digital textbook access on smartphones significantly reduces heavy physical backpack burdens and educational material costs.",
            "E-learning integrations enable remote participation and asynchronous class contribution for working or commuting students.",
            "Mobile language translation and dictionary tools support international students in comprehending complex academic lectures.",
            "Interactive learning apps turn passive lecture listening into active, participatory educational experiences.",
            "Leveraging mobile devices for digital assignment submission streamlines grading workflows and reduces paper consumption.",
            "Campus navigation and scheduling apps on smartphones help students manage dense academic timetables and course locations.",
            "Modern pedagogical research shows that gamified mobile quizzes increase student retention of key course concepts.",
            "Allowing smartphones models real-world professional environments where individuals must balance device utility with task focus.",
            "Digital portfolio tools on mobile devices empower students to document and showcase project achievements in real time.",
        ],
        "con_arguments": [
            "Unrestricted smartphone usage during college lectures causes severe cognitive distraction, significantly impairing information retention and focus.",
            "Constant phone availability in lecture halls facilitates real-time academic dishonesty and widespread exam misconduct.",
            "Digital notifications and social media multitasking during instruction reduce deep learning and critical analytical thinking.",
            "Unrestricted device usage in academic settings erodes face-to-face interpersonal communication and vibrant seminar discussions.",
            "Screen-induced distraction in classrooms creates a secondary ripple effect, disturbing nearby peers and instructors alike.",
            "Over-reliance on mobile search shortcuts undermines the development of deep research skills and memorization capacity.",
            "Facilitating constant digital connectivity in lectures increases student anxiety, FOMO, and mental health strain.",
            "Enforcing classroom phone bans fosters an intentional environment dedicated to sustained attention and active listening.",
            "Compulsive phone checking during lectures degrades attention spans, making complex academic subjects harder to master.",
            "Socioeconomic disparities in mobile hardware quality can create subtle social divides and technological inequity among peers.",
            "Digital distractions during class reduce overall lecture attendance quality, leading to higher course failure and drop rates.",
            "Unregulated device usage disrespects teaching faculty and disrupts the professional decorum of university instruction.",
            "Cyberbullying, non-consensual recording, and privacy violations increase when smartphones are unrestricted in campus spaces.",
            "Relying on small smartphone screens for complex academic reading leads to digital eye strain and physical posture fatigue.",
            "In-class phone usage promotes superficial browsing over rigorous, sustained engagement with primary academic literature.",
            "Constant digital interruptions prevent students from entering 'flow states' necessary for mastering technical concepts.",
            "Clear boundaries against device usage help students develop self-regulation and impulse control essential for long-term career success.",
            "Loud alerts, ringtones, and vibration sounds disrupt the acoustic environment of large lecture halls.",
            "Excessive classroom phone usage harms overall campus community culture by replacing spontaneous social interaction with screen isolation.",
            "Instituting phone-free academic zones restores the traditional integrity and scholarly focus of higher education.",
        ],
        "pro_rebuttals": {
            "distraction": "Digital literacy includes mastering self-regulation; restricting technology deprives students of learning how to manage distraction professionally.",
            "cheating": "Secure digital assessment browsers and honor code protocols effectively prevent exam misconduct without needing device bans.",
        },
        "con_rebuttals": {
            "distraction": "Empirical studies consistently demonstrate that multi-tasking on smartphones during lectures reduces test scores by up to a full letter grade.",
            "cheating": "Instant messaging and hidden search tools make real-time classroom cheating virtually undetectable during live examinations.",
        },
    },
    "ro": {
        "pro_facts": [
            "RO water purifiers utilize multi-stage reverse osmosis membranes to filter out 99.9% of dissolved solids, heavy metals, and bacterial pathogens.",
            "Advanced filtration systems ensure consistent, laboratory-grade drinking water purity regardless of municipal supply contamination.",
            "Modern RO units provide high-throughput, automated purification with real-time total dissolved solids (TDS) monitoring for health safety.",
            "Reverse osmosis technology removes toxic industrial runoff, lead, arsenic, and chemical contaminants that standard clay filters cannot isolate.",
        ],
        "con_facts": [
            "Traditional clay mud pots naturally cool drinking water through evaporative cooling without drawing any electrical power.",
            "Natural unglazed clay pots leach essential minerals like calcium and magnesium back into drinking water while maintaining an optimal alkaline pH.",
            "Reverse osmosis filtration is ecologically wasteful, discarding up to three gallons of wastewater for every single gallon of purified water produced.",
            "Intense RO membrane filtration strips beneficial natural minerals from drinking water, resulting in demineralized and slightly acidic water.",
        ],
        "pro_arguments": [
            "RO water purifiers utilize multi-stage reverse osmosis membranes to filter out 99.9% of dissolved solids, heavy metals, microplastics, and waterborne pathogens.",
            "Advanced filtration systems ensure consistent, laboratory-grade drinking water purity regardless of municipal pipeline contamination or seasonal monsoon runoff.",
            "Modern RO units provide high-throughput, automated purification with real-time total dissolved solids (TDS) monitoring for health safety.",
            "Reverse osmosis technology removes toxic industrial runoff, lead, arsenic, and chemical contaminants that standard porous clay filters cannot isolate.",
            "High-capacity electric purifiers deliver reliable, continuous clean drinking water for dense urban households and commercial facilities.",
            "Integrated UV sterilizers in RO units neutralize viruses and bacteria, preventing severe gastrointestinal infections.",
            "Multi-stage carbon pre-filters eliminate unpleasant chlorine odors and volatile organic compounds from municipal tap supplies.",
            "Automated self-cleaning cycles in modern filtration units prevent internal biofilm growth and bacterial colonization.",
            "Regulated filtration standards guarantee compliant drinking water quality across diverse geographical regions.",
            "High-efficiency RO units with recovery pumps maximize clean water yield while minimizing electrical power draw.",
        ],
        "con_arguments": [
            "Traditional clay mud pots naturally cool drinking water through evaporative cooling without drawing any electrical power.",
            "Natural unglazed clay pots leach essential minerals like calcium, magnesium, and iron back into drinking water while maintaining an optimal alkaline pH.",
            "Reverse osmosis filtration is ecologically wasteful, discarding up to three gallons of wastewater for every single gallon of purified water produced.",
            "Intense RO membrane filtration strips beneficial natural minerals from drinking water, resulting in demineralized and slightly acidic water.",
            "Eco-friendly earthenware mud pots produce zero plastic waste, electronic e-waste, or recurring filter replacement costs.",
            "Porous clay surfaces naturally neutralize water acidity, enhancing digestive comfort and natural hydration.",
            "Clay pot manufacturing relies on sustainable local craft traditions and biodegradable raw materials rather than petroleum-based plastics.",
            "Traditional pot cooling operates continuously during electrical grid power outages and power cuts without requiring backup generators.",
            "Stagnant water in uncleaned RO storage tanks can harbor secondary bacterial contamination if filters are not replaced regularly.",
            "Demineralized RO water over long-term consumption has been linked by health studies to reduced dietary mineral intake.",
        ],
        "pro_rebuttals": {
            "minerals": "Modern RO purifiers feature active remineralization cartridges that restore balanced calcium and magnesium levels after filtration.",
            "waste": "New zero-waste RO systems recirculate reject water into household utility tanks for washing and cleaning.",
        },
        "con_rebuttals": {
            "minerals": "Unglazed clay pots naturally balance water pH and infuse essential trace minerals organically without synthetic chemical cartridges.",
            "waste": "Passive clay pots require zero water rejection, conserving 100% of collected tap and rainwater.",
        },
    },
    "data centre": {
        "pro_facts": [
            "AI data centers provide the indispensable computational bedrock required for scientific breakthroughs, drug discovery, and climate modeling.",
            "Abolishing data centers would cripple modern cloud infrastructure, paralyzing economic productivity and critical digital services.",
            "Modern data centers increasingly utilize 100% renewable energy contracts and advanced closed-loop liquid cooling systems.",
            "Hyperscale computing clusters enable real-time grid balancing by operating as flexible electrical loads during peak demand.",
        ],
        "con_facts": [
            "AI data centers place an intolerable burden on regional power grids, consuming gigawatt-hours that drive up electricity prices for households.",
            "Cooling massive AI server clusters consumes millions of gallons of local drinking water daily, worsening regional droughts.",
            "The rapid two-year hardware replacement cycle in AI computing generates massive volumes of non-recyclable electronic waste.",
            "Using massive energy to run climate models is a self-defeating paradox when training single models emits hundreds of tons of carbon.",
        ],
        "pro_arguments": [
            "AI data centers provide the indispensable computational bedrock required for scientific breakthroughs, drug discovery, and climate modeling.",
            "Abolishing data centers would cripple modern cloud infrastructure, paralyzing economic productivity and critical digital services.",
            "Modern data centers increasingly utilize 100% renewable energy contracts and advanced closed-loop liquid cooling systems.",
            "Hyperscale computing clusters enable real-time grid balancing by operating as flexible electrical loads during peak demand.",
            "Industry standard has shifted to dry closed-loop liquid cooling and air-to-air heat exchangers that consume zero municipal potable water.",
            "Modern facilities integrate grid-scale Battery Energy Storage Systems (BESS) and load-shedding algorithms to supply power back to the grid during regional peak surges.",
            "Hyperscale operators enforce mandatory hardware circularity programs, refurbishing and recycling over 95% of decommissioned server components.",
            "High-density compute infrastructure optimizes energy usage per floating-point operation, outperforming fragmented legacy server rooms.",
            "Local economic investments from data center operators fund clean energy grid infrastructure and municipal tax baselines.",
            "Cloud data centers centralize cybersecurity defense, protecting vital national infrastructure against global cyber threats.",
            "AI workloads enable rapid optimization of smart grid power distribution, mitigating overall national carbon emissions.",
            "Next-generation geothermal and small modular nuclear reactors are being directly financed and anchored by data center power purchase agreements.",
            "Decentralized edge computing nodes powered by micro-renewables reduce transmission line losses across power grids.",
            "Industrial waste heat capture systems from data centers are redirected to heat municipal residential district water systems.",
            "Global digital economy productivity relies directly on resilient, high-availability hyperscale data centers.",
            "Synthetic biology and material science breakthroughs driven by data center AI accelerate the transition away from fossil fuels.",
            "Advanced liquid immersion cooling technologies reduce overall cooling energy consumption by over 90% compared to legacy air systems.",
            "Regulated data center expansion incentivizes utility providers to modernize aging electrical transmission lines.",
            "Automated energy management software inside hyperscale clusters minimizes idle power consumption during low-traffic hours.",
            "Consolidation into green data centers eliminates inefficient, high-emission on-premise enterprise server rooms.",
        ],
        "con_arguments": [
            "AI data centers place an intolerable burden on regional power grids, consuming gigawatt-hours that drive up electricity prices for households.",
            "Cooling massive AI server clusters consumes millions of gallons of local drinking water daily, worsening regional droughts.",
            "The rapid two-year hardware replacement cycle in AI computing generates massive volumes of non-recyclable electronic waste.",
            "Using massive energy to run climate models is a self-defeating paradox when training single models emits hundreds of tons of carbon.",
            "Evaporative cooling towers in arid regions continue to abstract millions of gallons of potable water daily, directly competing with local municipal supplies.",
            "Unrestricted grid demand from hyperscale facilities forces regional utilities to fire up fossil-fueled peaker plants during peak hours, driving up household power rates.",
            "The relentless two-year hardware replacement cycle in AI facilities creates massive volumes of non-recyclable electronic waste containing hazardous heavy metals.",
            "Grid congestion caused by computing clusters diverts clean energy capacity away from residential decarbonization goals.",
            "Thermal pollution discharged from once-through cooling systems disrupts local aquatic ecosystems and biodiversity.",
            "Hyperscale data centers generate noise pollution from industrial cooling fans, impacting neighboring residential communities.",
            "Land consumption for sprawling server farms encroaches on agricultural land and natural wildlife habitats.",
            "Concentration of data centers in specific regions strains localized water tables and groundwater aquifers beyond sustainable limits.",
            "Backup diesel generators at data center sites emit particulate matter and nitrogen oxides during grid outages and routine testing.",
            "The carbon footprint of silicon manufacturing and chip fabrication for AI accelerators negates operational efficiency gains.",
            "Water stress index metrics indicate that over 20% of global data center capacity draws directly from high-water-stress watersheds.",
            "Long-term utility contracts lock local communities into subsidizing grid infrastructure buildouts for private tech firms.",
            "E-waste processing export to developing nations creates severe environmental justice and public health hazards.",
            "Skyrocketing power requirements for AI clusters delay the retirement of legacy coal-fired power stations.",
            "Resource extraction for rare earth elements used in high-performance server GPUs causes severe ecological destruction.",
            "Centralized data center hubs create vulnerable single-point failure targets for physical grid disruption and climate disasters.",
        ],
        "pro_rebuttals": {
            "water": "Industry standard has shifted to dry closed-loop liquid cooling and air-to-air heat exchangers that consume zero municipal potable water.",
            "grid": "Modern facilities integrate grid-scale Battery Energy Storage Systems (BESS) and load-shedding algorithms to supply power back to the grid during regional peak surges.",
            "waste": "Hyperscale operators enforce mandatory hardware circularity programs, refurbishing and recycling over 95% of decommissioned server components.",
        },
        "con_rebuttals": {
            "water": "Evaporative cooling towers in arid regions continue to abstract millions of gallons of potable water daily, directly competing with local municipal supplies.",
            "grid": "Unrestricted grid demand from hyperscale facilities forces regional utilities to fire up fossil-fueled peaker plants during peak hours, driving up household power rates.",
            "waste": "The relentless two-year hardware replacement cycle in AI facilities creates massive volumes of non-recyclable electronic waste containing hazardous heavy metals.",
        },
    },
    "exam": {
        "pro_facts": [
            "Standardized exams provide a uniform, objective benchmark for evaluating academic proficiency across diverse schools.",
            "Standardized testing data enables educational authorities to identify systemic achievement gaps and allocate funding to under-resourced schools.",
            "Objective exam scores protect students from subjective grading bias and teacher favoritism.",
            "National exams incentivize rigorous curriculum adherence and foundational subject mastery.",
        ],
        "con_facts": [
            "Standardized exams measure test-taking strategy and socioeconomic privilege rather than genuine intelligence or creativity.",
            "High-stakes testing causes severe psychological anxiety, burnout, and depression among students.",
            "Teaching to the test narrows educational curricula, eliminating arts, humanities, and critical inquiry.",
            "Standardized test scores correlate strongly with family household income rather than individual student effort.",
        ],
        "pro_arguments": [
            "Standardized exams provide a uniform, objective benchmark for evaluating academic proficiency across diverse schools.",
            "Standardized testing data enables educational authorities to identify systemic achievement gaps and allocate funding to under-resourced schools.",
            "Objective exam scores protect students from subjective grading bias and teacher favoritism.",
            "National exams incentivize rigorous curriculum adherence and foundational subject mastery.",
            "Standardized assessment metrics allow universities to compare applicants fairly across varying high school grading standards.",
            "Longitudinal testing data helps educators identify learning loss early and implement targeted remedial interventions.",
            "Structured exams prepare students for professional licensure and credentialing requirements in medicine, law, and engineering.",
            "Standardized tests provide actionable diagnostic data to evaluate teacher efficacy and institutional performance.",
            "Unbiased standardized testing creates opportunities for high-achieving students from low-income backgrounds to demonstrate merit.",
            "Consistent exam benchmarks maintain international academic competitiveness in STEM disciplines.",
        ],
        "con_arguments": [
            "Standardized exams measure test-taking strategy and socioeconomic privilege rather than genuine intelligence or creativity.",
            "High-stakes testing causes severe psychological anxiety, burnout, and depression among students.",
            "Teaching to the test narrows educational curricula, eliminating arts, humanities, and critical inquiry.",
            "Standardized test scores correlate strongly with family household income rather than individual student effort.",
            "Single-day high-stakes testing fails to measure long-term critical thinking, problem-solving, or emotional intelligence.",
            "Commercial test preparation courses create unfair advantages for wealthy families who can afford expensive tutoring.",
            "Over-reliance on test scores incentivizes school districts to manipulate student enrollment and attendance metrics.",
            "Cultural and linguistic biases embedded in exam questions disadvantage non-native English speakers and minority students.",
            "Test-centric schooling fosters a fixed mindset and reduces intrinsic motivation for lifelong learning.",
            "Holistic admissions portfolios offer a far more comprehensive and accurate prediction of post-secondary success.",
        ],
        "pro_rebuttals": {
            "bias": "Standardized tests replace subjective teacher bias with impartial, blind-graded evaluation criteria.",
            "anxiety": "Properly paced formative assessments build resilience and familiarize students with realistic evaluation environments.",
        },
        "con_rebuttals": {
            "bias": "Test questions frequently incorporate subtle socioeconomic assumptions that privilege affluent demographics.",
            "anxiety": "High-stakes single-day testing creates excessive stress that impairs memory retrieval and performance accuracy.",
        },
    },
    "ai regulation": {
        "pro_facts": [
            "Comprehensive AI regulation establishes guardrails against algorithmic discrimination, deepfakes, and privacy violations.",
            "Mandatory AI safety audits prevent the deployment of autonomous systems with catastrophic failure modes.",
            "Legal regulatory frameworks foster public trust, accelerating responsible AI adoption across critical industries.",
            "Standardized safety compliance prevents predatory data harvesting and unauthorized copyrighted training.",
        ],
        "con_facts": [
            "Excessive AI regulation creates legal monopolies for tech incumbents while crushing open-source innovation and startups.",
            "Preemptive regulatory hurdles slow down technological progress and delay life-saving medical AI applications.",
            "Over-regulating domestic AI developments drives top engineering talent and capital to offshore jurisdictions.",
            "Rigid regulatory policies become quickly obsolete when faced with rapid artificial intelligence advancements.",
        ],
        "pro_arguments": [
            "Comprehensive AI regulation establishes guardrails against algorithmic discrimination, deepfakes, and privacy violations.",
            "Mandatory AI safety audits prevent the deployment of autonomous systems with catastrophic failure modes.",
            "Legal regulatory frameworks foster public trust, accelerating responsible AI adoption across critical industries.",
            "Standardized safety compliance prevents predatory data harvesting and unauthorized copyrighted training.",
            "Tiered regulatory frameworks exempt open-source startups while targeting oversight strictly at frontier models.",
            "Clear, stable safety regulations reduce legal uncertainty, unlocking institutional capital for vetted AI ventures.",
            "International safety agreements ensure global compliance, preventing rogue actors while maintaining high standards.",
            "Regulation focuses strictly on technical safety, data privacy, and systemic risk rather than dictating speech.",
        ],
        "con_arguments": [
            "Excessive AI regulation creates legal monopolies for tech incumbents while crushing open-source innovation and startups.",
            "Preemptive regulatory hurdles slow down technological progress and delay life-saving medical AI applications.",
            "Over-regulating domestic AI developments drives top engineering talent and capital to offshore jurisdictions.",
            "Rigid regulatory policies become quickly obsolete when faced with rapid artificial intelligence advancements.",
            "Even tiered regulations create massive compliance paperwork that favors incumbent tech giants with legal teams.",
            "Preemptive restrictions force innovative startups to delay deployment while waiting for slow approvals.",
            "Strict domestic laws simply drive top engineering talent and venture capital to less restrictive jurisdictions.",
        ],
        "pro_rebuttals": {
            "monopoly": "Tiered regulatory frameworks exempt open-source startups and individual researchers, targeting oversight strictly at mega-scale frontier models.",
            "innovation": "Clear, stable safety regulations reduce legal uncertainty, unlocking trillions in institutional capital for vetted AI ventures.",
            "security": "International safety agreements ensure global compliance, preventing rogue actors while maintaining high technical standards.",
        },
        "con_rebuttals": {
            "monopoly": "Even tiered regulations create massive compliance paperwork that favors incumbent tech giants with established legal teams.",
            "innovation": "Preemptive restrictions force innovative startups to delay deployment while waiting for slow bureaucratic approvals.",
            "offshore": "Strict domestic laws simply drive top engineering talent and venture capital to less restrictive international jurisdictions.",
        },
    },
}


def _match_prepackaged_key(topic: str) -> str | None:
    """Find matching key in PREPACKAGED_KNOWLEDGE if topic contains exact domain terms."""
    topic_lower = topic.lower()

    if any(w in topic_lower for w in ["hostel", "hosteller", "dayscholar", "day scholar"]):
        return "hostel"
    if any(w in topic_lower for w in ["samsung dex", "dex station"]):
        return "dex"
    if any(w in topic_lower for w in ["phone in class", "smartphone in college", "use phones at college"]):
        return "phone"
    if any(w in topic_lower for w in ["ro machine", "ro water", "mud pot", "earthen pot", "clay pot", "water purifier"]) or re.search(r"\b(ro|r\.o\.)\b", topic_lower):
        return "ro"
    if any(w in topic_lower for w in ["data centre", "data center", "hyperscale compute"]):
        return "data centre"
    if re.search(r"\b(ai regulation|regulate ai|regulating ai)\b", topic_lower):
        return "ai regulation"
    if re.search(r"\b(exam|standardized test|standardized testing)\b", topic_lower):
        return "exam"

    return None


def _extract_natural_subjects(topic: str) -> tuple[str, str]:
    """Extract natural, grammatically fluent Proposer & Opponent subject phrases from any debate topic."""
    t_lower = topic.lower().strip()

                                  
    if any(w in t_lower for w in ["hostel", "hosteller", "dayscholar", "day scholar"]):
        return "campus hostel residency", "commuting as a day scholar"
    if "samsung dex" in t_lower:
        return "Samsung DeX desktop environments", "traditional travel laptops"
    if any(w in t_lower for w in ["phone in class", "smartphone in college"]):
        return "smartphone access in academic environments", "unrestricted device usage during instruction"
    if any(k in t_lower for k in ["ro machine", "ro water", "mud pot", "earthen pot", "clay pot", "water purifier"]) or re.search(r"\b(ro|r\.o\.)\b", t_lower):
        return "multi-stage RO water purification", "traditional earthenware clay pots"

                                             
    for sep in [" vs ", " v ", " or ", " versus "]:
        if sep in t_lower:
            parts = re.split(re.escape(sep), t_lower, flags=re.IGNORECASE)
            sub_a = _clean_phrase(parts[0])
            sub_b = _clean_phrase(parts[1]) if len(parts) > 1 else "traditional alternatives"
            return sub_a, sub_b

    cleaned = _clean_phrase(t_lower)
    return cleaned, f"unrestricted adoption of {cleaned}"


def _clean_phrase(phrase: str) -> str:
    """Clean grammatical question prefixes and filler verbs while preserving subject nouns."""
    p = phrase.strip()
    p = re.sub(r"^(should|is|are|do|does|why|how|whether|can|could|would|shall)\s+", "", p, flags=re.IGNORECASE)
    p = re.sub(r"^(students|college students|people|countries|india|we|you)\s+(should|must|can|need|want|rely\s+on|use|get|adopt|choose|prefer)?\s*", "", p, flags=re.IGNORECASE)
    p = re.sub(r"^(rely\s+on|get|adopt|buy|use|choose|prefer|opt\s+for)\s+", "", p, flags=re.IGNORECASE)
    p = re.sub(r"^(a|an|the)\s+", "", p, flags=re.IGNORECASE)
    p = " ".join(p.split()).strip(" ?.")

                                
    if "samsung dex" in p.lower():
        p = re.sub(r"\bsamsung dex\b", "Samsung DeX", p, flags=re.IGNORECASE)

    return p if p else phrase.strip()


def get_topic_grounded_facts(topic: str) -> list[FactRecord]:
    """Generate rich, highly concrete FactRecord objects for a debate topic."""
    matched_key = _match_prepackaged_key(topic)
    records: list[FactRecord] = []

    if matched_key:
        pkg = PREPACKAGED_KNOWLEDGE[matched_key]
        clean_atom = "".join(w.capitalize() for w in matched_key.split() if w.isalnum())[:12]
        for i, text in enumerate(pkg["pro_facts"]):
            prop = f"{clean_atom}Benefit{i+1} → OutcomesPositive"
            records.append(FactRecord(
                text=text,
                propositional=prop,
                clause=parse_propositional_form(prop),
                relationship="supports_proposition",
            ))
        for i, text in enumerate(pkg["con_facts"]):
            prop = f"{clean_atom}Risk{i+1} → OperationalStress"
            records.append(FactRecord(
                text=text,
                propositional=prop,
                clause=parse_propositional_form(prop),
                relationship="contradicts_proposition",
            ))
        return records

    side_a, side_b = _extract_natural_subjects(topic)
    clean_atom = "".join(w.capitalize() for w in side_a.split() if w.isalnum())[:12] or "Topic"

    pro_fact_texts = [
        f"Integrating {side_a} provides structured operational benefits and enhanced performance.",
        f"Empirical evidence demonstrates that {side_a} optimizes productivity and quality standards.",
        f"Consistent deployment of {side_a} enables reliable monitoring and safety compliance.",
        f"Structured implementation of {side_a} mitigates long-term operational risks.",
    ]

    con_fact_texts = [
        f"Decentralized alternatives like {side_b} operate with lower resource overhead and zero complex dependencies.",
        f"Over-reliance on {side_a} introduces substantial maintenance expenditure and administrative friction.",
        f"Systemic evaluations indicate that {side_a} can create single-point operational vulnerabilities.",
        f"Traditional approaches like {side_b} preserve flexibility without heavy management overhead.",
    ]

    for i, text in enumerate(pro_fact_texts):
        prop = f"{clean_atom}Advantage{i+1} → PositiveOutcome"
        records.append(FactRecord(
            text=text,
            propositional=prop,
            clause=parse_propositional_form(prop),
            relationship="supports_proposition",
        ))

    for i, text in enumerate(con_fact_texts):
        prop = f"{clean_atom}Drawback{i+1} → SystemicRisk"
        records.append(FactRecord(
            text=text,
            propositional=prop,
            clause=parse_propositional_form(prop),
            relationship="contradicts_proposition",
        ))

    return records


def get_topic_proposer_points(topic: str, spoken_claims: set[str] | None = None) -> list[str]:
    """Return Proposer argument points."""
    spoken = {s.strip().lower() for s in (spoken_claims or set())}
    matched_key = _match_prepackaged_key(topic)

    if matched_key:
        pool = PREPACKAGED_KNOWLEDGE[matched_key]["pro_arguments"]
    else:
        pool = _generate_dynamic_proposer_pool(topic)

    filtered = [p for p in pool if p.strip().lower() not in spoken]
    return filtered if filtered else pool


def get_topic_opponent_points(topic: str, spoken_claims: set[str] | None = None) -> list[str]:
    """Return Opponent argument points."""
    spoken = {s.strip().lower() for s in (spoken_claims or set())}
    matched_key = _match_prepackaged_key(topic)

    if matched_key:
        pool = PREPACKAGED_KNOWLEDGE[matched_key]["con_arguments"]
    else:
        pool = _generate_dynamic_opponent_pool(topic)

    filtered = [p for p in pool if p.strip().lower() not in spoken]
    return filtered if filtered else pool


def get_targeted_rebuttal(topic: str, opponent_claim: str, role: str, spoken_claims: set[str] | None = None) -> str | None:
    """Lookup direct counter-rebuttal targeted specifically to opponent_claim."""
    if not opponent_claim:
        return None

    spoken = {s.strip().lower() for s in (spoken_claims or set())}
    matched_key = _match_prepackaged_key(topic)
    claim_lower = opponent_claim.lower()

    if matched_key:
        role_key = "pro_rebuttals" if role == "proposer" else "con_rebuttals"
        if role_key in PREPACKAGED_KNOWLEDGE[matched_key]:
            rebuttals = PREPACKAGED_KNOWLEDGE[matched_key][role_key]
            for kw, reply in rebuttals.items():
                if kw in claim_lower and reply.strip().lower() not in spoken:
                    return reply

    return None


def _generate_dynamic_proposer_pool(topic: str) -> list[str]:
    """Universal safety-net fallback for Proposer arguments without administrative boilerplate."""
    side_a, side_b = _extract_natural_subjects(topic)

    return [
        f"{side_a.capitalize()} provides a structured framework that enhances overall operational efficiency.",
        f"Empirical evidence demonstrates that prioritizing {side_a} fosters long-term innovation.",
        f"Promoting {side_a} establishes clear, verifiable quality benchmarks across diverse environments.",
        f"Adopting {side_a} enables teams to identify operational bottlenecks early and allocate resources effectively.",
        f"Systematic integration of {side_a} mitigates systemic risks while maximizing long-term performance.",
        f"Encouraging {side_a} promotes sustainable practices aligned with modern industry standards.",
        f"Structured evaluation of {side_a} ensures consistent quality control and transparency.",
        f"Integrating {side_a} supports operational resilience, allowing systems to adapt effectively to changing conditions.",
        f"Advocating for {side_a} empowers stakeholders with transparent data, fostering trust and clarity.",
        f"Investment in {side_a} yields cumulative long-term benefits for organizational growth.",
        f"Standardized guidelines for {side_a} reduce subjective biases and improve decision accuracy.",
        f"Periodic review of {side_a} ensures continuous improvement and prevents structural stagnation.",
        f"A clear strategic policy regarding {side_a} clarifies responsibilities and drives focused execution.",
        f"Promoting {side_a} aligns internal incentives with benchmarked best practices.",
        f"Proactive management of {side_a} reduces unexpected disruptions and emergency overhead.",
        f"Widespread adoption of {side_a} creates a shared baseline for quality and safety.",
        f"Fostering {side_a} encourages skill building, innovation, and ongoing professional development.",
        f"Establishing robust protocols for {side_a} protects institutional integrity against volatility.",
        f"Transparent governance surrounding {side_a} facilitates seamless collaboration.",
        f"Prioritizing {side_a} builds a resilient foundation for long-term competitiveness.",
    ]


def _generate_dynamic_opponent_pool(topic: str) -> list[str]:
    """Universal safety-net fallback for Opponent arguments without administrative boilerplate."""
    side_a, side_b = _extract_natural_subjects(topic)

    return [
        f"{side_b.capitalize()} provides a cost-effective, sustainable alternative to {side_a}.",
        f"Critical analysis shows that heavy reliance on {side_a} introduces unnecessary operational complexity.",
        f"Adopting {side_b} preserves flexibility and reduces long-term maintenance overhead.",
        f"High upfront implementation costs for {side_a} create financial strain compared to {side_b}.",
        f"Systemic risks associated with {side_a} can lead to operational vulnerabilities.",
        f"Unintended consequences of prioritizing {side_a} include resource inefficiency and management friction.",
        f"Traditional approaches like {side_b} offer proven reliability without requiring complex infrastructure.",
        f"Over-indexing on {side_a} diverts capital and focus away from foundational priorities.",
        f"Disparities in access make {side_a} structurally less equitable than decentralized solutions like {side_b}.",
        f"Empirical studies indicate that {side_b} achieves comparable results with significantly lower overhead.",
        f"Rigid requirements for {side_a} reduce organizational agility during unexpected environmental shifts.",
        f"Over-reliance on {side_a} creates long-term vendor and supplier dependency risks.",
        f"Alternative strategies centered on {side_b} minimize administrative burnout and compliance stress.",
        f"Premature adoption of {side_a} risks locking systems into rigid frameworks before technology matures.",
        f"Simplifying operational workflows with {side_b} improves user satisfaction and localized control.",
        f"Resource allocation toward {side_a} yields diminishing returns after initial deployment.",
        f"Operational friction in managing {side_a} can disrupt primary core objectives.",
        f"Decentralized methods using {side_b} eliminate complex centralized failure risks.",
        f"Long-term lifecycle costs for {side_a} often exceed initial projected benefits.",
        f"Streamlined solutions like {side_b} maintain continuous stability with minimal ongoing overhead.",
    ]


def clean_claim_text(text: str) -> str:
    """
    Strips out LLM introductory meta-text prefixes, conversational framing, and surrounding quotes.
    Ensures that only the direct, substantive counter or claim point is returned.
    """
    if not text:
        return ""

    s = text.strip()

                                               
    meta_patterns = [
        r"^(the|a)\s+(generated|proposed|final|selected)\s+(claim|response|answer|rebuttal|argument|point)\s+(is|says|states)?:?\s*",
        r"^here\s+is\s+the\s+(claim|response|rebuttal|argument|point):?\s*",
        r"^this\s+response\s+is\s+a\s+continuation[^\n]*\n*",
        r"^as\s+the\s+(proposer|opponent|agent\s+[ab]):?\s*",
        r"^agent\s+[ab]:?\s*",
        r"^claim:?\s*",
        r"^rebuttal:?\s*",
    ]

    for pat in meta_patterns:
        s = re.sub(pat, "", s, flags=re.IGNORECASE | re.MULTILINE).strip()

                                         
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

                                                                       
    for pat in meta_patterns:
        s = re.sub(pat, "", s, flags=re.IGNORECASE | re.MULTILINE).strip()

    return s
