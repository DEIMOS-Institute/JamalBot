
require("dotenv").config();
const fs = require('fs').promises;
const path = require('path');
const {
  Client,
  GatewayIntentBits,
  REST,
  Routes,
  SlashCommandBuilder,
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
} = require("discord.js");

// ===== GAME IMPORTS (optional) =====
let trivia, scratch;
try {
  trivia = require('./games/trivia');
  scratch = require('./games/scratch');
} catch (e) {
  console.warn("⚠️ Game files missing – trivia and scratch may not work.", e.message);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.GuildMembers,
  ],
  partials: ["CHANNEL"],
});

const token = process.env.DISCORD_TOKEN;
const guildId = "1445307822689620090";
const clientId = process.env.CLIENT_ID;
const JOSE_ID = "701435755553095761";

if (!token) {
  console.error("Error: DISCORD_TOKEN not found");
  process.exit(1);
}

// ============================================
// 📁 DATA PERSISTENCE SYSTEM
// ============================================

const DATA_FILE = path.join(__dirname, 'playerData.json');
let playerData = new Map();
let saveTimeout = null;
let autoSaveInterval = null;

const defaultPlayerData = {
  bread: 1000,
  streetCred: 0,
  inventory: [],
  trapHouseLevel: 1,
  multiplier: 1,
  lastDaily: 0,
  lastWork: 0,
  lastRob: 0,
  lastLick: 0,
  lastScavenge: 0,
  lastHustle: 0,
  roastsGiven: 0,
  roastsReceived: 0,
  heat: 0,
  respect: 50,
  casesWon: 0,
  casesLost: 0,
  drillsCompleted: 0,
  achievements: [],
  stashedBread: 0,
  stashCapacity: 5000,
  lastMonthly: 0,
  hood: {
    name: null,
    joined: 0,
    loyalty: 0,
    lastLoyaltyUpdate: 0,
  }
};

async function loadPlayerData() {
  try {
    const data = await fs.readFile(DATA_FILE, 'utf8');
    const parsed = JSON.parse(data);
    playerData = new Map(parsed.map(entry => [entry[0], entry[1]]));
    for (const [userId, data] of playerData) {
      if (!data) continue;
      playerData.set(userId, { ...defaultPlayerData, ...data });
    }
    console.log(`✅ Loaded ${playerData.size} player records`);
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.log('📁 No existing player data found, starting fresh');
    } else {
      console.error('❌ Error loading player data:', error);
    }
    playerData = new Map();
  }
}

async function savePlayerData(immediate = false) {
  if (saveTimeout && !immediate) {
    clearTimeout(saveTimeout);
  }
  const saveFunc = async () => {
    try {
      const dataArray = Array.from(playerData.entries());
      const tempFile = DATA_FILE + '.tmp';
      await fs.writeFile(tempFile, JSON.stringify(dataArray, null, 2));
      await fs.rename(tempFile, DATA_FILE);
      console.log(`💾 Saved ${playerData.size} player records`);
    } catch (error) {
      console.error('❌ Error saving player data:', error);
    }
    saveTimeout = null;
  };
  if (immediate) {
    await saveFunc();
  } else {
    saveTimeout = setTimeout(saveFunc, 5000);
  }
}

function scheduleSave() {
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  saveTimeout = setTimeout(() => savePlayerData(), 5000);
}

async function gracefulShutdown() {
  console.log('🔄 Saving data before shutdown...');
  clearInterval(autoSaveInterval);
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  await savePlayerData(true);
  console.log('✅ Data saved. Goodbye!');
  process.exit(0);
}

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

// ============================================
// 🔥 ENHANCED ROAST DATABASE (FULL)
// ============================================

const roastCategories = {
  appearance: [
    "You look like what happens when you press 'randomize' on a character creator.",
    "I've seen better-looking potatoes.",
    "If ugliness was a crime, you'd get life without parole.",
    "You look like a before picture.",
    "Your face makes onions cry.",
    "You look like a mistake, but someone made you twice.",
    "When you were born, the doctor slapped your parents.",
    "You're so ugly, when you look in the mirror, your reflection looks away.",
    "You have the kind of face that makes people appreciate their own.",
    "Your birth certificate is an apology letter from the condom factory.",
    "You look like a Picasso painting that fell down the stairs.",
    "Your face could scare a hungry bear away from a picnic.",
    "You look like you were drawn by someone who's never seen a human.",
    "If your face was a movie, it would be directed by M. Night Shamalan and still suck.",
    "You look like a Walmart brand version of a person.",
    "Your reflection probably asks for a different mirror.",
    "You're so ugly, you make blind kids cry.",
    "Your face looks like it caught on fire and someone put it out with a fork.",
    "You look like a mistake, but in 4K.",
    "If you were a spice, you'd be flour.",
  ],
  intelligence: [
    "You have two brain cells and they're both fighting for third place.",
    "If brains were dynamite, you wouldn't have enough to blow your nose.",
    "You're about as sharp as a marble.",
    "I'd explain it to you, but I don't have any crayons with me.",
    "You're the reason they put instructions on shampoo bottles.",
    "Your idea of a balanced diet is a chip in each hand.",
    "You couldn't pour water out of a boot if the instructions were on the heel.",
    "You're not the stupidest person on the planet, but you better hope they don't die.",
    "You have the IQ of a grilled cheese sandwich.",
    "You're like a cloud—when you disappear, it's a beautiful day.",
    "You're dumber than a box of rocks, and the rocks are smarter.",
    "If stupidity was a sport, you'd be the MVP.",
    "You're the human equivalent of a 404 error.",
    "You're about as useful as a screen door on a submarine.",
    "You have the mental capacity of a goldfish with amnesia.",
    "You're proof that evolution can go in reverse.",
    "You're so dumb you think Taco Bell is a Mexican phone company.",
    "You'd struggle to pour water out of a boot with instructions on the heel.",
    "You're not stupid; you just have bad luck thinking.",
    "You have the problem-solving skills of a broken calculator.",
  ],
  personality: [
    "Your personality is like a haunted house—scary and empty.",
    "If personality were money, you'd be broke.",
    "You're the human equivalent of a participation trophy.",
    "You're about as useful as a chocolate teapot.",
    "You bring everyone so much joy... when you leave the room.",
    "You're like a software update—every time I see you, I think 'not now'.",
    "You're the reason the gene pool needs a lifeguard.",
    "You have the charm of a wet paper bag.",
    "You're not annoying, you're just... naturally unlikable.",
    "You're the human version of a typo.",
    "You have the personality of a dial-up modem.",
    "You're as interesting as watching paint dry, but less colorful.",
    "You have the charisma of a damp rag.",
    "Your personality is so bland, you make mayonnaise look spicy.",
    "You're the human equivalent of beige wallpaper.",
    "You're as exciting as a tax form.",
    "You have the social skills of a cactus.",
    "You're like a human snooze button.",
    "Your presence is as welcome as a fart in a spacesuit.",
    "You're the reason some animals eat their young.",
  ],
  hood: [
    "You tryna be hard but your gang sign looks like you're ordering a pizza.",
    "You claim the streets but you get nervous when the ice cream truck plays music.",
    "You talk about trapping but your biggest sale was lemonade in 2012.",
    "You say you're from the trenches but you flinch when a plastic bag blows by.",
    "You got 'street cred' from watching Power.",
    "You claim you're a shooter but the only thing you're popping is bubble wrap.",
    "You talk about your 'ops' but your biggest enemy is your WiFi password.",
    "You say you're outside but you're really in your mom's basement.",
    "You claim you're a kingpin but your plug is Amazon Prime.",
    "You talk about drippin' but your chain came from a vending machine.",
    "You claim you're a driller but you still ask your mom for permission to stay out late.",
    "You say you're 'really from the hood' but your address has an HOA.",
    "You talk about spinning blocks but you get lost in a parking lot.",
    "You claim you're a street pharmacist but you're selling Flintstones vitamins.",
    "You say you're about that life but you're scared of fireworks.",
    "You talk about your 'strap' but you're holding a water gun.",
    "You claim you're a OG but you were born in 2005.",
    "You say you're a trap star but you're still using an allowance.",
    "You talk about your 'gang' but it's just you and your cat.",
    "You claim you're a king but your crown came from Burger King.",
  ],
  savage: [
    "Your existence is an argument for birth control.",
    "You're the reason they invented the middle finger.",
    "I'd agree with you but then we'd both be wrong.",
    "You're not stupid; you just have bad luck thinking.",
    "I don't know what makes you so stupid, but it really works.",
    "You're like a penny—two-faced and worthless.",
    "If laughter is the best medicine, your face must be curing the world.",
    "You're proof that evolution can go in reverse.",
    "I'd roast you but my mom said not to burn trash.",
    "You're the reason aliens won't talk to us.",
    "You're about as useful as a fork in a soup kitchen.",
    "You're the human equivalent of a participation trophy.",
    "You have the face of a person who'd return a Christmas gift to an orphan.",
    "You're so dense, light bends around you.",
    "You're the reason they put warning labels on everything.",
    "You have the warmth of a dead star.",
    "You're like a broken pencil—pointless.",
    "You're the reason some people believe in sterilization.",
    "You're about as helpful as a parachute that opens on the second bounce.",
    "You're the human version of a 'do not resuscitate' order.",
  ],
};

const randomRoasts = [
  ...roastCategories.appearance,
  ...roastCategories.intelligence,
  ...roastCategories.personality,
  ...roastCategories.hood,
  ...roastCategories.savage,
];

// ============================================
// 🔥 ENHANCED N-WORD ROASTS (FULL)
// ============================================

const hardRReplies = [
  "AYO WHO TF YOU THINK YOU IS SAYING THAT WITH THE HARD R? YOU AIN'T EVEN FROM THE BLOCK, YOU PROBABLY FROM SUBURBIA WITH YOUR WHITE ASS.",
  "OH NAH, I KNOW YOU DIDN'T JUST DROP THE HARD R. I SEEN YOUR PROFILE PIC, YOU LOOK LIKE YOU DRINK SOY MILK AND DO YOGA.",
  "YOU REALLY OUT HERE SAYING 'NIGGER' WHEN YOUR GRANDPA PROBABLY OWNED MY GREAT GRANDPA. THE AUDACITY IS CRAZY.",
  "BOY IF YOU DON'T GET YOUR WANNABE ASS OUTTA HERE. YOU PROBABLY LISTEN TO IGGY AZALEA AND THINK YOU'RE DOWN.",
  "HARD R? HARD R? YOU LOOK LIKE YOU GET SUNBURNED WATCHING THE NEWS. SIT YOUR VANILLA ASS DOWN.",
  "WHO LET YOU COOK? YOU SAYING 'NIGGER' LIKE YOU EVER BEEN ANYWHERE NEAR THE TRENCHES. YOU PROBABLY THINK 'THE WIRE' IS A DOCUMENTARY.",
  "YOU DROPPING N-BOMBS BUT YOUR LAST MEAL WAS AVOCADO TOAST. BE FOR REAL.",
  "I CAN TELL BY HOW YOU TYPE YOU WHITE. YOU USING PROPER PUNCTUATION AND SHIT. NIGGAS DON'T USE SEMICOLONS.",
  "YOU SAID THE HARD R WITH YOUR CHEST BUT I BET YOU CROSS THE STREET WHEN YOU SEE A GROUP OF BLACK PEOPLE.",
  "MY NIGGA YOU AIN'T BLACK, YOU WHITER THAN MAYONNAISE IN A SNOWSTORM. STOP PLAYING.",
  "YOU GOT THE AUDACITY TO SAY 'NIGGER' BUT YOUR FAMILY TREE STRAIGHTER THAN THE LINE AT THE DMV.",
  "NAH, YOU REALLY JUST SAID THAT? I BET YOUR ANESTORS ARE ROLLING IN THEIR GRAVES FROM EMBARRASSMENT.",
  "YOU'RE WHITER THAN A GHOST IN A CLOUD OF FLOUR. SIT DOWN BEFORE I CALL YOUR MAMA.",
  "I KNOW YOU DIDN'T JUST TYPE 'NIGGER' FROM YOUR PARENTS' BASEMENT. GET A JOB.",
  "THE ONLY THING YOU KNOW ABOUT THE STREETS IS HOW TO GET TO WHOLE FOODS. CHILL.",
  "YOU PROBABLY CAN'T EVEN SEASON CHICKEN RIGHT. DON'T TALK TO ME ABOUT NOTHING.",
  "YOU'RE OUT HERE SAYING THE HARD R BUT YOU PROBABLY STILL ASK YOUR MOM FOR PERMISSION TO STAY UP PAST 10.",
  "NAH THIS CAN'T BE REAL. YOU TYPE LIKE YOU WEAR SOCKS WITH SANDALS. EMBARRASSING.",
  "YOU'RE THE REASON YOUR ANCESTORS LOST THE CIVIL WAR. WEAK GENES.",
  "I BET YOU THINK 'CRACKER' IS A RACIAL SLUR TOO. SNOWFLAKE ASS.",
  "YOU DROPPING THE HARD R LIKE YOU EVER HAD TO DEAL WITH REDLINING. YOUR BIGGEST HOUSING ISSUE IS CHOOSING BETWEEN GRANITE OR QUARTZ COUNTERTOPS.",
  "HARD R COMING FROM SOMEONE WHO PROBABLY CALLS THE COPS WHEN THEY HEAR LOUD MUSIC. YOU'RE THE NEIGHBORHOOD SNITCH BY DEFAULT.",
  "YOU SAID 'NIGGER' BUT YOUR SOUL IS AS COLORLESS AS YOUR DIET OF UNSEASONED CHICKEN. BASIC ASS.",
  "THE AUDACITY TO USE THE HARD R WHEN YOU CAN'T EVEN CLAP ON BEAT. YOUR RHYTHM IS AS OFF AS YOUR MORALS.",
  "WHO LET YOU OUT THE SUBURBS? DROPPING N-BOMBS BUT YOU GET SCARED WHEN A FIREWORK GOES OFF. PUSSY ASS.",
  "YOU USING THE HARD R LIKE YOU EVER FACED DISCRIMINATION. YOUR ONLY DISCRIMINATION IS WHETHER TO GET REGULAR OR DECAF.",
  "HARD R WITH YOUR PRIVILEGED ASS? YOU PROBABLY THINK SYSTEMIC RACISM IS A MYTH. EDUCATE YOURSELF.",
  "YOU SAID 'NIGGER' BUT YOU CAN'T EVEN HANDLE MILD SAUCE. YOUR PALATE IS AS WEAK AS YOUR CHARACTER.",
  "THE ONLY THING HARD ABOUT YOU IS YOUR HEAD FROM BEING SO DENSE. YOU'RE THE HUMAN VERSION OF A PARTICIPATION TROPHY.",
  "YOU DROPPING THE HARD R LIKE YOU EVER HAD TO CODE-SWITCH. YOUR ONLY SWITCH IS FROM BUSINESS CASUAL TO CASUAL FRIDAY.",
  "HARD R COMING FROM SOMEONE WHOSE CULTURE IS STARBUCKS AND APPLEBEES. YOU AIN'T GOT NO SAUCE.",
  "YOU OUT HERE USING SLAVE OWNER LANGUAGE BUT YOU GET ANXIETY IN A CROWD. PICK A STRUGGLE.",
  "YOU SAID 'NIGGER' WITH YOUR WHOLE CHEST BUT YOUR BLOODLINE IS AS PLAIN AS WONDER BREAD. BORING ASS.",
  "THE HARD R FROM SOMEONE WHO PROBABLY THINKS 'WAKANDA' IS A REAL PLACE. YOU'RE EMBARRASSING.",
  "YOU USING THAT WORD LIKE YOU EVER HAD TO WORRY ABOUT DRIVING WHILE BLACK. YOUR ONLY WORRY IS MERGING ON THE HIGHWAY.",
  "HARD R BUT YOU CAN'T EVEN COOK A POT OF RICE RIGHT. YOUR SEASONING CONSISTS OF SALT AND REGRET.",
  "YOU DROPPING N-BOMBS BUT YOUR MUSIC TASTE IS COLDPLAY AND MUMFORD & SONS. YOU AIN'T STREET, YOU SUBURBAN.",
  "YOU SAID 'NIGGER' LIKE YOU EVER BEEN ANYWHERE NEAR A PROJECT. YOUR IDEA OF THE HOOD IS WHEN YOUR UBER TAKES A WRONG TURN.",
  "THE AUDACITY TO USE THE HARD R WHEN YOU PROBABLY CAN'T NAME 5 BLACK HISTORICAL FIGURES. IGNORANT ASS.",
  "HARD R COMING FROM SOMEONE WHOSE BIGGEST TRAUMA IS THEIR PHONE BATTERY DYING. PRIVILEGE IS SHOWING.",
  "YOU USING THAT WORD BUT YOU STILL LIVE WITH YOUR PARENTS AT 30. FOCUS ON GETTING YOUR OWN PLACE FIRST.",
  "YOU DROPPING THE HARD R LIKE YOU EVER HAD TO WORK TWICE AS HARD FOR HALF THE RECOGNITION. YOUR DADDY GOT YOU THAT JOB.",
  "HARD R FROM SOMEONE WHO PROBABLY THINKS 'BLACK LIVES MATTER' IS A TREND. YOU'RE PART OF THE PROBLEM.",
  "YOU SAID 'NIGGER' BUT YOUR FAMILY REUNIONS ARE QUIETER THAN A LIBRARY. NO RHYTHM, NO CULTURE, NOTHING.",
  "THE HARD R COMING FROM A KEYBOARD WARRIOR WHO WOULDN'T SAY THAT SHIT IN PERSON. INTERNET GANGSTER.",
  "YOU USING THAT WORD LIKE YOU EVER HAD TO DEAL WITH MICROAGGRESSIONS. YOUR ONLY AGGRESSION IS WHEN THE BARISTA GETS YOUR ORDER WRONG.",
  "HARD R BUT YOU CAN'T EVEN GROW FACIAL HAIR. YOU LOOK LIKE A PREPUBESCENT BOY TRYING TO BE EDGY.",
  "YOU DROPPING N-BOMBS BUT YOUR IDEA OF DANGER IS A 'CHECK ENGINE' LIGHT. YOU AIN'T SEEN NO REAL PROBLEMS.",
  "YOU SAID 'NIGGER' WITH CONFIDENCE BUT YOU STILL ASK FOR PERMISSION TO USE THE BATHROOM. GROW UP.",
  "THE AUDACITY TO USE THE HARD R WHEN YOU PROBABLY CAN'T EVEN NAME 3 BLACK AUTHORS. YOUR EDUCATION FAILED YOU.",
  "HARD R COMING FROM SOMEONE WHOSE ENTIRE PERSONALITY IS CRAFT BEER AND CROSSFIT. YOU BASIC AS HELL.",
  "YOU USING THAT WORD BUT YOU GET NERVOUS WHEN CASHIERS MAKE EYE CONTACT. SOCIAL ANXIETY AND RACISM IS A WILD COMBO.",
  "YOU DROPPING THE HARD R LIKE YOU EVER HAD TO WORRY ABOUT YOUR HAIR BEING 'PROFESSIONAL'. YOUR HAIRCUT IS FROM GREAT CLIPS.",
  "HARD R FROM SOMEONE WHO PROBABLY THINKS SOUL FOOD IS JUST 'FRIED CHICKEN'. YOUR CULTURAL IGNORANCE IS SHOWING.",
  "YOU SAID 'NIGGER' BUT YOU CAN'T EVEN DOUBLE DUTCH. YOU LACK COORDINATION AND COMMON SENSE.",
  "THE HARD R COMING FROM A PERSON WHO STILL USES INTERNET EXPLORER. YOU'RE OUTDATED IN EVERY WAY.",
  "YOU USING THAT WORD LIKE YOU EVER HAD TO REPRESENT YOUR ENTIRE RACE. YOUR ONLY REPRESENTATION IS YOUR FANDOM FOR THE OFFICE.",
  "HARD R BUT YOU PROBABLY THINK JIM CROW WAS A PERSON. HISTORICALLY ILLITERATE ASS.",
  "YOU DROPPING N-BOMBS BUT YOUR BIGGEST ACCOMPLISHMENT IS FINISHING A NETFLIX SERIES. AIM HIGHER.",
  "YOU SAID 'NIGGER' WITH YOUR WHOLE CHEST BUT YOU STILL WEAR LIGHT UP SNEAKERS. YOU AIN'T GROWN, YOU GROWING OLD.",
  "THE AUDACITY TO USE THE HARD R WHEN YOU CAN'T EVEN MAKE INSTANT RAMEN RIGHT. YOU'RE USELESS.",
  "HARD R COMING FROM SOMEONE WHOSE IDEA OF ADVENTURE IS TRYING A NEW CHAIN RESTAURANT. YOU'RE NOT DANGEROUS, YOU'RE BORING.",
  "YOU USING THAT WORD BUT YOU PROBABLY THINK 'CODE SWITCHING' IS SOMETHING PROGRAMMERS DO. CLUELESS ASS.",
  "YOU DROPPING THE HARD R LIKE YOU EVER HAD TO TEACH YOUR KIDS HOW TO INTERACT WITH POLICE. YOUR KIDS' BIGGEST FEAR IS BEDTIME.",
  "HARD R FROM SOMEONE WHO PROBABLY THINKS AFFIRMATIVE ACTION IS REVERSE RACISM. CHECK YOUR PRIVILEGE, THEN CHECK YOURSELF.",
  "YOU SAID 'NIGGER' BUT YOU CAN'T EVEN NAME THREE BLACK NEIGHBORHOODS IN YOUR CITY. YOU LIVE IN A BUBBLE.",
  "THE HARD R COMING FROM A PERSON WHO STILL GETS AN ALLOWANCE. GET YOUR OWN MONEY BEFORE YOU GET YOUR OWN OPINIONS.",
  "YOU USING THAT WORD LIKE YOU EVER HAD TO WORRY ABOUT SUNGLASSES BEING TOO DARK. YOUR SKIN IS TRANSLUCENT.",
  "HARD R BUT YOUR CULTURAL REFERENCES ARE FROM TIKTOK WHITE BOYS. YOU HAVE NO ORIGINALITY.",
  "YOU DROPPING N-BOMBS BUT YOU GET LOST USING PUBLIC TRANSPORTATION. YOU AIN'T STREET SMART, YOU STREET DUMB.",
  "YOU SAID 'NIGGER' WITH CONFIDENCE BUT YOU STILL USE TRAINING WHEELS ON YOUR BIKE. LITERAL CHILD BEHAVIOR.",
];

