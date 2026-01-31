from datetime import datetime, timedelta
from models import Venue, Beer, SocialPost

# Sydney breweries and craft beer bars
SYDNEY_VENUES = [
    Venue(
        id="young-henrys",
        name="Young Henrys",
        type="brewery",
        address="76 Wilford St, Newtown",
        suburb="Newtown",
        location=(-33.8969, 151.1795),
        instagram_handle="@younghenrys",
        tags=["craft", "local", "popular"]
    ),
    Venue(
        id="batch-brewing",
        name="Batch Brewing Company",
        type="brewery",
        address="44 Sydenham Rd, Marrickville",
        suburb="Marrickville",
        location=(-33.9115, 151.1638),
        instagram_handle="@batchbrewingcompany",
        tags=["craft", "experimental", "sours"]
    ),
    Venue(
        id="wayward-brewing",
        name="Wayward Brewing Co",
        type="brewery",
        address="1-3 Gehrig Pl, Camperdown",
        suburb="Camperdown",
        location=(-33.8886, 151.1823),
        instagram_handle="@waywardbrewing",
        tags=["craft", "hoppy", "IPA"]
    ),
    Venue(
        id="grifter-brewing",
        name="Grifter Brewing Co",
        type="brewery",
        address="391 Enmore Rd, Marrickville",
        suburb="Marrickville",
        location=(-33.9042, 151.1671),
        instagram_handle="@grifterbrewing",
        tags=["craft", "sessionable", "pale-ale"]
    ),
    Venue(
        id="the-rocks-brewing",
        name="The Rocks Brewing Co",
        type="brewery",
        address="160 Bourke Rd, Alexandria",
        suburb="Alexandria",
        location=(-33.9105, 151.2034),
        instagram_handle="@therocksbrewing",
        tags=["craft", "traditional", "pub-style"]
    ),
    # NEW BREWERIES
    Venue(
        id="bracket-brewing",
        name="Bracket Brewing",
        type="brewery",
        address="42-44 Sydney St, Marrickville",
        suburb="Marrickville",
        location=(-33.9142, 151.1567),
        instagram_handle="@bracketbrewing",
        tags=["craft", "innovative", "small-batch"]
    ),
    Venue(
        id="future-brewing",
        name="Future Brewing Co",
        type="brewery",
        address="9-11 Milperra Rd, Banksmeadow",
        suburb="Banksmeadow",
        location=(-33.9391, 151.2117),
        instagram_handle="@futurebrewing",
        tags=["craft", "experimental", "hazy"]
    ),
    Venue(
        id="range-brewing",
        name="Range Brewing",
        type="brewery",
        address="52 Bishop St, Kelvin Grove",
        suburb="Brisbane",
        location=(-27.4511, 153.0185),
        instagram_handle="@rangebrewing",
        tags=["craft", "IPA-focused", "limited-releases"]
    ),
    Venue(
        id="mountain-culture",
        name="Mountain Culture Beer Co",
        type="brewery",
        address="23-25 Parke St, Katoomba",
        suburb="Katoomba",
        location=(-33.7158, 150.3121),
        instagram_handle="@mountainculturebeerco",
        tags=["craft", "adventure-beer", "blue-mountains"]
    ),
    Venue(
        id="kicks-brewing",
        name="Kicks Brewing",
        type="brewery",
        address="12 Frederick St, Artarmon",
        suburb="Artarmon",
        location=(-33.8167, 151.1833),
        instagram_handle="@kicksbrewing",
        tags=["craft", "sports-themed", "sessionable"]
    ),
    # MORE BREWERIES
    Venue(
        id="4-pines",
        name="4 Pines Brewing",
        type="brewery",
        address="4c 9-13 Winbourne Rd, Brookvale",
        suburb="Brookvale",
        location=(-33.7583, 151.2775),
        instagram_handle="@4pinesbeer",
        tags=["craft", "mainstream-craft", "beach-culture"]
    ),
    Venue(
        id="white-bay",
        name="White Bay Beer Co",
        type="brewery",
        address="26-36 Mansfield St, Rozelle",
        suburb="Rozelle",
        location=(-33.8619, 151.1703),
        instagram_handle="@whitebaybeerco",
        tags=["craft", "lagers", "balanced"]
    ),
    # BARS
    Venue(
        id="blood-orange-liquor",
        name="Blood Orange Liquor Bar",
        type="bar",
        address="78 Campbell St, Surry Hills",
        suburb="Surry Hills",
        location=(-33.8815, 151.2101),
        instagram_handle="@bloodorangeliquorbar",
        tags=["cocktail", "craft-beer", "trendy"]
    ),
    Venue(
        id="the-tilbury",
        name="The Tilbury",
        type="bar",
        address="12-18 Nicholson St, Woolloomooloo",
        suburb="Woolloomooloo",
        location=(-33.8691, 151.2209),
        instagram_handle="@thetilbury",
        tags=["gastropub", "craft-beer", "dining"]
    ),
    Venue(
        id="ddc",
        name="Dulcie's Dove Club",
        type="bar",
        address="44 King St, Newtown",
        suburb="Newtown",
        location=(-33.8956, 151.1834),
        instagram_handle="@dulciesdoveclub",
        tags=["cocktail", "craft-beer", "live-music"]
    ),
    Venue(
        id="basketball-liquor",
        name="Basketball Liquor",
        type="bar",
        address="324B Stanmore Rd, Petersham",
        suburb="Petersham",
        location=(-33.8912, 151.1554),
        instagram_handle="@basketballliquor",
        tags=["dive-bar", "craft-beer", "locals"]
    ),
    Venue(
        id="tiva",
        name="Tiva",
        type="bar",
        address="159 King St, Newtown",
        suburb="Newtown",
        location=(-33.8945, 151.1856),
        instagram_handle="@tivabarsyd",
        tags=["natural-wine", "craft-beer", "small-plates"]
    ),
    # NEW BARS
    Venue(
        id="hotel-sweeneys",
        name="Hotel Sweeney's",
        type="bar",
        address="236 Clarence St, Sydney",
        suburb="Sydney CBD",
        location=(-33.8688, 151.2053),
        instagram_handle="@hotelsweeneys",
        tags=["pub", "craft-beer", "live-music", "rooftop"]
    ),
    # MORE BARS
    Venue(
        id="jb-and-sons",
        name="JB & Sons",
        type="bar",
        address="2/476 Pacific Hwy, Crows Nest",
        suburb="Crows Nest",
        location=(-33.8275, 151.1992),
        instagram_handle="@jbandsons",
        tags=["craft-beer", "sports-bar", "american-style"]
    ),
    Venue(
        id="noble-hops",
        name="Noble Hops",
        type="bar",
        address="356 Cleveland St, Redfern",
        suburb="Redfern",
        location=(-33.8886, 151.2108),
        instagram_handle="@noblehopsbar",
        tags=["craft-beer", "wine-bar", "neighbourhood"]
    ),
    Venue(
        id="union-hotel",
        name="The Union Hotel",
        type="bar",
        address="576 King St, Newtown",
        suburb="Newtown",
        location=(-33.9036, 151.1786),
        instagram_handle="@theunionhotelnewtown",
        tags=["pub", "craft-beer", "live-music", "garden"]
    ),
    Venue(
        id="bitter-phew",
        name="Bitter Phew",
        type="bar",
        address="328 Oxford St, Darlinghurst",
        suburb="Darlinghurst",
        location=(-33.8778, 151.2172),
        instagram_handle="@bitterphew",
        tags=["craft-beer", "dive-bar", "late-night"]
    ),
    Venue(
        id="harts-pub",
        name="Harts Pub",
        type="bar",
        address="Corner of Essex & Gloucester St, The Rocks",
        suburb="The Rocks",
        location=(-33.8594, 151.2075),
        instagram_handle="@hartspub",
        tags=["pub", "craft-beer", "historic", "cask-ale"]
    ),
]

