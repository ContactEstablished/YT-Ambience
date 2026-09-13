// Curated reference facts, not live telemetry. See FACTS-SOURCES.md.
const nasaMars = ['NASA — Mars facts', 'https://science.nasa.gov/mars/facts/'];
const nasaPhobos = ['NASA — Phobos', 'https://science.nasa.gov/mars/moons/phobos/'];
const nasaDeimos = ['NASA — Deimos', 'https://science.nasa.gov/mars/moons/deimos/'];
const orbits = ['JPL — Satellite mean elements', 'https://ssd.jpl.nasa.gov/sats/elem/'];
const landers = ['NASA GISS — Mars landing dates and coordinates', 'https://www.giss.nasa.gov/tools/mars24/help/landers.html'];
const sol = ['NASA/JPL — Mars at a glance', 'https://www.jpl.nasa.gov/news/press_kits/insight/landing/facts/mars-at-a-glance/'];
const mission = (name, path) => [`NASA — ${name}`, `https://science.nasa.gov/mission/${path}/`];
const LANDING_DETAILS = {
  viking1: {
    summary: 'The first fully successful Mars landing opened a new era of surface exploration, returning photographs and studying the atmosphere and soil.',
    details: 'Viking carried a robotic sampling arm and three biology experiments. The experiments revealed unusual soil chemistry, but no clear evidence of living microorganisms.',
    stats: [['Mission type', 'Stationary lander with an accompanying orbiter'], ['Surface operations', 'More than 6 years']],
    events: [['1975-08-20', 'Launched from Cape Canaveral.'], ['1976-07-20', 'Returned the first photograph from the Martian surface.']],
    source: mission('Viking project', 'viking'),
  },
  viking2: {
    summary: 'Viking 2 explored the rocky plains of Utopia Planitia, complementing Viking 1 with a second laboratory on the surface.',
    details: 'The lander and its orbiter studied Mars’s surface and atmosphere. Like Viking 1, its soil biology experiments did not establish that life was present.',
    stats: [['Mission type', 'Stationary lander with an accompanying orbiter'], ['Biology experiments', '3']],
    events: [['1975-09-09', 'Launched from Cape Canaveral.'], ['1980-04-11', 'Last data received from the lander.']],
    source: mission('Viking project', 'viking'),
  },
  pathfinder: {
    summary: 'Pathfinder used airbags to cushion its landing and delivered Sojourner, the first robotic rover to operate on Mars.',
    details: 'The lander and rover examined rocks, soil, and weather. Their observations supported a warmer, wetter Martian past.',
    stats: [['Mission type', 'Lander and Sojourner rover'], ['Sojourner mass', '10.6 kg'], ['Lander images returned', 'More than 16,500']],
    events: [['1996-12-04', 'Launched toward Mars.'], ['1997-09-27', 'Final data transmission.']],
    source: mission('Mars Pathfinder', 'mars-pathfinder'),
  },
  spirit: {
    summary: 'Spirit searched Gusev Crater for clues to past water and found evidence that Mars had once been much wetter.',
    details: 'Spirit and Opportunity were twin mobile geology laboratories. Their robotic arms carried instruments to examine rocks and soil up close.',
    stats: [['Mission type', 'Mars Exploration Rover A'], ['Total distance driven', '7.73 km'], ['Surface operations', '6 years, 2 months, 19 days']],
    events: [['2003-06-10', 'Launched toward Mars.'], ['2011-05-25', 'NASA ended efforts to contact the rover.']],
    source: mission('Spirit', 'mer-spirit'),
  },
  opportunity: {
    summary: 'Opportunity examined the geology of Meridiani Planum and found evidence of ancient environments that could have supported microbial life.',
    details: 'Designed for 90 Martian days, the rover far exceeded its planned mission. Its final resting place is Perseverance Valley, separate from the landing position marked here.',
    stats: [['Mission type', 'Mars Exploration Rover B'], ['Total distance driven', '45.16 km'], ['Planned surface mission', '90 sols']],
    events: [['2019-02-13', 'NASA declared the mission complete.']],
    source: mission('Opportunity', 'mer-opportunity'),
  },
  phoenix: {
    summary: 'Phoenix dug into the northern plains and confirmed water ice beneath the Martian surface.',
    details: 'Its laboratory analyzed soil and ice, while weather instruments monitored the polar environment. Phoenix also detected perchlorate in the soil.',
    stats: [['Mission type', 'Stationary polar lander'], ['Robotic arm length', 'About 2.5 m'], ['Planned surface mission', '90 days']],
    events: [['2008-07-31', 'NASA announced confirmation of water in a sample analyzed by Phoenix.']],
    source: mission('Mars Phoenix', 'mars-phoenix'),
  },
  curiosity: {
    summary: 'Curiosity investigated whether ancient Mars offered conditions suitable for microbes, finding chemical and mineral evidence of past habitable environments.',
    details: 'Its onboard geology laboratory analyzes samples from Gale Crater. A drill collects powdered rock, and a laser examines targets from a distance.',
    stats: [['Mission type', 'Mars Science Laboratory rover'], ['Rover mass', '899 kg'], ['Science instruments', '10'], ['Robotic arm reach', 'About 2.2 m']],
    events: [['2011-11-26', 'Launched toward Mars.']],
    source: mission('Curiosity', 'msl-curiosity'),
  },
  insight: {
    summary: 'InSight studied the interior of Mars, using a seismometer to investigate the planet beneath its surface.',
    details: 'A smooth equatorial landing site helped the stationary lander safely place instruments on the ground. Its sensors also recorded vibrations caused by Martian wind.',
    stats: [['Mission type', 'Stationary geophysical lander'], ['Robotic arm length', 'About 1.8 m'], ['Science focus', 'Interior structure and seismic activity']],
    events: [['2018-05-05', 'Launched toward Mars.'], ['2018-12-01', 'Sensors captured vibrations produced by Martian wind.']],
    source: mission('InSight', 'insight'),
  },
  perseverance: {
    summary: 'Perseverance was sent to Jezero Crater to investigate ancient habitability, seek signs of past microbial life, and collect rock and soil samples.',
    details: 'Jezero preserves an ancient lake and river delta. The mission also demonstrated a helicopter and technology to produce oxygen on Mars; evidence of past habitability is not proof of past life.',
    stats: [['Mission type', 'Mars 2020 rover'], ['Jezero Crater diameter', 'About 45 km'], ['Sample collection', 'Rock cores and regolith for possible future return']],
    events: [['2020-07-30', 'Launched toward Mars.'], ['2021-04-19', 'Its companion Ingenuity made the first powered, controlled flight on another planet.']],
    source: mission('Perseverance', 'mars-2020-perseverance'),
  },
};