const softAReplies = [
  "AYO WHO TF GAVE YOU THE PASS? YOU AIN'T MY NIGGA, YOU A CUSTOMER AT STARBUCKS.",
  "OH YOU THINK YOU CAN SAY 'NIGGA' CUZ YOU LISTEN TO DRILL MUSIC? YOU PROBABLY FROM CONNECTICUT.",
  "YOU'RE WHITER THAN A SHEET OF PAPER IN A BLIZZARD. DON'T EVER CALL ME YOUR NIGGA.",
  "I KNOW YOU DIDN'T JUST SAY 'NIGGA' WITH YOUR EUROPEAN ASS. YOUR FAMILY PROBABLY STILL HAS A CASTLE.",
  "YOU CAN'T SAY THAT WORD. YOU LOOK LIKE YOU'VE NEVER SEEN A FIGHT IN YOUR LIFE.",
  "MY NIGGA? MY NIGGA? YOU AIN'T MY NIGGA, YOU A WHITE BOY FROM THE SUBURBS.",
  "YOU PROBABLY THINK CHICKEN AND WAFFLES IS EXOTIC. SIT DOWN.",
  "I CAN SMELL THE PRIVILEGE THROUGH THE SCREEN. STOP IT.",
  "YOU'RE THE TYPE TO SAY 'NIGGA' ONLINE BUT CLUTCH YOUR PURSE IN REAL LIFE.",
  "YOU CAN'T EVEN DANCE AND YOU TRYNA SAY 'NIGGA'? THE AUDACITY.",
  "YOUR ENTIRE PERSONALITY IS BASED ON RAP MUSIC YOU DON'T UNDERSTAND. SAD.",
  "YOU PROBABLY THINK 'NO CAP' MEANS YOU'RE NOT WEARING A HAT. I'M DONE.",
  "YOU'RE OUT HERE USING AAVE BUT YOUR REAL VOICE SOUNDS LIKE A NPR HOST.",
  "I BET YOU PRONOUNCE IT 'NI-GUH' LIKE YOU'RE ORDERING AT A FRENCH RESTAURANT.",
  "YOU'RE WHITER THAN THE INSIDE OF A BANANA. STOP TRYING TO BE DOWN.",
  "THE ONLY GANG YOU'RE IN IS THE BOOK CLUB. CHILL.",
  "YOU PROBABLY THINK 'OPPS' MEANS OPPORTUNITIES. I CAN'T.",
  "YOUR IDEA OF BEING 'STREET' IS USING THE EXPRESS LANE AT TARGET. BYE.",
  "YOU CAN'T SAY 'NIGGA' WHEN YOUR BIGGEST PROBLEM IS YOUR MACBOOK PRO BATTERY LIFE.",
  "Ayo who tf gave you the pass to say 'nigga'? You look like you still ask your mom to cut the crust off your sandwiches.",
  "Nigga? Nigga? You whiter than the inside of an Oreo. Stay in your lane, Walmart brand.",
  "Oh you think you can say 'nigga' cuz you watched 'ATL' one time? You probably from Idaho talking like that.",
  "You calling me 'nigga' but you get nervous when the ice cream truck plays music. Scared ass.",
  "Who let you in the cookout? You saying 'nigga' like you know how to make mac and cheese from scratch.",
  "You claim you my 'nigga' but your biggest struggle is choosing which Netflix show to binge. Privileged ass.",
  "Nigga please, you can't even dance at a wedding without looking like a malfunctioning robot. Rhythmless wonder.",
  "You out here saying 'nigga' but you still wear cargo shorts and New Balance. You're 35 going on 65.",
  "I know you didn't just call me your 'nigga'. You look like you still believe in Santa Claus.",
  "You think you can say 'nigga' cuz you got a black friend? That friend is probably just being polite.",
  "Nigga? Boy you whiter than a sheet of paper in a snowstorm. Your ancestors invented mayonnaise.",
  "You saying 'nigga' like you ever been in a fight. Your only fight is with seasonal allergies.",
  "Who gave you permission? The only 'nigga' you should be saying is 'nigga please sit down'.",
  "You calling people 'nigga' but you can't even handle mild salsa. Your palate is weak, just like your game.",
  "Nigga you ain't from the hood, you from the suburbs with an HOA. You probably call the cops on loud barbecues.",
  "You think you can say 'nigga' cuz you listen to Drake? You probably sing along to 'Hotline Bling' in the shower.",
  "Nigga please, you still sleep with a stuffed animal. You ain't hard, you're barely awake.",
  "You out here saying 'nigga' but you get winded walking up stairs. Out of shape and out of line.",
  "Who let you cook? You saying 'nigga' like you know what a food stamp looks like. Privilege is showing.",
  "Nigga? You look like you still use a flip phone. You're outdated in every way possible.",
  "You calling me 'nigga' but you can't even name three Tupac songs. Fake ass fan.",
  "Nigga you ain't street, you suburban with extra steps. Your idea of danger is a pothole.",
  "You think you can say 'nigga' cuz you played Grand Theft Auto? You probably can't even parallel park.",
  "Nigga please, you still get an allowance from your parents. Get your own money first.",
  "You out here saying 'nigga' but you're scared of thunderstorms. Jump at your own shadow type beat.",
  "Who gave you the green light? You saying 'nigga' like you ever missed a meal. Your biggest hunger is for attention.",
  "Nigga? You look like you drink milk with every meal. Basic and boring.",
  "You calling people 'nigga' but you can't even throw a football spiral. Uncoordinated ass.",
  "Nigga you ain't tough, you tender. You probably cry during Hallmark commercials.",
  "You think you can say 'nigga' cuz you been to a rap concert? You were probably in the nosebleeds.",
  "Nigga please, you still use training wheels on your bike. Literal child behavior.",
  "You out here saying 'nigga' but you're afraid of dogs. Scared of a golden retriever type energy.",
  "Who let you in the function? You saying 'nigga' like you know how to two-step. Rhythm deficit real.",
  "Nigga? You look like you still believe in cooties. Immature as hell.",
  "You calling me 'nigga' but you can't even cook instant ramen right. Useless in the kitchen and in life.",
  "Nigga you ain't cool, you're a tool. You probably still wear braces as an adult.",
  "You think you can say 'nigga' cuz you got a fade? Your barber is probably white too.",
  "Nigga please, you still sleep with a nightlight. Afraid of the dark and afraid of reality.",
  "You out here saying 'nigga' but you get carsick on short drives. Weak stomach, weak character.",
  "Who gave you the pass? You saying 'nigga' like you ever worked a day in your life. Trust fund baby.",
  "Nigga? You look like you still play with Legos. Grow up before you try to grow a pair.",
  "You calling people 'nigga' but you can't even swim. Sink or swim and you sinking.",
  "Nigga you ain't him, you're them. You probably still live in your childhood bedroom.",
  "You think you can say 'nigga' cuz you got a tattoo? It's probably a tribal design from 2005.",
  "Nigga please, you still ask for help tying your shoes. Incompetent at life.",
  "You out here saying 'nigga' but you're allergic to grass. Can't even touch grass properly.",
  "Who let you in the studio? You saying 'nigga' like you can freestyle. Your best rhyme is cat/hat.",
  "Nigga? You look like you still use AOL email. Stuck in the past like your mindset.",
  "You calling me 'nigga' but you can't even drive stick. Manual failure, just like your social skills.",
  "Nigga you ain't about that life, you about that wifi life. Your biggest risk is a weak password.",
  "You think you can say 'nigga' cuz you wear Jordans? You probably keep the tags on them.",
  "Nigga please, you still believe in the tooth fairy. Delusional and desperate.",
  "You out here saying 'nigga' but you can't handle spicy food. Your tongue is as weak as your game.",
  "Who gave you permission? You saying 'nigga' like you ever been outside past 9 PM. Curfew king.",
  "Nigga? You look like you still use dial-up internet. Slow in every aspect of life.",
  "You calling people 'nigga' but you can't even change a tire. Useless when it matters most.",
  "Nigga you ain't real, you're a deal. You probably still shop at the kids' section.",
  "You think you can say 'nigga' cuz you been to a cookout? You probably brought store-bought potato salad.",
  "Nigga please, you still watch cartoons on Saturday morning. You're not a kid, you're just childish.",
  "You out here saying 'nigga' but you're scared of elevators. Claustrophobic and cowardly.",
  "Who let you in the cypher? You saying 'nigga' like you can beatbox. You sound like a broken dishwasher.",
  "Nigga? You look like you still use a paper map. Can't navigate life or conversations.",
  "You calling me 'nigga' but you can't even grill a burger. Burn everything you touch.",
  "Nigga you ain't street smart, you street dumb. You probably get lost in your own neighborhood.",
  "You think you can say 'nigga' cuz you got a chain? It's probably from Claire's.",
  "Nigga please, you still believe in horoscopes. Your sign is 'delusional'.",
  "You out here saying 'nigga' but you can't parallel park. Can't maneuver life either.",
  "Who gave you the mic? You saying 'nigga' like you can sing. You sound like a dying cat.",
  "Nigga? You look like you still use a VCR. Outdated technology, outdated mindset.",
  "You calling people 'nigga' but you can't even do a push-up. Physically and mentally weak.",
  "Nigga you ain't about action, you're about distraction. Your biggest move is changing your profile picture.",
  "You think you can say 'nigga' cuz you got a durag? You probably sleep in it like pajamas.",
  "Nigga please, you still play Pokémon Go. Your biggest catch is disappointment.",
  "You out here saying 'nigga' but you're scared of bees. Buzz off, literally.",
  "Who let you in the studio? You saying 'nigga' like you can produce. Your beats are weaker than your game.",
  "Nigga? You look like you still use Myspace. Socially irrelevant.",
  "You calling me 'nigga' but you can't even swim. You sink in shallow water and deep conversations.",
  "Nigga you ain't making moves, you're making mistakes. Your biggest accomplishment is breathing.",
  "You think you can say 'nigga' cuz you got a snapback? You wear it backwards and it shows.",
  "Nigga please, you still collect beanie babies. Your investments are as bad as your judgment.",
  "You out here saying 'nigga' but you can't handle caffeine. Jittery and jumpy like your personality.",
  "Who gave you the floor? You saying 'nigga' like you can dance. You move like a baby deer on ice.",
  "Nigga? You look like you still use Windows 95. Your operating system needs an update.",
  "You calling people 'nigga' but you can't even cook an egg. Can't handle heat in the kitchen or the streets.",
  "Nigga you ain't building, you're breaking. Your only construction is deconstructing your own credibility.",
  "You think you can say 'nigga' cuz you got a tattoo sleeve? It's probably all tribal and Chinese symbols.",
  "Nigga please, you still believe in Bigfoot. Your reality is as fictional as your street cred.",
  "You out here saying 'nigga' but you're scared of commitment. Can't commit to a relationship or a hairstyle.",
  "Who let you in the booth? You saying 'nigga' like you can rap. Your flow is weaker than your handshake.",
  "Nigga? You look like you still use a pager. Can't get with the times or the rhymes.",
  "You calling me 'nigga' but you can't even fix a leaky faucet. Useless with tools and common sense.",
  "Nigga you ain't making waves, you're making puddles. Your impact is as small as your ambition.",
  "You think you can say 'nigga' cuz you got a gold tooth? It's probably just gold-plated.",
  "Nigga please, you still play with action figures. Your idea of action is moving them around.",
  "You out here saying 'nigga' but you're scared of thunderstorms. Jump at loud noises type energy.",
  "Who gave you the stage? You saying 'nigga' like you can perform. Your act is tired, just like your jokes.",
  "Nigga? You look like you still use cassette tapes. Your taste in music and life is outdated.",
  "You calling people 'nigga' but you can't even grow a beard. Patchy in facial hair and personality.",
  "Nigga you ain't dropping gems, you're dropping dimes. And by dimes, I mean worthless opinions.",
  "You think you can say 'nigga' cuz you got a pitbull? You probably got it from a breeder, not the streets.",
  "Nigga please, you still believe in fairy tales. Your life is a fantasy, just like your credibility.",
  "You out here saying 'nigga' but you can't handle rejection. Your ego is as fragile as your confidence.",
  "Who let you in the circle? You saying 'nigga' like you belong. You're as welcome as a fart in an elevator.",
  "I KNOW YOU'RE TYPING THIS FROM YOUR DORM ROOM AT A PRIVATE COLLEGE. LOG OFF.",
];

// ============================================
// 📦 LOOT, QUOTES, STEAL ITEMS, SLANG MAP (FULL)
// ============================================

const lootItems = [
  "wallet", "purse", "KFC Bucket", "phone", "BITCH", "AirPods", "Jordan 4s",
  "Stimulus check", "respect", "girl's number", "gold teeth", "fake chain",
  "pride", "lunch money", "catalytic converter", "rim", "Stolen Corvette Keys",
  "diamond ring", "watermelon", "fried chicken", "Kool-Aid", "Glock 17",
  "Cocaine", "Hennessy", "Tims", "Newport 100s", "whole rack", "Percocet",
  "Double Cup", "Ski Mask", "9mm", "Jordan 11s", "Dior Puffy Jacket",
  "Amiri Jeans", "B.B. Simon Belt", "Vlone Shirt", "Cartier Glasses",
  "Stolen EBT Card", "Trap Phone", "Bag of Zaza", "Promethazine Bottle",
  "Gold Grillz", "Designer Ski Mask", "Stolen Hellcat Keys", "Stack of Blue Hundreds",
  "Diamond Link Chain", "Supreme Money Gun", "Chrome Heart Ring", "Off-White Belt",
  "Yeezy Slides", "iPhone 15", "Brick of White", "Glock Drum Mag", "Moncler Vest",
  "Balenciaga Track Runners", "Stolen Link Card", "Cup of Wock", "Foreign Whip",
  "Stolen Airfryer", "Box of Backwoods", "Faygo Bottle", "Section 8 Voucher",
  "Court Date Paperwork", "Child Support Notice", "Warrant for Arrest",
  "Bag of Flaming Hot Cheetos", "Half-eaten Turkey Leg", "Stolen Porch Package",
  "Gently Used Pitbull", "Respect", "Huzz", "BITCHES", "Broken PlayStation 4",
  "Bottle of Blue Nuvo", "Fake Gucci Wallet", "Gas Station Sushi",
  "Used Scratch-off Ticket", "backpack", "duffel bag", "snapback", "beanie",
  "hoodie", "AA cup bra", "A cup bra", "B cup bra", "C cup bra", "D cup bra",
  "DD cup bra", "DDD cup bra", "E cup bra", "F cup bra", "G cup bra", "H cup bra",
  "I cup bra", "J cup bra", "K cup bra", "L cup bra", "M cup bra", "N cup bra",
  "O cup bra", "P cup bra", "Q cup bra", "sweatpants", "joggers", "jordan 4s",
  "air force 1", "nike air max", "adidas superstars", "fila disruptor",
  "vans sk8-hi", "converse chucks", "timberland boots", "slides", "crocs",
  "grillz", "cuban link chain", "rope chain", "watch", "casio watch", "g-shock",
  "bracelet", "earrings", "rings", "necklace", "pendant", "headphones",
  "earbuds", "portable speaker", "bluetooth speaker", "laptop", "tablet",
  "charger", "usb cable", "airpods", "ps5", "xbox", "switch", "video games",
  "skateboard", "bmx bike", "basketball", "soccer ball", "baseball glove",
  "box gloves", "energy drink", "monster", "red bull", "rockstar", "kool-aid",
  "sprite", "coca-cola", "pepsi", "mountain dew", "2-liter soda", "candy",
  "chips", "takis", "hot cheetos", "gum", "ice cream", "cookie", "snack cakes",
  "hennessy", "crown royal", "smirnoff", "vodka", "rum", "beer", "cheap wine",
  "blunt wrap", "rolling papers", "grinder", "bong", "pipe", "vape pen",
  "vape juice", "hookah", "ashtray", "zip bags", "rubber bands", "safe",
  "cheap safe", "mini fridge", "lamp", "led lights", "lava lamp", "wall poster",
  "rapper poster", "car poster", "vinyl record", "cd", "dvd", "blu-ray",
  "board game", "playing cards", "dice", "sticker", "graffiti marker",
  "spray paint", "stencil", "wallet chain", "belt chain", "phone chain",
  "fanny pack", "tote bag", "backpack chain", "cheap rims", "hubcaps",
  "spoiler", "steering wheel cover", "seat cover", "floor mats", "dashboard cover",
  "car air freshener", "windshield decal", "rear window sticker", "hood decal",
  "neon underglow", "car subwoofer", "amplifier", "jumper cables", "tire inflator",
  "oil funnel", "car jack", "tool kit", "screwdriver set", "wrench set",
  "socket set", "cheap perfume", "cologne", "hat", "bucket hat", "visor",
  "scarf", "gloves", "fingerless gloves", "arm sleeves", "wristband",
  "headband", "shoe lace", "charms", "cheap belt", "designer knockoff belt",
  "cheap hoodie", "cheap pants", "cheap tee", "graphic tee", "sports jersey",
  "track jacket", "windbreaker", "denim jacket", "puffer jacket", "flannel",
  "camouflage pants", "leggings", "shorts", "tank top", "crop top", "slides",
  "slippers", "flip-flops", "house slippers", "socks", "thermal underwear",
  "long johns", "anklet", "toe ring", "cheap grill", "fake diamond ring",
  "fake chain", "fake watch", "phone case", "custom phone case", "laptop sticker",
  "car sticker", "fast food bag", "mcdonalds fries", "wendys spicy nuggets",
  "popeyes chicken", "taco bell taco", "jack in the box tacos", "burger king whopper",
  "pizza slice", "hot pockets", "frozen burrito", "ramen noodles", "cup noodles",
  "cheetos", "takis", "doritos", "king size candy bar", "soda can", "slushie",
  "icees", "kool-aid pouch", "fruit punch", "energy drink can", "hennessy mini",
  "crown royal mini",
];

