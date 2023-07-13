import random

Name = "Character"

ParamExtra = "character_extra"
ParamFromUI = "from_webui"
ParamMultiEnabled = "multi_enabled"
ParamMultiCount = "multi_count"
ParamMultiSameSeed = "multi_same_seed"
ParamImage = "image_i2i"
ParamTryOnCloth = "image_tryon_cloth"
ParamTryOnModel = "image_tryon_model"
ParamControlNet0 = "image_cn_0"
ParamIgnoreCaption = "ignore_caption"

# 物品识别和重绘
ParamSegmentLabels = "segment_labels"
ParamSegmentErase = "segment_erase"

ParamRepairFace = "repair_face"
ParamFormat = "response_format"

# 年龄
ParamIgnoreAge = "ignore_age"

# 扩展参数名字
ExtraImageCaption = "image-caption"
ExtraHasIllegalWords = "has-illegal-words"

# 各种组件
ExNameT2I = "Character Text2Image"
ExNameI2I = "Character Image2Image"
ExNameTryOn = "Character TryOn"
ExNameEffects = "Character Effects"
ExNameInfo = "Character Info"

# 各种组件的执行顺序
ExIndexInfo = -1
ExIndexEffects = -2
ExIndexTryOn = -3
ExIndexFaceEditor = -4