export const BODY_FACTS = {
  mars: {
    id: 'mars', title: 'Mars', category: 'Planet',
    summary: 'A rocky world with polar ice, enormous volcanoes, and traces of ancient rivers and lakes.',
    stats: [
      ['Mean radius', '3,390 km'], ['Average distance from Sun', 'About 228 million km'],
      ['Orbital speed', 'About 24.1 km/s (circular approximation)'],
      ['Rotation (sidereal)', 'About 24.623 Earth hours'], ['Solar day (one sol)', '24.660 Earth hours'],
      ['Equatorial rotation speed', 'About 240 m/s (derived from mean radius and rotation)'],
      ['Year around the Sun', 'About 687 Earth days'], ['Surface temperature range', 'About −153 to +20 °C'],
      ['Natural satellites', '2 — Phobos and Deimos'],
    ],
    events: [
      ['1976-07-20', 'Viking 1 made the first fully successful landing on Mars.'],
      ['1997-07-04', 'Pathfinder delivered the Sojourner rover.'],
      ['2021-04-19', 'Ingenuity achieved powered, controlled flight on another planet.'],
    ],
    sources: [nasaMars, sol, landers, ['NASA — Ingenuity first flight', 'https://science.nasa.gov/resource/nasas-ingenuity-mars-helicopter-successfully-completes-first-flight-2/']],
  },
  phobos: {
    id: 'phobos', title: 'Phobos', category: 'Inner moon',
    summary: 'A cratered, irregular moon dominated by Stickney crater. Its rotation is synchronous: the same side faces Mars.',
    stats: [
      ['Approximate dimensions', '27 × 22 × 18 km'], ['Mean orbital distance', '9,375 km from Mars’s center'],
      ['Altitude above mean Mars radius', 'About 5,985 km'], ['Orbital speed', 'About 2.14 km/s (circular approximation)'],
      ['Orbit / sidereal rotation', '7.649 Earth hours'], ['Solar day', 'About 7.652 Earth hours (derived)'],
      ['Year around the Sun', 'About 687 Earth days, with Mars'], ['Measured surface temperatures', 'About −112 to −4 °C'],
      ['Stickney crater', 'About 9 km across'], ['Discovery (NASA date)', '1877-08-17 — Asaph Hall'],
    ],
    events: [['1877', 'Discovered during Asaph Hall’s search for Martian moons.'], ['Long-term evolution', 'Phobos is spiraling inward; NASA estimates collision or disruption on a timescale of roughly 50 million years.']],
    sources: [nasaPhobos, orbits, nasaMars],
  },
  deimos: {
    id: 'deimos', title: 'Deimos', category: 'Outer moon',
    summary: 'Smaller and smoother-looking than Phobos, with dusty material partly filling its craters. The same side always faces Mars.',
    stats: [
      ['Approximate dimensions', '15 × 12 × 11 km'], ['Mean orbital distance', '23,457 km from Mars’s center'],
      ['Altitude above mean Mars radius', 'About 20,067 km'], ['Orbital speed', 'About 1.35 km/s (circular approximation)'],
      ['Orbit / sidereal rotation', '30.300 Earth hours'], ['Solar day', 'About 30.356 Earth hours (derived)'],
      ['Year around the Sun', 'About 687 Earth days, with Mars'],
      ['Surface temperature', 'Varies with sunlight; the cited flyby report gives no global numerical range'],
      ['Largest crater', 'About 2.3 km across'], ['Discovery (NASA date)', '1877-08-11 — Asaph Hall'],
    ],
    events: [['1877', 'Discovered by Asaph Hall.'], ['2025-03-12', 'ESA’s Hera imaged Deimos in thermal infrared during its Mars flyby.']],
    sources: [nasaDeimos, orbits, nasaMars, ['ESA/JAXA — Deimos thermal observations', 'https://www.esa.int/ESA_Multimedia/Images/2025/03/Mars_and_Deimos_viewed_by_Hera_s_TIRI']],
  },
};