const quotes = [
  "Black lives matter", "Fly High King Von", "Do you got fried chicken?",
  "Pass me the joint", "i joined the crips", "OH SHIT THE ONE TIME",
  "FREE MY NIGGA MELLY", "I'm really out here hooping", "Hold this 9mm for me",
  "Father? Never heard of him", "Bout to abandon some kids real quick",
  "Pants sagged so low you can see the future", "Niggas really be tripping",
  "On god for real", "I'm really the king of the hood", "Stop looking at my bitch",
  "Yo can I borrow $5? I'll pay you back on Tuesday", "12 is on the way, hide the strap!",
  "Who want some koolaid?", "I'm just tryna hoop and stay out the way",
  "Slide for Von", "Big GDK", "I'm smoking on that pack", "Got the glizzy on me",
  "On folks grave", "Spinning the block", "Free the guys", "Free the real",
  "Street code over everything", "Don't be a snitch, nobody likes a rat",
  "Hustle hard or stay broke", "From the mud to the top",
  "Keep your circle small and your glock loaded", "Trust nobody, not even your own shadow",
  "Moving in silence like lasagna", "Respect is earned, not given",
  "Trap house jumping today", "Money talks, bullshit walks",
  "Every day is a struggle in the trenches", "Keep it 100 or keep it away from me",
  "Loyalty is royalty", "Stay dangerous, the ops are watching",
  "Finessing the system daily", "Concrete jungle dreams", "Living fast, dying young",
  "The block is hot, stay low", "Real recognizes real", "Doing it for the set",
  "I'm really out here spinning for the guys", "Smoking on that dead opp pack",
  "We outside till the sun come up", "Ain't no love in these streets",
  "Glizzy in the Dior bag, don't trip", "I'm really a trench baby",
  "Stop claiming my set, you a civilian", "Bout to go for a drill real quick",
  "Free Young Thug till it's backwards", "I'm popping percs till I can't feel my face",
  "Moving weight like a bodybuilder", "Don't get smoked like a backwood",
  "I really came from nothing", "The plug just called, gotta run",
  "Sipping lean out a styrofoam cup", "My glock got a switch, don't make me use it",
  "On my momma I'm really like that", "No face, no case",
  "Keep that same energy when I see you", "I'm just tryna see my brothers win",
  "Hood legend in the making", "Trap phone ringing off the hook",
  "I'm really a street pharmacist", "They talk behind my back cause they can't front",
  "Gotta stay focused on the bag", "The streets ain't for the weak",
  "I'm really a product of my environment", "Big pressure, no diamonds",
  "I'm really a hood superstar", "Don't get it twisted, I'm really outside",
  "I'm really built for this shit", "They hating on the glow up",
  "Moving smart, staying sharp", "I'm really a trench king",
  "The marathon continues, long live Nip", "Stay true to yourself, fuck the rest",
  "I'm really a diamond in the rough", "They tried to bury me, they didn't know I was a seed",
  "I'm really a street poet", "The grind never stops", "You see the laser? Don't move.",
  "My baby mama trippin again", "Just beat the case, let's celebrate",
  "I'm smoking zaza in the library", "Why you lookin at my chain like that?",
  "I really got it out the mud", "Told the judge I was hooping",
  "My lawyer is Jewish, I'm straight", "Moving silent like the 'g' in gnome",
  "I'm the one who knocks... at the trap house", "The feds took my pictures, I'm famous",
  "Just finessed a scammer, recursion!", "Pockets fat like Biggie",
  "I'm really a certified stealer", "Don't make me get the guys involved",
  "I'm spinning the block in a Prius", "Save some chicken for me",
  "I'm really a spiritual driller", "My glock got personality",
  "I'm popping out at the cookout", "Stop asking for a discount, the price is the price",
  "I'm really him, no cap",
];

const stealItems = lootItems; // reuse

const slangMap = {
  hi: "yo wassup", hello: "yo", "how are you": "how u livin", friend: "cuz",
  man: "nigga", police: "the 12", gun: "strap", money: "bread", good: "fire",
  bad: "wack", brother: "homie", sister: "shawty", girl: "bitch", house: "crib",
  cool: "dope", really: "no cap", truth: "on god", scared: "pussy", ok: "bet",
  yes: "yuh", no: "nah", please: "on my mama", "thank you": "respect",
  bye: "peace out", "whats going on": "what it do", "what are you doing": "what you on",
  "where are you": "where you at", leave: "dip", "run away": "skedaddle",
  tired: "beat", angry: "heated", "calm down": "chill", relax: "kick back",
  fight: "throw hands", win: "catch a W", lose: "take an L", joke: "clown",
  lying: "cappin", "stop lying": "cut the cap", "trust me": "believe that",
  look: "peep", listen: "hear me out", understand: "feel me", agree: "facts",
  disagree: "miss me with that", embarrassing: "cringe", impressive: "tough",
  amazing: "go crazy", popular: "lit", party: "function", drunk: "faded",
  high: "smacked", dangerous: "sketchy", suspicious: "shady", steal: "jack",
  argument: "back-and-forth", problem: "issue", plan: "move", style: "drip",
  clothes: "fit", shoes: "kicks", car: "whip", fast: "movin different",
  slow: "draggin", quiet: "lowkey", obvious: "highkey", serious: "deadass",
  nothing: "ain't shit", everything: "the whole thing", "right now": "right quick",
  later: "in a minute", left: "dipped", leaving: "dipping", run: "dash",
  ran: "dashed", running: "dashin", escape: "slide", escaped: "slid",
  escaping: "slidin", relaxed: "chilled", relaxing: "chillin", "hang out": "kick it",
  "hung out": "kicked it", "hanging out": "kickin it", fought: "threw hands",
  fighting: "throwin hands", argued: "went back and forth", arguing: "goin back and forth",
  lied: "capped", cappin: "cappin", flex: "flex", flexed: "flexed",
  flexin: "flexin", stunt: "stunt", stunted: "stunted", stuntin: "stuntin",
  peep: "peep", peeped: "peeped", peepin: "peepin", "feel me": "feel me",
  "felt me": "felt me", "feelin me": "feelin me", "rock with it": "rock with it",
  "rocked with it": "rocked with it", "rockin with it": "rockin with it",
  "miss me with that": "miss me with that", "missed me with that": "missed me with that",
  "missin me with that": "missin me with that", "turn up": "turn up",
  "turned up": "turned up", "turnin up": "turnin up", "catch a W": "catch a W",
  "caught a W": "caught a W", "catchin Ws": "catchin Ws", "take an L": "take an L",
  "took an L": "took an L", "takin Ls": "takin Ls", jack: "jack",
  jacked: "jacked", jackin: "jackin", whip: "whip", whipped: "whipped",
  whippin: "whippin", drip: "drip", "dripped out": "dripped out", drippin: "drippin",
  lowkey: "lowkey", "been lowkey": "been lowkey", "stayin lowkey": "stayin lowkey",
  highkey: "highkey", "been highkey": "been highkey", "actin highkey": "actin highkey",
  "pull up": "pull up", "pulled up": "pulled up", "pullin up": "pullin up",
  "kick off": "kick off", "kicked off": "kicked off", "kickin off": "kickin off",
  "cut it": "cut it", "cuttin it": "cuttin it", "hold up": "hold up",
  "held up": "held up", "holdin up": "holdin up", "slide thru": "slide thru",
  "slid thru": "slid thru", "slidin thru": "slidin thru", speed: "speed",
  sped: "sped", speedin: "speedin", "cool it": "cool it", "cooled it": "cooled it",
  "coolin it": "coolin it", "check it": "check it", "checked it": "checked it",
  "checkin it": "checkin it", "show love": "show love", "showed love": "showed love",
  "showin love": "showin love", "brush off": "brush off", "brushed off": "brushed off",
  "brushin off": "brushin off", "sleep on": "sleep on", "slept on": "slept on",
  "sleepin on": "sleepin on", hate: "hate", hated: "hated", hatin: "hatin",
  bite: "bite", bit: "bit", bitin: "bitin", play: "play", played: "played",
  playin: "playin", grind: "grind", grinded: "grinded", grindin: "grindin",
  "lock in": "lock in", "locked in": "locked in", "lockin in": "lockin in",
  ghost: "ghost", ghosted: "ghosted", ghostin: "ghostin", catch: "catch",
  caught: "caught", catchin: "catchin", "make it": "make it", "made it": "made it",
  "makin it": "makin it", fold: "fold", folded: "folded", foldin: "foldin",
  whine: "whine", whined: "whined", whinin: "whinin", clean: "clean",
  "was clean": "was clean", "lookin clean": "lookin clean",
};

function niggifier(text) {
  let words = text.split(/\s+/);
  let transformed = words.map((word) => {
    let clean = word.toLowerCase().replace(/[^a-z]/g, "");
    if (slangMap[clean]) {
      return slangMap[clean].toUpperCase();
    }
    return word.toUpperCase();
  });
  return transformed.join(" ");
}

const ignoredRoles = ["1445970213710594260", "1460191925918367859"];

// ============================================
// 🏙️ HOOD SYSTEM DEFINITIONS
// ============================================

const HOODS = {
  southside: {
    name: "Southside",
    fullName: "🏚️ Southside – The Bottom",
    story: "Southside is where the city was born – old brick buildings, corner stores, and generations of families. It's poor but proud. Everybody knows everybody, and loyalty runs deep. The cops don't come around much, so the streets run on their own code. If you're from The Bottom, you learn to survive with what you got.",
    perks: {
      description: "• **Hood Famous** – +10% respect gain (lower heat from small crimes)\n• **Hand Me Downs** – 5% chance to find an extra item when scavenging\n• **Family Ties** – Slightly better prices from Jamal",
      modifiers: {
        heatFromSmallCrimes: 0.9,
        scavengeBonusChance: 0.05,
        shopDiscount: 0.95,
      }
    },
    color: 0x8B4513,
    emoji: "🏚️"
  },
  northside: {
    name: "Northside",
    fullName: "🏙️ Northside – Uptown",
    story: "Uptown is where dreams are made – high-rises, fancy boutiques, and celebrities. Everyone here is trying to make it big. The hustle is real, but so are the eyes. Cops patrol regularly, so you gotta be slick. Uptown is for those who want the spotlight but can handle the heat.",
    perks: {
      description: "• **Glossy Drip** – +15% earnings from legal work\n• **Connections** – Better odds in gambling (win chance +5%)\n• **Safe Streets** – Stash house has +20% default security",
      modifiers: {
        workEarnings: 1.15,
        gambleWinChance: 0.05,
        stashSecurity: 1.2,
      }
    },
    color: 0x1E90FF,
    emoji: "🏙️"
  },
  eastside: {
    name: "Eastside",
    fullName: "🏭 Eastside – The Industrial",
    story: "Factories, warehouses, and abandoned lots – Eastside is the city's engine room. It's rough, loud, and full of opportunities if you're willing to get your hands dirty. The real money is in moving product through the industrial corridors. You'll work hard, but you'll eat well.",
    perks: {
      description: "• **Heavy Lifting** – +20% earnings from `/hustle work`\n• **Warehouse Access** – +10% stash capacity\n• **No Questions Asked** – 10% cheaper black market prices",
      modifiers: {
        hustleWorkEarnings: 1.2,
        stashCapacity: 1.1,
        blackMarketDiscount: 0.9,
      }
    },
    color: 0x808080,
    emoji: "🏭"
  },
  westside: {
    name: "Westside",
    fullName: "🏡 Westside – The Suburbs",
    story: "The suburbs look peaceful – manicured lawns, white picket fences. But underneath, it's where white-collar crime thrives. Identity theft, credit card fraud, and quiet deals in home offices. Westsiders are sneaky; they don't look like criminals, but they run the digital streets.",
    perks: {
      description: "• **Clean Cut** – Heat decays 20% faster\n• **Digital Hustle** – Better outcomes from `/crime` (tech crimes)\n• **Garage Stash** – Car items are 15% more effective",
      modifiers: {
        heatDecay: 1.2,
        crimeSuccessTech: 1.15,
        carEffectiveness: 1.15,
      }
    },
    color: 0x32CD32,
    emoji: "🏡"
  },
  downtown: {
    name: "Downtown",
    fullName: "🏢 Downtown – The Core",
    story: "Downtown is the heart of power – city hall, corporate towers, and underground clubs. It's where deals are made and backs are stabbed. You're either a player or a pawn. Downtown demands respect, connections, and a thick skin. If you can make it here, you can make it anywhere.",
    perks: {
      description: "• **City Hall Connections** – 20% lower fines\n• **Elite Network** – Access to high-stakes gambling (higher limits, +10% odds)\n• **Insider Trading** – +5% on investments",
      modifiers: {
        fineReduction: 0.8,
        gambleHighStakes: true,
        investmentBonus: 1.05,
      }
    },
    color: 0x800080,
    emoji: "🏢"
  }
};

// ============================================
// 🛠️ HELPER FUNCTIONS
// ============================================

const getPlayerData = (userId) => {
  if (!playerData.has(userId)) {
    playerData.set(userId, { ...defaultPlayerData });
    scheduleSave();
  }
  return playerData.get(userId);
};

function updateStreetCred(userId, amount) {
  const data = getPlayerData(userId);
  data.streetCred += amount;
  if (data.streetCred >= 1000 && !data.achievements.includes("hood_king")) {
    data.achievements.push("hood_king");
    data.bread += 500;
    scheduleSave();
    return `🏆 Achievement Unlocked: **Hood King**! +500 bread!`;
  }
  scheduleSave();
  return null;
}

function getStreetRank(bread) {
  if (bread > 1000000) return { name: "💎 Kingpin", cdMult: 0.5 };
  if (bread > 500000) return { name: "🔥 Boss", cdMult: 0.7 };
  if (bread > 100000) return { name: "💸 Hustler", cdMult: 0.85 };
  if (bread > 50000) return { name: "📍 Corner Kid", cdMult: 0.95 };
  return { name: "🥚 Newbie", cdMult: 1.0 };
}

// ============================================
// 🎮 GAME STATE
// ============================================

const ticTacToeGames = new Map(); // key: gameId, value: { player1, player2, board, turn, bet }
const activeTrivia = new Map();
const blackjackGames = new Map();

// ============================================
// ♠️ BLACKJACK HELPER FUNCTIONS
// ============================================

function createDeck() {
  const suits = ['♠', '♥', '♦', '♣'];
  const ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
  const deck = [];
  for (const suit of suits) {
    for (const rank of ranks) {
      deck.push({ rank, suit });
    }
  }
  return shuffle(deck);
}