# Generate sample beers with some being "new releases" (within last 7 days)
_now = datetime.now()
SYDNEY_BEERS = [
    Beer(
        id="beer-001",
        name="Newtown Jets IPA",
        brewery_id="young-henrys",
        style="IPA",
        abv=6.5,
        description="Hazy IPA with tropical notes",
        release_date=_now - timedelta(days=2),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-002",
        name="Cloudy Cider",
        brewery_id="young-henrys",
        style="Cider",
        abv=5.0,
        description="Crisp apple cider",
        release_date=_now - timedelta(days=30),
        is_new_release=False
    ),
    Beer(
        id="beer-003",
        name="Eskimo Juice",
        brewery_id="batch-brewing",
        style="NEIPA",
        abv=6.8,
        description="Juicy New England IPA",
        release_date=_now - timedelta(days=5),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-004",
        name="Lemonade Sour",
        brewery_id="batch-brewing",
        style="Sour",
        abv=4.5,
        description="Tart lemonade sour",
        release_date=_now - timedelta(days=3),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-005",
        name="Funky Fruit Punch",
        brewery_id="batch-brewing",
        style="Fruited Sour",
        abv=5.5,
        description="Tropical fruit sour",
        release_date=_now - timedelta(days=1),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-006",
        name="Camperdown 1",
        brewery_id="wayward-brewing",
        style="Pale Ale",
        abv=5.2,
        description="Classic Australian pale",
        release_date=_now - timedelta(days=45),
        is_new_release=False
    ),
    Beer(
        id="beer-007",
        name="Raspberry Berliner",
        brewery_id="wayward-brewing",
        style="Berliner Weisse",
        abv=3.8,
        description="Light and fruity sour",
        release_date=_now - timedelta(days=4),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-008",
        name="Serpent's Kiss",
        brewery_id="grifter-brewing",
        style="Watermelon Pilsner",
        abv=4.6,
        description="Refreshing summer beer",
        release_date=_now - timedelta(days=20),
        is_new_release=False
    ),
    Beer(
        id="beer-009",
        name="The Champ",
        brewery_id="grifter-brewing",
        style="Pale Ale",
        abv=5.6,
        description="Hoppy session pale",
        release_date=_now - timedelta(days=6),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-010",
        name="Conviction Pale",
        brewery_id="the-rocks-brewing",
        style="Pale Ale",
        abv=4.8,
        description="Balanced English-style pale",
        release_date=_now - timedelta(days=7),  # NEW (just made it!)
        is_new_release=True
    ),
    Beer(
        id="beer-011",
        name="Hart of the Rocks",
        brewery_id="the-rocks-brewing",
        style="IPA",
        abv=6.2,
        description="Classic West Coast IPA",
        release_date=_now - timedelta(days=60),
        is_new_release=False
    ),
    # NEW BEERS - Bracket Brewing
    Beer(
        id="beer-012",
        name="Double Bracket IPA",
        brewery_id="bracket-brewing",
        style="DDH IPA",
        abv=7.2,
        description="Double dry-hopped with Citra and Mosaic",
        release_date=_now - timedelta(days=2),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-013",
        name="Sour Bracket",
        brewery_id="bracket-brewing",
        style="Kettle Sour",
        abv=4.8,
        description="Raspberry and passionfruit kettle sour",
        release_date=_now - timedelta(days=5),  # NEW
        is_new_release=True
    ),
    # NEW BEERS - Future Brewing
    Beer(
        id="beer-014",
        name="Future Perfect",
        brewery_id="future-brewing",
        style="Triple IPA",
        abv=10.5,
        description="Hazy triple IPA with notes of pineapple and stone fruit",
        release_date=_now - timedelta(days=3),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-015",
        name="Time Dilation",
        brewery_id="future-brewing",
        style="Cold IPA",
        abv=6.8,
        description="Crisp, clean cold IPA with lager yeast",
        release_date=_now - timedelta(days=1),  # NEW
        is_new_release=True
    ),
    # NEW BEERS - Range Brewing
    Beer(
        id="beer-016",
        name="Origin Story",
        brewery_id="range-brewing",
        style="DDH IPA",
        abv=6.8,
        description="Hazy IPA with Galaxy and Enigma hops",
        release_date=_now - timedelta(days=4),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-017",
        name="Infinite Range",
        brewery_id="range-brewing",
        style="Imperial Stout",
        abv=12.0,
        description="Barrel-aged imperial stout with vanilla and coffee",
        release_date=_now - timedelta(days=10),
        is_new_release=False
    ),
    # NEW BEERS - Mountain Culture
    Beer(
        id="beer-018",
        name="Status Quo",
        brewery_id="mountain-culture",
        style="Pale Ale",
        abv=5.2,
        description="Easy drinking pale ale with citrus notes",
        release_date=_now - timedelta(days=15),
        is_new_release=False
    ),
    Beer(
        id="beer-019",
        name="Cult IPA",
        brewery_id="mountain-culture",
        style="IPA",
        abv=6.5,
        description="West Coast style IPA, piney and resinous",
        release_date=_now - timedelta(days=6),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-020",
        name="The Third Eye",
        brewery_id="mountain-culture",
        style="DDH NEIPA",
        abv=7.0,
        description="Juicy, hazy, tropical bomb",
        release_date=_now - timedelta(days=2),  # NEW
        is_new_release=True
    ),
    # NEW BEERS - Kicks Brewing
    Beer(
        id="beer-021",
        name="Kickflip IPA",
        brewery_id="kicks-brewing",
        style="IPA",
        abv=6.2,
        description="Sessionable IPA with citrus and pine",
        release_date=_now - timedelta(days=5),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-022",
        name="Heelflip Hazy",
        brewery_id="kicks-brewing",
        style="NEIPA",
        abv=6.5,
        description="Hazy IPA with mango and passionfruit",
        release_date=_now - timedelta(days=3),  # NEW
        is_new_release=True
    ),
    # NEW BEERS - 4 Pines
    Beer(
        id="beer-023",
        name="Freshy Extra Refreshing Ale",
        brewery_id="4-pines",
        style="Golden Ale",
        abv=3.5,
        description="Ultra sessionable, crisp and refreshing",
        release_date=_now - timedelta(days=45),
        is_new_release=False
    ),
    Beer(
        id="beer-024",
        name="Keller Door: Hazy IPA",
        brewery_id="4-pines",
        style="Hazy IPA",
        abv=6.0,
        description="Limited release hazy with tropical hops",
        release_date=_now - timedelta(days=4),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-025",
        name="Brookvale Union Ginger Beer",
        brewery_id="4-pines",
        style="Ginger Beer",
        abv=4.0,
        description="Spicy ginger beer with a kick",
        release_date=_now - timedelta(days=60),
        is_new_release=False
    ),
    # NEW BEERS - White Bay
    Beer(
        id="beer-026",
        name="White Bay Lager",
        brewery_id="white-bay",
        style="Lager",
        abv=4.5,
        description="Crisp, clean Australian lager",
        release_date=_now - timedelta(days=20),
        is_new_release=False
    ),
    Beer(
        id="beer-027",
        name="Bicycle Beer",
        brewery_id="white-bay",
        style="Pale Ale",
        abv=4.2,
        description="Easy drinking session ale",
        release_date=_now - timedelta(days=3),  # NEW
        is_new_release=True
    ),
    Beer(
        id="beer-028",
        name="Underground IPA",
        brewery_id="white-bay",
        style="IPA",
        abv=6.5,
        description="West Coast style with firm bitterness",
        release_date=_now - timedelta(days=6),  # NEW
        is_new_release=True
    ),
]