export const LOCATIONS = [
  { id: 'olympus', title: 'Olympus Mons', category: 'Feature', lat: 18.65, lon: 226.20,
    summary: 'The largest volcano in the solar system, a broad shield volcano in the Tharsis region.',
    stats: [['Named feature diameter', 'About 610 km']], sources: [nasaMars, ['USGS/IAU — Olympus Mons', 'https://planetarynames.wr.usgs.gov/Feature/4453']] },
  { id: 'hellas', title: 'Hellas Planitia', category: 'Feature', lat: -42.43, lon: 70.50,
    summary: 'The floor of a vast southern impact basin. Hera thermal imagery showed this region comparatively cool during its March 2025 flyby.',
    stats: [['Basin diameter', 'About 2,300 km']], sources: [['USGS/IAU — Hellas Planitia', 'https://planetarynames.wr.usgs.gov/Feature/2432'], ['ESA/JAXA — Hellas in thermal infrared', 'https://www.esa.int/ESA_Multimedia/Images/2025/03/Mars_and_Deimos_viewed_by_Hera_s_TIRI']] },
  ...[
    ['viking1', 'Viking 1', 22.27, 312.05, '1976-07-20', 'Chryse Planitia'],
    ['viking2', 'Viking 2', 48.27, 134.28, '1976-09-03', 'Utopia Planitia'],
    ['pathfinder', 'Pathfinder / Sojourner', 19.47, 326.75, '1997-07-04', 'Ares Vallis'],
    ['spirit', 'Spirit', -14.57, 175.48, '2004-01-04', 'Gusev Crater'],
    ['opportunity', 'Opportunity', -1.95, 354.47, '2004-01-25', 'Meridiani Planum'],
    ['phoenix', 'Phoenix', 68.22, 234.25, '2008-05-25', 'Vastitas Borealis'],
    ['curiosity', 'Curiosity', -4.59, 137.44, '2012-08-06', 'Gale Crater'],
    ['insight', 'InSight', 4.50, 135.62, '2018-11-26', 'Elysium Planitia'],
    ['perseverance', 'Perseverance', 18.44, 77.45, '2021-02-18', 'Jezero Crater'],
  ].map(([id, title, lat, lon, date, region]) => {
    const detail = LANDING_DETAILS[id];
    return {
      id, title, category: 'Landing site', lat, lon,
      summary: detail.summary,
      details: `${detail.details} This marker shows the historic landing position, not a rover’s present location.`,
      stats: [['Landing date (UTC)', date], ['Region', region], ...detail.stats],
      events: detail.events,
      sources: [landers, detail.source],
    };
  }),
  { id: 'ingenuity', title: 'Ingenuity’s first flight', category: 'Event', lat: 18.44, lon: 77.45,
    summary: 'The first powered, controlled flight on another planet took place in Jezero Crater. This marker uses the nearby Perseverance landing position as a regional reference, not the exact takeoff point.',
    stats: [['Date (UTC)', '2021-04-19'], ['Location precision', 'Regional reference']],
    sources: [landers, ['NASA — Ingenuity first flight', 'https://science.nasa.gov/resource/nasas-ingenuity-mars-helicopter-successfully-completes-first-flight-2/']] },
  { id: 'phoenix-ice', title: 'Water ice confirmed', category: 'Event', lat: 68.22, lon: 234.25,
    summary: 'Phoenix’s laboratory analyzed a sample containing water, confirming the ice beneath the northern plains.',
    stats: [['Date (UTC)', '2008-07-31'], ['Mission', 'Phoenix'], ['Location', 'Phoenix landing site']],
    sources: [landers, mission('Mars Phoenix', 'mars-phoenix')] },
  { id: 'opportunity-finale', title: 'Opportunity’s mission concludes', category: 'Event', lat: -1.95, lon: 354.47,
    summary: 'NASA declared Opportunity’s mission complete after a journey of 45.16 km. This marker uses its original landing site as a regional reference; the rover finished in Perseverance Valley.',
    stats: [['Date (UTC)', '2019-02-13'], ['Total distance driven', '45.16 km'], ['Location precision', 'Regional reference, not final rover position']],
    sources: [landers, mission('Opportunity', 'mer-opportunity')] },
];