function shuffle(deck) {
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

function cardValue(card) {
  if (['J', 'Q', 'K'].includes(card.rank)) return 10;
  if (card.rank === 'A') return 11;
  return parseInt(card.rank);
}

function handTotal(hand) {
  let total = 0;
  let aces = 0;
  for (const card of hand) {
    if (card.rank === 'A') aces++;
    total += cardValue(card);
  }
  while (total > 21 && aces > 0) {
    total -= 10;
    aces--;
  }
  return total;
}

function handToString(hand) {
  return hand.map(c => `${c.rank}${c.suit}`).join(' ');
}

// ============================================
// 🎮 TIC-TAC-TOE HELPERS
// ============================================

function createTicTacToeBoard() {
  return [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '];
}

function checkTicTacToeWinner(board) {
  const winPatterns = [
    [0,1,2], [3,4,5], [6,7,8],
    [0,3,6], [1,4,7], [2,5,8],
    [0,4,8], [2,4,6]
  ];
  for (const pattern of winPatterns) {
    const [a,b,c] = pattern;
    if (board[a] !== ' ' && board[a] === board[b] && board[a] === board[c]) {
      return board[a];
    }
  }
  if (board.every(cell => cell !== ' ')) return 'tie';
  return null;
}

// ============================================
// 💀 DUMB WAYS TO DIE
// ============================================

const killMessages = [
  "died from their own stupidity.",
  "stubbed their toe and died.",
  "choked on air.",
  "tried to drink bleach but missed.",
  "got hit by a falling piano.",
  "was scared to death by their own reflection.",
  "forgot how to breathe.",
  "tried to fight a goose and lost.",
  "ate too many hot wings and ascended.",
  "slipped on a banana peel and hit their head.",
  "was killed by a rogue shopping cart.",
  "fell into a manhole while texting.",
  "got lost in a corn maze and gave up.",
  "was flattened by a vending machine.",
  "tried to pet a lion.",
  "died of cringe.",
  "was eliminated by a Minecraft bed.",
  "forgot to save and got overwritten.",
  "was deleted by a system update.",
  "drowned in a puddle.",
  "was crushed by a stack of pancakes.",
  "had a heart attack from bad grammar.",
  "was vaporized by a laser pointer.",
  "got abducted by aliens and probed to death.",
  "was smited by an angry god.",
  "died of laughter from a terrible joke.",
  "was beaten to death by a angry mob of gnomes.",
  "fell off a cliff while taking a selfie.",
  "was buried alive by their own ego.",
  "exploded for no reason.",
  "was disintegrated by a microwave.",
  "tried to time travel and got stuck in a wall.",
  "was erased from existence by a paradox.",
  "died of boredom during this command.",
  "was killed by a wild Karen.",
  "got doxxed and died of shame.",
  "was roasted so hard they combusted.",
  "drank expired milk and perished.",
  "was taken out by a boomerang.",
  "fell into a black hole.",
  "was smacked by a flying fish.",
  "got hit by a stray bullet from a Nerf war.",
  "was poked by a very sharp stick.",
  "died of FOMO.",
  "was scared by a shadow.",
  "fell asleep and never woke up.",
  "was unplugged mid-sentence.",
  "got folded like laundry.",
  "was yeeted into the sun.",
  "lost a staring contest with the sun.",
  "was killed by a hypothetical question.",
  "died waiting for the bus.",
  "was done in by a rogue sock.",
  "choked on a watermelon seed.",
  "was assassinated by a ninja squirrel.",
  "got taken out by a rogue Roomba.",
  "was defeated by a level 1 slime.",
  "fell into a pit of marshmallows and suffocated.",
  "was beaten by a grandma with a purse.",
  "died from a paper cut that got infected.",
  "was struck by lightning while holding a metal stick.",
  "got hit by a car while crossing the street legally.",
  "was killed by a falling coconut.",
  "drank too much lean and flatlined.",
  "was smoked by the opps.",
  "got caught lacking and never recovered.",
  "was finished by a critical hit.",
  "died of secondhand embarrassment.",
];

// ============================================
// 🗣️ JAMAL'S RANDOM SPEAKING & REACTIONS
// ============================================

let speakCounter = 0;
let speakThreshold = Math.floor(Math.random() * (40 - 20 + 1)) + 20;

// Phrases when mentioned or replied to
const mentionReplies = [
  "Yo what it do?",
  "You talkin to me?",
  "Wassup cuz?",
  "You need somethin?",
  "I'm out here, what's good?",
  "Don't be shy, speak your mind.",
  "Yeah?",
  "You rang?",
  "Who summon me?",
  "Ayy, I'm here.",
  "Spit it out, homie.",
  "You want somethin from Jamal?",
  "I'm listenin.",
  "Talk to me nice.",
  "What's the word on the block?",
  "You know I'm always around.",
  "You need a favor or somethin?",
  "I see you.",
  "Respect.",
  "Keep it 100 with me.",
  "On my mama, I'm here for you.",
  "You got my attention.",
  "Let's hear it.",
  "What's poppin?",
  "Say that again?",
  "I'm tuned in.",
  "Go ahead, I'm locked in.",
  "You called?",
  "What's the move?",
  "You good?",
];

// ============================================
// 🎯 MESSAGE HANDLER (with fried chicken mini-game)
// ============================================

let wisdomCounter = 0;
let nextWisdom = Math.floor(Math.random() * (50 - 30 + 1)) + 30;
let interactionCounter = 0;
let nextInteraction = Math.floor(Math.random() * (100 - 50 + 1)) + 50;

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;
  if (message.member && message.member.roles.cache.some((r) => ignoredRoles.includes(r.id))) return;

  const content = message.content.toLowerCase();
  const nWordRegex = /\bnigg[ae]r?\b/i;
  if (nWordRegex.test(message.content)) {
    const data = getPlayerData(message.author.id);
    data.roastsReceived++;

    if (/\bnigger\b/i.test(message.content)) {
      const roast = hardRReplies[Math.floor(Math.random() * hardRReplies.length)];
      message.reply(`${roast}\n\n⚠️ **HEAT +20** - The 12 are watching you now!`);
      data.heat += 20;
      if (data.heat > 100) data.heat = 100;
    } else if (/\bnigga\b/i.test(message.content)) {
      const roast = softAReplies[Math.floor(Math.random() * softAReplies.length)];
      message.reply(`${roast}\n\n⚠️ **HEAT +10** - You're attracting attention!`);
      data.heat += 10;
      if (data.heat > 100) data.heat = 100;
    }

    scheduleSave();

    if (data.heat >= 80 && Math.random() > 0.7) {
      setTimeout(() => {
        message.channel.send(
          `🚔 **POLICE RAID!** <@${message.author.id}>, the 12 just hit your trap house! You lost ${Math.floor(data.bread * 0.3)} bread!`
        );
        data.bread = Math.floor(data.bread * 0.7);
        data.heat = Math.floor(data.heat * 0.5);
        scheduleSave();
      }, 3000);
    }
    return; // n-word takes priority, so we return early
  }

  // ---------- REPLY/MENTION DETECTION ----------
  const isMentioned = message.mentions.has(client.user);
  let isReplyToBot = false;
  if (message.reference) {
    try {
      const referenced = await message.channel.messages.fetch(message.reference.messageId);
      if (referenced.author.id === client.user.id) isReplyToBot = true;
    } catch (e) {
      // Ignore if message was deleted or inaccessible
    }
  }

  if (isMentioned || isReplyToBot) {
    // Pick a random reply phrase
    let phrase = mentionReplies[Math.floor(Math.random() * mentionReplies.length)];
    // 30% chance to add a second sentence from quotes
    if (Math.random() < 0.3) {
      const second = quotes[Math.floor(Math.random() * quotes.length)];
      phrase = `${phrase} ${second}`;
    }
    // 20% chance to add a third sentence
    if (Math.random() < 0.2) {
      const third = quotes[Math.floor(Math.random() * quotes.length)];
      phrase = `${phrase} ${third}`;
    }
    await message.reply(phrase);
    // Don't return – let random events still happen (counters increment)
  }

  // ---------- WISDOM & INTERACTION COUNTERS (unchanged) ----------
  wisdomCounter++;
  if (wisdomCounter >= nextWisdom) {
    wisdomCounter = 0;
    nextWisdom = Math.floor(Math.random() * (50 - 30 + 1)) + 30;
  }

  interactionCounter++;
  if (interactionCounter >= nextInteraction) {
    interactionCounter = 0;
    nextInteraction = Math.floor(Math.random() * (100 - 50 + 1)) + 50;
    const event = Math.random();
    const data = getPlayerData(message.author.id);

    if (event < 0.3) {
      const item = lootItems[Math.floor(Math.random() * lootItems.length)];
      data.inventory.push(item);
      scheduleSave();
      message.channel.send(`🎁 **RANDOM EVENT:** Jamal blessed <@${message.author.id}> with ${item}! Added to your inventory.`);
    } else if (event < 0.6) {
      if (data.inventory.length > 0) {
        const stolenIndex = Math.floor(Math.random() * data.inventory.length);
        const stolenItem = data.inventory.splice(stolenIndex, 1)[0];
        scheduleSave();
        message.channel.send(`😈 **RANDOM EVENT:** Jamal stole <@${message.author.id}>'s ${stolenItem}! Better watch your stuff!`);
      } else {
        message.channel.send(`🤡 **RANDOM EVENT:** Jamal tried to rob <@${message.author.id}> but you're broke as hell!`);
      }
    } else if (event < 0.8) {
      if (data.heat > 50) {
        const fine = Math.floor(data.bread * 0.2);
        data.bread -= fine;
        data.heat -= 30;
        scheduleSave();
        message.channel.send(`🚓 **POLICE CHECKPOINT:** <@${message.author.id}> got stopped by the 12! Paid ${fine} bread in fines. Heat -30`);
      } else {
        message.channel.send(`✅ **POLICE CHECKPOINT:** <@${message.author.id}> slid through clean. Your heat level is low enough (${data.heat}%).`);
      }
    } else {
      const win = Math.random() > 0.5;
      if (win) {
        const winnings = Math.floor(Math.random() * 500) + 100;
        data.bread += winnings;
        data.streetCred += 10;
        scheduleSave();
        message.channel.send(`🥊 **STREET FIGHT:** <@${message.author.id}> won the fight! +${winnings} bread, +10 street cred!`);
      } else {
        const loss = Math.floor(data.bread * 0.1);
        data.bread -= loss;
        scheduleSave();
        message.channel.send(`😵 **STREET FIGHT:** <@${message.author.id}> got knocked out! Lost ${loss} bread.`);
      }
    }

    // Fried chicken mini-game (20% chance)
    if (Math.random() < 0.2) {
      const victim = message.author;
      const chickenMsg = `🍗 **FRIED CHICKEN ALERT!** Jamal just snatched <@${victim.id}>'s bucket of fried chicken! Click the button to give him another one before he gets mad!`;
      const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId("give_chicken").setLabel("Give Chicken").setStyle(ButtonStyle.Primary)
      );
      message.channel.send({ content: chickenMsg, components: [row] });
    }

    // Hood event (10% chance)
    if (data.hood && data.hood.name) {
      const hoodEvent = Math.random();
      if (hoodEvent < 0.1) {
        switch (data.hood.name) {
          case 'southside':
            message.channel.send(`🏚️ **HOOD EVENT:** An old lady from Southside gave you some homemade cookies. +50 bread.`);
            data.bread += 50;
            break;
          case 'northside':
            message.channel.send(`🏙️ **HOOD EVENT:** A businessman slipped you a tip. +100 bread.`);
            data.bread += 100;
            break;
          case 'eastside':
            message.channel.send(`🏭 **HOOD EVENT:** Found some scrap metal to sell. +75 bread.`);
            data.bread += 75;
            break;
          case 'westside':
            message.channel.send(`🏡 **HOOD EVENT:** Your neighbor paid you to watch their house. +80 bread.`);
            data.bread += 80;
            break;
          case 'downtown':
            message.channel.send(`🏢 **HOOD EVENT:** A lobbyist gave you a 'consultation fee'. +200 bread.`);
            data.bread += 200;
            break;
        }
        scheduleSave();
      }
    }
  }

  // ---------- RANDOM REACTION (5% chance) ----------
  if (Math.random() < 0.05) {
    const emoji = Math.random() < 0.5 ? '💀' : '🥷🏿';
    try {
      await message.react(emoji);
    } catch (e) {
      // Ignore if we can't react (no permission, etc.)
    }
  }

  // ---------- RANDOM SPEAKING (after a certain number of messages) ----------
  speakCounter++;
  if (speakCounter >= speakThreshold) {
    speakCounter = 0;
    speakThreshold = Math.floor(Math.random() * (40 - 20 + 1)) + 20;
    // Send a random quote to the same channel
    const quote = quotes[Math.floor(Math.random() * quotes.length)];
    message.channel.send(quote).catch(() => {});
  }
});

// ============================================
// 🎮 SLASH COMMANDS REGISTRATION (NO DUPLICATES)
// ============================================

