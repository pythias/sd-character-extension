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
    "Alpine Meadow": "Vast expanses of green, wildflowers in bloom, distant snow-capped peaks, bleating mountain goats, fresh breezes, gentle streams, sunlit valleys, tranquility, challenging hikes, peaceful picnics",
    "Ancient City": "Historical traces, ancient architecture, folk tales, echoes on cobblestone streets, rich cultural atmosphere, tales from dynasties, scenic beauty, unique marketplaces, charming sights, historical sedimentation",
    "Castle": "Heavy stone walls, towering spires, mysterious dungeons, opulent decorations, ancient stories, glorious knights, dense secret passages, echoing armor sounds, rusty cannons, past splendor",
    "City": "Bustling streets, modern architecture, diverse crowds, hectic pace of life, neon lights at night, various entertainment facilities, historical landmarks, casual chats in coffee shops, urban noise, opportunities and challenges",
    "Coral Reef": "Colorful corals, diverse marine life, tranquil turquoise waters, hidden caves, bright sunbeams, shipwrecks and relics, underwater currents, beauty and fragility, saltwater scent, peaceful floating",
    "Crystal Cavern": "Sparkling formations, rainbow-like reflections, towering geodes, secret passages, mysterious glow, cool air, hidden pools, fairy-like atmosphere, echoing footsteps, magical minerals",
    "Cybernetic City": "Gleaming cyborgs, high-tech infrastructure, neon holograms, dizzying data streams, perpetual nightlife, bustling streets, futuristic vehicles, virtual realities, towering data hubs, sprawling networks",
    "Desert": "Endless sand dunes, scorching sun, mirage, threats of sandstorms, morning tranquility, rare oases, sparse life, magnificent sunrises and sunsets, perfect solitude, awe-inspiring openness",
    "Dinosaur Era": "Strong dinosaurs, verdant forests, primal ecosystems, violent predation, dangerous environment, mysterious fossils, giant eggshells, overflowing vitality, fear and excitement, survival challenges",
    "Enchanted Forest": "Mysterious woodland creatures, glowing flowers, whispering trees, magical springs, elusive unicorns, sparkling fairy dust, ancient tree homes, labyrinthine paths, starlit clearings, enchanting melodies",
    "Forest": "Dense trees, vibrant life, sunlight filters through, distant bird calls, clear streams, autumn leaves, spring buds, winter snowscapes, solitary trails, forest secrets",
    "Futuristic Metropolis": "Advanced technology, gleaming skyscrapers, flying cars, neon signage, diversity of alien species, high-tech devices, artificial intelligence, crowded skyways, endless opportunities, bright future",
    "Ghost Town": "Abandoned buildings, dusty streets, silence and eeriness, remnants of life, whispers of the past, faded signs, broken windows, haunting wind, mystery and secrets, solitude",
    "Glacier": "Massive icebergs, blue ice caves, heavy snow, dazzling sunlight reflections, unique ecosystems, sounds of ice cracking, majestic, cruel beauty, centuries of silence, cliff edges",
    "Grand Canyon": "Steep cliffs, deep valleys, spectacular landscapes, historical traces, roaring river, sunlight pouring in, color changes, unique ecosystem, vivid echoes, exploratory challenges",
    "Haunted Mansion": "Gothic architecture, creaking floorboards, cobweb-filled rooms, mysterious apparitions, echoing laughter, shadowy corners, flickering candlelight, old portraits, chilling atmosphere, spine-tingling encounters",
    "Ice Age": "Frozen landscapes, massive glaciers, woolly mammoths, frost-covered trees, icy caves, survival struggles, primitive humans, haunting wind, pure white snow, harsh beauty",
    "Jungle Temple": "Hidden among dense foliage, sacred statues, stone steps overrun by vines, echoing animal calls, ancient rituals, forgotten gods, mossy carvings, shadowy chambers, decaying splendor, vibrant parrots",
    "Lava Zone": "Blistering magma, crustal fractures, volcanic eruptions, sweltering air, dark rocks, endless scorched earth, dangerous environment, glaring red light, tenacity of life, elemental clashes",
    "Lighthouse Island": "Vast ocean, towering lighthouse, eternal light, lonely lighthouse keeper, seagull cries, waves crashing, desolate environment, shells on the beach, pitch-black night, guiding hope",
    "Lost Civilization": "Ruined temples, overgrown jungle, forgotten lore, ancient artifacts, mossy stone statues, glyphs and inscriptions, abandoned homes, crumbling infrastructures, hidden traps, spirit of exploration",
    "Moon": "Barren landscapes, tiny Earth in the sky, weightless leaps, secrets within the lunar crust, silent moon base, dark starry sky, vast impact craters, cool scientific exploration, tracks of lunar rovers, endless silence",
    "Mountain": "Majestic peaks, fresh air, risky routes, breathtaking sunrises, thick snow, winding mountain roads, tranquil valleys, challenging climbs, victory at the summit, endless horizon",
    "Mysterious Island": "Breezy coconut palms, white sandy beaches, crystal clear waters, mysterious relics, abundant marine life, undulating mountains, tropical rainforest, adventurous exploration, unique landscapes, hidden treasures",
    "Pirate Ship": "Creaking timbers, snapping sails, bustling deck, treasure maps, boisterous crew, salty sea air, vast horizon, fierce sea battles, swaying hammocks, calls of 'ahoy'",
    "Post-apocalyptic City": "Crumbling buildings, overgrown streets, survivors' graffiti, haunting silence, scarce resources, remnants of past glory, hopeful survivors, rusting vehicles, harsh survival, signs of renewal",
    "Prairie": "Expansive views, rich fauna and flora, spring wildflowers, sound of wind, free herd of horses, autumnal gold, dawn and dusk, migrating birds, tranquil pastoral songs, endless journeys",
    "Rainforest": "Thick green jungle, vibrant scent, dappled sunlight, biodiversity, endless natural sounds, dense canopy, cool air, tranquil waterfalls, teeming ecosystems, freshness after rain",
    "Sky Kingdom": "Floating islands, ethereal creatures, azure skies, soaring towers, rainbow bridges, clouds as ground, dizzying heights, magical winds, panoramic vistas, aerial adventures",
    "Space": "Boundless starry sky, mysterious black holes, deafening silence, splendid nebulas, icy asteroids, unknown lifeforms, weightless environment, enchanting cosmic views, sci-fi space stations, lone astronauts",
    "Steampunk City": "Victorian architecture, flying airships, brass and gears, bustling markets, intricate machines, steam and smoke, contrast of rich and poor, energetic city life, technological marvels, ingenious inventions",
    "Sunken City": "Water-logged buildings, lost culture, dark waters, vibrant sea life, eerie tranquility, forgotten treasures, crumbling statues, encrusted relics, silhouettes in the mist, mysterious legends",
    "Tibetan Plateau": "Endless grasslands, snow-capped peaks, crystal-clear lakes, low houses, Tibetan culture, plateau sunlight, serene monasteries, mysterious rituals, tough Tibetans, endless journeys",
    "Tropical Rainforest": "Diverse lifeforms, intense sunlight, deep forests, humid climate, beautiful birds, vibrant flowers, endless green, sound of rain, miracles of life, mysterious indigenous people",
    "Underground Cave": "Endless darkness, damp and cool atmosphere, stalactites and stalagmites, echo of dripping water, bats fluttering, narrow passages, mysterious carvings, eerie silence, luminescent fungi, secret treasures",
    "Undersea": "Deep blue depths, rich marine life, beauty of coral reefs, hidden underwater caves, mysterious shipwrecks, huge underwater canyons, floating jellyfish, lost civilizations, deep-sea explorers, dark abyss",
    "Village": "Peaceful countryside, simple houses, autumn harvest, morning sunlight, shade of old trees, country roads, green fields, rustic atmosphere, sounds of roosters and dogs, leisurely life",
    "Volcanic Island": "Fiery eruptions, black sandy beaches, lush tropical vegetation, wild animal life, smoke-filled sky, rugged cliffs, lava tubes, native tribal culture, incessant rumble, ashes rain",
    "War Trench": "Mud and dirt, barbed wire, distant explosions, whispers of soldiers, looming threat, strewn war relics, camaraderie, harsh conditions, adrenaline rush, courageous heroes",
    "Zen Garden": "Raked sand patterns, tranquil pond, moss-covered stones, chirping cicadas, peaceful bamboo grove, blooming cherry blossoms, delicate tea ceremony, serene meditations, quiet paths, harmony of elements",
}

def random_sights(count = 16):
    values = random.sample(sights.keys(), count)
    return [sights[v] for v in values]