sights = {
    "Abandoned Factory": "Rusty machinery, echoing silence, broken windows, overgrown vegetation, dust-covered assembly line, creeping shadows, industrial decay, metallic echoes, stray wildlife, forgotten relics",
    "Abandoned Space Station": "Drifting debris, flickering lights, eerie silence, weightless environment, ominous warning signs, claustrophobic corridors, zero-g artifacts, decompressed modules, technological ruins, mysterious malfunctions",
    "Alien Desert": "Otherworldly plants, shifting sands, unknown constellations, unusual rock formations, strange creatures, harsh environment, alien oasis, colorful dunes, mysterious ruins, extraterrestrial survival",
    "Alpine Meadow": "Vast expanses of green, wildflowers in bloom, distant snow-capped peaks, bleating mountain goats, fresh breezes, gentle streams, sunlit valleys, tranquility, challenging hikes, peaceful picnics",
    "Ancient City": "Historical traces, ancient architecture, folk tales, echoes on cobblestone streets, rich cultural atmosphere, tales from dynasties, scenic beauty, unique marketplaces, charming sights, historical sedimentation",
    "Arctic Tundra": "Bitter cold, northern lights, endless white, migrating reindeer, igloo villages, hardy flora and fauna, blizzard threats, ice crackling, isolated explorers, vast solitude",
    "Astral Plane": "Otherworldly colors, starry expanses, floating islands, alien constellations, celestial creatures, ethereal energy, shifting realities, spiritual essence, interdimensional portals, infinite exploration",
    "Bamboo Forest": "Towering bamboo, rustling leaves, peaceful pandas, gentle winds, tranquil paths, filtered sunlight, bird songs, rustling grove, stone lanterns, zen atmosphere",
    "Castle": "Heavy stone walls, towering spires, mysterious dungeons, opulent decorations, ancient stories, glorious knights, dense secret passages, echoing armor sounds, rusty cannons, past splendor",
    "City": "Bustling streets, modern architecture, diverse crowds, hectic pace of life, neon lights at night, various entertainment facilities, historical landmarks, casual chats in coffee shops, urban noise, opportunities and challenges",
    "Clockwork Castle": "Ticking clocks, winding gears, mechanical servants, pendulum swings, brass and copper, hidden compartments, steam-powered contraptions, precise timekeeping, ornate detailing, rhythmic sounds",
    "Coral Reef": "Colorful corals, diverse marine life, tranquil turquoise waters, hidden caves, bright sunbeams, shipwrecks and relics, underwater currents, beauty and fragility, saltwater scent, peaceful floating",
    "Coral Reef V2": "Colorful corals, exotic fish, waving sea anemones, sunken treasures, curious sea turtles, shimmering schools of fish, vibrant underwater flora, hidden caves, dappled sunlight, crystal clear water",
    "Crystal Cavern": "Sparkling formations, rainbow-like reflections, towering geodes, secret passages, mysterious glow, cool air, hidden pools, fairy-like atmosphere, echoing footsteps, magical minerals",
    "Crystal Palace": "Gleaming chandeliers, polished floors, mirrored walls, prismatic light, beautiful reflections, grand banquets, opulent details, garden views, shimmering elegance, echoing footsteps",
    "Cybernetic City": "Gleaming cyborgs, high-tech infrastructure, neon holograms, dizzying data streams, perpetual nightlife, bustling streets, futuristic vehicles, virtual realities, towering data hubs, sprawling networks",
    "Cybernetic Ruins": "Broken androids, flashing holograms, corroded metal structures, digital echoes, overgrown tech, malfunctioning machines, remnants of AI, exposed wiring, towering monoliths, eerie silence",
    "Cyberpunk City": "Neon lights, towering skyscrapers, bustling night markets, flying vehicles, augmented humans, digital billboards, dystopian atmosphere, hidden alleys, advanced tech, underground movements",
    "Deep Sea Trench": "Bioluminescent creatures, crushing pressures, silhouetted leviathans, cold darkness, hydrothermal vents, alien environment, seafloor ridges, submarine explorers, mysterious chasms, eerie silence",
    "Desert": "Endless sand dunes, scorching sun, mirage, threats of sandstorms, morning tranquility, rare oases, sparse life, magnificent sunrises and sunsets, perfect solitude, awe-inspiring openness",
    "Dinosaur Era": "Strong dinosaurs, verdant forests, primal ecosystems, violent predation, dangerous environment, mysterious fossils, giant eggshells, overflowing vitality, fear and excitement, survival challenges",
    "Dragon's Lair": "Glittering treasure, scorched bones, ominous echoes, claw marks, cavernous space, smoky air, slumbering dragon, hidden exit, ancient legends, eerie quiet",
    "Dreamworld": "Shifting landscapes, surreal structures, impossible physics, dream creatures, fluid reality, ethereal beauty, subconscious symbols, lucid control, abstract concepts, timeless space",
    "Elven Kingdom": "Graceful architecture, ancient trees, crystal clear rivers, majestic palaces, enchanted glades, magical fauna and flora, harmonious life, skilled craftsmen, artistic elegance, tranquil atmosphere",
    "Enchanted Forest": "Mysterious woodland creatures, glowing flowers, whispering trees, magical springs, elusive unicorns, sparkling fairy dust, ancient tree homes, labyrinthine paths, starlit clearings, enchanting melodies",
    "Fairy Ring": "Mushroom circle, pixie dust, soft glow, whispering flora, nocturnal music, enchanted dances, magical festivities, miniature feasts, tiny creatures, moonlit rituals",
    "Fairy Village": "Tiny houses, mushroom stools, sparkling lights, flower petal roofs, buzzing dragonflies, magical tree hollows, cheerful music, dewdrop refreshments, small footpaths, enchanted inhabitants",
    "Fantasy Bazaar": "Colorful stalls, mythical items, mystical vendors, enchanted artifacts, rare creatures, magical aromas, haggling wizards, bustling crowd, exotic goods, tantalizing potions",    
    "Floating City": "Sky-high skyscrapers, airborne traffic, cloud parks, panoramic views, vertigo-inducing heights, airborne vessels, lofty towers, hover platforms, advanced tech, clean energy",
    "Flower Meadow": "Blooming wildflowers, soft grass underfoot, honeybees buzzing, colorful butterflies, gentle breeze, tranquil picnic, sunny tranquility, vibrant colors, fresh floral scent, serene sounds",
    "Forest": "Dense trees, vibrant life, sunlight filters through, distant bird calls, clear streams, autumn leaves, spring buds, winter snowscapes, solitary trails, forest secrets",
    "Futuristic Metropolis": "Advanced technology, gleaming skyscrapers, flying cars, neon signage, diversity of alien species, high-tech devices, artificial intelligence, crowded skyways, endless opportunities, bright future",
    "Futuristic Spaceport": "Docked spaceships, bustling crowds, intergalactic travelers, alien vendors, hovercrafts, exotic goods, neon signs, advanced tech, interstellar journeys, panoramic star views",
    "Futuristic Suburb": "Smart homes, autonomous vehicles, robot servants, manicured lawns, virtual playgrounds, neighborhood drones, clean energy, suburban quiet, solar panel roofs, advanced security",
    "Ghost Town": "Abandoned buildings, dusty streets, silence and eeriness, remnants of life, whispers of the past, faded signs, broken windows, haunting wind, mystery and secrets, solitude",
    "Ghost Town V2": "Boarded-up buildings, tumbleweeds, eerie silence, dilapidated saloon, rusting sheriff’s badge, faded signs, abandoned belongings, crumbling chapel, dust-covered streets, haunting past",
    "Giant Anthill": "Endless tunnels, busy ants, queen's chamber, eggs and larvae, constant activity, pheromone trails, strategic defense, food storage, complex society, organized chaos",
    "Giant's Castle": "Oversized furniture, towering walls, large footprints, echoing roars, monstrous pets, gigantic feasts, king-sized armor, enormous treasures, hidden passages, looming danger",
    "Glacier": "Massive icebergs, blue ice caves, heavy snow, dazzling sunlight reflections, unique ecosystems, sounds of ice cracking, majestic, cruel beauty, centuries of silence, cliff edges",
    "Gnome Village": "Underground burrows, lush gardens, stone pathways, animal friends, whimsical gadgets, mushroom umbrellas, cozy interiors, communal meals, hardworking inhabitants, hidden entrances",
    "Goblin Market": "Cluttered stalls, exotic wares, unusual smells, haggling creatures, hanging lanterns, strange delicacies, rusty weapons, bustling atmosphere, raucous laughter, exotic bargains",
    "Grand Canyon": "Steep cliffs, deep valleys, spectacular landscapes, historical traces, roaring river, sunlight pouring in, color changes, unique ecosystem, vivid echoes, exploratory challenges",
    "Haunted Mansion": "Gothic architecture, creaking floorboards, cobweb-filled rooms, mysterious apparitions, echoing laughter, shadowy corners, flickering candlelight, old portraits, chilling atmosphere, spine-tingling encounters",
    "Hidden Oasis": "Palm trees, fresh water, soft sand, desert wildlife, shade under trees, reflected sky, fruit-bearing plants, refreshing swim, solitary peace, unexpected paradise",
    "Ice Age": "Frozen landscapes, massive glaciers, woolly mammoths, frost-covered trees, icy caves, survival struggles, primitive humans, haunting wind, pure white snow, harsh beauty",
    "Ice Cavern": "Glittering icicles, frozen lake, echoing drips, frosty air, slippery paths, hidden crevices, crystal formations, hibernating creatures, cold isolation, mysterious echoes",
    "Japanese Tea Garden": "Tranquil pond, ornate tea house, rustling bamboo, stone lanterns, koi fish, cherry blossom trees, stepping stone paths, spiritual harmony, peaceful reflections, tea ceremony",
    "Jungle Temple": "Hidden among dense foliage, sacred statues, stone steps overrun by vines, echoing animal calls, ancient rituals, forgotten gods, mossy carvings, shadowy chambers, decaying splendor, vibrant parrots",
    "Jungle Waterfall": "Roaring cascades, rainbow mist, moss-covered rocks, tropical birds, refreshing pools, hidden caves, verdant foliage, dappled sunlight, serene tranquility, rushing water sounds",
    "Lava Zone": "Blistering magma, crustal fractures, volcanic eruptions, sweltering air, dark rocks, endless scorched earth, dangerous environment, glaring red light, tenacity of life, elemental clashes",
    "Lighthouse Island": "Vast ocean, towering lighthouse, eternal light, lonely lighthouse keeper, seagull cries, waves crashing, desolate environment, shells on the beach, pitch-black night, guiding hope",
    "Lost City of Atlantis": "Sunken ruins, marine life, hidden treasures, mysterious glyphs, ancient technologies, eerie silence, submerged palaces, underwater currents, aquatic mysteries, forgotten civilization",
    "Lost Civilization": "Ruined temples, overgrown jungle, forgotten lore, ancient artifacts, mossy stone statues, glyphs and inscriptions, abandoned homes, crumbling infrastructures, hidden traps, spirit of exploration",
    "Magical School": "Whispering portraits, shifting staircases, floating candles, ancient spell books, magical creatures, broomstick flying lessons, enchanted artifacts, mystical lessons, towering turrets, magical mischief",
    "Mars Colony": "Reddish landscapes, advanced life-support systems, remote greenhouses, terraformed areas, rough Martian terrains, astronauts in suits, interstellar pioneers, challenging survival, barren beauty, alien sunsets",
    "Medieval Tournament": "Colorful pavilions, jousting knights, bustling crowds, heraldic banners, cheering spectators, elegant ladies, armored duelists, regal king and queen, thrilling competitions, noble chivalry",
    "Misty Mountain": "Fog-covered peaks, slippery paths, echo of distant animals, dew-drenched grass, shadowy shapes, hidden valleys, obscured vision, cool mist, quiet isolation, eerie echoes",
    "Moon Base": "Futuristic habitats, lunar dust, Earthrise, sparse vegetation, technological marvels, extraterrestrial research, resource mining, desolate expanse, low gravity, silence of the void",
    "Moon": "Barren landscapes, tiny Earth in the sky, weightless leaps, secrets within the lunar crust, silent moon base, dark starry sky, vast impact craters, cool scientific exploration, tracks of lunar rovers, endless silence",
    "Mountain": "Majestic peaks, fresh air, risky routes, breathtaking sunrises, thick snow, winding mountain roads, tranquil valleys, challenging climbs, victory at the summit, endless horizon",
    "Mysterious Island": "Breezy coconut palms, white sandy beaches, crystal clear waters, mysterious relics, abundant marine life, undulating mountains, tropical rainforest, adventurous exploration, unique landscapes, hidden treasures",
    "Mystic Graveyard": "Crooked tombstones, shadowy figures, ancient crypts, whispering winds, gothic gates, spectral apparitions, moonlit paths, eerie tranquility, hallowed ground, forgotten stories",
    "Old Library": "Musty parchment smell, towering bookshelves, dust motes in sunbeams, hidden scrolls, whispering echoes, secret doorways, ancient tomes, creaking wooden floors, cozy reading corners, hushed reverence",
    "Olympus": "Majestic palaces, immortals feasting, golden ambrosia, mythic creatures, view of the cosmos, divine gardens, whispering muses, awe-inspiring peaks, sacred ground, godly affairs",
    "Pirate Cove": "Hidden harbor, wooden dock, smuggled treasure, bonfire stories, secluded beach, scurrying crabs, rum-filled barrels, piratical hideout, tropical foliage, restless sea",
    "Pirate Ship": "Creaking timbers, snapping sails, bustling deck, treasure, boisterous crew, salty sea air, vast horizon, fierce sea battles, swaying hammocks, calls of 'ahoy'",
    "Post-apocalyptic City": "Crumbling buildings, overgrown streets, survivors' graffiti, haunting silence, scarce resources, remnants of past glory, hopeful survivors, rusting vehicles, harsh survival, signs of renewal",
    "Prairie": "Expansive views, rich fauna and flora, spring wildflowers, sound of wind, free herd of horses, autumnal gold, dawn and dusk, migrating birds, tranquil pastoral songs, endless journeys",
    "Pyramid Interior": "Mysterious hieroglyphs, flickering torchlight, ominous echoes, sacred burial chamber, gold treasures, hidden traps, winding corridors, ancient secrets, spiritual aura, stifling air",
    "Rainforest": "Thick green jungle, vibrant scent, dappled sunlight, biodiversity, endless natural sounds, dense canopy, cool air, tranquil waterfalls, teeming ecosystems, freshness after rain",
    "Savannah": "Tall golden grasses, acacia trees silhouettes, hot sun, dust kicked by wildebeest, distant roar of lions, watering holes, grand migrations, ant mounds, wide-open vistas, endless horizons",
    "Secluded Monastery": "Ancient scriptures, chanting monks, tranquil gardens, hilltop vistas, peaceful meditation, rustic buildings, fresh mountain air, sacred rituals, serene lifestyle, spiritual wisdom",
    "Sky Kingdom": "Floating islands, ethereal creatures, azure skies, soaring towers, rainbow bridges, clouds as ground, dizzying heights, magical winds, panoramic vistas, aerial adventures",
    "Space Market": "Alien vendors, exotic goods, bustling crowds, interspecies interactions, neon signs, hovering stalls, exotic foods, tech bargains, unique commodities, lively atmosphere",
    "Space": "Boundless starry sky, mysterious black holes, deafening silence, splendid nebulas, icy asteroids, unknown lifeforms, weightless environment, enchanting cosmic views, sci-fi space stations, lone astronauts",
    "Spaceship Junkyard": "Derelict spacecraft, rusted metal, scavenged parts, hidden treasures, rogue robots, alien tech, drifting debris, forgotten histories, interstellar relics, hazardous wastes",
    "Spider Web": "Intricate webbing, glistening dewdrops, trapped prey, lurking spider, quiet patience, sticky strands, deadly beauty, suspended danger, spiral patterns, silken threads",
    "Steampunk City": "Victorian architecture, flying airships, brass and gears, bustling markets, intricate machines, steam and smoke, contrast of rich and poor, energetic city life, technological marvels, ingenious inventions",
    "Steampunk Metropolis": "Steam-powered machines, airships, cobblestone streets, Victorian fashion, intricate gears, bustling factories, inventors' workshops, grand clock tower, brass and leather, sooty sky",
    "Stone Circle": "Ancient monoliths, whispering winds, druidic rituals, mystical energy, celestial alignments, historical enigma, mossy stones, archaeological fascination, spiritual resonance, time-worn carvings",
    "Sunken City": "Water-logged buildings, lost culture, dark waters, vibrant sea life, eerie tranquility, forgotten treasures, crumbling statues, encrusted relics, silhouettes in the mist, mysterious legends",
    "Tibetan Plateau": "Endless grasslands, snow-capped peaks, crystal-clear lakes, low houses, Tibetan culture, plateau sunlight, serene monasteries, mysterious rituals, tough Tibetans, endless journeys",
    "Time Machine": "Flashing lights, complex control panel, temporal distortions, glimpses of past and future, whirring gears, spinning dials, chronological chaos, quantum mechanics, disorienting travels, historical explorations",
    "Tropical Beach": "Soft white sand, clear turquoise water, rustling palm fronds, colorful seashells, warm sun, leisurely atmosphere, beach volleyball, cool cocktails, bright bathing suits, soothing waves",
    "Tropical Rainforest": "Dense vegetation, vibrant wildlife, exotic birds, humid climate, twisting vines, towering canopies, hidden trails, distant drumbeats, tropical fruits, teeming biodiversity",
    "Tropical Rainforest V2": "Diverse lifeforms, intense sunlight, deep forests, humid climate, beautiful birds, vibrant flowers, endless green, sound of rain, miracles of life, mysterious indigenous people",
    "Underground Cave": "Endless darkness, damp and cool atmosphere, stalactites and stalagmites, echo of dripping water, bats fluttering, narrow passages, mysterious carvings, eerie silence, luminescent fungi, secret treasures",
    "Undersea": "Deep blue depths, rich marine life, beauty of coral reefs, hidden underwater caves, mysterious shipwrecks, huge underwater canyons, floating jellyfish, lost civilizations, deep-sea explorers, dark abyss",
    "Underwater City": "Bio-luminescent lighting, aquatic architecture, marine citizens, underwater vegetation, oceanic vistas, bubble vehicles, coral buildings, currents as roads, marine culture, floating markets",
    "Urban Rooftops": "Overlooking city views, distant sirens, clandestine meetings, graffiti art, sunset skyline, stealthy movements, pigeon flocks, cool breezes, hidden escape routes, lofty solitude",
    "Victorian London": "Cobblestone streets, foggy alleys, horse-drawn carriages, bustling markets, towering Big Ben, lamplighters, soot-stained buildings, ornate architecture, echo of footsteps, Dickensian spirit",
    "Village": "Peaceful countryside, simple houses, autumn harvest, morning sunlight, shade of old trees, country roads, green fields, rustic atmosphere, sounds of roosters and dogs, leisurely life",
    "Volcanic Island": "Fiery eruptions, black sandy beaches, lush tropical vegetation, wild animal life, smoke-filled sky, rugged cliffs, lava tubes, native tribal culture, incessant rumble, ashes rain",
    "Volcanic Island V2": "Steaming hot springs, black sand beaches, tropical flora, soaring seagulls, lava flows, magma chamber, volcanic rocks, eruptive events, towering volcano, ocean views",
    "War Trench": "Mud and dirt, barbed wire, distant explosions, whispers of soldiers, looming threat, strewn war relics, camaraderie, harsh conditions, adrenaline rush, courageous heroes",
    "Warlock's Tower": "Dusty spell books, flickering candles, mystical artifacts, pentagrams, magical wards, brewing potions, enchanted mirrors, secret rooms, arcane symbols, eerie portraits",
    "Wild West": "Dusty main street, wooden saloons, creaking windmill, distant cacti, blazing sunsets, local sheriff, horseback riders, sound of spurs, tumbleweeds, raw wilderness",
    "Witches' Forest": "Crooked trees, glowing mushrooms, bubbling cauldrons, whispering spirits, magical herbs, ancient rituals, nocturnal creatures, mystical fog, mossy paths, enchanting spells",
    "Zen Garden": "Raked sand patterns, tranquil pond, moss-covered stones, chirping cicadas, peaceful bamboo grove, blooming cherry blossoms, delicate tea ceremony, serene meditations, quiet paths, harmony of elements",
    "Zen Monastery": "Meditation rooms, sand gardens, tranquil waterfall, tea ceremonies, chanting monks, mountain views, martial arts training, peaceful lifestyle, ancient scriptures, spiritual teachings",
}

def random_sights(count = 50):
    values = random.sample(sights.keys(), count)
    return [sights[v] for v in values]