const commands = [
  // Roast command
  new SlashCommandBuilder()
    .setName("roast")
    .setDescription("🔥 Roast someone into oblivion")
    .addSubcommand(sub => sub.setName("user").setDescription("Roast a specific user").addUserOption(opt => opt.setName("target").setDescription("Who needs to be roasted?").setRequired(true)).addStringOption(opt => opt.setName("category").setDescription("Type of roast").addChoices(
      { name: "🔥 Appearance", value: "appearance" },
      { name: "🧠 Intelligence", value: "intelligence" },
      { name: "👤 Personality", value: "personality" },
      { name: "🏙️ Hood", value: "hood" },
      { name: "💀 Savage", value: "savage" },
      { name: "🎲 Random", value: "random" }
    )))
    .addSubcommand(sub => sub.setName("list").setDescription("Show all roast categories"))
    .addSubcommand(sub => sub.setName("random").setDescription("Roast a random user in the server"))
    .addSubcommand(sub => sub.setName("self").setDescription("Roast yourself (you brave soul)"))
    .addSubcommand(sub => sub.setName("jamal").setDescription("Try to roast Jamal (not recommended)")),

  // Economy
  new SlashCommandBuilder().setName("bread").setDescription("Check your bread balance"),
  new SlashCommandBuilder().setName("daily").setDescription("Claim your daily bread"),
  new SlashCommandBuilder().setName("shop").setDescription("Buy enhancers and multipliers for more bread"),
  new SlashCommandBuilder().setName("buy").setDescription("Buy an item from the shop").addStringOption(opt => opt.setName("item").setDescription("Item ID").setRequired(true)),
  new SlashCommandBuilder().setName("monthly").setDescription("Claim your monthly bread (Requires Monthly Pass)"),
  new SlashCommandBuilder().setName("pockets").setDescription("Check someone's pockets").addUserOption(opt => opt.setName("user").setDescription("User to check")),
  new SlashCommandBuilder().setName("leaderboard").setDescription("Show the richest players"),

  // Fun commands
  new SlashCommandBuilder().setName("slap").setDescription("Slap someone for talking crazy").addUserOption(opt => opt.setName("user").setDescription("Who needs a reality check").setRequired(true)),
  new SlashCommandBuilder().setName("twerk").setDescription("Jamal shows off his moves"),
  new SlashCommandBuilder().setName("sniff").setDescription("Sniff the chat to see if something is fishy"),
  new SlashCommandBuilder().setName("fish").setDescription("Go fishing for bread").addIntegerOption(opt => opt.setName("amount").setDescription("Bet amount").setRequired(true).setMinValue(10)),
  new SlashCommandBuilder().setName("kill").setDescription("🔪 Kill someone (just for fun)").addUserOption(opt => opt.setName("user").setDescription("Who to kill").setRequired(true)),
  new SlashCommandBuilder().setName("8ball").setDescription("Ask the magic 8-ball a question").addStringOption(opt => opt.setName("question").setDescription("Your question").setRequired(true)),
  new SlashCommandBuilder().setName("dab").setDescription("Dab on the haters").addUserOption(opt => opt.setName("user").setDescription("Who to dab on (optional)").setRequired(false)),
  new SlashCommandBuilder().setName("yeet").setDescription("Yeet something or someone").addStringOption(opt => opt.setName("thing").setDescription("What to yeet").setRequired(true)),
  new SlashCommandBuilder().setName("mock").setDescription("Mock someone's message").addStringOption(opt => opt.setName("text").setDescription("Text to mock").setRequired(true)),
  new SlashCommandBuilder().setName("fact").setDescription("Get a random fun fact"),
  new SlashCommandBuilder().setName("joke").setDescription("Tell a random joke"),
  new SlashCommandBuilder().setName("pun").setDescription("Get a terrible pun"),

  // Crime
  new SlashCommandBuilder().setName("crime").setDescription("Commit a random crime (risky)"),

  // Games
  new SlashCommandBuilder()
    .setName("play")
    .setDescription("🎮 Play games")
    .addSubcommand(sub => sub.setName("tictactoe").setDescription("Play Tic-Tac-Toe").addUserOption(opt => opt.setName("opponent").setDescription("Play against a friend").setRequired(true)).addIntegerOption(opt => opt.setName("bet").setDescription("Bet amount (optional)").setRequired(false).setMinValue(10)))
    .addSubcommand(sub => sub.setName("trivia").setDescription("Hood trivia challenge"))
    .addSubcommand(sub => sub.setName("coinflip").setDescription("Flip a coin with someone").addUserOption(opt => opt.setName("opponent").setDescription("Your opponent").setRequired(true)).addIntegerOption(opt => opt.setName("amount").setDescription("Bet amount").setRequired(true).setMinValue(10)))
    .addSubcommand(sub => sub.setName("type").setDescription("Type race challenge").addUserOption(opt => opt.setName("opponent").setDescription("Your opponent").setRequired(true)))
    .addSubcommand(sub => sub.setName("blackjack").setDescription("Play blackjack against another player or the dealer").addIntegerOption(opt => opt.setName("bet").setDescription("Bet amount").setRequired(true).setMinValue(10)).addUserOption(opt => opt.setName("opponent").setDescription("Opponent (leave empty to play against the dealer)").setRequired(false))),

  // Bet command (button-based coinflip)
  new SlashCommandBuilder().setName("bet").setDescription("Challenge someone to a coin flip bet (with buttons)").addUserOption(opt => opt.setName("user").setDescription("Opponent").setRequired(true)).addIntegerOption(opt => opt.setName("amount").setDescription("Bet amount").setRequired(true).setMinValue(10)),

  // Scratch
  new SlashCommandBuilder().setName("scratch").setDescription("Buy a scratch-off ticket (cost 500 bread)"),

  // Rob
  new SlashCommandBuilder().setName("rob").setDescription("Rob another user").addUserOption(opt => opt.setName("user").setDescription("Who to rob").setRequired(true)),

  // Gamble
  new SlashCommandBuilder().setName("gamble").setDescription("Gamble your bread (40% win chance)").addIntegerOption(opt => opt.setName("amount").setDescription("Amount to bet").setRequired(true).setMinValue(10)),

  // Slots
  new SlashCommandBuilder().setName("slots").setDescription("Play the slot machine").addIntegerOption(opt => opt.setName("amount").setDescription("Bet amount").setRequired(true).setMinValue(10)),

  // Race
  new SlashCommandBuilder().setName("race").setDescription("Join an illegal street race").addIntegerOption(opt => opt.setName("amount").setDescription("Entry fee").setRequired(true).setMinValue(10)),

  // Drill
  new SlashCommandBuilder().setName("drill").setDescription("Go on a drill (risky)").addIntegerOption(opt => opt.setName("amount").setDescription("Optional gear-up cost").setMinValue(0)),

  // Scavenge
  new SlashCommandBuilder().setName("scavenge").setDescription("Scavenge the block for bread"),

  // Hustle command with all subcommands
  new SlashCommandBuilder()
    .setName("hustle")
    .setDescription("Various street hustles")
    .addSubcommand(sub => sub.setName("work").setDescription("Do some legal work"))
    .addSubcommand(sub => sub.setName("random").setDescription("Random hustle opportunity"))
    .addSubcommand(sub => sub.setName("corner").setDescription("Work the corner (risky)"))
    .addSubcommand(sub => sub.setName("freestyle").setDescription("Freestyle for some bread"))
    .addSubcommand(sub => sub.setName("pickpocket").setDescription("Try to pickpocket someone"))
    .addSubcommand(sub => sub.setName("hijack").setDescription("Hijack a car (very risky)")),

  // Jamal command with all subcommands (ONLY ONE steal with optional item)
  new SlashCommandBuilder()
    .setName("jamal")
    .setDescription("Jamal interaction")
    .addSubcommand(sub => sub.setName("give").setDescription("Jamal gives someone something").addUserOption(opt => opt.setName("user").setDescription("Who to give to").setRequired(true)))
    .addSubcommand(sub => sub.setName("lick").setDescription("Lick someone's money").addUserOption(opt => opt.setName("user").setDescription("Who to lick").setRequired(true)))
    .addSubcommand(sub => sub.setName("say").setDescription("Jamal says something random"))
    .addSubcommand(sub => sub.setName("stash").setDescription("Hide bread in your crib").addIntegerOption(opt => opt.setName("amount").setDescription("Amount to stash").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("unstash").setDescription("Get bread from your crib").addIntegerOption(opt => opt.setName("amount").setDescription("Amount to unstash").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("rap").setDescription("Jamal drops a fire verse"))
    .addSubcommand(sub => sub.setName("steal").setDescription("Jamal starts a robbery").addUserOption(opt => opt.setName("user").setDescription("Who to steal from").setRequired(true)).addStringOption(opt => opt.setName("item").setDescription("What to steal (optional)").setRequired(false)))
    .addSubcommand(sub => sub.setName("dice").setDescription("Play street craps dice game").addIntegerOption(opt => opt.setName("bet").setDescription("Amount to bet").setMinValue(10)))
    .addSubcommand(sub => sub.setName("share").setDescription("Share bread with another user").addUserOption(opt => opt.setName("user").setDescription("Who to share with").setRequired(true)).addIntegerOption(opt => opt.setName("amount").setDescription("Amount of bread to share").setMinValue(1).setRequired(true)))
    .addSubcommand(sub => sub.setName("block").setDescription("Check how hot the block is"))
    .addSubcommand(sub => sub.setName("drip").setDescription("Jamal rates your hood drip"))
    .addSubcommand(sub => sub.setName("ops").setDescription("Check for ops in the area"))
    .addSubcommand(sub => sub.setName("smoke").setDescription("Jamal sparks one up with you"))
    .addSubcommand(sub => sub.setName("drill").setDescription("Jamal goes on a drill").addUserOption(opt => opt.setName("target").setDescription("The target for the drill").setRequired(true)))
    .addSubcommand(sub => sub.setName("flex").setDescription("Flex your items in the chat"))
    .addSubcommand(sub => sub.setName("lean").setDescription("Jamal pours up a double cup"))
    .addSubcommand(sub => sub.setName("court").setDescription("Jamal goes to court for his charges"))
    .addSubcommand(sub => sub.setName("bando").setDescription("Visit the abandoned house with Jamal"))
    .addSubcommand(sub => sub.setName("trap").setDescription("Jamal puts you to work in the trap"))
    .addSubcommand(sub => sub.setName("spin").setDescription("Jamal spins the block for you"))
    .addSubcommand(sub => sub.setName("chill").setDescription("Chill in the cut with Jamal"))
    .addSubcommand(sub => sub.setName("bail").setDescription("Bail Jamal out of jail"))
    .addSubcommand(sub => sub.setName("stimulus").setDescription("Check if your stimulus check hit"))
    .addSubcommand(sub => sub.setName("snitch").setDescription("Jamal deals with a snitch").addUserOption(opt => opt.setName("user").setDescription("The suspected rat").setRequired(true))),

  // Utilities
  new SlashCommandBuilder().setName("niggifier").setDescription("Turn text into hood talk").addStringOption(opt => opt.setName("text").setDescription("The text to transform").setRequired(true)),
  new SlashCommandBuilder().setName("fetchuser").setDescription("Fetch user info by ID").addStringOption(opt => opt.setName("userid").setDescription("The User ID").setRequired(true)),

  // Admin
  new SlashCommandBuilder()
    .setName("jose")
    .setDescription("🔒 Developer commands (Jose only)")
    .addSubcommand(sub => sub.setName("give_bread").setDescription("Give bread to a user").addUserOption(opt => opt.setName("user").setDescription("User to give bread to").setRequired(true)).addIntegerOption(opt => opt.setName("amount").setDescription("Amount of bread").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("give_item").setDescription("Give item to a user").addUserOption(opt => opt.setName("user").setDescription("User to give item to").setRequired(true)).addStringOption(opt => opt.setName("item").setDescription("Item name").setRequired(true)).addIntegerOption(opt => opt.setName("quantity").setDescription("Quantity (default: 1)").setMinValue(1)))
    .addSubcommand(sub => sub.setName("wipe").setDescription("Wipe a user's data").addUserOption(opt => opt.setName("user").setDescription("User to wipe").setRequired(true)))
    .addSubcommand(sub => sub.setName("set_multiplier").setDescription("Set a user's multiplier").addUserOption(opt => opt.setName("user").setDescription("User to modify").setRequired(true)).addNumberOption(opt => opt.setName("value").setDescription("Multiplier value").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("set_heat").setDescription("Set a user's heat level").addUserOption(opt => opt.setName("user").setDescription("User to modify").setRequired(true)).addIntegerOption(opt => opt.setName("value").setDescription("Heat value (0-100)").setRequired(true).setMinValue(0).setMaxValue(100)))
    .addSubcommand(sub => sub.setName("set_cred").setDescription("Set a user's street cred").addUserOption(opt => opt.setName("user").setDescription("User to modify").setRequired(true)).addIntegerOption(opt => opt.setName("value").setDescription("Street cred value").setRequired(true).setMinValue(0)))
    .addSubcommand(sub => sub.setName("set_stash").setDescription("Set a user's stash capacity").addUserOption(opt => opt.setName("user").setDescription("User to modify").setRequired(true)).addIntegerOption(opt => opt.setName("value").setDescription("Stash capacity").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("reset_cooldowns").setDescription("Reset a user's cooldowns").addUserOption(opt => opt.setName("user").setDescription("User to reset").setRequired(true)))
    .addSubcommand(sub => sub.setName("transfer_bread").setDescription("Transfer bread from one user to another").addUserOption(opt => opt.setName("from").setDescription("User to take bread from").setRequired(true)).addUserOption(opt => opt.setName("to").setDescription("User to give bread to").setRequired(true)).addIntegerOption(opt => opt.setName("amount").setDescription("Amount to transfer").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("inspect").setDescription("Inspect a user's data").addUserOption(opt => opt.setName("user").setDescription("User to inspect").setRequired(true)))
    .addSubcommand(sub => sub.setName("global_bonus").setDescription("Give bonus to all users").addIntegerOption(opt => opt.setName("amount").setDescription("Amount per user").setRequired(true).setMinValue(1)))
    .addSubcommand(sub => sub.setName("set_level").setDescription("Set a user's trap house level").addUserOption(opt => opt.setName("user").setDescription("User to modify").setRequired(true)).addIntegerOption(opt => opt.setName("level").setDescription("Level (1-5)").setRequired(true).setMinValue(1).setMaxValue(5)))
    .addSubcommand(sub => sub.setName("save_data").setDescription("Force save all player data immediately")),

  // Hood commands
  new SlashCommandBuilder()
    .setName("hood")
    .setDescription("🏙️ Hood system – rep your turf")
    .addSubcommand(sub =>
      sub.setName("pick")
        .setDescription("Choose your hood (one-time free choice)")
        .addStringOption(opt =>
          opt.setName("hood")
            .setDescription("The hood you want to rep")
            .setRequired(true)
            .addChoices(
              { name: "🏚️ Southside – The Bottom", value: "southside" },
              { name: "🏙️ Northside – Uptown", value: "northside" },
              { name: "🏭 Eastside – The Industrial", value: "eastside" },
              { name: "🏡 Westside – The Suburbs", value: "westside" },
              { name: "🏢 Downtown – The Core", value: "downtown" }
            )
        )
    )
    .addSubcommand(sub =>
      sub.setName("info")
        .setDescription("View your current hood's story and perks")
    )
    .addSubcommand(sub =>
      sub.setName("stats")
        .setDescription("View hood loyalty and reputation")
    )
    .addSubcommand(sub =>
      sub.setName("change")
        .setDescription("Switch hoods (costs 1,000,000 bread)")
    )
    .addSubcommand(sub =>
      sub.setName("loyalty")
        .setDescription("Check your loyalty level to your hood")
    )
    .addSubcommand(sub =>
      sub.setName("leaderboard")
        .setDescription("See hood rankings")
    ),
].map(cmd => cmd.toJSON());

// ========== CREATE REST CLIENT ==========
const rest = new REST({ version: "10" }).setToken(token);

// ========== REGISTER COMMANDS ==========
(async () => {
  try {
    console.log('⏳ Registering slash commands...');
    await rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: commands });
    console.log('✅ Slash commands registered!');
  } catch (error) {
    console.error('❌ Failed to register commands:', error);
  }
})();

// ============================================
// 🎯 INTERACTION HANDLER
// ============================================

client.on("interactionCreate", async (interaction) => {
  // ---------- BUTTON HANDLERS ----------
  if (interaction.isButton()) {
    const parts = interaction.customId.split("_");

    // Bet buttons
    if (parts[0] === "bet") {
      const action = parts[1];
      const challengerId = parts[2];
      const targetId = parts[3];
      const amount = parseInt(parts[4]);

      if (interaction.user.id !== targetId) {
        return interaction.reply({ content: "This ain't your bet, move along.", ephemeral: true });
      }

      if (action === "decline") {
        return interaction.update({ content: "Bet declined. Pussy.", embeds: [], components: [] });
      }

      if (action === "accept") {
        const challengerData = getPlayerData(challengerId);
        const targetData = getPlayerData(targetId);

        if (challengerData.bread < amount || targetData.bread < amount) {
          return interaction.update({ content: "Someone ain't got the bread no more. Bet cancelled.", embeds: [], components: [] });
        }

        const win = Math.random() > 0.5;
        if (win) {
          challengerData.bread += amount;
          targetData.bread -= amount;
          interaction.update({ content: `🎰 <@${challengerId}> won the flip and snatched **${amount}** bread from <@${targetId}>!`, embeds: [], components: [] });
        } else {
          challengerData.bread -= amount;
          targetData.bread += amount;
          interaction.update({ content: `🎰 <@${targetId}> won the flip and snatched **${amount}** bread from <@${challengerId}>!`, embeds: [], components: [] });
        }
        scheduleSave();
      }
      return;
    }

    // TicTacToe buttons
    if (parts[0] === "ttt") {
      const gameId = parts[1];
      const action = parts[2];
      const game = ticTacToeGames.get(gameId);
      if (!game) return interaction.update({ content: "Game expired!", components: [] });

      // Check if it's the player's turn
      if (interaction.user.id !== game.turn) {
        return interaction.reply({ content: "It's not your turn!", ephemeral: true });
      }

      if (action === "quit") {
        ticTacToeGames.delete(gameId);
        return interaction.update({ content: `🚪 Game ended.`, components: [] });
      }

      const index = parseInt(action);
      if (game.board[index] !== ' ') {
        return interaction.reply({ content: "That spot is already taken!", ephemeral: true });
      }

      // Place mark
      const symbol = game.turn === game.player1 ? 'X' : 'O';
      game.board[index] = symbol;

      // Check winner
      const winner = checkTicTacToeWinner(game.board);
      if (winner) {
        ticTacToeGames.delete(gameId);
        let resultMsg = "";
        if (winner === 'tie') {
          resultMsg = `🤝 **It's a tie!**`;
          if (game.bet) {
            // return bets (no transfer)
          }
        } else {
          const winnerId = winner === 'X' ? game.player1 : game.player2;
          const loserId = winner === 'X' ? game.player2 : game.player1;
          if (game.bet) {
            const winnerData = getPlayerData(winnerId);
            const loserData = getPlayerData(loserId);
            winnerData.bread += game.bet;
            loserData.bread -= game.bet;
            scheduleSave();
            resultMsg = `🎉 **<@${winnerId}> wins!** +${game.bet} bread! <@${loserId}> lost ${game.bet} bread.`;
          } else {
            resultMsg = `🎉 **<@${winnerId}> wins!**`;
          }
        }
        return interaction.update({ content: resultMsg, components: [] });
      }

      // Switch turn
      game.turn = game.turn === game.player1 ? game.player2 : game.player1;

      // Render new board
      const rows = [];
      for (let i = 0; i < 3; i++) {
        const buttons = [];
        for (let j = 0; j < 3; j++) {
          const idx = i*3 + j;
          const cell = game.board[idx];
          const disabled = cell !== ' ' || game.turn !== interaction.user.id;
          buttons.push(
            new ButtonBuilder()
              .setCustomId(`ttt_${gameId}_${idx}`)
              .setLabel(cell === ' ' ? '⬜' : cell)
              .setStyle(cell === 'X' ? ButtonStyle.Primary : cell === 'O' ? ButtonStyle.Success : ButtonStyle.Secondary)
              .setDisabled(disabled)
          );
        }
        rows.push(new ActionRowBuilder().addComponents(...buttons));
      }
      rows.push(
        new ActionRowBuilder().addComponents(
          new ButtonBuilder()
            .setCustomId(`ttt_${gameId}_quit`)
            .setLabel("🚪 Quit")
            .setStyle(ButtonStyle.Danger)
        )
      );

      return interaction.update({
        content: `🎮 **Tic-Tac-Toe**\n<@${game.player1}> (X) vs <@${game.player2}> (O)\n\nCurrent turn: <@${game.turn}>`,
        components: rows
      });
    }

    // Trivia buttons
    if (parts[0] === "trivia") {
      const gameId = parts[1];
      const answerIndex = parseInt(parts[2]);
      const game = activeTrivia.get(gameId);
      if (!game) return interaction.update({ content: "Trivia expired!", components: [] });

      const isCorrect = answerIndex === game.question.answer;
      const userData = getPlayerData(interaction.user.id);

      if (isCorrect) {
        const reward = 100;
        userData.bread += reward;
        userData.streetCred += 5;
        const achievementMsg = updateStreetCred(interaction.user.id, 0);
        scheduleSave();
        interaction.update({
          content: `✅ **CORRECT!** +${reward} bread, +5 street cred!\n${achievementMsg ? achievementMsg + "\n" : ""}\nAnswer: **${game.question.options[game.question.answer]}**`,
          components: []
        });
      } else {
        userData.bread -= 50;
        scheduleSave();
        interaction.update({
          content: `❌ **WRONG!** -50 bread\nCorrect answer: **${game.question.options[game.question.answer]}**`,
          components: []
        });
      }
      activeTrivia.delete(gameId);
      return;
    }

    // Fried chicken button
    if (interaction.customId === "give_chicken") {
      const chance = Math.random();
      if (chance < 0.3) {
        return interaction.update({ content: 'Jamal: "ALRIGHT CUZ, WE STRAIGHT FOR NOW. DON\'T LET ME CATCH YOU SLIPPING AGAIN."', embeds: [], components: [] });
      } else {
        const responses = [
          'Jamal: "ONLY ONE BUCKET? YOU THINK I\'M SOME KIND OF BUM? GIVE ME ANOTHER ONE."',
          'Jamal: "THIS CHICKEN DRY AS HELL. GIVE ME MORE BEFORE I GET TRIGGERED."',
          'Jamal: "MY COUSIN NEED SOME TOO. PASS ANOTHER BUCKET."',
          'Jamal: "KEEP \'EM COMING. I\'M HUNGRY FOR REAL."'
        ];
        return interaction.update({ content: responses[Math.floor(Math.random() * responses.length)], components: interaction.message.components });
      }
    }

    // Blackjack buttons
    if (parts[0] === "bj") {
      const gameId = parts[1];
      const action = parts[2];
      const game = blackjackGames.get(gameId);
      if (!game) return interaction.update({ content: "Game expired!", components: [] });

      // Only the current player can act
      const isPlayer1 = interaction.user.id === game.player1.id;
      const isPlayer2 = game.player2 && interaction.user.id === game.player2.id;
      if (!isPlayer1 && !isPlayer2 && game.opponent !== 'dealer') {
        return interaction.reply({ content: "This isn't your game.", ephemeral: true });
      }
      if (game.opponent === 'dealer') {
        if (interaction.user.id !== game.player1.id) return interaction.reply({ content: "This isn't your game.", ephemeral: true });
      }

      if (action === 'hit') {
        if (game.opponent === 'dealer') {
          game.playerHand.push(game.deck.pop());
          const total = handTotal(game.playerHand);
          if (total > 21) {
            game.status = 'ended';
            const loss = game.bet;
            game.player1Data.bread -= loss;
            scheduleSave();
            blackjackGames.delete(gameId);
            return interaction.update({
              content: `🃏 **BUST!** Your hand: ${handToString(game.playerHand)} (${total})\nYou lost **${loss}** bread.`,
              components: []
            });
          } else {
            const embed = new EmbedBuilder()
              .setTitle("♠️ Blackjack")
              .setDescription(`Your hand: ${handToString(game.playerHand)} (${total})\nDealer shows: ${handToString([game.dealerHand[0]])}`)
              .setColor(0x00ff00);
            const row = new ActionRowBuilder().addComponents(
              new ButtonBuilder().setCustomId(`bj_${gameId}_hit`).setLabel("Hit").setStyle(ButtonStyle.Primary),
              new ButtonBuilder().setCustomId(`bj_${gameId}_stand`).setLabel("Stand").setStyle(ButtonStyle.Secondary),
              new ButtonBuilder().setCustomId(`bj_${gameId}_quit`).setLabel("Quit").setStyle(ButtonStyle.Danger)
            );
            return interaction.update({ embeds: [embed], components: [row] });
          }
        } else {
          const currentPlayer = interaction.user.id === game.player1.id ? game.player1 : game.player2;
          const currentHand = interaction.user.id === game.player1.id ? game.player1Hand : game.player2Hand;
          currentHand.push(game.deck.pop());
          const total = handTotal(currentHand);
          if (total > 21) {
            game.status = 'ended';
            const winner = interaction.user.id === game.player1.id ? game.player2 : game.player1;
            const loser = interaction.user;
            const winnerData = interaction.user.id === game.player1.id ? game.player2Data : game.player1Data;
            const loserData = interaction.user.id === game.player1.id ? game.player1Data : game.player2Data;
            winnerData.bread += game.bet;
            loserData.bread -= game.bet;
            scheduleSave();
            blackjackGames.delete(gameId);
            return interaction.update({
              content: `🃏 **BUST!** <@${loser.id}> busted! <@${winner.id}> wins **${game.bet}** bread!`,
              components: []
            });
          } else {
            if (interaction.user.id === game.player1.id) {
              game.currentPlayer = game.player2.id;
            } else {
              game.currentPlayer = game.player1.id;
            }
            const nextPlayer = game.currentPlayer === game.player1.id ? game.player1 : game.player2;
            const nextHand = game.currentPlayer === game.player1.id ? game.player1Hand : game.player2Hand;
            const nextTotal = handTotal(nextHand);
            const embed = new EmbedBuilder()
              .setTitle("♠️ Blackjack – Player vs Player")
              .setDescription(`<@${nextPlayer.id}>'s turn\nYour hand: ${handToString(nextHand)} (${nextTotal})`)
              .setColor(0x00ff00);
            const row = new ActionRowBuilder().addComponents(
              new ButtonBuilder().setCustomId(`bj_${gameId}_hit`).setLabel("Hit").setStyle(ButtonStyle.Primary),
              new ButtonBuilder().setCustomId(`bj_${gameId}_stand`).setLabel("Stand").setStyle(ButtonStyle.Secondary),
              new ButtonBuilder().setCustomId(`bj_${gameId}_quit`).setLabel("Quit").setStyle(ButtonStyle.Danger)
            );
            return interaction.update({ embeds: [embed], components: [row] });
          }
        }
      }

      if (action === 'stand') {
        if (game.opponent === 'dealer') {
          while (handTotal(game.dealerHand) < 17) {
            game.dealerHand.push(game.deck.pop());
          }
          const playerTotal = handTotal(game.playerHand);
          const dealerTotal = handTotal(game.dealerHand);
          let result;
          if (dealerTotal > 21 || playerTotal > dealerTotal) {
            result = `You win! +${game.bet} bread`;
            game.player1Data.bread += game.bet;
          } else if (dealerTotal === playerTotal) {
            result = `Push – your bet returned.`;
          } else {
            result = `Dealer wins! You lose ${game.bet} bread`;
            game.player1Data.bread -= game.bet;
          }
          scheduleSave();
          game.status = 'ended';
          blackjackGames.delete(gameId);
          return interaction.update({
            content: `🃏 **Final**\nYour hand: ${handToString(game.playerHand)} (${playerTotal})\nDealer hand: ${handToString(game.dealerHand)} (${dealerTotal})\n${result}`,
            components: []
          });
        } else {
          const player1Total = handTotal(game.player1Hand);
          const player2Total = handTotal(game.player2Hand);
          let result;
          if (player1Total > 21 || (player2Total <= 21 && player2Total > player1Total)) {
            result = `<@${game.player2.id}> wins **${game.bet}** bread!`;
            game.player2Data.bread += game.bet;
            game.player1Data.bread -= game.bet;
          } else if (player2Total > 21 || (player1Total <= 21 && player1Total > player2Total)) {
            result = `<@${game.player1.id}> wins **${game.bet}** bread!`;
            game.player1Data.bread += game.bet;
            game.player2Data.bread -= game.bet;
          } else {
            result = `It's a push – bets returned.`;
          }
          scheduleSave();
          game.status = 'ended';
          blackjackGames.delete(gameId);
          return interaction.update({
            content: `🃏 **Final**\n<@${game.player1.id}>: ${handToString(game.player1Hand)} (${player1Total})\n<@${game.player2.id}>: ${handToString(game.player2Hand)} (${player2Total})\n${result}`,
            components: []
          });
        }
      }

      if (action === 'quit') {
        blackjackGames.delete(gameId);
        return interaction.update({ content: "Game abandoned.", components: [] });
      }
    }
  }

  // ---------- SLASH COMMAND HANDLERS ----------
  if (interaction.isChatInputCommand()) {
    const commandName = interaction.commandName;

    // ============ FUN COMMANDS ============
    if (commandName === "twerk") {
      const responses = [
        "Jamal starts throwing it back in the middle of the chat! 🍑💨",
        "Jamal twerks so hard the whole server shakes! 🥵",
        "Jamal drops it low... real low. Too low. Now his back hurts.",
        "Jamal's twerking skills are unmatched. The opps are jealous.",
      ];
      return interaction.reply(responses[Math.floor(Math.random() * responses.length)]);
    }

    if (commandName === "sniff") {
      const smells = [
        "It smells like broke in here.",
        "I smell zaza...",
        "I smell 12 nearby...",
        "It smells like straight snitch in this chat.",
        "I smell fresh bread!",
        "Someone's been smoking that loud pack.",
        "Smells like opps are lurking.",
        "It smells like victory... or is that just my cologne?",
      ];
      return interaction.reply(`👃 Jamal takes a deep sniff...\n\n**"${smells[Math.floor(Math.random() * smells.length)]}"**`);
    }

    if (commandName === "8ball") {
      const question = interaction.options.getString("question");
      const responses = [
        "Yes", "No", "Maybe", "Hell nah", "For sure", "Keep dreaming", 
        "Jamal says yes", "Try again later", "Ask the opps", "On folks grave, yes",
        "In your dreams", "The 12 say no", "Hell yeah", "Absolutely not",
      ];
      return interaction.reply(`🎱 **8-Ball:** ${responses[Math.floor(Math.random() * responses.length)]}`);
    }

    if (commandName === "kill") {
      const target = interaction.options.getUser("user");
      const killer = interaction.user;
      const deathMsg = killMessages[Math.floor(Math.random() * killMessages.length)];
      return interaction.reply(`🔪 **${killer.username}** killed **${target.username}** – ${deathMsg}`);
    }

    if (commandName === "dab") {
      const target = interaction.options.getUser("user");
      if (target) {
        return interaction.reply(`💃 <@${interaction.user.id}> just dabbed on <@${target.id}>! Get rekt!`);
      } else {
        return interaction.reply(`💃 <@${interaction.user.id}> dabbed on the haters!`);
      }
    }

    if (commandName === "yeet") {
      const thing = interaction.options.getString("thing");
      const responses = [
        `🚀 **YEET!** ${thing} went flying into the sun!`,
        `💨 <@${interaction.user.id}> yeeted ${thing} into oblivion!`,
        `🤾‍♂️ ${thing} got yeeted so hard it landed in 3012.`,
        `🎯 ${thing} was yeeted perfectly into the trash can.`,
      ];
      return interaction.reply(responses[Math.floor(Math.random() * responses.length)]);
    }

    if (commandName === "mock") {
      let text = interaction.options.getString("text");
      // Convert to SpOnGeBoB mOcKiNg CaSe
      let mocked = text.split('').map((c, i) => i % 2 === 0 ? c.toLowerCase() : c.toUpperCase()).join('');
      return interaction.reply(`😤 **MOCKING:** ${mocked}`);
    }

    if (commandName === "fact") {
      const facts = [
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts.",
        "Bananas are berries, but strawberries aren't.",
        "Honey never spoils. Archaeologists found 3000-year-old honey still edible!",
        "A day on Venus is longer than a year on Venus.",
        "Wombat poop is cube-shaped.",
        "The shortest war in history was between Britain and Zanzibar in 1896 – it lasted 38 minutes.",
        "Cows have best friends and get stressed when separated.",
        "The Eiffel Tower can be 15 cm taller during summer.",
        "There's a species of jellyfish that is biologically immortal.",
      ];
      return interaction.reply(`📚 **FUN FACT:** ${facts[Math.floor(Math.random() * facts.length)]}`);
    }

    if (commandName === "joke") {
      const jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "What do you call a fake noodle? An impasta!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "How does a penguin build its house? Igloos it together!",
        "Why don't skeletons fight each other? They don't have the guts.",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why can't you give Elsa a balloon? Because she will let it go!",
        "What do you call a fish wearing a bowtie? So-fish-ticated!",
      ];
      return interaction.reply(`😂 **JOKE:** ${jokes[Math.floor(Math.random() * jokes.length)]}`);
    }

    if (commandName === "pun") {
      const puns = [
        "I used to be a baker, but I couldn't make enough dough.",
        "I'm reading a book on anti-gravity. It's impossible to put down!",
        "I don't trust stairs. They're always up to something.",
        "What do you call a cheese that's not yours? Nacho cheese!",
        "I would tell you a construction pun, but I'm still working on it.",
        "I have a fear of speed bumps. I'm slowly getting over it.",
        "I used to play piano by ear, but now I use my hands.",
        "I'm on a seafood diet. I see food and I eat it.",
      ];
      return interaction.reply(`🥁 **PUN:** ${puns[Math.floor(Math.random() * puns.length)]}`);
    }

    // ============ HUSTLE COMMAND ============
    if (commandName === "hustle") {
      const sub = interaction.options.getSubcommand();
      const data = getPlayerData(interaction.user.id);
      const rank = getStreetRank(data.bread + (data.stashedBread || 0));
      const carBonus = data.inventory && data.inventory.includes("car") ? 0.8 : 1.0;
      const finalCdMult = rank.cdMult * carBonus;
      const now = Date.now();

      if (sub === "work") {
        const workCooldown = (15 * 60 * 1000) * finalCdMult;
        if (data.lastWork && now - data.lastWork < workCooldown) {
          const remaining = Math.ceil((workCooldown - (now - data.lastWork)) / 60000);
          return interaction.reply({ content: `[${rank.name}] Clocked out. Wait ${remaining} mins.`, ephemeral: true });
        }
        data.lastWork = now;
        let pay = Math.floor(Math.random() * 200) + 150;
        if (data.hood && data.hood.name === 'eastside') {
          pay = Math.floor(pay * HOODS.eastside.perks.modifiers.hustleWorkEarnings);
        }
        data.bread += pay;
        scheduleSave();
        return interaction.reply(`💼 **[${rank.name}]** You did some legal street work and earned **${pay}** bread.`);
      }

      if (sub === "random") {
        const hustleCooldown = (30 * 60 * 1000) * finalCdMult;
        if (data.lastHustle && now - data.lastHustle < hustleCooldown) {
          const remaining = Math.ceil((hustleCooldown - (now - data.lastHustle)) / 60000);
          return interaction.reply({ content: `[${rank.name}] Wait ${remaining} minutes.`, ephemeral: true });
        }
        data.lastHustle = now;
        const hustles = [
          { m: "Flipped some kicks for **{p}** bread.", min: 200, max: 600 },
          { m: "Helped move boxes for **{p}** bread.", min: 100, max: 400 },
          { m: "Fixed a screen for **{p}** bread.", min: 300, max: 700 },
          { m: "Sold some lemonade for **{p}** bread.", min: 50, max: 200 },
        ];
        const h = hustles[Math.floor(Math.random() * hustles.length)];
        let p = Math.floor(Math.random() * (h.max - h.min)) + h.min;
        data.bread += p;
        scheduleSave();
        return interaction.reply(`💰 **[${rank.name}]** ${h.m.replace("{p}", p)}`);
      }

      if (sub === "corner") {
        if (Math.random() < 0.35) {
          const loss = Math.floor(data.bread * 0.15);
          data.bread -= loss;
          scheduleSave();
          return interaction.reply(`🚨 **[${rank.name}]** The corner got hot! You lost **${loss}** bread escaping the ops.`);
        }
        let p = Math.floor(Math.random() * 1200) + 600;
        data.bread += p;
        scheduleSave();
        return interaction.reply(`📍 **[${rank.name}]** You posted up on the corner and made **${p}** bread.`);
      }

      if (sub === "freestyle") {
        let p = Math.floor(Math.random() * 500) + 150;
        data.bread += p;
        scheduleSave();
        return interaction.reply(`🎤 **[${rank.name}]** Fire verse! The crowd threw you **${p}** bread.`);
      }

      if (sub === "pickpocket") {
        if (Math.random() < 0.55) {
          const fine = 400;
          data.bread -= fine;
          scheduleSave();
          return interaction.reply(`🕵️ **[${rank.name}]** Caught! You lost **${fine}** bread in legal fees.`);
        }
        let p = Math.floor(Math.random() * 800) + 300;
        data.bread += p;
        scheduleSave();
        return interaction.reply(`🕵️ **[${rank.name}]** Snatched **${p}** bread! Slick move.`);
      }

      if (sub === "hijack") {
        if (Math.random() < 0.8) {
          const fine = 2000;
          data.bread -= fine;
          scheduleSave();
          return interaction.reply(`🚓 **[${rank.name}]** Busted hijacking! Lost **${fine}** bread in the chase.`);
        }
        let p = Math.floor(Math.random() * 9000) + 4000;
        data.bread += p;
        scheduleSave();
        return interaction.reply(`🏎️ **[${rank.name}]** BIG SCORE! Sold the hijacked whip for **${p}** bread!`);
      }
    }

    // ============ JAMAL COMMAND ============
    if (commandName === "jamal") {
      const sub = interaction.options.getSubcommand();
      const data = getPlayerData(interaction.user.id);

      switch (sub) {
        case "give": {
          const target = interaction.options.getUser("user");
          const item = lootItems[Math.floor(Math.random() * lootItems.length)];
          return interaction.reply(`Jamal handed <@${target.id}> a **${item}**. "Here, you need this more than me."`);
        }

        case "lick": {
          const targetUser = interaction.options.getUser("user");
          if (targetUser.id === interaction.user.id) {
            return interaction.reply({ content: "You tryna lick yourself? That's nasty, bro.", ephemeral: true });
          }
          const now = Date.now();
          const lickCooldown = 30 * 60 * 1000;
          if (data.lastLick && now - data.lastLick < lickCooldown) {
            const remaining = Math.ceil((lickCooldown - (now - data.lastLick)) / 60000);
            return interaction.reply({ content: `Slow down! Your tongue needs a break. Wait ${remaining} more minutes.`, ephemeral: true });
          }
          data.lastLick = now;

          const attackerData = getPlayerData(interaction.user.id);
          const targetData = getPlayerData(targetUser.id);
          const targetPocket = targetData.bread || 0;

          if (targetPocket <= 0) {
            return interaction.reply({ content: "This person is flat broke. You can't lick what ain't there.", ephemeral: true });
          }

          const roll = Math.random();
          if (roll < 0.3) {
            const fine = Math.floor(attackerData.bread * 0.15);
            attackerData.bread -= fine;
            scheduleSave();
            return interaction.reply(`🚨 **CAUGHT SLIPPING!** <@${targetUser.id}> caught you tryna lick 'em and slapped you silly! You dropped **${fine}** bread running away.`);
          } else if (roll < 0.6) {
            const portion = Math.floor(targetPocket * (Math.random() * 0.3 + 0.1));
            targetData.bread -= portion;
            attackerData.bread += portion;
            scheduleSave();
            return interaction.reply(`👅 **LICKED!** You managed to snatch a decent portion of bread from <@${targetUser.id}>'s pockets. You got **${portion}** bread!`);
          } else if (roll < 0.9) {
            const portion = Math.floor(targetPocket * (Math.random() * 0.4 + 0.4));
            targetData.bread -= portion;
            attackerData.bread += portion;
            scheduleSave();
            return interaction.reply(`💰 **FAT LICK!** You cleaned out most of <@${targetUser.id}>'s pockets! You snatched **${portion}** bread!`);
          } else {
            const stolen = targetPocket;
            targetData.bread = 0;
            attackerData.bread += stolen;
            scheduleSave();
            return interaction.reply(`💎 **ULTIMATE LICK!** You caught <@${targetUser.id}> completely off guard and took **EVERYTHING** in their pockets! **${stolen}** bread is now yours!`);
          }
        }

        case "say": {
          return interaction.reply(quotes[Math.floor(Math.random() * quotes.length)]);
        }

        case "stash": {
          const amount = interaction.options.getInteger("amount");
          if (data.bread < amount) return interaction.reply({ content: "You ain't even got that much bread in your pockets, clown.", ephemeral: true });
          let totalCapacity = 5000 + (data.stashCapacity || 0);
          if (data.hood && data.hood.name === 'eastside') {
            totalCapacity = Math.floor(totalCapacity * HOODS.eastside.perks.modifiers.stashCapacity);
          }
          const currentStashed = data.stashedBread || 0;
          if (currentStashed + amount > totalCapacity) {
            return interaction.reply({ content: `Your stash house is full! Max capacity is **${totalCapacity}** bread. Buy some **Safe Boxes** from the \`/shop\` to increase it!`, ephemeral: true });
          }
          data.bread -= amount;
          data.stashedBread = currentStashed + amount;
          scheduleSave();
          return interaction.reply(`🏠 You stashed **${amount}** bread in your crib. It's safe from licks now! Total stashed: **${data.stashedBread}**/**${totalCapacity}**`);
        }

        case "unstash": {
          const amount = interaction.options.getInteger("amount");
          const currentStashed = data.stashedBread || 0;
          if (currentStashed < amount) return interaction.reply({ content: "You don't even have that much stashed, stop capping.", ephemeral: true });
          data.stashedBread -= amount;
          data.bread += amount;
          scheduleSave();
          return interaction.reply(`💰 You pulled **${amount}** bread out of your stash and put it in your pockets. Careful out there!`);
        }

        case "rap": {
          const verses = [
            "Came from the mud, now the fit all clean",
            "Late nights grinding, chasing big dreams",
            "Bread on my mind, no time for beef",
            "From the block to the court, elite feet",
            "Rain on the pavement, still I shine",
            "Clock keep ticking, money on time",
            "Hood lessons taught me how to move",
            "Silent with it, nothing to prove",
          ];
          return interaction.reply(verses[Math.floor(Math.random() * verses.length)]);
        }

        case "steal": {
          const target = interaction.options.getUser("user");
          const chosenItem = interaction.options.getString("item");
          let item;
          if (chosenItem) {
            item = chosenItem;
          } else {
            item = stealItems[Math.floor(Math.random() * stealItems.length)];
          }
          return interaction.reply(`Jamal popped out the cut and stole <@${target.id}>'s **${item}**! NO CAP!`);
        }

        case "dice": {
          const bet = interaction.options.getInteger("bet") || 50;
          if (data.bread < bet) return interaction.reply({ content: `You don't have enough bread! You have ${data.bread}, need ${bet}.`, ephemeral: true });
          const die1 = Math.floor(Math.random() * 6) + 1;
          const die2 = Math.floor(Math.random() * 6) + 1;
          const total = die1 + die2;
          let result, winnings = 0;

          if (total === 7 || total === 11) {
            result = "🎲 NATURAL! You win!";
            winnings = bet * 2;
            data.bread += winnings;
            data.streetCred += 3;
          } else if (total === 2 || total === 3 || total === 12) {
            result = "💀 CRAPS! You lose!";
            data.bread -= bet;
          } else {
            const point = total;
            let newRoll;
            do {
              newRoll = Math.floor(Math.random() * 6) + 1 + Math.floor(Math.random() * 6) + 1;
            } while (newRoll !== 7 && newRoll !== point);

            if (newRoll === point) {
              result = `🎯 Hit your point (${point})! You win!`;
              winnings = bet * 1.5;
              data.bread += winnings;
              data.streetCred += 2;
            } else {
              result = `😭 Seven out! You lose!`;
              data.bread -= bet;
            }
          }
          scheduleSave();
          const embed = new EmbedBuilder()
            .setColor(winnings > 0 ? 0x00ff00 : 0xff0000)
            .setTitle("🎰 STREET CRAPS")
            .setDescription(`**Roll:** ${die1} + ${die2} = **${total}**\n\n${result}`)
            .addFields(
              { name: "Bet", value: `${bet} bread`, inline: true },
              { name: "Result", value: winnings > 0 ? `+${winnings} bread` : `-${bet} bread`, inline: true },
              { name: "New Balance", value: `${data.bread} bread`, inline: true }
            );
          return interaction.reply({ embeds: [embed] });
        }

        case "share": {
          const target = interaction.options.getUser("user");
          const amount = interaction.options.getInteger("amount");
          const targetData = getPlayerData(target.id);
          if (target.id === interaction.user.id) return interaction.reply({ content: "You can't share bread with yourself!", ephemeral: true });
          if (data.bread < amount) return interaction.reply({ content: `You don't have enough bread! You have ${data.bread}, need ${amount}.`, ephemeral: true });
          data.bread -= amount;
          targetData.bread += amount;
          scheduleSave();
          const embed = new EmbedBuilder()
            .setColor(0x00ff00)
            .setTitle("💰 BREAD SHARED")
            .setDescription(`<@${interaction.user.id}> shared ${amount} bread with <@${target.id}>!`)
            .addFields(
              { name: "From", value: `<@${interaction.user.id}>`, inline: true },
              { name: "To", value: `<@${target.id}>`, inline: true },
              { name: "Amount", value: `${amount} bread`, inline: true }
            )
            .setFooter({ text: "Real recognize real!" });
          return interaction.reply({ embeds: [embed] });
        }

        case "block": {
          const heat = data.heat;
          if (heat < 30) return interaction.reply("The block is quiet right now. Good time to move.");
          if (heat < 60) return interaction.reply("Block is warm. Keep your eyes open.");
          if (heat < 90) return interaction.reply("Block is hot! The 12 is lurking.");
          return interaction.reply("BLOCK IS ON FIRE! Get low or get caught!");
        }

        case "drip": {
          const dripRating = Math.floor(Math.random() * 100) + 1;
          if (dripRating > 80) return interaction.reply(`Jamal checks you out: "AYOOO THAT FIT HARD! Drip rating: **${dripRating}**! You clean!"`);
          if (dripRating > 50) return interaction.reply(`Jamal nods: "Yeah you cool, but you could do better. Drip rating: **${dripRating}**."`);
          return interaction.reply(`Jamal laughs: "Bruh... you look like you got dressed in the dark. Drip rating: **${dripRating}**. Embarrassing."`);
        }

        case "ops": {
          const found = Math.random() > 0.6;
          if (found) {
            return interaction.reply("🚨 **ALERT!** Ops spotted in the area! Stay dangerous!");
          } else {
            return interaction.reply("✅ All clear. No ops around. We outside.");
          }
        }

        case "smoke": {
          const responses = [
            "Jamal passes the blunt. You take a hit and feel relaxed.",
            "Jamal sparks one up and starts talking about life. Deep.",
            "You smoke with Jamal and forget all your problems.",
            "Jamal: 'This za za got me zonin'. I'm good cuz.'",
            "You cough so hard you lose 5 bread.",
          ];
          return interaction.reply(responses[Math.floor(Math.random() * responses.length)]);
        }

        case "drill": {
          const target = interaction.options.getUser("target");
          const success = Math.random() > 0.7;
          if (success) {
            const loot = Math.floor(Math.random() * 1000) + 500;
            data.bread += loot;
            data.drillsCompleted = (data.drillsCompleted || 0) + 1;
            scheduleSave();
            return interaction.reply(`🔫 **DRILL SUCCESS!** You and Jamal hit <@${target.id}>'s block and came back with **${loot}** bread!`);
          } else {
            const loss = Math.floor(data.bread * 0.2);
            data.bread -= loss;
            scheduleSave();
            return interaction.reply(`💔 **DRILL FAILED.** The ops was waiting. You lost **${loss}** bread escaping.`);
          }
        }

        case "flex": {
          if (!data.inventory || data.inventory.length === 0) {
            return interaction.reply("You ain't got nothing to flex, broke boy.");
          }
          const topItems = data.inventory.slice(0, 5).join(", ");
          return interaction.reply(`💰 **FLEX:** <@${interaction.user.id}> showing off: ${topItems}... and more.`);
        }

        case "lean": {
          const responses = [
            "Jamal pours up a double cup. Sippin slow.",
            "You sip some lean and feel the codeine creep in.",
            "Jamal: 'This that wockhardt, not that trash.'",
            "You nod off after that cup. Too strong.",
            "You spill the lean all over your white tee. Lost 100 bread.",
          ];
          return interaction.reply(responses[Math.floor(Math.random() * responses.length)]);
        }

        case "court": {
          const win = Math.random() > 0.6;
          if (win) {
            data.casesWon = (data.casesWon || 0) + 1;
            scheduleSave();
            return interaction.reply(`⚖️ **COURT WIN!** The judge dismissed your case. You a free man! (Cases won: ${data.casesWon})`);
          } else {
            let fine = Math.floor(data.bread * 0.3);
            if (data.hood && data.hood.name === 'downtown') {
              fine = Math.floor(fine * HOODS.downtown.perks.modifiers.fineReduction);
            }
            data.bread -= fine;
            data.casesLost = (data.casesLost || 0) + 1;
            scheduleSave();
            return interaction.reply(`🔒 **COURT LOSS.** You got sentenced and paid **${fine}** bread in fines. (Cases lost: ${data.casesLost})`);
          }
        }

        case "bando": {
          const found = Math.random() > 0.5 ? Math.floor(Math.random() * 500) + 100 : 0;
          if (found > 0) {
            data.bread += found;
            scheduleSave();
            return interaction.reply(`You and Jamal searched the bando and found **${found}** bread!`);
          } else {
            return interaction.reply("The bando empty. Only rats and roaches.");
          }
        }

        case "trap": {
          const earnings = Math.floor(Math.random() * 1000) + 200 * data.trapHouseLevel;
          data.bread += earnings;
          scheduleSave();
          return interaction.reply(`🏚️ You served customers all day at the trap. Made **${earnings}** bread.`);
        }

        case "spin": {
          const response = Math.random() > 0.5 
            ? "Spun the block and nobody was home. Weird." 
            : "Spun the block and saw ops! We dipped.";
          return interaction.reply(response);
        }

        case "chill": {
          return interaction.reply(`You're chilling in the cut with Jamal. He's counting bread and listening to Lil Durk. "Stay low, keep firing cuz."`);
        }

        case "bail": {
          const cost = 2000;
          if (data.bread < cost) return interaction.reply({ content: `You need ${cost} bread to bail Jamal out.`, ephemeral: true });
          data.bread -= cost;
          scheduleSave();
          return interaction.reply(`You just bailed Jamal out! He's back on the streets. "On folks grave, I knew you was real! Let's go to the mall!"`);
        }

        case "stimulus": {
          const chance = Math.random();
          if (chance < 0.3) {
            const amount = Math.floor(Math.random() * 2000) + 500;
            data.bread += amount;
            scheduleSave();
            return interaction.reply(`💵 **STIMULUS CHECK HIT!** You got **${amount}** bread from the government!`);
          } else {
            return interaction.reply("Stimulus ain't hit yet. Keep waiting, broke boy.");
          }
        }

        case "snitch": {
          const target = interaction.options.getUser("user");
          const response = Math.random() > 0.3
            ? `Jamal confronts <@${target.id}>: "I heard you been talkin to the 12!" They deny it.`
            : `Jamal catches <@${target.id}> with a wire! "GET THIS RAT OUTTA HERE!"`;
          return interaction.reply(response);
        }

        default:
          return interaction.reply({ content: "That jamal subcommand isn't implemented yet.", ephemeral: true });
      }
    }

    // ============ PLAY COMMAND SUBCOMMANDS ============
    if (commandName === "play") {
      const sub = interaction.options.getSubcommand();

      if (sub === "tictactoe") {
        const opponent = interaction.options.getUser("opponent");
        const bet = interaction.options.getInteger("bet") || 0;
        if (opponent.id === interaction.user.id) return interaction.reply({ content: "You can't play against yourself!", ephemeral: true });

        const player1Data = getPlayerData(interaction.user.id);
        const player2Data = getPlayerData(opponent.id);

        if (bet > 0) {
          if (player1Data.bread < bet) return interaction.reply({ content: `You don't have enough bread! You have ${player1Data.bread}, need ${bet}.`, ephemeral: true });
          if (player2Data.bread < bet) return interaction.reply({ content: `<@${opponent.id}> doesn't have enough bread!`, ephemeral: true });
        }

        const gameId = `${interaction.user.id}-${opponent.id}-${Date.now()}`;
        const game = {
          player1: interaction.user.id,
          player2: opponent.id,
          board: createTicTacToeBoard(),
          turn: interaction.user.id,
          bet: bet
        };
        ticTacToeGames.set(gameId, game);

        const embed = new EmbedBuilder()
          .setTitle("🎮 Tic-Tac-Toe")
          .setDescription(`<@${interaction.user.id}> (X) vs <@${opponent.id}> (O)\n\nCurrent turn: <@${interaction.user.id}>`)
          .setColor(0x00ff00);
        const rows = [];
        for (let i = 0; i < 3; i++) {
          const buttons = [];
          for (let j = 0; j < 3; j++) {
            buttons.push(
              new ButtonBuilder()
                .setCustomId(`ttt_${gameId}_${i*3+j}`)
                .setLabel('⬜')
                .setStyle(ButtonStyle.Secondary)
                .setDisabled(false)
            );
          }
          rows.push(new ActionRowBuilder().addComponents(...buttons));
        }
        rows.push(
          new ActionRowBuilder().addComponents(
            new ButtonBuilder()
              .setCustomId(`ttt_${gameId}_quit`)
              .setLabel("🚪 Quit")
              .setStyle(ButtonStyle.Danger)
          )
        );
        return interaction.reply({ embeds: [embed], components: rows });
      }

      if (sub === "trivia") {
        if (!trivia) return interaction.reply({ content: "Trivia game not loaded.", ephemeral: true });
        return trivia.start(interaction);
      }

      if (sub === "coinflip") {
        const target = interaction.options.getUser("opponent");
        const amount = interaction.options.getInteger("amount");
        const data = getPlayerData(interaction.user.id);
        const targetData = getPlayerData(target.id);
        if (target.id === interaction.user.id) return interaction.reply({ content: 'Challenge someone else.', ephemeral: true });
        if (data.bread < amount || targetData.bread < amount) return interaction.reply({ content: 'One of yall is too broke.', ephemeral: true });
        interaction.reply({ content: `🪙 <@${target.id}>, <@${interaction.user.id}> challenged you to a **${amount}** bread coin flip! Type **'accept'** to roll.` })
          .then(() => {
            const filter = m => m.author.id === target.id && m.content.toLowerCase() === 'accept';
            interaction.channel.awaitMessages({ filter, max: 1, time: 30000, errors: ['time'] })
              .then(() => {
                const win = Math.random() > 0.5;
                const winner = win ? interaction.user : target;
                const loser = win ? target : interaction.user;
                getPlayerData(winner.id).bread += amount;
                getPlayerData(loser.id).bread -= amount;
                interaction.channel.send(`🪙 The coin landed on ${win ? 'HEADS' : 'TAILS'}! <@${winner.id}> takes the **${amount}** bread!`);
                scheduleSave();
              }).catch(() => interaction.channel.send('Challenge expired.'));
          });
        return;
      }

      if (sub === "type") {
        const target = interaction.options.getUser("opponent");
        if (target.id === interaction.user.id) return interaction.reply({ content: 'No.', ephemeral: true });
        const words = ['hustle', 'bread', 'street', 'jamal', 'pockets', 'block'];
        const word = words[Math.floor(Math.random() * words.length)];
        interaction.reply(`⌨️ <@${target.id}> vs <@${interaction.user.id}>! First to type **${word}** wins!`);
        const filter = m => [target.id, interaction.user.id].includes(m.author.id) && m.content.toLowerCase() === word;
        interaction.channel.awaitMessages({ filter, max: 1, time: 30000 })
          .then(collected => {
            const winner = collected.first().author;
            getPlayerData(winner.id).bread += 500;
            interaction.channel.send(`🏆 <@${winner.id}> was faster! They earned **500** bread!`);
            scheduleSave();
          }).catch(() => interaction.channel.send('Yall too slow.'));
        return;
      }

      if (sub === "blackjack") {
        const bet = interaction.options.getInteger("bet");
        const opponent = interaction.options.getUser("opponent");
        const player = interaction.user;
        const playerData = getPlayerData(player.id);

        if (playerData.bread < bet) {
          return interaction.reply({ content: `You don't have enough bread! You have ${playerData.bread}, need ${bet}.`, ephemeral: true });
        }

        if (!opponent) {
          const deck = createDeck();
          const playerHand = [deck.pop(), deck.pop()];
          const dealerHand = [deck.pop(), deck.pop()];
          const gameId = `${player.id}-${Date.now()}`;
          const game = {
            id: gameId,
            player1: player,
            player1Data: playerData,
            opponent: 'dealer',
            bet,
            deck,
            playerHand,
            dealerHand,
            status: 'active'
          };
          blackjackGames.set(gameId, game);
          const playerTotal = handTotal(playerHand);
          const embed = new EmbedBuilder()
            .setTitle("♠️ Blackjack vs Dealer")
            .setDescription(`Your hand: ${handToString(playerHand)} (${playerTotal})\nDealer shows: ${handToString([dealerHand[0]])}`)
            .setColor(0x00ff00);
          const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId(`bj_${gameId}_hit`).setLabel("Hit").setStyle(ButtonStyle.Primary),
            new ButtonBuilder().setCustomId(`bj_${gameId}_stand`).setLabel("Stand").setStyle(ButtonStyle.Secondary),
            new ButtonBuilder().setCustomId(`bj_${gameId}_quit`).setLabel("Quit").setStyle(ButtonStyle.Danger)
          );
          return interaction.reply({ embeds: [embed], components: [row] });
        } else {
          if (opponent.id === player.id) {
            return interaction.reply({ content: "You can't play against yourself!", ephemeral: true });
          }
          const opponentData = getPlayerData(opponent.id);
          if (opponentData.bread < bet) {
            return interaction.reply({ content: `<@${opponent.id}> doesn't have enough bread!`, ephemeral: true });
          }

          const gameId = `${player.id}-${opponent.id}-${Date.now()}`;
          const deck = createDeck();
          const player1Hand = [deck.pop(), deck.pop()];
          const player2Hand = [deck.pop(), deck.pop()];
          const game = {
            id: gameId,
            player1: player,
            player1Data: playerData,
            player2: opponent,
            player2Data: opponentData,
            opponent: 'player',
            bet,
            deck,
            player1Hand,
            player2Hand,
            currentPlayer: player.id,
            status: 'active'
          };
          blackjackGames.set(gameId, game);
          const total = handTotal(player1Hand);
          const embed = new EmbedBuilder()
            .setTitle("♠️ Blackjack – Player vs Player")
            .setDescription(`<@${player.id}>'s turn\nYour hand: ${handToString(player1Hand)} (${total})`)
            .setColor(0x00ff00);
          const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId(`bj_${gameId}_hit`).setLabel("Hit").setStyle(ButtonStyle.Primary),
            new ButtonBuilder().setCustomId(`bj_${gameId}_stand`).setLabel("Stand").setStyle(ButtonStyle.Secondary),
            new ButtonBuilder().setCustomId(`bj_${gameId}_quit`).setLabel("Quit").setStyle(ButtonStyle.Danger)
          );
          return interaction.reply({ embeds: [embed], components: [row] });
        }
      }
    }

    // ============ HOOD COMMANDS ============
    if (commandName === "hood") {
      const sub = interaction.options.getSubcommand();
      const data = getPlayerData(interaction.user.id);

      if (sub === "pick") {
        if (data.hood.name) {
          return interaction.reply({
            content: `You're already repping **${HOODS[data.hood.name].fullName}**. If you want to switch, use \`/hood change\` (costs 1,000,000 bread).`,
            ephemeral: true
          });
        }
        const chosen = interaction.options.getString("hood");
        data.hood.name = chosen;
        data.hood.joined = Date.now();
        data.hood.loyalty = 0;
        data.hood.lastLoyaltyUpdate = Date.now();
        scheduleSave();
        const embed = new EmbedBuilder()
          .setColor(HOODS[chosen].color)
          .setTitle(`${HOODS[chosen].emoji} Welcome to ${HOODS[chosen].fullName}`)
          .setDescription(HOODS[chosen].story)
          .addFields({ name: "🔥 Hood Perks", value: HOODS[chosen].perks.description })
          .setFooter({ text: "Represent! You can never change for free." });
        return interaction.reply({ embeds: [embed] });
      }

      if (sub === "info") {
        if (!data.hood.name) return interaction.reply({ content: "You haven't picked a hood yet! Use `/hood pick` to choose.", ephemeral: true });
        const hood = HOODS[data.hood.name];
        const embed = new EmbedBuilder()
          .setColor(hood.color)
          .setTitle(`${hood.emoji} ${hood.fullName}`)
          .setDescription(hood.story)
          .addFields(
            { name: "🔥 Your Perks", value: hood.perks.description },
            { name: "📊 Loyalty", value: `Level ${Math.floor(data.hood.loyalty / 100)} (${data.hood.loyalty} points)` }
          );
        return interaction.reply({ embeds: [embed] });
      }

      if (sub === "stats") {
        if (!data.hood.name) return interaction.reply({ content: "You haven't picked a hood yet!", ephemeral: true });
        const hood = HOODS[data.hood.name];
        const loyaltyLevel = Math.floor(data.hood.loyalty / 100);
        const nextLevel = (loyaltyLevel + 1) * 100;
        const progress = data.hood.loyalty % 100;
        const bar = "▓".repeat(Math.floor(progress / 10)) + "░".repeat(10 - Math.floor(progress / 10));
        const embed = new EmbedBuilder()
          .setColor(hood.color)
          .setTitle(`${hood.emoji} Your Hood Stats`)
          .addFields(
            { name: "Hood", value: hood.fullName, inline: true },
            { name: "Loyalty Level", value: `${loyaltyLevel}`, inline: true },
            { name: "Progress to Next", value: `${bar} ${progress}/100`, inline: false },
            { name: "Loyalty Points", value: `${data.hood.loyalty}`, inline: true },
            { name: "Days Repped", value: `${Math.floor((Date.now() - data.hood.joined) / 86400000)}`, inline: true }
          );
        return interaction.reply({ embeds: [embed] });
      }

      if (sub === "change") {
        if (!data.hood.name) return interaction.reply({ content: "You haven't even picked a hood yet! Use `/hood pick` first.", ephemeral: true });
        const cost = 1000000;
        if (data.bread < cost) return interaction.reply({ content: `You need **${cost.toLocaleString()}** bread to switch hoods.`, ephemeral: true });
        data.bread -= cost;
        data.hood = { name: null, joined: 0, loyalty: 0, lastLoyaltyUpdate: 0 };
        scheduleSave();
        return interaction.reply({ content: `💰 You paid **${cost.toLocaleString()}** bread and are now hoodless. Use \`/hood pick\` to choose a new turf.`, ephemeral: true });
      }

      if (sub === "loyalty") {
        if (!data.hood.name) return interaction.reply({ content: "You haven't picked a hood yet!", ephemeral: true });
        const hood = HOODS[data.hood.name];
        const loyaltyLevel = Math.floor(data.hood.loyalty / 100);
        const embed = new EmbedBuilder()
          .setColor(hood.color)
          .setTitle(`${hood.emoji} Loyalty Level ${loyaltyLevel}`)
          .setDescription("Loyalty unlocks perks:")
          .addFields(
            { name: "Level 0", value: "Base perks", inline: false },
            { name: "Level 1 (100 pts)", value: "Unlock hood‑only shop item", inline: false },
            { name: "Level 2 (300 pts)", value: "Hood title (e.g., 'Southside Legend')", inline: false },
            { name: "Level 3 (1000 pts)", value: "Permanent hood‑wide buff for all members", inline: false }
          );
        return interaction.reply({ embeds: [embed] });
      }

      if (sub === "leaderboard") {
        const hoodTotals = {
          southside: { count: 0, wealth: 0 },
          northside: { count: 0, wealth: 0 },
          eastside: { count: 0, wealth: 0 },
          westside: { count: 0, wealth: 0 },
          downtown: { count: 0, wealth: 0 }
        };
        playerData.forEach((data, userId) => {
          if (data.hood && data.hood.name) {
            const hoodName = data.hood.name;
            hoodTotals[hoodName].count++;
            hoodTotals[hoodName].wealth += data.bread + (data.stashedBread || 0);
          }
        });
        const sorted = Object.entries(hoodTotals).filter(([_, v]) => v.count > 0).sort((a, b) => b[1].wealth - a[1].wealth);
        if (sorted.length === 0) return interaction.reply("No hoods have members yet.");
        const embed = new EmbedBuilder()
          .setTitle("🏆 Hood Leaderboard")
          .setColor(0xffd700)
          .setDescription(sorted.map(([hood, stats], i) => `${i+1}. ${HOODS[hood].emoji} **${HOODS[hood].name}** — ${stats.count} members — **${stats.wealth.toLocaleString()}** total wealth`).join("\n"));
        return interaction.reply({ embeds: [embed] });
      }
    }

    // ============ ECONOMY COMMANDS ============
    if (commandName === "bread") {
      const data = getPlayerData(interaction.user.id);
      return interaction.reply(`🍞 You currently have **${data.bread}** pieces of bread and **${data.streetCred}** street cred.`);
    }

    if (commandName === "daily") {
      const data = getPlayerData(interaction.user.id);
      const now = Date.now();
      const cooldown = 24 * 60 * 60 * 1000;
      if (now - data.lastDaily < cooldown) {
        const remaining = cooldown - (now - data.lastDaily);
        const hours = Math.floor(remaining / (60 * 60 * 1000));
        return interaction.reply({ content: `Chill out! You can claim more daily bread in ${hours} hours.`, ephemeral: true });
      }
      let amount = 500 * (data.multiplier || 1);
      data.bread += amount;
      data.lastDaily = now;
      if (data.hood && data.hood.name) {
        const oneDay = 86400000;
        if (!data.hood.lastLoyaltyUpdate || now - data.hood.lastLoyaltyUpdate > oneDay) {
          data.hood.loyalty += 1;
          data.hood.lastLoyaltyUpdate = now;
        }
      }
      scheduleSave();
      return interaction.reply(`💰 You claimed your daily bread and got **${amount}**! Total: ${data.bread}`);
    }

    if (commandName === "shop") {
      const embed = new EmbedBuilder()
        .setTitle("🛒 Jamal's Enhancement Shop")
        .setDescription("Get these to run the streets better!")
        .setColor(0xffff00)
        .addFields(
          { name: "🍞 Bread Magnet (magnet)", value: "Permanent 1.5x multiplier\nCost: **1,000** bread", inline: true },
          { name: "🔥 Industrial Oven (oven)", value: "Permanent 2.0x multiplier\nCost: **5,000** bread", inline: true },
          { name: "💎 Gold Kneader (kneader)", value: "Permanent 3.0x multiplier\nCost: **15,000** bread", inline: true },
          { name: "📦 Safe Box (safe_box)", value: "Increase stash capacity by 500-4,000\nCost: **2,500** bread", inline: true },
          { name: "🎫 Monthly Pass (pass)", value: "Unlock /monthly stimulus\nCost: **50,000** bread", inline: true },
          { name: "🍀 Lucky Charm (lucky_charm)", value: "Slightly better odds in /gamble\nCost: **10,000** bread", inline: true },
          { name: "📜 Bail Bond (jail_card)", value: "Avoid fine when caught robbing\nCost: **7,500** bread", inline: true },
          { name: "🎭 Ski Mask (mask)", value: "Reduces chance of getting caught in robberies\nCost: **15,000** bread", inline: true },
          { name: "🔫 Strap (weapon)", value: "Increases robbery success rate significantly\nCost: **25,000** bread", inline: true },
          { name: "🏎️ Whip (car)", value: "Reduces cooldowns for work and hustles\nCost: **50,000** bread", inline: true },
          { name: "⚡ Energy Drink (energy_drink)", value: "Removes your current robbery cooldown\nCost: **5,000** bread", inline: true }
        );
      return interaction.reply({ embeds: [embed] });
    }

    if (commandName === "buy") {
      const itemId = interaction.options.getString("item");
      const quantity = interaction.options.getInteger("quantity") || 1;
      const data = getPlayerData(interaction.user.id);
      if (!data.inventory) data.inventory = [];

      const items = {
        magnet: { cost: 1000, type: "multiplier", mult: 1.5, name: "Bread Magnet" },
        oven: { cost: 5000, type: "multiplier", mult: 2.0, name: "Industrial Oven" },
        kneader: { cost: 15000, type: "multiplier", mult: 3.0, name: "Gold Kneader" },
        safe_box: { cost: 2500, type: "special", name: "Safe Box" },
        pass: { cost: 50000, type: "special", name: "Monthly Pass" },
        lucky_charm: { cost: 10000, type: "inventory", name: "Lucky Charm" },
        jail_card: { cost: 7500, type: "inventory", name: "Bail Bond" },
        mask: { cost: 15000, type: "inventory", name: "Ski Mask" },
        weapon: { cost: 25000, type: "inventory", name: "Strap" },
        car: { cost: 50000, type: "inventory", name: "Whip" },
        energy_drink: { cost: 5000, type: "inventory", name: "Energy Drink" }
      };

      const item = items[itemId];
      if (!item) return interaction.reply({ content: "Jamal ain't selling that.", ephemeral: true });

      let totalCost = item.cost * quantity;
      if (data.hood && data.hood.name === 'southside') {
        totalCost = Math.floor(totalCost * HOODS.southside.perks.modifiers.shopDiscount);
      }

      if (data.bread < totalCost) return interaction.reply({ content: `You need **${totalCost}** bread for ${quantity}x ${item.name}!`, ephemeral: true });

      if (item.type === 'multiplier') {
        if (quantity > 1) return interaction.reply({ content: "Multipliers don't stack like that, just buy one.", ephemeral: true });
        if ((data.multiplier || 1) * item.mult > 10) return interaction.reply({ content: "Your multiplier is already too high!", ephemeral: true });
        data.multiplier = (data.multiplier || 1) * item.mult;
      } else if (itemId === 'safe_box') {
        let totalIncrease = 0;
        for (let i = 0; i < quantity; i++) {
          totalIncrease += Math.floor(Math.random() * (4000 - 500 + 1)) + 500;
        }
        data.stashCapacity = (data.stashCapacity || 0) + totalIncrease;
      } else if (itemId === 'pass') {
        if (quantity > 1) return interaction.reply({ content: "One pass is enough, don't be a clown.", ephemeral: true });
        if (data.inventory.includes("monthly_command")) return interaction.reply({ content: "You already got the pass.", ephemeral: true });
        data.inventory.push("monthly_command");
      } else if (item.type === 'inventory') {
        for (let i = 0; i < quantity; i++) {
          data.inventory.push(itemId);
        }
      }

      data.bread -= totalCost;
      scheduleSave();
      return interaction.reply(`✅ You bought **${quantity}x ${item.name}** for **${totalCost}** bread!`);
    }

    if (commandName === "monthly") {
      const data = getPlayerData(interaction.user.id);
      if (!data.inventory || !data.inventory.includes("monthly_command")) {
        return interaction.reply({ content: "You need to buy the **Monthly Pass** from the shop first!", ephemeral: true });
      }
      const now = Date.now();
      const cooldown = 30 * 24 * 60 * 60 * 1000;
      if (data.lastMonthly && now - data.lastMonthly < cooldown) {
        return interaction.reply({ content: "Chill! Your monthly stimulus hasn't reset yet.", ephemeral: true });
      }
      const amount = 20000;
      data.bread += amount;
      data.lastMonthly = now;
      scheduleSave();
      return interaction.reply(`💎 **MONTHLY STIMULUS!** You received **${amount}** pieces of bread.`);
    }

    if (commandName === "pockets") {
      const target = interaction.options.getUser("user") || interaction.user;
      const data = getPlayerData(target.id);
      return interaction.reply(`👀 **POCKET CHECK:** <@${target.id}> is carrying **${data.bread}** bread. ${data.bread > 5000 ? "Damn, they loaded!" : "They looking a bit light..."}`);
    }

    if (commandName === "leaderboard") {
      const sorted = Array.from(playerData.entries())
        .sort((a, b) => b[1].bread - a[1].bread)
        .slice(0, 10);
      if (sorted.length === 0) return interaction.reply("No players yet.");
      const embed = new EmbedBuilder()
        .setTitle("🏆 Bread Leaderboard")
        .setColor(0xffd700)
        .setDescription(sorted.map(([id, data], i) => `${i+1}. <@${id}> — **${data.bread}** bread`).join("\n"));
      return interaction.reply({ embeds: [embed] });
    }

    if (commandName === "slap") {
      const target = interaction.options.getUser("user");
      const responses = [
        `Jamal reached across the screen and slapped the taste out of <@${target.id}>'s mouth!`,
        `<@${interaction.user.id}> hit <@${target.id}> with a backhand so hard they saw their ancestors.`,
        `Jamal: "KEEP MY NAME OUT YOUR MOUTH!" *SLAPS <@${target.id}>*`,
        `The whole chat heard that slap on <@${target.id}>. Embarrassing.`
      ];
      return interaction.reply(responses[Math.floor(Math.random() * responses.length)]);
    }

    if (commandName === "fish") {
      const amount = interaction.options.getInteger("amount");
      const data = getPlayerData(interaction.user.id);
      if (data.bread < amount) return interaction.reply({ content: "You don't have enough bread!", ephemeral: true });
      const caught = Math.random() < 0.4;
      if (caught) {
        const fishValue = amount * 2;
        data.bread += fishValue;
        scheduleSave();
        return interaction.reply(`🐟 You cast your line and caught a big fish! You gained **${fishValue}** bread!`);
      } else {
        data.bread -= amount;
        scheduleSave();
        return interaction.reply(`🐟 You fished all day and caught nothing... Lost **${amount}** bread.`);
      }
    }

    if (commandName === "crime") {
      const data = getPlayerData(interaction.user.id);
      const outcomes = [
        { text: "You tried to rob a store but the clerk had a gun. You lost 200 bread.", loss: 200 },
        { text: "You sold fake watches and got caught. Paid 150 bread fine.", loss: 150 },
        { text: "You helped move some packages and got paid 300 bread!", gain: 300 },
        { text: "You ran a small scam and made 250 bread.", gain: 250 },
        { text: "The cops raided your spot. You lost 400 bread.", loss: 400 },
        { text: "You found an unlocked car and took the cash inside. +350 bread.", gain: 350 },
      ];
      let outcome = outcomes[Math.floor(Math.random() * outcomes.length)];
      if (outcome.gain) {
        data.bread += outcome.gain;
        scheduleSave();
        return interaction.reply(`💀 **CRIME:** ${outcome.text} You now have **${data.bread}** bread.`);
      } else {
        data.bread -= outcome.loss;
        if (data.bread < 0) data.bread = 0;
        scheduleSave();
        return interaction.reply(`💀 **CRIME:** ${outcome.text} You now have **${data.bread}** bread.`);
      }
    }

    if (commandName === "bet") {
      const target = interaction.options.getUser("user");
      const amount = interaction.options.getInteger("amount");
      const challengerData = getPlayerData(interaction.user.id);
      const targetData = getPlayerData(target.id);

      if (target.id === interaction.user.id) {
        return interaction.reply({ content: "You can't bet against yourself!", ephemeral: true });
      }
      if (challengerData.bread < amount) {
        return interaction.reply({ content: "You don't have enough bread!", ephemeral: true });
      }
      if (targetData.bread < amount) {
        return interaction.reply({ content: "They don't have enough bread!", ephemeral: true });
      }

      const embed = new EmbedBuilder()
        .setTitle("🤝 BET CHALLENGE")
        .setDescription(`<@${interaction.user.id}> challenged <@${target.id}> to a coin flip for **${amount}** bread!\n\n<@${target.id}>, accept or decline below.`)
        .setColor(0x00ffff);

      const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId(`bet_accept_${interaction.user.id}_${target.id}_${amount}`).setLabel("Accept").setStyle(ButtonStyle.Success),
        new ButtonBuilder().setCustomId(`bet_decline_${interaction.user.id}_${target.id}`).setLabel("Decline").setStyle(ButtonStyle.Danger)
      );

      return interaction.reply({ embeds: [embed], components: [row] });
    }

    if (commandName === "scratch") {
      if (!scratch) return interaction.reply({ content: "Scratch game not loaded.", ephemeral: true });
      const data = getPlayerData(interaction.user.id);
      const cost = 500;
      if (data.bread < cost) return interaction.reply({ content: "You need 500 bread for a ticket!", ephemeral: true });
      data.bread -= cost;
      const result = await scratch.start(interaction, cost);
      if (result.win) data.bread += result.amount;
      scheduleSave();
      return interaction.reply({ embeds: [result.embed] });
    }

    if (commandName === "rob") {
      const targetUser = interaction.options.getUser("user");
      const data = getPlayerData(interaction.user.id);
      const targetData = getPlayerData(targetUser.id);

      if (targetUser.id === interaction.user.id) return interaction.reply({ content: 'Robbing yourself? Thats just sad.', ephemeral: true });

      const now = Date.now();
      const rank = getStreetRank(data.bread + (data.stashedBread || 0));
      const robCooldown = 3600000 * rank.cdMult;

      if (data.lastRob && now - data.lastRob < robCooldown) {
        const remaining = Math.ceil((robCooldown - (now - data.lastRob)) / 60000);
        return interaction.reply({ content: `The heat is too high. Wait ${remaining} minutes.`, ephemeral: true });
      }

      if (targetData.bread < 100) return interaction.reply({ content: 'Theyre too broke to rob.', ephemeral: true });

      let successChance = 0.45;
      if (data.inventory && data.inventory.includes('weapon')) successChance += 0.15;
      if (data.hood && data.hood.name === 'eastside') {
        successChance += 0.05;
      }

      const success = Math.random() < successChance;
      data.lastRob = now;

      if (success) {
        const stolen = Math.floor(targetData.bread * (Math.random() * 0.3 + 0.2));
        targetData.bread -= stolen;
        data.bread += stolen;
        scheduleSave();
        return interaction.reply(`🥷 **[${rank.name}] SUCCESS!** You robbed **${stolen}** bread from <@${targetUser.id}>!`);
      } else {
        let caughtChance = 0.5;
        if (data.inventory && data.inventory.includes('mask')) caughtChance -= 0.2;

        if (Math.random() < caughtChance) {
          if (data.inventory && data.inventory.includes('jail_card')) {
            const cardIndex = data.inventory.indexOf('jail_card');
            data.inventory.splice(cardIndex, 1);
            scheduleSave();
            return interaction.reply(`🚔 **[${rank.name}]** The feds almost had you, but you used your **Bail Bond** to walk free!`);
          }
          const fine = Math.floor(data.bread * 0.2);
          data.bread -= fine;
          scheduleSave();
          return interaction.reply(`🚔 **[${rank.name}] CAUGHT!** You got bagged and paid **${fine}** bread in fines.`);
        }
        return interaction.reply(`🏃 **[${rank.name}]** You failed the robbery but managed to lose the feds.`);
      }
    }

    if (commandName === "gamble") {
      const amount = interaction.options.getInteger("amount");
      const data = getPlayerData(interaction.user.id);

      if (amount <= 0) return interaction.reply({ content: "You can't gamble air.", ephemeral: true });
      if (data.bread < amount) return interaction.reply({ content: "You're too broke for that bet.", ephemeral: true });

      let winChance = 0.40;
      if (data.inventory && data.inventory.includes("lucky_charm")) {
        winChance = 0.46;
        const charmIndex = data.inventory.indexOf("lucky_charm");
        data.inventory.splice(charmIndex, 1);
      }

      if (data.hood && data.hood.name === 'northside') {
        winChance += HOODS.northside.perks.modifiers.gambleWinChance;
      }

      const win = Math.random() < winChance;
      if (win) {
        data.bread += amount;
        scheduleSave();
        return interaction.reply(`🎰 **WIN!** You doubled your bet and now have **${data.bread}** bread! ${winChance > 0.45 ? "🍀 Your Lucky Charm did the trick!" : ""}`);
      } else {
        data.bread -= amount;
        scheduleSave();
        return interaction.reply(`📉 **LOSS!** You lost **${amount}** bread. Better luck next time.`);
      }
    }

    if (commandName === "slots") {
      const amount = interaction.options.getInteger("amount");
      const data = getPlayerData(interaction.user.id);
      if (data.bread < amount) return interaction.reply({ content: "You're too broke for these stakes.", ephemeral: true });

      const emojis = ["🍎", "🍊", "🍇", "💎", "🔔", "💀"];
      const slot1 = emojis[Math.floor(Math.random() * emojis.length)];
      const slot2 = emojis[Math.floor(Math.random() * emojis.length)];
      const slot3 = emojis[Math.floor(Math.random() * emojis.length)];

      let resultMsg = `[ ${slot1} | ${slot2} | ${slot3} ]\n\n`;
      if (slot1 === slot2 && slot2 === slot3 && slot1 !== "💀") {
        const win = amount * 4;
        data.bread += win;
        resultMsg += `💎 **JACKPOT!** You won **${win}** bread!`;
      } else if ((slot1 === slot2 || slot2 === slot3 || slot1 === slot3) && slot1 !== "💀" && slot2 !== "💀" && slot3 !== "💀") {
        const win = Math.floor(amount * 1.2);
        data.bread += win;
        resultMsg += `✅ **MATCH!** You won **${win}** bread!`;
      } else {
        data.bread -= amount;
        resultMsg += `💀 **BUST.** You lost **${amount}** bread.`;
      }
      scheduleSave();
      return interaction.reply(resultMsg);
    }

    if (commandName === "race") {
      const amount = interaction.options.getInteger("amount");
      const data = getPlayerData(interaction.user.id);
      if (data.bread < amount) return interaction.reply({ content: "You can't afford the entry fee.", ephemeral: true });

      const win = Math.random() > 0.9;
      if (win) {
        const winnings = amount * 4;
        data.bread += winnings;
        interaction.reply(`🏎️💨 **SKRRRRR!** You gapped them ops and won the race! You took home **${winnings}** bread!`);
      } else {
        data.bread -= amount;
        interaction.reply(`🚔 **WEE-OOO!** The feds crashed the race and impounded your whip! You lost **${amount}** bread.`);
      }
      scheduleSave();
      return;
    }

    if (commandName === "drill") {
      const amount = interaction.options.getInteger("amount") || 0;
      const data = getPlayerData(interaction.user.id);

      if (amount > 0 && data.bread < amount) return interaction.reply({ content: "You can't afford to gear up for a drill.", ephemeral: true });

      const win = Math.random() > 0.9;
      if (win) {
        const reward = amount > 0 ? amount * 6 : 2500;
        data.bread += reward;
        interaction.reply(`🔫 **DRILL SUCCESS!** You caught them slipping and hit a major score! You got **${reward}** bread!`);
      } else {
        const loss = amount > 0 ? amount : 750;
        data.bread -= loss;
        interaction.reply(`🚔 **DRILL FAILED.** The ops were ready for you. You lost **${loss}** bread escaping.`);
      }
      scheduleSave();
      return;
    }

    if (commandName === "scavenge") {
      const data = getPlayerData(interaction.user.id);
      const now = Date.now();
      const scavCooldown = 2 * 60 * 60 * 1000;

      if (data.lastScavenge && now - data.lastScavenge < scavCooldown) {
        const remaining = Math.ceil((scavCooldown - (now - data.lastScavenge)) / 60000);
        return interaction.reply({ content: `The block is dry. Check back in ${remaining} minutes.`, ephemeral: true });
      }

      data.lastScavenge = now;
      const found = Math.random() > 0.5 ? Math.floor(Math.random() * 300) + 50 : 0;
      if (found > 0) {
        data.bread += found;
        if (data.hood && data.hood.name === 'southside' && Math.random() < HOODS.southside.perks.modifiers.scavengeBonusChance) {
          const extraItem = lootItems[Math.floor(Math.random() * lootItems.length)];
          data.inventory.push(extraItem);
          interaction.reply(`🗑️ You scavenged and found **${found}** bread, and also found a **${extraItem}**!`);
        } else {
          interaction.reply(`🗑️ You scavenged the back alleys and found **${found}** pieces of bread!`);
        }
      } else {
        interaction.reply("🗑️ You looked everywhere but the block is completely empty. Tough luck.");
      }
      scheduleSave();
      return;
    }

    if (commandName === "niggifier") {
      const text = interaction.options.getString("text");
      return interaction.reply(niggifier(text) || "Error");
    }

    if (commandName === "fetchuser") {
      const userId = interaction.options.getString("userid");
      try {
        const user = await client.users.fetch(userId);
        const embed = new EmbedBuilder()
          .setTitle("User Information")
          .setColor(0x00ff00)
          .setThumbnail(user.displayAvatarURL())
          .addFields(
            { name: "Username", value: user.username, inline: true },
            { name: "User ID", value: user.id, inline: true },
            { name: "Bot", value: user.bot ? "Yes" : "No", inline: true },
            { name: "Account Created", value: user.createdAt.toDateString(), inline: true }
          );
        return interaction.reply({ embeds: [embed] });
      } catch (e) {
        return interaction.reply({ content: "Could not find a user with that ID.", ephemeral: true });
      }
    }

    // ============ ADMIN COMMANDS ============
    if (commandName === "jose") {
      if (interaction.user.id !== JOSE_ID) {
        return interaction.reply({ content: "🚫 **ACCESS DENIED:** Only Jose can use these commands!", ephemeral: true });
      }
      const sub = interaction.options.getSubcommand();
      const targetUser = interaction.options.getUser("user");
      const targetData = targetUser ? getPlayerData(targetUser.id) : null;
      const amount = interaction.options.getInteger("amount");
      const value = interaction.options.getNumber ? interaction.options.getNumber("value") : null;
      const itemName = interaction.options.getString("item");
      const quantity = interaction.options.getInteger("quantity") || 1;

      switch (sub) {
        case "give_bread": {
          targetData.bread += amount;
          scheduleSave();
          return interaction.reply({ content: `✅ Gave **${amount}** bread to <@${targetUser.id}>.`, ephemeral: true });
        }
        case "give_item": {
          if (!targetData.inventory) targetData.inventory = [];
          for (let i = 0; i < quantity; i++) targetData.inventory.push(itemName);
          scheduleSave();
          return interaction.reply({ content: `✅ Gave **${quantity}x ${itemName}** to <@${targetUser.id}>.`, ephemeral: true });
        }
        case "wipe": {
          playerData.delete(targetUser.id);
          scheduleSave();
          return interaction.reply({ content: `✅ Wiped data for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "set_multiplier": {
          targetData.multiplier = value;
          scheduleSave();
          return interaction.reply({ content: `✅ Set multiplier to ${value}x for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "set_heat": {
          targetData.heat = value;
          scheduleSave();
          return interaction.reply({ content: `✅ Set heat to ${value} for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "set_cred": {
          targetData.streetCred = value;
          scheduleSave();
          return interaction.reply({ content: `✅ Set street cred to ${value} for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "set_stash": {
          targetData.stashCapacity = value;
          scheduleSave();
          return interaction.reply({ content: `✅ Set stash capacity to ${value} for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "reset_cooldowns": {
          targetData.lastDaily = 0;
          targetData.lastWork = 0;
          targetData.lastRob = 0;
          targetData.lastLick = 0;
          targetData.lastScavenge = 0;
          targetData.lastHustle = 0;
          targetData.lastMonthly = 0;
          scheduleSave();
          return interaction.reply({ content: `✅ Reset cooldowns for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "transfer_bread": {
          const fromUser = interaction.options.getUser("from");
          const toUser = interaction.options.getUser("to");
          const fromData = getPlayerData(fromUser.id);
          const toData = getPlayerData(toUser.id);
          if (fromData.bread < amount) return interaction.reply({ content: `❌ <@${fromUser.id}> only has ${fromData.bread} bread.`, ephemeral: true });
          fromData.bread -= amount;
          toData.bread += amount;
          scheduleSave();
          return interaction.reply({ content: `✅ Transferred **${amount}** bread from <@${fromUser.id}> to <@${toUser.id}>.`, ephemeral: true });
        }
        case "inspect": {
          const embed = new EmbedBuilder()
            .setTitle(`Data for ${targetUser.tag}`)
            .setColor(0x9c27b0)
            .addFields(
              { name: "Bread", value: `${targetData.bread}`, inline: true },
              { name: "Street Cred", value: `${targetData.streetCred}`, inline: true },
              { name: "Heat", value: `${targetData.heat}`, inline: true },
              { name: "Multiplier", value: `${targetData.multiplier}x`, inline: true },
              { name: "Trap House Level", value: `${targetData.trapHouseLevel}`, inline: true },
              { name: "Stash", value: `${targetData.stashedBread || 0}/${targetData.stashCapacity}`, inline: true },
              { name: "Inventory", value: `${targetData.inventory?.length || 0} items`, inline: true },
              { name: "Achievements", value: `${targetData.achievements?.length || 0}`, inline: true },
              { name: "Hood", value: targetData.hood?.name ? HOODS[targetData.hood.name]?.fullName : "None", inline: true },
              { name: "Loyalty", value: targetData.hood?.loyalty || 0, inline: true }
            );
          return interaction.reply({ embeds: [embed], ephemeral: true });
        }
        case "global_bonus": {
          let count = 0;
          playerData.forEach((data, userId) => {
            data.bread += amount;
            count++;
          });
          scheduleSave();
          return interaction.reply({ content: `✅ Gave **${amount}** bread to **${count}** users.`, ephemeral: true });
        }
        case "set_level": {
          const level = interaction.options.getInteger("level");
          targetData.trapHouseLevel = level;
          scheduleSave();
          return interaction.reply({ content: `✅ Set trap house level to ${level} for <@${targetUser.id}>.`, ephemeral: true });
        }
        case "save_data": {
          await savePlayerData(true);
          return interaction.reply({ content: "✅ Data saved.", ephemeral: true });
        }
        default:
          return interaction.reply({ content: "Admin subcommand not implemented.", ephemeral: true });
      }
    }
  }
});

// ============================================
// 🚀 CLIENT READY
// ============================================
client.once("ready", async () => {
  console.log(`🔥 Jamal is online as ${client.user.tag}`);
  try {
    await loadPlayerData();
    console.log(`📁 Loaded ${playerData.size} player records`);
    autoSaveInterval = setInterval(() => savePlayerData(true), 30000);
  } catch (error) {
    console.error('❌ Error during startup:', error);
  }
  client.user.setActivity("/roast | Cooking fools", { type: "PLAYING" });
});

client.login(token);