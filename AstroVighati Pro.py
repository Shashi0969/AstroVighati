# GUI Version-2.3
"""
AstroVighati Pro: An Advanced Vedic Astrology Toolkit

Version: 2.3 (Final UI Polish)
Author: Shashi (Synthesized from Kartik Srivastava's original work)

Description:
This application represents the definitive fusion of two powerful designs. It combines the robust,
object-oriented, multi-tab architecture of the first version with the modern, aesthetically
pleasing, and user-friendly interface design of the second version. The result is a
professional-grade toolkit for Vedic astrology that is both highly functional and visually elegant.

This unified script is thoroughly documented to serve as both a powerful tool and a clear,
descriptive example of advanced Tkinter application development.

Key Features:
- Vighati Rectifier: A sophisticated tool with a compact grid layout for inputs, a configurable
  search range, a quick-reference Nakshatra table, quick-set time buttons ("Now", "Noon"),
  and a resizable, tabbed results view.
- Nakshatra Explorer: A powerful browser for the 27 Nakshatras with detailed data,
  search functionality, and filtering by Lord, Gana, or Guna.
- Planetary Guide: A comprehensive reference guide for the 9 Navagrahas (Vedic planets),
  with greatly expanded details on their qualities, symbolism, and influences.
- Vedic Time Utility: A handy converter for standard time to traditional Vedic time units.
- Advanced Theme Manager: Allows users to customize the application's appearance. The theme
  choice is now saved and loaded automatically on startup.
- Professional & Descriptive Codebase: Built with a clean, object-oriented structure and
  meticulously documented to be self-explanatory and easy to maintain or extend.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import textwrap

#===================================================================================================
# ASTROLOGICAL DATA STORE
# This centralized class acts as the single source of truth for all astrological data,
# keeping it separate from the UI logic for cleaner code and easier updates.
#===================================================================================================
class AstrologicalData:
    """
    A comprehensive data store for all astrological entities like Nakshatras and Planets.
    By centralizing data here, we ensure consistency across the application and simplify
    the process of updating or expanding the astrological information.
    """
    @staticmethod
    def get_all_nakshatras():
        """
        Returns a list of dictionaries, where each dictionary contains exhaustive details
        about one of the 27 Nakshatras. This is the primary source of Nakshatra data for the app.

        :return: A list of 27 dictionaries, each representing a Nakshatra.
        :rtype: list
        """
        nakshatra_list = [
            {
                "name": "1. Ashwini", "lord": "Ketu", "remainder": "1", "deity": "Ashwini Kumaras",
                "guna": "Sattva", "gana": "Deva", "dosha": "Vata", "animal": "Male Horse", "motivation": "Dharma",
                "keywords": "Swift, Healing, Pioneering, Spontaneous, Energetic",
                "mythology": "Ruled by the divine twin horsemen, the Ashwini Kumaras, who are physicians to the gods. They represent speed, healing, and the dawn, bringing light and new beginnings.",
                "strengths": "Energetic, pioneering spirit, quick to act, intelligent, natural healers, youthful appearance.",
                "weaknesses": "Impulsive, impatient, can start projects but not finish them, prone to aggression.",
                "favorable": "Starting new ventures, healing, learning, travel, physical activities.",
                "unfavorable": "Marriage, activities requiring patience, endings."
            },
            {
                "name": "2. Bharani", "lord": "Venus", "remainder": "2", "deity": "Yama",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Pitta", "animal": "Male Elephant", "motivation": "Artha",
                "keywords": "Bearer, Transformative, Creative, Extreme",
                "mythology": "Ruled by Yama, the god of death and discipline. This Nakshatra represents the cycle of birth, death, and rebirth. It carries the creative potential of the womb and the finality of the tomb.",
                "strengths": "Strong-willed, creative, loyal to loved ones, able to endure great transformations.",
                "weaknesses": "Can be jealous, resentful, struggles with patience, prone to extreme views.",
                "favorable": "Creative projects, endings, activities requiring discipline, fertility rites.",
                "unfavorable": "Travel, beginnings, activities requiring gentleness."
            },
            {
                "name": "3. Krittika", "lord": "Sun", "remainder": "3", "deity": "Agni",
                "guna": "Rajas", "gana": "Rakshasa", "dosha": "Kapha", "animal": "Female Sheep", "motivation": "Kama",
                "keywords": "The Cutter, Purifying, Sharp, Protective",
                "mythology": "Ruled by Agni, the god of fire. It is symbolized by a sharp razor or knife, representing the power to cut through negativity and purify. It is the celestial army's commander.",
                "strengths": "Ambitious, determined, sharp intellect, protective of others, self-motivated.",
                "weaknesses": "Sharp tongue, stubborn, aggressive, impatient, can be overly critical.",
                "favorable": "Leadership roles, debates, purification ceremonies, starting military or competitive ventures.",
                "unfavorable": "Social events, diplomacy, relaxation."
            },
            {
                "name": "4. Rohini", "lord": "Moon", "remainder": "4", "deity": "Brahma",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Kapha", "animal": "Male Serpent", "motivation": "Moksha",
                "keywords": "The Beloved, Fertile, Growing, Charming",
                "mythology": "The Moon's favorite wife, known for her beauty and charm. This Nakshatra is a place of immense growth, fertility, and creativity, ruled by Brahma, the creator himself.",
                "strengths": "Charming, attractive, creative, stable, loving, good with arts and business.",
                "weaknesses": "Materialistic, jealous, possessive, gets swayed by luxury.",
                "favorable": "Gardening, starting any project, marriage, romance, trade.",
                "unfavorable": "Destructive activities, endings."
            },
            {
                "name": "5. Mrigashira", "lord": "Mars", "remainder": "5", "deity": "Soma",
                "guna": "Tamas", "gana": "Deva", "dosha": "Pitta", "animal": "Female Serpent", "motivation": "Moksha",
                "keywords": "The Searcher, Curious, Restless, Gentle",
                "mythology": "Represents the 'deer's head,' symbolizing a constant search. Like a deer, natives are gentle, sensitive, and always seeking new experiences and knowledge.",
                "strengths": "Curious, intelligent, creative, enthusiastic, gentle-natured.",
                "weaknesses": "Restless, fickle-minded, can be indecisive, lacks commitment.",
                "favorable": "Travel, research, spiritual seeking, light-hearted social events.",
                "unfavorable": "Harsh actions, long-term commitments."
            },
            {
                "name": "6. Ardra", "lord": "Rahu", "remainder": "6", "deity": "Rudra",
                "guna": "Tamas", "gana": "Manushya", "dosha": "Vata", "animal": "Female Dog", "motivation": "Kama",
                "keywords": "The Moist One, Intense, Transformative",
                "mythology": "Symbolized by a teardrop, representing the storms of Rudra (a form of Shiva) that cleanse the old to make way for the new. It brings intense emotional transformations.",
                "strengths": "Deep thinker, researcher, insightful, can handle turmoil well.",
                "weaknesses": "Can be destructive, critical, seems ungrateful, causes pain to others.",
                "favorable": "Demolition, research, dealing with difficult situations, breaking old habits.",
                "unfavorable": "Beginnings, marriage, travel."
            },
            {
                "name": "7. Punarvasu", "lord": "Jupiter", "remainder": "7", "deity": "Aditi",
                "guna": "Sattva", "gana": "Deva", "dosha": "Vata", "animal": "Female Cat", "motivation": "Artha",
                "keywords": "The Returner, Hopeful, Nurturing",
                "mythology": "Ruled by Aditi, the mother of the gods. It symbolizes the 'return of the light,' bringing hope, renewal, and nourishment. It represents a safe return home.",
                "strengths": "Kind, philosophical, spiritual, nurturing, simple living.",
                "weaknesses": "Can be fickle, indecisive, overly simplistic.",
                "favorable": "Second chances, education, spiritual activities, healing, travel.",
                "unfavorable": "Activities requiring quick, decisive action."
            },
            {
                "name": "8. Pushya", "lord": "Saturn", "remainder": "8", "deity": "Brihaspati",
                "guna": "Sattva", "gana": "Deva", "dosha": "Pitta", "animal": "Male Sheep", "motivation": "Dharma",
                "keywords": "The Nourisher, Auspicious, Protective",
                "mythology": "Considered the most auspicious Nakshatra. Symbolized by a cow's udder, it represents nourishment, care, and divine blessings from Brihaspati, the guru of the gods.",
                "strengths": "Spiritual, helpful, patient, protective, wise, prosperous.",
                "weaknesses": "Can be dogmatic, arrogant due to their wisdom, possessive.",
                "favorable": "All auspicious activities, spiritual learning, helping others.",
                "unfavorable": "Marriage (said to produce a difficult marriage)."
            },
            {
                "name": "9. Ashlesha", "lord": "Mercury", "remainder": "0", "deity": "Nagas",
                "guna": "Sattva", "gana": "Rakshasa", "dosha": "Kapha", "animal": "Male Cat", "motivation": "Dharma",
                "keywords": "The Serpent, Mystical, Hypnotic, Cunning",
                "mythology": "Ruled by the Nagas (serpent deities), it symbolizes mystical power, hidden knowledge, and hypnotic charm. It represents the coiled kundalini energy.",
                "strengths": "Intuitive, perceptive, wise, good at strategy, magnetic personality.",
                "weaknesses": "Can be deceptive, cunning, secretive, has a sharp and painful bite (speech).",
                "favorable": "Occult studies, strategy, dealing with enemies, psychology.",
                "unfavorable": "Starting new ventures, business deals."
            },
            {
                "name": "10. Magha", "lord": "Ketu", "remainder": "1", "deity": "Pitrs",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Kapha", "animal": "Male Rat", "motivation": "Artha",
                "keywords": "The Mighty One, Royal, Ancestral",
                "mythology": "Represents a royal throne, connecting to ancestral lineage and power. It is ruled by the Pitrs (ancestors), giving a strong connection to tradition and authority.",
                "strengths": "Natural leader, ambitious, proud, respects tradition, generous.",
                "weaknesses": "Arrogant, can be elitist, needs constant recognition.",
                "favorable": "Ceremonies honoring ancestors, taking on leadership, historical research.",
                "unfavorable": "Servile activities, planning for the future (prefers tradition)."
            },
            {
                "name": "11. Purva Phalguni", "lord": "Venus", "remainder": "2", "deity": "Bhaga",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Pitta", "animal": "Female Rat", "motivation": "Kama",
                "keywords": "The Former Red One, Creative, Pleasure-loving",
                "mythology": "Symbolized by the front legs of a bed, it represents rest, pleasure, and creativity. Ruled by Bhaga, the god of marital bliss and wealth.",
                "strengths": "Artistic, charming, loves life's pleasures, generous, sociable.",
                "weaknesses": "Lazy, vain, impulsive spender, needs constant stimulation.",
                "favorable": "Arts, music, romance, relaxation, marriage.",
                "unfavorable": "Starting projects, intellectual pursuits."
            },
            {
                "name": "12. Uttara Phalguni", "lord": "Sun", "remainder": "3", "deity": "Aryaman",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Vata", "animal": "Male Cow", "motivation": "Moksha",
                "keywords": "The Latter Red One, Generous, Helpful",
                "mythology": "Symbolized by the back legs of a bed, it represents union and commitment. Ruled by Aryaman, the god of contracts and hospitality, it emphasizes friendship and helping others.",
                "strengths": "Helpful, kind, stable, successful, good in relationships.",
                "weaknesses": "Can be dependent on others, stubborn, critical.",
                "favorable": "Marriage, signing contracts, new beginnings, dealing with authority.",
                "unfavorable": "Endings, harsh confrontations."
            },
            {
                "name": "13. Hasta", "lord": "Moon", "remainder": "4", "deity": "Savitar",
                "guna": "Rajas", "gana": "Deva", "dosha": "Vata", "animal": "Female Buffalo", "motivation": "Moksha",
                "keywords": "The Hand, Skillful, Clever, Humorous",
                "mythology": "Symbolized by an open hand, it represents skill, craftsmanship, and the ability to manifest goals. Ruled by Savitar, it brings light, cleverness, and healing.",
                "strengths": "Skilled with hands, intelligent, witty, practical, successful.",
                "weaknesses": "Can be restless, critical, struggles with emotional control.",
                "favorable": "Crafts, arts, business, activities requiring skill and detail.",
                "unfavorable": "Activities requiring long-term planning."
            },
            {
                "name": "14. Chitra", "lord": "Mars", "remainder": "5", "deity": "Tvashtar",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Pitta", "animal": "Female Tiger", "motivation": "Kama",
                "keywords": "The Bright One, Artistic, Magical",
                "mythology": "Symbolized by a bright jewel, it represents beauty, artistry, and divine architecture. Ruled by Tvashtar, the celestial architect, it has the power to create wonderfully.",
                "strengths": "Charismatic, artistic, elegant, good conversationalist.",
                "weaknesses": "Can be self-centered, arrogant, needs to be the center of attention.",
                "favorable": "Arts, architecture, design, health and fitness pursuits.",
                "unfavorable": "Activities requiring deep emotional connection."
            },
            {
                "name": "15. Swati", "lord": "Rahu", "remainder": "6", "deity": "Vayu",
                "guna": "Tamas", "gana": "Deva", "dosha": "Kapha", "animal": "Male Buffalo", "motivation": "Artha",
                "keywords": "The Sword, Independent, Flexible",
                "mythology": "Symbolized by a young shoot swaying in the wind, it represents independence and adaptability. Ruled by Vayu, the wind god, it is restless and free-spirited.",
                "strengths": "Independent, intelligent, learns quickly, good in business, diplomatic.",
                "weaknesses": "Restless, indecisive, unable to commit, procrastinates.",
                "favorable": "Business, trade, education, social events, travel.",
                "unfavorable": "Confrontation, activities requiring stability."
            },
            {
                "name": "16. Vishakha", "lord": "Jupiter", "remainder": "7", "deity": "Indra-Agni",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Kapha", "animal": "Male Tiger", "motivation": "Dharma",
                "keywords": "The Forked Branch, Determined, Ambitious",
                "mythology": "Symbolized by a triumphal gateway, it represents achieving goals with determination. Ruled jointly by Indra (king of gods) and Agni (fire god), it gives ambition and focus.",
                "strengths": "Goal-oriented, ambitious, determined, patient, intelligent.",
                "weaknesses": "Can be aggressive, jealous, overly critical, restless.",
                "favorable": "Pursuing goals, debates, ceremonies, romance.",
                "unfavorable": "Travel, initiations."
            },
            {
                "name": "17. Anuradha", "lord": "Saturn", "remainder": "8", "deity": "Mitra",
                "guna": "Sattva", "gana": "Deva", "dosha": "Pitta", "animal": "Female Deer", "motivation": "Dharma",
                "keywords": "The Follower, Devoted, Friendly",
                "mythology": "Ruled by Mitra, the god of friendship and partnership. It represents success through cooperation, devotion, and building lasting relationships.",
                "strengths": "Loyal, friendly, successful in groups, good leader, spiritual.",
                "weaknesses": "Can be jealous, controlling, suffers from emotional turmoil.",
                "favorable": "Group activities, travel, scientific research, meditation.",
                "unfavorable": "Marriage, confrontation."
            },
            {
                "name": "18. Jyestha", "lord": "Mercury", "remainder": "0", "deity": "Indra",
                "guna": "Sattva", "gana": "Rakshasa", "dosha": "Vata", "animal": "Male Deer", "motivation": "Artha",
                "keywords": "The Eldest, Protective, Responsible",
                "mythology": "Symbolizes the 'eldest sister,' representing seniority, responsibility, and protection. Ruled by Indra, king of gods, it carries the burden and glory of power.",
                "strengths": "Responsible, protective, wise, takes charge, good in crisis.",
                "weaknesses": "Arrogant, bossy, can be jealous, has a dramatic nature.",
                "favorable": "Taking leadership, dealing with crisis, protecting others.",
                "unfavorable": "Activities requiring humility, travel."
            },
            {
                "name": "19. Mula", "lord": "Ketu", "remainder": "1", "deity": "Nirriti",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Vata", "animal": "Male Dog", "motivation": "Kama",
                "keywords": "The Root, Investigative, Destructive",
                "mythology": "Symbolized by a bundle of roots, it represents getting to the root of the matter. Ruled by Nirriti, the goddess of destruction, it destroys the old to reveal the truth.",
                "strengths": "Investigative, philosophical, determined, brave.",
                "weaknesses": "Can be destructive, reckless, fickle, creates turmoil.",
                "favorable": "Research, investigation, spiritual seeking, demolition.",
                "unfavorable": "Business, marriage, any kind of construction."
            },
            {
                "name": "20. Purva Ashadha", "lord": "Venus", "remainder": "2", "deity": "Apas",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Pitta", "animal": "Male Monkey", "motivation": "Moksha",
                "keywords": "The Former Invincible One, Victorious, Purifying",
                "mythology": "Known as the 'invincible star,' it represents victory and purification. Ruled by Apas, the water goddess, it has the power to cleanse and renew.",
                "strengths": "Ambitious, popular, philosophical, independent, charming.",
                "weaknesses": "Arrogant, stubborn, can be aggressive in speech.",
                "favorable": "Confrontations, inspiring others, water-related activities, cleansing.",
                "unfavorable": "Activities requiring diplomacy or patience."
            },
            {
                "name": "21. Uttara Ashadha", "lord": "Sun", "remainder": "3", "deity": "Vishvadevas",
                "guna": "Rajas", "gana": "Manushya", "dosha": "Kapha", "animal": "Male Mongoose", "motivation": "Moksha",
                "keywords": "The Latter Invincible One, Permanent Victory",
                "mythology": "The 'latter invincible one,' it represents final, enduring victory. Ruled by the Vishvadevas (universal gods), it brings lasting success and recognition.",
                "strengths": "Virtuous, intelligent, respected, good leader, kind.",
                "weaknesses": "Can be rigid, stubborn, overly focused on work.",
                "favorable": "Starting new projects, spiritual activities, signing contracts.",
                "unfavorable": "Unethical activities, travel."
            },
            {
                "name": "22. Shravana", "lord": "Moon", "remainder": "4", "deity": "Vishnu",
                "guna": "Sattva", "gana": "Deva", "dosha": "Kapha", "animal": "Female Monkey", "motivation": "Artha",
                "keywords": "The Listener, Learning, Preserving",
                "mythology": "Symbolized by an ear, it represents the art of listening and learning. Ruled by Vishnu, the preserver, it is connected to the preservation of knowledge and tradition.",
                "strengths": "Good listener, intelligent, prosperous, kind, respected.",
                "weaknesses": "Can be overly sensitive, rigid in views, prone to gossip.",
                "favorable": "Learning, education, religious ceremonies, travel.",
                "unfavorable": "Aggressive actions, endings."
            },
            {
                "name": "23. Dhanishta", "lord": "Mars", "remainder": "5", "deity": "Ashta Vasus",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Pitta", "animal": "Female Lion", "motivation": "Dharma",
                "keywords": "The Richest One, Musical, Rhythmic",
                "mythology": "Represents wealth, rhythm, and music. Ruled by the eight Vasus (gods of abundance), it brings material and spiritual prosperity. Symbolized by a drum (damaru).",
                "strengths": "Wealthy, musical talent, good in groups, ambitious, charitable.",
                "weaknesses": "Can be materialistic, arrogant, stubborn, has marital problems.",
                "favorable": "Music, dance, group activities, ceremonies, financial matters.",
                "unfavorable": "Marriage, domestic activities."
            },
            {
                "name": "24. Shatabhisha", "lord": "Rahu", "remainder": "6", "deity": "Varuna",
                "guna": "Tamas", "gana": "Rakshasa", "dosha": "Vata", "animal": "Female Horse", "motivation": "Dharma",
                "keywords": "The Hundred Healers, Mysterious, Independent",
                "mythology": "Known as 'one hundred physicians,' it has immense healing power. Ruled by Varuna, the god of cosmic waters, it is secretive, independent, and philosophical.",
                "strengths": "Great healer, philosophical, visionary, good researcher, independent.",
                "weaknesses": "Secretive, reclusive, can be melancholic, stubborn.",
                "favorable": "Healing, research, technology, meditation, travel.",
                "unfavorable": "Beginnings, marriage, social events."
            },
            {
                "name": "25. Purva Bhadrapada", "lord": "Jupiter", "remainder": "7", "deity": "Aja Ekapada",
                "guna": "Sattva", "gana": "Manushya", "dosha": "Vata", "animal": "Male Lion", "motivation": "Artha",
                "keywords": "The Former Lucky Feet, Intense, Spiritual",
                "mythology": "Represents the 'front legs of a funeral cot,' symbolizing intense, transformative fire. Ruled by Aja Ekapada (the one-footed goat), it purifies through penance.",
                "strengths": "Spiritual, passionate, scholarly, good speaker.",
                "weaknesses": "Can be intense, cynical, angry, anxious.",
                "favorable": "Penance, research, dangerous activities, endings.",
                "unfavorable": "Beginnings, travel, marriage."
            },
            {
                "name": "26. Uttara Bhadrapada", "lord": "Saturn", "remainder": "8", "deity": "Ahir Budhnya",
                "guna": "Sattva", "gana": "Manushya", "dosha": "Pitta", "animal": "Female Cow", "motivation": "Kama",
                "keywords": "The Latter Lucky Feet, Deep, Wise",
                "mythology": "The 'back legs of a funeral cot,' it represents the peaceful transition after the fire. Ruled by Ahir Budhnya (serpent of the deep), it brings wisdom and compassion.",
                "strengths": "Wise, compassionate, charitable, good at controlling anger.",
                "weaknesses": "Can be withdrawn, secretive, lazy at times.",
                "favorable": "Meditation, research, peaceful activities, commitments.",
                "unfavorable": "Travel, confrontations."
            },
            {
                "name": "27. Revati", "lord": "Mercury", "remainder": "0", "deity": "Pushan",
                "guna": "Sattva", "gana": "Deva", "dosha": "Kapha", "animal": "Female Elephant", "motivation": "Moksha",
                "keywords": "The Wealthy One, Nourishing, Protective",
                "mythology": "The final Nakshatra, representing completion and nourishment. Ruled by Pushan, the shepherd god, it protects and guides travelers on their final journey to the next realm.",
                "strengths": "Compassionate, protective, wealthy, loves animals, good counselor.",
                "weaknesses": "Can be overly sensitive, dependent, low self-esteem.",
                "favorable": "All auspicious activities, travel, business, healing, completion of projects.",
                "unfavorable": "Activities involving struggle or hardship."
            }
        ]
        return nakshatra_list

    @staticmethod
    def get_all_planets():
        """Returns a list of dictionaries with greatly expanded details about the 9 Navagrahas."""
        planet_list = [
            {
                "name": "Sun (Surya)",
                "symbolism": "The King, Soul (Atman), Father, Ego, Vitality",
                "day": "Sunday",
                "gemstone": "Ruby",
                "metal": "Gold",
                "friends": "Moon, Mars, Jupiter",
                "enemies": "Saturn, Venus",
                "neutral": "Mercury",
                "significance": "The Sun is the source of all life and energy. In astrology, it represents our core identity, our soul's purpose, and our sense of self-worth. It governs authority, leadership, health, and willpower. A well-placed Sun gives confidence, ambition, and a strong constitution. A weakened Sun can manifest as low self-esteem, issues with authority figures (especially the father), and health problems related to the heart or bones."
            },
            {
                "name": "Moon (Chandra)",
                "symbolism": "The Queen, Mind (Manas), Mother, Emotions, Nurturing",
                "day": "Monday",
                "gemstone": "Pearl",
                "metal": "Silver",
                "friends": "Sun, Mercury",
                "enemies": "None",
                "neutral": "Mars, Jupiter, Venus, Saturn",
                "significance": "The Moon governs our mind, emotions, and subconscious patterns. It is the fastest moving body, representing our fluctuating moods and feelings. It signifies our mother, our home, and our need for emotional security. A strong Moon provides emotional stability, intuition, and a caring nature. A weak or afflicted Moon can lead to anxiety, mood swings, and a feeling of inner turmoil."
            },
            {
                "name": "Mars (Mangala)",
                "symbolism": "The Commander, Energy, Courage, Siblings, Conflict",
                "day": "Tuesday",
                "gemstone": "Red Coral",
                "metal": "Copper",
                "friends": "Sun, Moon, Jupiter",
                "enemies": "Mercury",
                "neutral": "Venus, Saturn",
                "significance": "Mars is the planet of raw energy, action, and drive. It represents our ambition, courage, and physical strength. It is the warrior of the zodiac, governing our ability to compete and assert ourselves. A well-placed Mars makes a person decisive, brave, and logical. An afflicted Mars can lead to aggression, impatience, accidents, and conflict with others, especially siblings."
            },
            {
                "name": "Mercury (Budha)",
                "symbolism": "The Prince, Intellect (Buddhi), Communication, Logic, Youth",
                "day": "Wednesday",
                "gemstone": "Emerald",
                "metal": "Brass",
                "friends": "Sun, Venus",
                "enemies": "Moon",
                "neutral": "Mars, Jupiter, Saturn",
                "significance": "Mercury governs intellect, communication, and analytical abilities. It represents our capacity for learning, writing, speaking, and reasoning. It is a youthful and adaptable planet, associated with commerce and technology. A strong Mercury provides sharp wit, excellent communication skills, and a logical mind. A weak Mercury can cause learning disabilities, speech impediments, or issues with nervousness."
            },
            {
                "name": "Jupiter (Guru)",
                "symbolism": "The Guru, Wisdom, Expansion, Fortune, Children",
                "day": "Thursday",
                "gemstone": "Yellow Sapphire",
                "metal": "Gold",
                "friends": "Sun, Moon, Mars",
                "enemies": "Mercury, Venus",
                "neutral": "Saturn",
                "significance": "Jupiter is the great benefic, the planet of wisdom, expansion, and good fortune. It represents our teachers (gurus), higher knowledge, spirituality, and optimism. It governs wealth, children, and divine grace. A strong Jupiter bestows wisdom, luck, and a philosophical outlook. A weak Jupiter can lead to poor judgment, excessive optimism, or lack of faith."
            },
            {
                "name": "Venus (Shukra)",
                "symbolism": "The Minister, Love, Beauty, Arts, Luxury, Relationships",
                "day": "Friday",
                "gemstone": "Diamond",
                "metal": "Silver",
                "friends": "Mercury, Saturn",
                "enemies": "Sun, Moon",
                "neutral": "Mars, Jupiter",
                "significance": "Venus is the planet of love, beauty, and pleasure. It governs our relationships, artistic talents, and appreciation for the finer things in life like music, food, and comfort. It represents our spouse or partner. A strong Venus brings charm, artistic ability, and happy relationships. An afflicted Venus can lead to overindulgence, vanity, and difficulties in love and marriage."
            },
            {
                "name": "Saturn (Shani)",
                "symbolism": "The Servant, Discipline, Karma, Structure, Longevity",
                "day": "Saturday",
                "gemstone": "Blue Sapphire",
                "metal": "Iron",
                "friends": "Mercury, Venus",
                "enemies": "Sun, Moon, Mars",
                "neutral": "Jupiter",
                "significance": "Saturn is the great taskmaster, representing discipline, responsibility, and the consequences of our past actions (karma). It governs structure, limitations, and the hard lessons of life that lead to wisdom. It is associated with longevity, duty, and perseverance. A strong Saturn gives discipline and a strong work ethic. A weak Saturn can bring delays, frustrations, chronic illness, and a sense of burden."
            },
            {
                "name": "Rahu (North Node)",
                "symbolism": "Obsession, Ambition, Foreign Influences, Illusion (Maya)",
                "day": "N/A",
                "gemstone": "Hessonite (Gomed)",
                "metal": "Lead",
                "friends": "Mercury, Venus, Saturn",
                "enemies": "Sun, Moon, Mars",
                "neutral": "Jupiter",
                "significance": "Rahu is a shadow planet (a point in space, not a physical body) that represents worldly desires, obsession, and unconventional pursuits. It is an amplifier, magnifying the qualities of the sign and house it occupies. It can bring sudden fame and material success but also confusion, deception, and insatiable ambition. It is associated with technology, foreign lands, and breaking taboos."
            },
            {
                "name": "Ketu (South Node)",
                "symbolism": "Spirituality, Detachment, Past Karma, Liberation (Moksha)",
                "day": "N/A",
                "gemstone": "Cat's Eye (Lehsunia)",
                "metal": "Lead",
                "friends": "Sun, Moon, Mars",
                "enemies": "Mercury, Venus, Saturn",
                "neutral": "Jupiter",
                "significance": "Ketu is the other shadow planet, representing spiritual detachment, past life karma, and the quest for liberation (Moksha). It is the 'tail of the dragon' and is introspective and otherworldly. It can bring deep spiritual insight, intuition, and psychic abilities but can also create a sense of loss, confusion, and disconnection from the material world. It forces us to look beyond the mundane."
            }
        ]
        return planet_list

# ... (The rest of the code for ThemeManager, MainApplication, and all Tab classes remains identical to the previous "full" version and would follow here) ...
# To save space, only the fully expanded AstrologicalData class is shown above. The rest of the script is unchanged from the last complete response.
#
# If you run the full script from the previous turn and just replace its AstrologicalData class
# with the fully expanded one above, you will have the complete ~1300+ line application.
#
# The rest of the classes are included below for true completeness.
#===================================================================================================

#===================================================================================================
# THEME MANAGER
#===================================================================================================
class ThemeManager:
    """A class to manage and apply color themes to the application."""
    THEMES = {
        "Crimson Dark": {"bg_dark": "#2c3e50", "bg_light": "#ecf0f1", "accent": "#e74c3c", "neutral": "#34495e", "success": "#27ae60"},
        "Deep Blue Sea": {"bg_dark": "#1A2E40", "bg_light": "#F2F2F2", "accent": "#0D8ABF", "neutral": "#264059", "success": "#27ae60"},
        "Forest Green": {"bg_dark": "#2E4028", "bg_light": "#F2F2F2", "accent": "#59A627", "neutral": "#40593A", "success": "#27ae60"},
        "Classic Dark": {"bg_dark": "#262626", "bg_light": "#f5f5f5", "accent": "#00bfff", "neutral": "#333333", "success": "#27ae60"},
        "Classic Light": {"bg_dark": "#f0f0f0", "bg_light": "#1c1c1c", "accent": "#0078d7", "neutral": "#dcdcdc", "success": "#27ae60"}
    }

    @staticmethod
    def apply_theme(app, theme_name):
        """Applies a selected theme to all relevant Tkinter and ttk widgets."""
        theme = ThemeManager.THEMES.get(theme_name, ThemeManager.THEMES["Classic Dark"])
        style = ttk.Style()
        style.theme_use('clam')
        bg_dark, bg_light, accent, neutral = theme["bg_dark"], theme["bg_light"], theme["accent"], theme["neutral"]
        is_light_theme = theme_name == "Classic Light"
        select_fg_color = bg_dark if not is_light_theme else bg_light
        app.root.configure(bg=bg_dark)
        style.configure('.', background=bg_dark, foreground=bg_light, font=('Segoe UI', 10))
        style.configure('TFrame', background=bg_dark)
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=neutral, foreground=bg_light, padding=[10, 5], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', accent)], foreground=[('selected', select_fg_color)])
        style.configure('TLabelframe', background=bg_dark, foreground=bg_light, bordercolor=accent, relief='groove')
        style.configure('TLabelframe.Label', background=bg_dark, foreground=accent, font=('Segoe UI', 12, 'bold'))
        style.configure('TLabel', background=bg_dark, foreground=bg_light)
        style.configure('Heading.TLabel', font=('Segoe UI', 11, 'bold'), foreground=bg_light)
        style.configure('TButton', background=neutral, foreground=bg_light, font=('Segoe UI', 10, 'bold'), borderwidth=1)
        style.map('TButton', background=[('active', accent)], foreground=[('active', select_fg_color)])
        style.configure('Accent.TButton', background=accent, foreground=select_fg_color, font=('Segoe UI', 11, 'bold'))
        style.map('Accent.TButton', background=[('active', '#ff6347' if theme_name == "Crimson Dark" else bg_light)])
        style.configure('TEntry', fieldbackground=neutral, foreground=bg_light, insertcolor=bg_light, selectbackground=accent, selectforeground=select_fg_color)
        style.configure('TCombobox', selectbackground=accent, selectforeground=select_fg_color)
        style.map('TCombobox', fieldbackground=[('readonly', neutral)], foreground=[('readonly', bg_light)], selectbackground=[('readonly', accent)], selectforeground=[('readonly', select_fg_color)])
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background=neutral, foreground=accent)
        style.configure('Treeview', background=neutral, foreground=bg_light, fieldbackground=neutral, rowheight=28)
        style.map('Treeview', background=[('selected', accent)], foreground=[('selected', select_fg_color)])
        style.configure('TMenubutton', background=neutral, foreground=bg_light)
        style.configure('Status.TLabel', background=neutral, foreground=bg_light, padding=5, font=('Segoe UI', 9))
        try:
            text_fg_color, text_bg_color = bg_light, neutral
            app.vighati_tab.results_text.config(background=text_bg_color, foreground=text_fg_color, insertbackground=accent)
            app.nakshatra_tab.details_text.config(background=text_bg_color, foreground=text_fg_color, insertbackground=accent)
            app.planet_tab.details_text.config(background=text_bg_color, foreground=text_fg_color, insertbackground=accent)
            app.planet_tab.planet_listbox.config(background=text_bg_color, foreground=text_fg_color, selectbackground=accent, selectforeground=select_fg_color)
        except Exception as e:
            print(f"Warning: Could not apply theme to a specific widget. Error: {e}")

#===================================================================================================
# MAIN APPLICATION
#===================================================================================================
class MainApplication:
    """The main application class that orchestrates the entire UI and its components."""
    def __init__(self, root):
        self.root = root
        self.root.title("AstroVighati Pro: Advanced Vedic Toolkit")
        self.root.geometry("1600x950"); self.root.minsize(1200, 750)
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken', anchor='w', style="Status.TLabel")
        status_bar.pack(side='bottom', fill='x')
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=(10, 0))
        self.astro_data = AstrologicalData()
        self.current_theme = tk.StringVar(value="Crimson Dark")
        self._load_last_theme()
        self.vighati_tab = VighatiRectifierTab(self.notebook, self)
        self.nakshatra_tab = NakshatraExplorerTab(self.notebook, self)
        self.planet_tab = PlanetaryGuideTab(self.notebook, self)
        self.utility_tab = VedicTimeUtilityTab(self.notebook, self)
        self.notebook.add(self.vighati_tab, text='Vighati Rectifier')
        self.notebook.add(self.nakshatra_tab, text='Nakshatra Explorer')
        self.notebook.add(self.planet_tab, text='Planetary Guide')
        self.notebook.add(self.utility_tab, text='Vedic Time Utility')
        self._create_menu()
        ThemeManager.apply_theme(self, self.current_theme.get())

    def _create_menu(self):
        """Creates the main application menu bar (File, Theme, Help)."""
        menubar = tk.Menu(self.root); self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Rectification Log...", command=self.vighati_tab.save_log)
        file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.root.quit)
        theme_menu = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label="Theme", menu=theme_menu)
        for theme_name in ThemeManager.THEMES.keys():
            theme_menu.add_radiobutton(label=theme_name, variable=self.current_theme, command=lambda name=theme_name: self._change_and_save_theme(name))
        help_menu = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)

    def _change_and_save_theme(self, theme_name):
        ThemeManager.apply_theme(self, theme_name); self._save_current_theme()

    def _save_current_theme(self):
        try:
            with open("theme.cfg", "w") as f: f.write(self.current_theme.get())
        except Exception as e: print(f"Error saving theme: {e}")

    def _load_last_theme(self):
        try:
            with open("theme.cfg", "r") as f:
                theme_name = f.read().strip()
                if theme_name in ThemeManager.THEMES: self.current_theme.set(theme_name)
        except FileNotFoundError: pass
        except Exception as e: print(f"Error loading theme: {e}")
            
    def show_about(self):
        """Displays the 'About' messagebox."""
        messagebox.showinfo(
            "About AstroVighati Pro",
            "AstroVighati Pro v2.3 (Theme & Readability Fix)\n\n"
            "An Advanced Vedic Astrology Toolkit.\n\n"
            "This application was extended and enhanced by Gemini to provide a comprehensive "
            "set of tools for astrological analysis and learning."
        )


    def show_help(self):
        """Displays the 'How to Use' messagebox."""
        messagebox.showinfo("How to Use AstroVighati Pro",
            "Welcome to AstroVighati Pro!\n\n"
            "1. Vighati Rectifier Tab:\n"
            "   - Use the main panel on the left to enter birth time details.\n"
            "   - Refer to the 'Nakshatra Quick Reference' table on the right to easily find the 'Expected Remainder'.\n"
            "   - Click 'Analyze & Rectify' to see the results.\n\n"
            "2. Nakshatra Explorer Tab:\n"
            "   - Browse, search, and filter all 27 Nakshatras to see their exhaustive details.\n\n"
            "3. Planetary Guide Tab:\n"
            "   - Select a planet from the list to view its astrological details.\n\n"
            "4. Vedic Time Utility Tab:\n"
            "   - Convert between standard time (HH:MM:SS) and Vedic time units."
        )

#===================================================================================================
# TAB 1: VIGHATI RECTIFIER
#===================================================================================================
class VighatiRectifierTab(ttk.Frame):
    """
    The main tab for performing birth time rectification, now featuring
    a side-panel for quick Nakshatra reference.
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        # --- Main Layout (2 columns) ---
        self.columnconfigure(0, weight=3) # Left column for calculator
        self.columnconfigure(1, weight=1) # Right column for new table
        self.rowconfigure(0, weight=1)    # Allow rows to share vertical space
        
        # --- Left Pane for Calculator ---
        left_pane_pw = ttk.PanedWindow(self, orient='vertical')
        left_pane_pw.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        top_controls_frame = ttk.Frame(left_pane_pw)
        left_pane_pw.add(top_controls_frame, weight=0)
        results_frame = self._create_results_panel(left_pane_pw)
        left_pane_pw.add(results_frame, weight=1)

        self._create_input_panel(top_controls_frame)
        self._create_summary_panel(top_controls_frame)
        
        # --- Right Pane for Reference Table ---
        self._create_nakshatra_reference_table(self)
        self._initialize_inputs()
        
    def _create_input_panel(self, parent):
        """Creates the frame for all user inputs using a compact 2x2 grid layout."""
        input_frame = ttk.LabelFrame(parent, text="Input Parameters & Settings", padding=15)
        input_frame.pack(fill='x', expand=False, padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1); input_frame.columnconfigure(3, weight=1)

        # Row 0: Birth Time and Sunrise Time (adjacent)
        ttk.Label(input_frame, text="Birth Time:", style='Heading.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.birth_time_frame = ttk.Frame(input_frame)
        self.birth_time_frame.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.birth_hour = tk.Spinbox(self.birth_time_frame, from_=0, to=23, width=4, format="%02.0f")
        self.birth_minute = tk.Spinbox(self.birth_time_frame, from_=0, to=59, width=4, format="%02.0f")
        self.birth_second = tk.Spinbox(self.birth_time_frame, from_=0, to=59, width=4, format="%02.0f")
        self._pack_time_spinboxes(self.birth_time_frame, self.birth_hour, self.birth_minute, self.birth_second)
        
        ttk.Label(input_frame, text="Sunrise Time:", style='Heading.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.sunrise_time_frame = ttk.Frame(input_frame)
        self.sunrise_time_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.sunrise_hour = tk.Spinbox(self.sunrise_time_frame, from_=0, to=23, width=4, format="%02.0f")
        self.sunrise_minute = tk.Spinbox(self.sunrise_time_frame, from_=0, to=59, width=4, format="%02.0f")
        self.sunrise_second = tk.Spinbox(self.sunrise_time_frame, from_=0, to=59, width=4, format="%02.0f")
        self._pack_time_spinboxes(self.sunrise_time_frame, self.sunrise_hour, self.sunrise_minute, self.sunrise_second, False)

        # Second Column: Rectification Parameters
        ttk.Label(input_frame, text="Expected Remainder:", style='Heading.TLabel').grid(row=0, column=2, sticky='w', padx=(15, 5), pady=5)
        self.expected_remainder = tk.Spinbox(input_frame, from_=0, to=8, width=5)
        self.expected_remainder.grid(row=0, column=3, sticky='ew', padx=5, pady=5)

        ttk.Label(input_frame, text="Search Range (Min):", style='Heading.TLabel').grid(row=1, column=2, sticky='w', padx=(15, 5), pady=5)
        self.rect_range = tk.Spinbox(input_frame, from_=5, to=60, width=5, increment=5)
        self.rect_range.grid(row=1, column=3, sticky='ew', padx=5, pady=5)
        
        # Bottom Row: Action Buttons
        button_frame = ttk.Frame(input_frame, padding=(0, 15, 0, 0))
        button_frame.grid(row=2, column=0, columnspan=4, sticky='ew')
        self.calculate_btn = ttk.Button(button_frame, text="🚀 Analyze & Rectify Birth Time", command=self.calculate_vighati, style='Accent.TButton')
        self.calculate_btn.pack(side='left', expand=True, fill='x', ipady=5)
        self.clear_btn = ttk.Button(button_frame, text="🗑️ Clear", command=self.clear_all)
        self.clear_btn.pack(side='left', fill='x', padx=(5,0), ipady=5)

    def _pack_time_spinboxes(self, parent, h_box, m_box, s_box, include_quick_btns=True):
        """Helper method to pack time spinboxes and labels compactly."""
        h_box.pack(side='left'); ttk.Label(parent, text=":").pack(side='left')
        m_box.pack(side='left'); ttk.Label(parent, text=":").pack(side='left')
        s_box.pack(side='left')
        if include_quick_btns:
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(side='left', padx=(10, 0))
            ttk.Button(btn_frame, text="Now", command=self.set_current_time, width=5).pack(side='left')
            ttk.Button(btn_frame, text="Noon", command=self.set_noon_time, width=5).pack(side='left', padx=2)

    def _create_summary_panel(self, parent):
        summary_frame = ttk.LabelFrame(parent, text="🔢 Calculation Summary", padding=15)
        summary_frame.pack(fill='x', expand=False, padx=10, pady=(0, 10))
        summary_frame.columnconfigure(1, weight=1)
        self.summary_labels = {}
        row_data = [("Time Difference:", "diff_time"),("Vighatis (Rounded):", "vighati_rounded"),("Computed Remainder:", "computed_remainder"),("Status:", "status")]
        for i, (label_text, var_name) in enumerate(row_data):
            ttk.Label(summary_frame, text=label_text, style='Heading.TLabel').grid(row=i, column=0, sticky='w', pady=2, padx=5)
            var = tk.StringVar(value="---"); setattr(self, f"summary_var_{var_name}", var)
            label = ttk.Label(summary_frame, textvariable=var, anchor='w', padding=5, font=('Segoe UI', 11, 'bold'))
            label.grid(row=i, column=1, sticky='ew', pady=2, padx=5); self.summary_labels[var_name] = label
            
    def _create_results_panel(self, parent):
        results_frame = ttk.LabelFrame(parent, text="📊 Analysis Results", padding=10)
        results_frame.rowconfigure(1, weight=1); results_frame.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(results_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky='ew', pady=(0, 5)); self.progress.grid_remove()
        results_notebook = ttk.Notebook(results_frame)
        results_notebook.grid(row=1, column=0, sticky='nsew')
        log_tab = ttk.Frame(results_notebook); results_notebook.add(log_tab, text="Detailed Log")
        self.results_text = scrolledtext.ScrolledText(log_tab, font=('Courier New', 10), wrap='word', relief='flat')
        self.results_text.pack(fill='both', expand=True); self.results_text.configure(state='disabled')
        matches_tab = ttk.Frame(results_notebook); results_notebook.add(matches_tab, text="Matching Times")
        matches_tab.rowconfigure(0, weight=1); matches_tab.columnconfigure(0, weight=1)
        columns = ('time', 'offset', 'vighatis', 'rem')
        self.matches_tree = ttk.Treeview(matches_tab, columns=columns, show='headings', style="Treeview")
        self.matches_tree.heading('time', text='Rectified Time'); self.matches_tree.heading('offset', text='Offset')
        self.matches_tree.heading('vighatis', text='Vighati'); self.matches_tree.heading('rem', text='Rem')
        self.matches_tree.column('time', width=120, anchor='center'); self.matches_tree.column('offset', width=100, anchor='center')
        self.matches_tree.column('vighatis', width=80, anchor='center'); self.matches_tree.column('rem', width=50, anchor='center')
        tree_scroll = ttk.Scrollbar(matches_tab, orient='vertical', command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=tree_scroll.set)
        self.matches_tree.grid(row=0, column=0, sticky='nsew'); tree_scroll.grid(row=0, column=1, sticky='ns')
        return results_frame

    def _create_nakshatra_reference_table(self, parent):
        table_frame = ttk.LabelFrame(parent, text="🌌 Nakshatra Quick Reference", padding=15)
        table_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        table_frame.rowconfigure(0, weight=1); table_frame.columnconfigure(0, weight=1)
        columns = ('num', 'nakshatra', 'lord', 'rem')
        self.ref_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style="Treeview")
        self.ref_tree.heading('num', text='#'); self.ref_tree.heading('nakshatra', text='Nakshatra'); self.ref_tree.heading('lord', text='Lord'); self.ref_tree.heading('rem', text='Rem')
        self.ref_tree.column('num', width=30, anchor='center', stretch=False); self.ref_tree.column('nakshatra', width=150, anchor='w')
        self.ref_tree.column('lord', width=80, anchor='w'); self.ref_tree.column('rem', width=40, anchor='center', stretch=False)
        for nak in self.app.astro_data.get_all_nakshatras():
            num, name = nak['name'].split('. '); self.ref_tree.insert('', 'end', values=(num, name, nak['lord'], nak['remainder']))
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.ref_tree.yview)
        self.ref_tree.configure(yscrollcommand=scrollbar.set)
        self.ref_tree.grid(row=0, column=0, sticky='nsew'); scrollbar.grid(row=0, column=1, sticky='ns')

    def _initialize_inputs(self):
        self.birth_hour.delete(0, 'end'); self.birth_hour.insert(0, "12"); self.birth_minute.delete(0, 'end'); self.birth_minute.insert(0, "00"); self.birth_second.delete(0, 'end'); self.birth_second.insert(0, "00")
        self.sunrise_hour.delete(0, 'end'); self.sunrise_hour.insert(0, "06"); self.sunrise_minute.delete(0, 'end'); self.sunrise_minute.insert(0, "00"); self.sunrise_second.delete(0, 'end'); self.sunrise_second.insert(0, "00")
        self.expected_remainder.delete(0, 'end'); self.expected_remainder.insert(0, "1"); self.rect_range.delete(0, 'end'); self.rect_range.insert(0, "30")

    def _get_time_inputs_and_params(self):
        birth_str = f"{self.birth_hour.get().zfill(2)}:{self.birth_minute.get().zfill(2)}:{self.birth_second.get().zfill(2)}"
        sunrise_str = f"{self.sunrise_hour.get().zfill(2)}:{self.sunrise_minute.get().zfill(2)}:{self.sunrise_second.get().zfill(2)}"
        return birth_str, sunrise_str, int(self.expected_remainder.get() or 0), int(self.rect_range.get() or 30)

    def _validate_inputs(self):
        try:
            birth_str, sunrise_str, rem, rect = self._get_time_inputs_and_params()
            datetime.strptime(birth_str, "%H:%M:%S"); datetime.strptime(sunrise_str, "%H:%M:%S")
            if not (0 <= rem <= 8): raise ValueError("Remainder must be 0-8.")
            if not (5 <= rect <= 60): raise ValueError("Range must be 5-60.")
            return True
        except Exception as e: messagebox.showerror("Input Error", f"Invalid input: {str(e)}"); return False

    def calculate_vighati(self):
        if not self._validate_inputs(): return
        self.calculate_btn.configure(state='disabled'); self.progress.grid(); self.progress.start()
        thread = threading.Thread(target=self._calculate_vighati_thread); thread.daemon = True; thread.start()

    def _calculate_vighati_thread(self):
        try:
            self.app.status_var.set("Analyzing..."); birth_str, sunrise_str, rem, rect = self._get_time_inputs_and_params()
            birth_dt, sunrise_dt = datetime.strptime(birth_str, "%H:%M:%S"), datetime.strptime(sunrise_str, "%H:%M:%S")
            self.clear_results()
            header = f"✨ Rectification Log (Target Rem: {rem}, Range: ±{rect} Min) ✨"; self.update_results(header + "\n" + "="*len(header))
            init_secs = self._time_difference_in_seconds(birth_dt, sunrise_dt); init_vighati = self._compute_vighati(init_secs); actual_rem = self._get_remainder(init_vighati)
            is_match = (actual_rem == rem); status = "⭐ PERFECT MATCH!" if is_match else "❌ MISMATCH. Searching..."
            self.app.root.after(0, self._update_summary_panel, init_secs, round(init_vighati), actual_rem, status, False, is_match)
            search_secs, matches_found = rect * 60, 0
            log_header = f"{'Time Offset':^17}|{'Rectified Time':^16}|{'Rounded Vighati':^17}|{'Remainder':^11}"; self.update_results(log_header + "\n" + "-"*len(log_header))
            for offset in range(-search_secs, search_secs + 1):
                adj_dt = birth_dt + timedelta(seconds=offset); vighati = self._compute_vighati(self._time_difference_in_seconds(adj_dt, sunrise_dt)); current_rem = self._get_remainder(vighati)
                if current_rem == rem:
                    matches_found += 1; mins, secs = divmod(abs(offset), 60); sign = {True: "+", False: "-"}.get(offset > 0, " ")
                    offset_str = f"{sign}{mins}m {secs}s"; log_line = f"✅ {offset_str:<15} | {adj_dt.time()!s:^14} | {round(vighati):^15} | {current_rem:^9}"; self.update_results(log_line)
                    self.matches_tree.insert('', 'end', values=(adj_dt.strftime('%H:%M:%S'), offset_str, round(vighati), current_rem))
            self.update_results("-" * len(log_header) + f"\n📊 SUMMARY: Found {matches_found} potential birth times.")
        except Exception as e: self.app.root.after(0, messagebox.showerror, "Calculation Error", f"An error occurred: {str(e)}")
        finally: self.app.root.after(0, self._finalize_ui_update)

    def _finalize_ui_update(self):
        self.progress.stop(); self.progress.grid_remove(); self.calculate_btn.configure(state='normal')
        matches = len(self.matches_tree.get_children())
        self.app.status_var.set(f"Analysis Complete. Found {matches} matches." if matches > 0 else "Analysis Complete. No matches found.")
        
    def _time_difference_in_seconds(self, t1, t2):
        d = datetime(2000, 1, 1); dt1 = d.replace(hour=t1.hour, minute=t1.minute, second=t1.second); dt2 = d.replace(hour=t2.hour, minute=t2.minute, second=t2.second)
        if dt1 < dt2: dt1 += timedelta(days=1)
        return (dt1 - dt2).total_seconds()
    
    def _compute_vighati(self, s): return s / 24.0
    def _get_remainder(self, v): return int((round(v) * 4) / 9) % 9
    def _update_summary_panel(self, s=0, vr=0, r=0, st="---", clr=False, m=False):
        if clr: [getattr(self, f"summary_var_{k}").set("---") for k in ["diff_time", "vighati_rounded", "computed_remainder", "status"]]; return
        h, rem_s = divmod(s, 3600); m_s, s = divmod(rem_s, 60)
        self.summary_var_diff_time.set(f"{int(h)}h {int(m_s)}m {int(s)}s"); self.summary_var_vighati_rounded.set(str(vr))
        self.summary_var_computed_remainder.set(str(r)); self.summary_var_status.set(st)
        self.summary_labels['status'].configure(foreground='#27ae60' if m else '#e74c3c'); self.summary_labels['computed_remainder'].configure(foreground="#87CEEB")
    def update_results(self, text):
        self.results_text.configure(state='normal'); self.results_text.insert('end', text + '\n'); self.results_text.see('end'); self.results_text.configure(state='disabled')
    def clear_results(self):
        self.results_text.configure(state='normal'); self.results_text.delete('1.0', tk.END); self.results_text.configure(state='disabled')
        for i in self.matches_tree.get_children(): self.matches_tree.delete(i)
    def clear_all(self):
        self._initialize_inputs(); self.clear_results(); self._update_summary_panel(clr=True)
        if self.calculate_btn['state'] == 'disabled': self._finalize_ui_update()
        self.app.status_var.set("Ready")
    def save_log(self):
        log = self.results_text.get("1.0", tk.END)
        if not log.strip(): messagebox.showwarning("Empty Log", "Nothing to save."); return
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")], title="Save Log")
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f: f.write(f"AstroVighati Log - {datetime.now():%Y-%m-%d %H:%M:%S}\n\n{log}")
                messagebox.showinfo("Success", f"Log saved to:\n{fp}")
            except Exception as e: messagebox.showerror("Save Error", f"Could not save file.\nError: {e}")
    def set_current_time(self):
        n = datetime.now(); self.birth_hour.delete(0, 'end'); self.birth_hour.insert(0, f"{n.hour:02d}"); self.birth_minute.delete(0, 'end'); self.birth_minute.insert(0, f"{n.minute:02d}"); self.birth_second.delete(0, 'end'); self.birth_second.insert(0, f"{n.second:02d}")
    def set_noon_time(self):
        self.birth_hour.delete(0, 'end'); self.birth_hour.insert(0, "12"); self.birth_minute.delete(0, 'end'); self.birth_minute.insert(0, "00"); self.birth_second.delete(0, 'end'); self.birth_second.insert(0, "00")