# Sample social media posts from venues
SYDNEY_POSTS = [
    SocialPost(
        id="post-001",
        venue_id="young-henrys",
        platform="instagram",
        content="🍺 NEW RELEASE! Newtown Jets IPA just dropped! Fresh hazy with notes of mango and passionfruit. On tap now! #newrelease #hazyipa #newtown",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-001"],
        post_url="https://instagram.com/p/abc123"
    ),
    SocialPost(
        id="post-002",
        venue_id="batch-brewing",
        platform="instagram",
        content="Three new sours hitting the taps this week! Lemonade Sour, Funky Fruit Punch and our collab with @friends. Come try them all! 🍋🍓",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-004", "beer-005"],
        post_url="https://instagram.com/p/def456"
    ),
    SocialPost(
        id="post-003",
        venue_id="wayward-brewing",
        platform="instagram",
        content="Weekend vibes with our Raspberry Berliner 🍇 Light, tart, and perfect for summer afternoons. Just released!",
        posted_at=_now - timedelta(days=4),
        mentions_beers=["beer-007"],
        post_url="https://instagram.com/p/ghi789"
    ),
    SocialPost(
        id="post-004",
        venue_id="grifter-brewing",
        platform="instagram",
        content="The Champ is back and better than ever! New batch of our Pale Ale just packaged 📦",
        posted_at=_now - timedelta(days=5),
        mentions_beers=["beer-009"],
        post_url="https://instagram.com/p/jkl012"
    ),
    SocialPost(
        id="post-005",
        venue_id="the-rocks-brewing",
        platform="instagram",
        content="Conviction Pale returns to the lineup. A true Sydney classic reborn. #paleale #craftbeer #sydney",
        posted_at=_now - timedelta(days=6),
        mentions_beers=["beer-010"],
        post_url="https://instagram.com/p/mno345"
    ),
    # NEW POSTS - Bracket Brewing
    SocialPost(
        id="post-009",
        venue_id="bracket-brewing",
        platform="instagram",
        content="Double Bracket IPA is here! DDH with Citra and Mosaic, expect tropical fruit salad in a glass 🥭🍍 #DDHIPA #craftbeer #marrickville",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-012"],
        post_url="https://instagram.com/p/bra001"
    ),
    SocialPost(
        id="post-010",
        venue_id="bracket-brewing",
        platform="instagram",
        content="Sour Bracket just landed! Raspberry + passionfruit kettle sour, perfect for these hot days ☀️ #sourbeer #kettlesour",
        posted_at=_now - timedelta(days=5),
        mentions_beers=["beer-013"],
        post_url="https://instagram.com/p/bra002"
    ),
    # NEW POSTS - Future Brewing
    SocialPost(
        id="post-011",
        venue_id="future-brewing",
        platform="instagram",
        content="Future Perfect Triple IPA 10.5% - our biggest beer yet! Pineapple, stone fruit, and dangerous drinkability 🚀 #tripleipa #hazyipa",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-014"],
        post_url="https://instagram.com/p/fut001"
    ),
    SocialPost(
        id="post-012",
        venue_id="future-brewing",
        platform="instagram",
        content="Time Dilation Cold IPA - crisp, clean, hoppy. Fermented with lager yeast for maximum crushability ❄️ #coldipa #crisp",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-015"],
        post_url="https://instagram.com/p/fut002"
    ),
    # NEW POSTS - Mountain Culture
    SocialPost(
        id="post-013",
        venue_id="mountain-culture",
        platform="instagram",
        content="Cult IPA fresh batch! West Coast vibes - pine, resin, and bitterness in perfect harmony 🌲 #westcoastipa #cultipa",
        posted_at=_now - timedelta(days=6),
        mentions_beers=["beer-019"],
        post_url="https://instagram.com/p/mc001"
    ),
    SocialPost(
        id="post-014",
        venue_id="mountain-culture",
        platform="instagram",
        content="The Third Eye DDH NEIPA just dropped! Open your mind to the tropical juice bomb 🧿🍊 #ddh #neipa #tropical",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-020"],
        post_url="https://instagram.com/p/mc002"
    ),
    # NEW POSTS - Kicks Brewing
    SocialPost(
        id="post-015",
        venue_id="kicks-brewing",
        platform="instagram",
        content="Kickflip IPA is back! Our sessionable IPA with citrus and pine notes. Perfect for after a skate session 🛹 #kickflip #ipa #skate",
        posted_at=_now - timedelta(days=5),
        mentions_beers=["beer-021"],
        post_url="https://instagram.com/p/kic001"
    ),
    SocialPost(
        id="post-016",
        venue_id="kicks-brewing",
        platform="instagram",
        content="Heelflip Hazy - our newest NEIPA with mango and passionfruit vibes 🥭🛹 #hazyipa #heelflip #craftbeer",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-022"],
        post_url="https://instagram.com/p/kic002"
    ),
    # NEW POSTS - Hotel Sweeney's
    SocialPost(
        id="post-017",
        venue_id="hotel-sweeneys",
        platform="instagram",
        content="Fresh @mountainculturebeerco The Third Eye and @futurebrewing Future Perfect just went on tap! Come get your hop fix in the CBD 🍺",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-020", "beer-014"],
        post_url="https://instagram.com/p/swe001"
    ),
    SocialPost(
        id="post-018",
        venue_id="hotel-sweeneys",
        platform="instagram",
        content="This weekend at Sweeney's: @kicksbrewing Kickflip IPA on tap + live music from 8pm Friday! 🎸🍻 #sydneybeer #livemusic",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-021"],
        post_url="https://instagram.com/p/swe002"
    ),
    # NEW POSTS - 4 Pines
    SocialPost(
        id="post-019",
        venue_id="4-pines",
        platform="instagram",
        content="Keller Door Hazy IPA is back! Limited release with tropical hop character and a smooth finish 🌴🍺 #kellerdoor #hazyipa #4pines",
        posted_at=_now - timedelta(days=4),
        mentions_beers=["beer-024"],
        post_url="https://instagram.com/p/4p001"
    ),
    # NEW POSTS - White Bay
    SocialPost(
        id="post-020",
        venue_id="white-bay",
        platform="instagram",
        content="Bicycle Beer is rolling out fresh this week! Our session pale ale perfect for summer rides 🚲🍺 #bicyclebeer #sessionable #rozelle",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-027"],
        post_url="https://instagram.com/p/wb001"
    ),
    SocialPost(
        id="post-021",
        venue_id="white-bay",
        platform="instagram",
        content="Underground IPA just surfaced! West Coast style with resinous pine and citrus bitterness 🌲 #undergroundipa #westcoast",
        posted_at=_now - timedelta(days=6),
        mentions_beers=["beer-028"],
        post_url="https://instagram.com/p/wb002"
    ),
    # NEW POSTS - JB and Sons
    SocialPost(
        id="post-022",
        venue_id="jb-and-sons",
        platform="instagram",
        content="Taps are looking good! Fresh @4pinesbeer Keller Door Hazy and @whitebaybeerco Bicycle Beer now pouring 🍻 #crowsnest #craftbeer",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-024", "beer-027"],
        post_url="https://instagram.com/p/jb001"
    ),
    SocialPost(
        id="post-023",
        venue_id="jb-and-sons",
        platform="instagram",
        content="Game day specials! $10 pints of @younghenrys all day while the footy is on 📺🏈 #gameday #sportspub #newtownjetsipa",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-001"],
        post_url="https://instagram.com/p/jb002"
    ),
    # NEW POSTS - Noble Hops
    SocialPost(
        id="post-024",
        venue_id="noble-hops",
        platform="instagram",
        content="New sour lineup! @bracketbrewing Sour Bracket and @batchbrewing Lemonade Sour both on tap 🍋 #sourbeer #redfern #craftbeer",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-013", "beer-004"],
        post_url="https://instagram.com/p/nh001"
    ),
    SocialPost(
        id="post-025",
        venue_id="noble-hops",
        platform="instagram",
        content="@mountainculturebeerco The Third Eye now pouring! Come taste what all the Blue Mountains hype is about 👁️🍺 #mountainculture #neipa",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-020"],
        post_url="https://instagram.com/p/nh002"
    ),
    # NEW POSTS - Union Hotel
    SocialPost(
        id="post-026",
        venue_id="union-hotel",
        platform="instagram",
        content="Live music tonight in the beer garden! Fresh @grifterbrewing The Champ and @waywardbrewing Raspberry Berliner on tap 🎸🍺 #newtown",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-009", "beer-007"],
        post_url="https://instagram.com/p/uh001"
    ),
    SocialPost(
        id="post-027",
        venue_id="union-hotel",
        platform="instagram",
        content="Sunday session vibes! @kicksbrewing Heelflip Hazy just tapped and it's tasting amazing 🛹🍺 #sundaysession #hazyipa #newtown",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-022"],
        post_url="https://instagram.com/p/uh002"
    ),
    # NEW POSTS - Bitter Phew
    SocialPost(
        id="post-028",
        venue_id="bitter-phew",
        platform="instagram",
        content="Triple IPA alert! @futurebrewing Future Perfect 10.5% now pouring. Approach with caution ⚠️🚀 #tripleipa #futurebrewing #darlinghurst",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-014"],
        post_url="https://instagram.com/p/bp001"
    ),
    SocialPost(
        id="post-029",
        venue_id="bitter-phew",
        platform="instagram",
        content="Sour Sunday! @bracketbrewing Sour Bracket and @batchbrewing Funky Fruit Punch both pouring now 🍓🍋 #sourbeer #sunday",
        posted_at=_now - timedelta(days=4),
        mentions_beers=["beer-013", "beer-005"],
        post_url="https://instagram.com/p/bp002"
    ),
    # NEW POSTS - Harts Pub
    SocialPost(
        id="post-030",
        venue_id="harts-pub",
        platform="instagram",
        content="Historic pub, modern beer! @whitebaybeerco Underground IPA and @4pinesbeer Keller Door now on tap #therocks #craftbeer #heritage",
        posted_at=_now - timedelta(days=3),
        mentions_beers=["beer-028", "beer-024"],
        post_url="https://instagram.com/p/hart001"
    ),
    SocialPost(
        id="post-031",
        venue_id="harts-pub",
        platform="instagram",
        content="Cask ale Wednesday! Plus fresh @grifterbrewing The Champ on the craft taps 🍺 #caskale #therocks #sydney",
        posted_at=_now - timedelta(days=5),
        mentions_beers=["beer-009"],
        post_url="https://instagram.com/p/hart002"
    ),
    # EXISTING POSTS - Bars mentioning beers
    SocialPost(
        id="post-006",
        venue_id="blood-orange-liquor",
        platform="instagram",
        content="Now pouring: @younghenrys Newtown Jets IPA and @batchbrewing Eskimo Juice. Fresh hazy vibes all week! 🍻",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-001", "beer-003"],
        post_url="https://instagram.com/p/pqr678"
    ),
    SocialPost(
        id="post-007",
        venue_id="the-tilbury",
        platform="instagram",
        content="New sour selection on tap! Come try the latest from @batchbrewing and @waywardbrewing",
        posted_at=_now - timedelta(days=2),
        mentions_beers=["beer-004", "beer-007"],
        post_url="https://instagram.com/p/stu901"
    ),
    SocialPost(
        id="post-008",
        venue_id="ddc",
        platform="instagram",
        content="Live music tonight + fresh @grifterbrewing The Champ on tap! 8pm start 🎸🍺",
        posted_at=_now - timedelta(days=1),
        mentions_beers=["beer-009"],
        post_url="https://instagram.com/p/vwx234"
    ),
]