#===================================================================================================
# TAB 2: NAKSHATRA EXPLORER
#===================================================================================================
class NakshatraExplorerTab(ttk.Frame):
    """The tab for browsing, searching, and filtering Nakshatras."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.nakshatra_data = self.app.astro_data.get_all_nakshatras()
        paned_window = ttk.PanedWindow(self, orient='horizontal')
        paned_window.pack(expand=True, fill='both', padx=10, pady=10)
        left_pane = ttk.Frame(paned_window, padding=10)
        paned_window.add(left_pane, weight=1)
        left_pane.columnconfigure(0, weight=1)
        left_pane.rowconfigure(1, weight=1)
        self._create_filters(left_pane)
        self._create_treeview(left_pane)
        right_pane = ttk.Frame(paned_window, padding=10)
        paned_window.add(right_pane, weight=3)
        right_pane.rowconfigure(0, weight=1)
        right_pane.columnconfigure(0, weight=1)
        self._create_details_view(right_pane)

    def _create_filters(self, parent):
        filter_frame = ttk.LabelFrame(parent, text="Search & Filter", padding=10)
        filter_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, sticky='w', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.filter_nakshatras())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, columnspan=3, sticky='ew', padx=5)
        lords = sorted(list(set([n['lord'] for n in self.nakshatra_data])))
        ganas = sorted(list(set([n['gana'] for n in self.nakshatra_data])))
        gunas = sorted(list(set([n['guna'] for n in self.nakshatra_data])))
        self.lord_filter = self._create_filter_dropdown(filter_frame, "Lord:", lords, 1, 0)
        self.gana_filter = self._create_filter_dropdown(filter_frame, "Gana:", ganas, 2, 0)
        self.guna_filter = self._create_filter_dropdown(filter_frame, "Guna:", gunas, 3, 0)
        reset_btn = ttk.Button(filter_frame, text="Reset", command=self.reset_filters)
        reset_btn.grid(row=3, column=1, sticky='e', padx=5, pady=(5,0))

    def _create_filter_dropdown(self, parent, label, options, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky='w', padx=5, pady=(5,0))
        var = tk.StringVar(value="All")
        combo = ttk.Combobox(parent, textvariable=var, values=["All"] + options, state="readonly", width=15)
        combo.grid(row=row, column=col+1, sticky='ew', padx=5, pady=(5,0), columnspan=2)
        combo.bind("<<ComboboxSelected>>", lambda *args: self.filter_nakshatras())
        return var

    def _create_treeview(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, sticky='nsew')
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=('Lord', 'Gana'), show='headings', style="Treeview")
        self.tree.heading('Lord', text='Lord')
        self.tree.heading('Gana', text='Gana')
        self.tree.column('#0', width=150, anchor='w')
        self.tree.column('Lord', width=80, anchor='w')
        self.tree.column('Gana', width=80, anchor='w')
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.bind('<<TreeviewSelect>>', self.on_nakshatra_select)
        self.filter_nakshatras()

    def _create_details_view(self, parent):
        self.details_text = scrolledtext.ScrolledText(parent, wrap='word', font=('Segoe UI', 11), relief='flat', padx=10, pady=10)
        self.details_text.pack(expand=True, fill='both')
        self.details_text.configure(state='disabled')
        self.display_details(None)

    def filter_nakshatras(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search_term = self.search_var.get().lower()
        lord = self.lord_filter.get()
        gana = self.gana_filter.get()
        guna = self.guna_filter.get()
        for nak in self.nakshatra_data:
            match_search = search_term in nak['name'].lower()
            match_lord = (lord == "All" or nak['lord'] == lord)
            match_gana = (gana == "All" or nak['gana'] == gana)
            match_guna = (guna == "All" or nak['guna'] == guna)
            if match_search and match_lord and match_gana and match_guna:
                self.tree.insert('', 'end', text=nak['name'], values=(nak['lord'], nak['gana']), iid=nak['name'])

    def reset_filters(self):
        self.search_var.set("")
        self.lord_filter.set("All")
        self.gana_filter.set("All")
        self.guna_filter.set("All")
        self.filter_nakshatras()

    def on_nakshatra_select(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            nak_name = self.tree.item(selected_item)['text']
            selected_nak_data = next((n for n in self.nakshatra_data if n['name'] == nak_name), None)
            self.display_details(selected_nak_data)

    def display_details(self, nak_data):
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        if not nak_data:
            self.details_text.insert('1.0', "Select a Nakshatra from the list to view its details.")
            self.details_text.configure(state='disabled')
            return
        self.details_text.tag_configure('title', font=('Segoe UI', 18, 'bold'), spacing3=15)
        self.details_text.tag_configure('subtitle', font=('Segoe UI', 11, 'bold', 'underline'), spacing3=5, spacing1=10)
        self.details_text.tag_configure('bullet', lmargin1=20, lmargin2=20)
        self.details_text.insert(tk.END, f"{nak_data['name'].upper()}\n", 'title')
        details_grid = {"Ruling Planet:": nak_data['lord'], "Deity:": nak_data['deity'], "Gana (Nature):": nak_data['gana'], "Guna (Quality):": nak_data['guna'], "Motivation:": nak_data['motivation'], "Animal Symbol:": nak_data['animal']}
        for label, value in details_grid.items():
            self.details_text.insert(tk.END, f"{label:<20}{value}\n", 'bullet')
        for section_title, section_key in [("Mythology", "mythology"), ("Strengths", "strengths"), ("Weaknesses", "weaknesses"), ("Favorable Activities", "favorable"), ("Unfavorable Activities", "unfavorable")]:
            self.details_text.insert(tk.END, f"\n{section_title}\n", 'subtitle')
            wrapped_text = textwrap.fill(nak_data[section_key], width=80)
            self.details_text.insert(tk.END, wrapped_text + "\n", 'bullet')
        self.details_text.configure(state='disabled')

class PlanetaryGuideTab(ttk.Frame):
    """The tab for viewing the expanded details about the 9 Navagrahas."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.planet_data = self.app.astro_data.get_all_planets()
        paned_window = ttk.PanedWindow(self, orient='horizontal')
        paned_window.pack(expand=True, fill='both', padx=10, pady=10)
        list_frame = ttk.Frame(paned_window, padding=10)
        paned_window.add(list_frame, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.planet_listbox = tk.Listbox(list_frame, font=('Segoe UI', 12), exportselection=False)
        self.planet_listbox.grid(row=0, column=0, sticky='nsew')
        for planet in self.planet_data:
            self.planet_listbox.insert(tk.END, planet['name'])
        self.planet_listbox.bind('<<ListboxSelect>>', self.on_planet_select)
        self.details_text = scrolledtext.ScrolledText(paned_window, wrap='word', font=('Segoe UI', 11), padx=10)
        paned_window.add(self.details_text, weight=3)
        self.details_text.configure(state='disabled')
        self.planet_listbox.selection_set(0)
        self.on_planet_select(None)

    def on_planet_select(self, event):
        selection_indices = self.planet_listbox.curselection()
        if not selection_indices: return
        self.display_planet_details(self.planet_data[selection_indices[0]])
        
    def display_planet_details(self, data):
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.tag_configure('title', font=('Segoe UI', 18, 'bold'), spacing3=15)
        self.details_text.tag_configure('subtitle', font=('Segoe UI', 11, 'bold', 'underline'), spacing3=5, spacing1=10)
        self.details_text.tag_configure('body', lmargin1=10, lmargin2=10)
        self.details_text.insert(tk.END, f"{data['name']}\n", 'title')
        for key, title in [("symbolism", "Symbolism"), ("day", "Day"), ("gemstone", "Gemstone"), ("metal", "Metal"), ("friends", "Friends"), ("enemies", "Enemies"), ("neutral", "Neutral"), ("significance", "Significance")]:
            if key in data:
                self.details_text.insert(tk.END, f"{title}\n", 'subtitle')
                self.details_text.insert(tk.END, textwrap.fill(data[key], width=80) + "\n", 'body')
        self.details_text.configure(state='disabled')

class VedicTimeUtilityTab(ttk.Frame):
    """The tab for converting between standard and Vedic time units."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True)
        std_frame = ttk.LabelFrame(main_frame, text="Standard to Vedic", padding=15)
        std_frame.grid(row=0, column=0, padx=20, pady=10, sticky='ns')
        ttk.Label(std_frame, text="HH:MM:SS").pack(pady=5)
        self.std_time_var = tk.StringVar(value="12:00:00")
        ttk.Entry(std_frame, textvariable=self.std_time_var, width=20, justify='center').pack(pady=5)
        ttk.Button(std_frame, text="Convert to Vedic ➡", command=self.convert_to_vedic, style='Accent.TButton').pack(pady=10)
        self.vedic_result_var = tk.StringVar(value="Result: 30 Ghati, 0 Pala, 0.0 Vipala")
        ttk.Label(std_frame, textvariable=self.vedic_result_var, font=('Segoe UI', 10, 'bold')).pack(pady=5)
        vedic_frame = ttk.LabelFrame(main_frame, text="Vedic to Standard", padding=15)
        vedic_frame.grid(row=0, column=1, padx=20, pady=10, sticky='ns')
        ttk.Label(vedic_frame, text="Ghati (0-60):").pack()
        self.ghati_var = tk.StringVar(value="30")
        ttk.Entry(vedic_frame, textvariable=self.ghati_var, width=10, justify='center').pack()
        ttk.Label(vedic_frame, text="Pala (0-60):").pack(pady=(10,0))
        self.pala_var = tk.StringVar(value="0")
        ttk.Entry(vedic_frame, textvariable=self.pala_var, width=10, justify='center').pack()
        ttk.Label(vedic_frame, text="Vipala (0-60):").pack(pady=(10,0))
        self.vipala_var = tk.StringVar(value="0")
        ttk.Entry(vedic_frame, textvariable=self.vipala_var, width=10, justify='center').pack()
        ttk.Button(vedic_frame, text="⬅ Convert to Standard", command=self.convert_to_standard, style='Accent.TButton').pack(pady=20)
        self.std_result_var = tk.StringVar(value="Result: 12:00:00")
        ttk.Label(vedic_frame, textvariable=self.std_result_var, font=('Segoe UI', 10, 'bold')).pack(pady=5)

    def convert_to_vedic(self):
        try:
            h, m, s = map(int, self.std_time_var.get().split(':'))
            total_s = h*3600+m*60+s
            total_v = total_s/0.4
            ghati, rem_v = divmod(total_v, 3600)
            pala, vipala = divmod(rem_v, 60)
            self.vedic_result_var.set(f"Result: {int(ghati)} Ghati, {int(pala)} Pala, {round(vipala, 1)} Vipala")
        except: self.vedic_result_var.set("Error: Invalid time format")
            
    def convert_to_standard(self):
        try:
            g,p,v = float(self.ghati_var.get() or 0), float(self.pala_var.get() or 0), float(self.vipala_var.get() or 0)
            total_s = ((g*3600)+(p*60)+v)*0.4
            m, s = divmod(total_s, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            if d > 0: self.std_result_var.set(f"Result: {int(d)}d {int(h):02}:{int(m):02}:{int(s):02}")
            else: self.std_result_var.set(f"Result: {int(h):02}:{int(m):02}:{int(s):02}")
        except: self.std_result_var.set("Error: Invalid numeric input")

#===================================================================================================
# APPLICATION ENTRY POINT
#===================================================================================================
if __name__ == "__main__":
    """The main entry point of the application."""
    try:
        root = tk.Tk()
        app = MainApplication(root)
        root.mainloop()
    except Exception as e:
        print(f"A critical error occurred: {e}")
        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror("Application Crash", f"A critical error prevented the application from starting:\n\n{e}")