# ==================== DYNAMIC DATA LOADING ====================

def load_dynamic_data():
    """Load dynamic updates from scraper/manual entries."""
    import json
    from pathlib import Path
    
    dynamic_file = Path(__file__).parent / "data" / "dynamic_updates.json"
    
    if not dynamic_file.exists():
        return [], []
    
    try:
        with open(dynamic_file) as f:
            data = json.load(f)
        
        beers = []
        posts = []
        
        # Load manual beers
        for beer_data in data.get("manual_beers", []):
            try:
                # Parse release date
                release_date = datetime.fromisoformat(beer_data["release_date"].replace('Z', '+00:00'))
                # Check if still "new" (within 7 days)
                is_new = (datetime.now() - release_date).days <= 7
                
                beers.append(Beer(
                    id=beer_data["id"],
                    name=beer_data["name"],
                    brewery_id=beer_data["brewery_id"],
                    style=beer_data.get("style"),
                    abv=beer_data.get("abv"),
                    description=beer_data.get("description"),
                    release_date=release_date,
                    is_new_release=is_new
                ))
            except Exception as e:
                print(f"Error loading beer {beer_data.get('id')}: {e}")
        
        # Load scraped posts
        for post_data in data.get("posts", []):
            try:
                # Use posted_at, scraped_at, or now
                date_str = post_data.get("posted_at") or post_data.get("scraped_at")
                if date_str:
                    posted_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    posted_at = datetime.now()
                
                # Skip posts older than 14 days
                if (datetime.now() - posted_at).days > 14:
                    continue
                
                posts.append(SocialPost(
                    id=post_data.get("id", f"dynamic-{posted_at.timestamp()}"),
                    venue_id=post_data["venue_id"],
                    platform=post_data.get("platform", "unknown"),
                    content=post_data["content"],
                    posted_at=posted_at,
                    mentions_beers=post_data.get("mentions_beers", []),
                    post_url=post_data.get("post_url")
                ))
            except Exception as e:
                print(f"Error loading post: {e}")
        
        return beers, posts
        
    except Exception as e:
        print(f"Error loading dynamic data: {e}")
        return [], []

# Merge dynamic data
_DYNAMIC_BEERS, _DYNAMIC_POSTS = load_dynamic_data()

# Add dynamic beers to list (avoiding duplicates by ID)
_existing_ids = {b.id for b in SYDNEY_BEERS}
for beer in _DYNAMIC_BEERS:
    if beer.id not in _existing_ids:
        SYDNEY_BEERS.append(beer)

# Add dynamic posts to list
_existing_post_ids = {p.id for p in SYDNEY_POSTS}
for post in _DYNAMIC_POSTS:
    if post.id not in _existing_post_ids:
        SYDNEY_POSTS.append(post)

print(f"[Data] Loaded {len(_DYNAMIC_BEERS)} dynamic beers, {len(_DYNAMIC_POSTS)} dynamic posts")
