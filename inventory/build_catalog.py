#!/usr/bin/env python3
"""
Build inventory/catalog.json from the transcribed Craftable item list.

Cues are deliberately short and describe only what survives a bad shelf photo:
bottle colour, capsule/cap colour, label colour, distinctive glass shape.
Where a brand is universally recognisable (Grey Goose, Jack Daniel's) the cue
is minimal — the model does not need help. Where two SKUs differ only by size
or expression, the cue names the discriminator explicitly.
"""
import json
import re

SHAPES = {
    "bordeaux":  {"diameter_in": 3.0, "height_in": 12.0, "desc": "high square shoulders"},
    "burgundy":  {"diameter_in": 3.5, "height_in": 12.0, "desc": "sloping shoulders, wider base"},
    "provence":  {"diameter_in": 3.0, "height_in": 13.0, "desc": "tall tapered flute, long neck"},
    "champagne": {"diameter_in": 3.5, "height_in": 12.5, "desc": "heavy, deep punt, foil over cage"},
    "half375":   {"diameter_in": 2.4, "height_in": 9.5,  "desc": "half bottle"},
    "split187":  {"diameter_in": 2.0, "height_in": 7.5,  "desc": "split / mini"},
    "sake":      {"diameter_in": 3.0, "height_in": 11.0, "desc": "varies by producer"},
    "spirit750": {"diameter_in": 3.2, "height_in": 11.5, "desc": "standard 750ml spirit"},
    "spirit1L":  {"diameter_in": 3.4, "height_in": 13.0, "desc": "1L — visibly TALLER than the 750ml"},
    "spirit175": {"diameter_in": 4.3, "height_in": 14.5, "desc": "1.75L handle"},
    "can12":     {"diameter_in": 2.6, "height_in": 4.8,  "desc": "12oz can"},
    "cansm":     {"diameter_in": 2.3, "height_in": 4.4,  "desc": "small can / slim"},
    "mixer200":  {"diameter_in": 1.9, "height_in": 6.0,  "desc": "200ml mixer bottle"},
    "water750":  {"diameter_in": 3.0, "height_in": 11.5, "desc": "750ml glass water bottle"},
    "syrup1L":   {"diameter_in": 3.2, "height_in": 11.0, "desc": "1L syrup bottle, plastic cap"},
    "bulk":      {"diameter_in": 0,   "height_in": 0,    "desc": "case / tin / bag, not a bottle"},
}

# (name, subcategory, size, shape, cue, confidence, needs_photo)
WINE = [
 ("Roseblood Rose 750ml","Rose","750ml","provence","Very pale salmon, clear glass. Ornate oval label ROSEBLOOD D'ESTOUBLON. Grey/pewter capsule.","high",0),
 ("Saracina Chardonnay 750ml","White","750ml","burgundy","Mendocino. Cases print SARACINA / MENDOCINO COUNTY in black on white.","medium",1),
 ("Laurent Perrier Cuvee Rose 750ml","Sparkling","750ml","champagne","Unmistakable: squat rounded bottle in a decorative wire net. Salmon wine.","high",0),
 ("Moet Imperial Rose 187ml","Sparkling","187ml","split187","Mini. Gold foil, RED crown seal, black label, gold ribbon X. ROSE IMPERIAL.","high",0),
 ("Accademia Prosecco 750ml","Sparkling","750ml","champagne","TRANSPARENT COLOURED GLASS — blue, red, green, orange, yellow or purple. Bottega's Accademia line. Nothing else looks like this.","high",0),
 ("Grande Dame 750ml","Sparkling","750ml","champagne","Veuve Clicquot prestige cuvee. Heavier bottle, cream/white label with gold. NOT the orange label.","medium",0),
 ("Ferrari Rose 375ml","Sparkling","375ml","half375","Half bottle. Copper/rose foil, black label, gold FERRARI script, TRENTODOC.","high",0),
 ("Veuve Clicquot Yellow Label W/ Fridge 750ml","Sparkling","750ml","champagne","Gift pack — bottle inside an ORANGE METAL TIN. Only distinguishable when the tin is present.","high",0),
 ("Une Femme 187ml","Sparkling","187ml","split187","Clear glass split, CROWN CAP not foil, amber-rose liquid, plain white label.","high",0),
 ("Scharffenberger 750ml","Sparkling","750ml","champagne","NAVY/PURPLE foil. Grey-silver label with small yellow flowers. BRUT EXCELLENCE.","high",0),
 ("Veuve Clicquot Yellow Label Reserve 750ml","Sparkling","750ml","champagne","Orange label, gold foil neck banded 'Veuve Clicquot'. Differs from standard only in label text.","medium",0),
 ("Chandon Brut Rose 187ml","Sparkling","187ml","split187","Mini. Pink wine, Chandon label, green-tinted glass.","medium",0),
 ("Cakebread Chardonnay 750ml","White","750ml","burgundy","Cream label, green grape-leaf art, CAKEBREAD CELLARS. Burgundy shoulders — the Sauv Blanc is a Bordeaux bottle.","high",0),
 ("Albrecht Cremant Brut Rose 750ml","Sparkling","750ml","champagne","PINK foil. Deep red label. LUCIEN ALBRECHT, CREMANT D'ALSACE BRUT ROSE.","high",0),
 ("Cliff Lede Sauvignon Blanc 19 750ml","White","750ml","bordeaux","Napa. Clean modern label.","low",1),
 ("Neiman Marcus Chardonnay 750ml","White","750ml","burgundy","BLACK label, white/gold script NEIMAN MARCUS, Mendocino. Dark capsule, branded cork.","high",0),
 ("Clos Pegase Chardonnay Mitsuko19 750ml","White","750ml","burgundy","Mitsuko's Vineyard, Carneros. Clos Pegase uses artwork labels.","low",1),
 ("Terlato Pinot Grigio 750ml","White","750ml","bordeaux","Tall slim Alsace-style bottle typical of Friuli Pinot Grigio.","low",1),
 ("Dom Perignon Luminous 750ml","Sparkling","750ml","champagne","LED-backlit label with a battery tab. Dark green bottle, shield label.","high",0),
 ("Miraval Cotes De Provence Rose 375ml","Rose","375ml","half375","Half. Curved 'hourglass' Provence bottle, GOLD capsule, pale salmon.","high",0),
 ("Attems Pino Grigio 750ml","White","750ml","bordeaux","GREY/SILVER capsule printed ATTEMS. White label with a small crest. Friuli DOC.","high",0),
 ("Daou Cabernet Sauvignon 750ml","Red","750ml","bordeaux","White label, DAOU in serif caps, Paso Robles. Standard tier.","high",0),
 ("Daou Cabernet Reserve 750ml","Red","750ml","bordeaux","Reserve tier — darker/heavier label, same DAOU wordmark. Read the tier line to tell it from the standard.","medium",0),
 ("Whispering Angel Rose 375ml","Rose","375ml","half375","Half. GOLD CHECKERBOARD capsule, white script label. Chateau d'Esclans.","high",0),
 ("LYRE'S CLASSICO 750ml","Non-Alcohol Wine","750ml","champagne","Non-alcoholic sparkling. Lyre's black label, gold lyre emblem.","medium",0),
 ("Cherry Pie Pinot Noir 750ml","Red","750ml","burgundy","Cherry-red label graphic. NOT wax-dipped — that's Belle Glos.","medium",0),
 ("Bottega Prosecco 750ml","Sparkling","750ml","champagne","GOLD METALLIC OPAQUE bottle, no visible glass. Bottega Gold. Distinct from Accademia's coloured transparent glass.","high",0),
 ("Joto Yuzu Flavored Sake 720ml","Sake","720ml","sake","720ml sake. Yuzu — pale cloudy yellow liquid.","medium",0),
 ("Whispering Angel Rose 750ml","Rose","750ml","provence","GOLD CHECKERBOARD capsule, tall tapered Provence bottle, white script label. Highest-volume rose here.","high",0),
 ("Sonoma Cutrer Chardonnay 750ml","White","750ml","burgundy","BRIGHT YELLOW capsule — the most distinctive capsule in the room. RUSSIAN RIVER RANCHES.","high",0),
 ("Une Femme Callie Sparkling Rose 187ml","Sparkling","187ml","split187","Clear split, crown cap, amber-rose. Label UNE FEMME / THE CALLIE.","high",0),
 ("Veuve Clicquot Yellow Label 750ml","Sparkling","750ml","champagne","ORANGE label, gold foil neck banded 'Veuve Clicquot'. The default Veuve.","high",0),
 ("Sparkling Sangria 750ml","Red","750ml","champagne","Brand not identified from the item name alone.","low",1),
 ("Trapiche Malbec 750ml","Red","750ml","bordeaux","Argentine Malbec, Trapiche label.","medium",0),
 ("Moet Brut Imperial 750ml","Sparkling","750ml","champagne","Full size. Gold foil, RED crown seal, black label, gold ribbon X.","high",0),
 ("Bisol Jeio Prosecco 750ml","Sparkling","750ml","champagne","GOLD label, Jeio in script, embossed circular 'B' medallion on the glass. PROSECCO D.O.C. BRUT.","high",0),
 ("Dom Perignon 10 750ml","Sparkling","750ml","champagne","2010 vintage. Dark green, shield label. Non-luminous.","high",0),
 ("Une Femme The Callie Sparkling Rose Neiman Marcus 187ml","Sparkling","187ml","split187","Neiman Marcus co-brand of the Callie split. Near-identical — look for NM branding.","medium",1),
 ("Studio Rose 2021 750ml","Rose","750ml","provence","Likely Studio by Miraval. Vintage-dated 2021.","low",1),
 ("Moet Imperial 187ml","Sparkling","187ml","split187","Mini. Gold foil, RED crown seal, MINI MOET on the body. Brut, not Rose.","high",0),
 ("Jaume Serra Cristalino Brut 750ml","Sparkling","750ml","champagne","Spanish cava, value tier — lighter glass than champagne.","medium",0),
 ("Cakebread Sauvignon Blanc 750ml","White","750ml","bordeaux","Cream label, green grape-leaf art, SAUVIGNON BLANC / NORTH COAST. Pale yellow-green wine, clear glass.","high",0),
 ("Cuvaison Chardonnay 750ml","White","750ml","burgundy","Cream label, minimal mark, ESTATE GROWN EST 1969, Los Carneros. Dark green glass.","high",0),
 ("Joto Yuzu Sake 500ml","Sake","500ml","sake","500ml. Same Joto Yuzu as the 720ml — separate SKU, do not merge.","medium",0),
 ("Belle Glos Pinot Noir 750ml","Red","750ml","burgundy","RED WAX-DIPPED capsule, thick and dripping. The single most recognisable bottle in the room.","high",0),
 ("Duckhorn Cabernet Sauvignon 18 750ml","Red","750ml","bordeaux","Napa. Cream label with a duck illustration.","medium",0),
 ("Miraval Cotes De Provence Rose 750ml","Rose","750ml","provence","Full size. Curved 'hourglass' bottle, GOLD capsule, pale salmon.","high",0),
 ("Tyku Cucumber Sake 330ml","Sake","330ml","sake","Small. TYKU uses frosted/coloured glass; cucumber is green-tinted.","medium",0),
 ("Heavensake Sake Baby 300ml","Sake","300ml","sake","300ml 'baby'. Minimalist white label.","medium",0),
 ("Wolffer Spring In A Bottle 750ml","Non-Alcohol Wine","750ml","bordeaux","Non-alcoholic. Round white label with a DAFFODIL, reads SPRING IN A BOTTLE. Rose liquid.","high",0),
]

LIQUOR = [
 ("Belle de Brillet Pear Liqueur 750ml","Liqueur","750ml","spirit750","PEAR-SHAPED bottle, cork top, amber. Neck band MAISON BRILLET COGNAC 1850.","high",0),
 ("Three Olives Vanilla Vodka 1L","Vodka","1L","spirit1L","Clear, Three Olives wordmark.","medium",0),
 ("Absolute Peppar 1L","Vodka","1L","spirit1L","Absolut medicine-bottle shape. PEPPAR — green/olive label text.","high",0),
 ("Absolute 1L","Vodka","1L","spirit1L","Absolut's squat medicine-bottle shape, clear, blue script. 1L is taller than the 750.","high",0),
 ("Hangar One Vodka 1L","Vodka","1L","spirit1L","Tall clear bottle, minimalist label.","medium",0),
 ("Hangar One Vodka 750ml","Vodka","750ml","spirit750","Same as the 1L but SHORTER. Size is the only discriminator.","medium",0),
 ("Grey Goose Vodka 750ml","Vodka","750ml","spirit750","Frosted glass, flying geese, French blue. 750 is the shorter one.","high",0),
 ("Grey Goose Vodka 1L","Vodka","1L","spirit1L","Frosted glass, flying geese. Visibly TALLER than the 750.","high",0),
 ("Ketel One Vodka 1L","Vodka","1L","spirit1L","Clear, blue/silver label, KETEL ONE. Taller than the 750.","high",0),
 ("Belvedere Organic Vodka 1L","Vodka","1L","spirit1L","Frosted white bottle with a tree/palace. Organic Infusions line — coloured label.","medium",0),
 ("Deep Eddy Ruby Red 1L","Vodka","1L","spirit1L","PINK/RED liquid, Texas grapefruit. Bright pink label.","high",0),
 ("Casamigos Reposado 1L","Tequila","1L","spirit1L","Clear glass, cream label, blue agave fan. Reposado = pale gold liquid. Cork PRODUCTOS CASAMIGOS.","high",0),
 ("Tito's Handmade Vodka 750ml","Vodka","750ml","spirit750","Clear, COPPER/BRONZE screwcap, cream label with a still. Your well vodka.","high",0),
 ("Casa Del Sol Blanco 750ml","Tequila","750ml","spirit750","Ornate rounded bottle. Blanco = clear liquid.","medium",0),
 ("Casa Del Sol Reposado 750ml","Tequila","750ml","spirit750","Same bottle as the Blanco, PALE GOLD liquid. Liquid colour is the discriminator.","medium",0),
 ("Casa Dragones Blanco 750ml","Tequila","750ml","spirit750","Tall slim clear bottle, minimalist, etched. Premium presentation.","medium",0),
 ("Brother's Bond Straight Bourbon Whiskey 750ml","Whiskey","750ml","spirit750","CORK top, cream neck band HAND SELECTED BATCH / 80 PROOF, BB monogram.","high",0),
 ("Reyka Vodka 1L","Vodka","1L","spirit1L","Icelandic. Clear, blue/white label.","medium",0),
 ("Bacardi Rum Light 750ml","Rum","750ml","spirit750","Clear liquid, RED BAT roundel on black/silver label.","high",0),
 ("Empress 1908 Gin 750ml","Gin","750ml","spirit750","INDIGO/PURPLE liquid — unmistakable. White label EMPRESS 1908 INDIGO GIN. A clear one is EMPTY.","high",0),
 ("Heering Cherry Liquer 750ml","Liqueur","750ml","spirit750","Dark red-black liquid. Cream label, red HEERING, SINCE 1818.","high",0),
 ("Lyre's Dry Spirit Italian Orange 700ml","Non-Alc","700ml","spirit750","Non-alcoholic. Lyre's black label with gold lyre. Orange expression.","medium",0),
 ("Belvedere Vodka 750ml","Vodka","750ml","spirit750","Frosted white bottle, palace silhouette, BELVEDERE.","high",0),
 ("Ketel One Vodka 750ml","Vodka","750ml","spirit750","Clear, blue/silver label. Shorter than the 1L.","high",0),
 ("Dekuyper Apricot 750ml","Liqueur","750ml","spirit750","Orange-amber liqueur, DeKuyper label.","medium",0),
 ("Dewar's White Label 750ml","Whiskey","750ml","spirit750","Scotch. White label, Dewar's script.","high",0),
 ("Ford's Gin 750ml","Gin","750ml","spirit750","Green glass, white/black label, FORD'S GIN.","medium",0),
 ("Smirnoff Twist of Vanilla 750ml","Vodka","750ml","spirit750","Clear, red Smirnoff label, vanilla flavour band.","medium",0),
 ("Gallo Sweet Vermouth 750ml","Vermouth","750ml","spirit750","Vermouth — refrigerate after opening. Gallo label.","medium",0),
 ("Captain Morgan White Rum 750ml","Rum","750ml","spirit750","Clear liquid. Captain Morgan label — WHITE, not the gold Spiced.","high",0),
 ("MT GAY 750ml","Rum","750ml","spirit750","Mount Gay Barbados rum. RED capsule.","high",0),
 ("Caravella Limoncello 750ml","Liqueur","750ml","spirit750","BRIGHT YELLOW liquid, clear glass. Caravella label.","high",0),
 ("White Claw Hard Seltzer 12oz","Seltzer","12oz","can12","Slim can, white with a coloured flavour band.","high",0),
 ("Surfside Starter Pack 12fl.oz","RTD","12oz","can12","Multi-pack of cans.","medium",0),
 ("Starlight Bourbon Whisky 750ml","Whiskey","750ml","spirit750","Indiana craft bourbon.","low",1),
 ("Vermouth Dry 1L","Vermouth","1L","spirit1L","Generic dry vermouth line item.","low",1),
 ("Vermouth Sweet 1L","Vermouth","1L","spirit1L","Generic sweet vermouth line item.","low",1),
 ("Aperol 1L","Liqueur","1L","spirit1L","BRIGHT ORANGE liquid, ribbed glass, NAVY cap with yellow A. Taller than the 750.","high",0),
 ("Aperol 750ml","Liqueur","750ml","spirit750","BRIGHT ORANGE liquid, ribbed glass, NAVY cap, APEROL 1919. Shorter than the 1L.","high",0),
 ("Brother's Bond Straight Bourbon 750ml","Whiskey","750ml","spirit750","Duplicate SKU of the other Brother's Bond entry — cork, HAND SELECTED BATCH band.","medium",0),
 ("Woodford Reserve Bourbon 1L","Whiskey","1L","spirit1L","Squat rounded bottle, cork, red wax-look seal. Taller than the 750.","high",0),
 ("Woodford Reserve Bourbon 750ml","Whiskey","750ml","spirit750","Squat rounded bottle, cork, WOODFORD RESERVE label.","high",0),
 ("Espolon Tequila Reposado 750ml","Tequila","750ml","spirit750","Tall clear bottle, rooster illustration, ESPOLON. Reposado = pale gold.","high",0),
 ("Shibui Japanese Whisky Sherry Cask 18Yr 750ml","Whiskey","750ml","spirit750","Japanese. SHERRY CASK 18YR on the label — the discriminator vs the 10Yr.","medium",0),
 ("Shibui Japanese Whisky Pure Malt 10Yr 750ml","Whiskey","750ml","spirit750","Japanese. PURE MALT 10YR on the label.","medium",0),
 ("Tullamore Dew 1L","Whiskey","1L","spirit1L","Irish. Green-tinted glass, gold/white label.","high",0),
 ("Absolut Vodka 1L","Vodka","1L","spirit1L","Medicine-bottle shape, clear, blue script ABSOLUT.","high",0),
 ("Jack Daniels Black 1L","Whiskey","1L","spirit1L","Square bottle, BLACK label, white Old No.7 script.","high",0),
 ("Baileys Irish Cream 1L","Liqueur","1L","spirit1L","Opaque cream liquid, dark bottle, gold script BAILEYS. Refrigerated after opening.","high",0),
 ("Chambord Liqueur 750ml","Liqueur","750ml","spirit750","GLOBE/ORB bottle with an ornate gold-and-purple crown cap. Unmistakable.","high",0),
 ("Ancho Reyes 750ml","Liqueur","750ml","spirit750","Dark bottle, colourful geometric label band. Chile liqueur.","medium",0),
 ("Disarrono Amaretto 1L","Liqueur","1L","spirit1L","SQUARE bottle, square black cap, amber. DISARONNO on the cap band.","high",0),
 ("Creme De Violette 750ml","Liqueur","750ml","spirit750","VIOLET/PURPLE liquid — colour is the giveaway.","high",0),
 ("Domaine Canton Ginger Liqueur 1L","Liqueur","1L","spirit1L","Bamboo-segmented bottle, black cap, gold DOMAINE DE CANTON.","high",0),
 ("Cointreau Orange Liqueur 750ml","Liqueur","750ml","spirit750","SQUAT SQUARE dark amber bottle, BRONZE knurled cap, ORANGE ribbon, gold 1849 seal.","high",0),
 ("Cointreau Orange Liqueur 1L","Liqueur","1L","spirit1L","Same square amber bottle and bronze cap, TALLER. Size is the discriminator.","high",0),
 ("Kahlua Coffee Liqueur 1L","Liqueur","1L","spirit1L","Rounded bottle, YELLOW/RED label, KAHLUA. Taller than the 750.","high",0),
 ("Licor 43 1L","Liqueur","1L","spirit1L","Bright yellow liquid, gold '43' on the label.","high",0),
 ("Grand Marnier 1L","Liqueur","1L","spirit1L","Squat rounded bottle, ORANGE-RED ribbon and seal, gold label.","high",0),
 ("Fiorente Elderflower Liqueur 700ml","Liqueur","700ml","spirit750","Pale bottle, floral label. Italian elderflower.","medium",0),
 ("Kahlua Coffee Liqueur 750ml","Liqueur","750ml","spirit750","Rounded bottle, YELLOW/RED label, RUM & COFFEE LIQUEUR.","high",0),
 ("Casamigos Blanco 1L","Tequila","1L","spirit1L","Clear liquid, cream label, blue agave fan, cork. 1L is taller.","high",0),
 ("Makers Mark Bourbon 1L","Whiskey","1L","spirit1L","RED WAX dripping capsule, square-ish bottle. Unmistakable.","high",0),
 ("Cinzano Sweet Vermouth 750ml","Vermouth","750ml","spirit750","Red/blue Cinzano label.","medium",0),
 ("Dos Maderas 5 + 3 Double Aged Rum 750ml","Rum","750ml","spirit750","RED/ORANGE capsule printed 'Dos Maderas'. Embossed shield on the glass.","high",0),
 ("COINTREAU 750ml","Liqueur","750ml","spirit750","Duplicate SKU of Cointreau 750 — square amber, bronze cap, orange ribbon.","medium",0),
 ("Bombay Sapphire 750ml","Gin","750ml","spirit750","BLUE glass bottle, Queen Victoria portrait. 750 is the shorter one.","high",0),
 ("Tanqueray Gin 1L","Gin","1L","spirit1L","GREEN cocktail-shaker-shaped bottle, RED seal with a pineapple, silver ridged cap.","high",0),
 ("Beefeater Gin 750ml","Gin","750ml","spirit750","Clear bottle, red/white label with a Beefeater guard.","high",0),
 ("Bombay Sapphire 1L","Gin","1L","spirit1L","BLUE glass, Queen Victoria portrait. Visibly taller than the 750.","high",0),
 ("Cointreau Liqueur 1L","Liqueur","1L","spirit1L","Duplicate SKU of Cointreau 1L — square amber, bronze cap.","medium",0),
 ("Casa Del Sol Anejo 750ml","Tequila","750ml","spirit750","Same ornate bottle as Blanco/Reposado, DARKEST amber liquid of the three.","medium",0),
 ("Bacardi Superior 750ml","Rum","750ml","spirit750","Clear liquid, RED BAT roundel. SUPERIOR on the label.","high",0),
 ("Mount Gay Rum Eclipse 1L","Rum","1L","spirit1L","RED capsule, ECLIPSE label. Taller than the 750.","high",0),
 ("Bacardi Rum Light 1L","Rum","1L","spirit1L","Clear liquid, RED BAT roundel. Taller than the 750.","high",0),
 ("Glenmorangie 10 Yr 750ml","Whiskey","750ml","spirit750","Tall slim ORANGE-toned label, THE ORIGINAL 10 YEARS.","high",0),
 ("Hennessy 750ml","Cognac","750ml","spirit750","Cognac. Dark amber, HENNESSY with the arm-and-axe emblem.","high",0),
 ("Glenmorangie X 750ml","Whiskey","750ml","spirit750","Bright modern label with a large X. Distinct from the 10Yr.","medium",0),
 ("Glenmorangie 750ml","Whiskey","750ml","spirit750","Generic Glenmorangie line item — check the expression on the label.","low",1),
 ("Monkey Shoulder 750ml","Whiskey","750ml","spirit750","Squat bottle with THREE BRASS MONKEYS on the shoulder. Unmistakable.","high",0),
 ("Woodford Reserve 750ml","Whiskey","750ml","spirit750","Duplicate SKU — squat rounded bottle, cork.","medium",0),
 ("Belvedere Vodka 1L","Vodka","1L","spirit1L","Frosted white bottle, palace silhouette. Taller than the 750.","high",0),
 ("Patron Teq Silver 750ml","Tequila","750ml","spirit750","Squat rounded hand-blown bottle, CORK with a bee, clear liquid.","high",0),
 ("Tito's Handmade Vodka 1L","Vodka","1L","spirit1L","Clear, COPPER screwcap, cream label. Taller than the 750.","high",0),
 ("Hendricks (generic) (L)","Gin","generic","spirit1L","Craftable GENERIC/pour line item, not a physical bottle on the shelf. Do not count from a photo.","high",0),
 ("Campari (generic) (L)","Liqueur","generic","spirit1L","Craftable GENERIC/pour line item, not a physical bottle. Do not count from a photo.","high",0),
 ("St. Germain (generic) (L)","Liqueur","generic","spirit1L","Craftable GENERIC/pour line item, not a physical bottle. Do not count from a photo.","high",0),
 ("Tequila,Repo (generic) (L)","Tequila","generic","spirit1L","Craftable GENERIC/pour line item, not a physical bottle. Do not count from a photo.","high",0),
 ("Aviation (generic) (L)","Gin","generic","spirit1L","Craftable GENERIC/pour line item, not a physical bottle. Do not count from a photo.","high",0),
 ("Campari 1L","Liqueur","1L","spirit1L","BRIGHT RED liquid, white/red CAMPARI label. Taller than the 750.","high",0),
 ("Campari 750ml","Liqueur","750ml","spirit750","BRIGHT RED liquid, white/red CAMPARI label.","high",0),
 ("St. Germain Elderflower 750ml","Liqueur","750ml","spirit750","Art-deco faceted bottle, pale yellow liquid, ST-GERMAIN.","high",0),
 ("Aviation 1L","Gin","1L","spirit1L","Squarish clear bottle, BLACK label AVIATION AMERICAN GIN. Taller than the 750.","high",0),
 ("Aviation 750ml","Gin","750ml","spirit750","Squarish clear bottle, BLACK label, AVIATION AMERICAN GIN, BATCH DISTILLED.","high",0),
 ("Hendricks 1L","Gin","1L","spirit1L","DARK APOTHECARY bottle, black, diamond label HENDRICK'S GIN, embossed cap.","high",0),
 ("Herradura Reposado 750ml","Tequila","750ml","spirit750","Clear glass, cream/white label with a horseshoe. Reposado = pale gold.","high",0),
 ("High West Barrel Select 1L","Whiskey","750ml","spirit750","PALE NATURAL CORK, mushroom top. NAVY-CHARCOAL label with HIGH WEST in COPPER caps, BARREL SELECT in copper script, white line-art of stacked barrels and mountains. Embossed lettering on the clear glass shoulder. Deep reddish-amber. ON THE MENU (Getaway Rider).","high",0),
 ("Giffard Banane du Bresil 1L","Liqueur","750ml","spirit750","BLACK neck sleeve printed E. Giffard in gold, SILVER ridged screwcap. E. Giffard script EMBOSSED into the clear glass shoulder. White label with a TORN/DECKLED top edge, GIFFARD DEPUIS 1885 / Banane du Bresil. Golden-amber. ON THE MENU (Bananas & Pajamas).","high",0),
 ("Aplos Arise 1L","Non-Alc","750ml","spirit750","Non-alcoholic spirit. NOT YET PURCHASED — expect ZERO until the first delivery. ON THE MENU (Chili Margarita).","low",1),
 ("Tost Sparkling 1L","Non-Alc","750ml","champagne","Non-alcoholic sparkling white tea, cranberry and ginger. Champagne-shaped bottle. NOT YET PURCHASED — expect ZERO until the first delivery. ON THE MENU (Tost Sangria).","low",1),
 ("Beer","Beer","each","can12","ANY beer, bottle or can, any brand. Do not identify the brand — Paulaner, Sapporo, Heineken, Einstok and everything else all report as this one line.","high",0),
]

NA = [
 ("Juice, Cranberry 1fl.oz","Juice","1fl.oz","bulk","Foodservice cranberry — Ocean Spray plastic jug.","medium",0),
 ("REAL PEACH INFUSED SYRUP 16fl.oz","Syrup","16oz","bulk","Re'al squeeze bottle, peach.","medium",0),
 ("Acqua Panna Natural Spring Water 8.8fl.oz","Water","8.8oz","water750","Small Acqua Panna. Cream/terracotta label, Tuscany.","high",0),
 ("Dammann Earl Grey Sachets 500ct","Tea","500ct","bulk","Tea case, not a bottle.","high",0),
 ("Dammann Sachets 500ct","Tea","500ct","bulk","Tea case.","high",0),
 ("Dammann Loose Tea 1case","Tea","1case","bulk","Tea case.","high",0),
 ("San Pellegrino Spk Water Gls Lse 250ml","Water","250ml","water750","Small green glass Pellegrino, red star.","high",0),
 ("Q Mixers Ginger Ale 7.5 7.5fl.oz","Mixer","7.5oz","cansm","Q Mixers slim can — ginger ale colourway.","high",0),
 ("Dammann Tea China Black Iced Tea 1ct","Tea","1ct","bulk","Tea.","medium",0),
 ("Tea Dammann Sachets 500ct","Tea","500ct","bulk","Tea case.","medium",0),
 ("Tea Dammann Iced Tea China Black 3.5fl.oz","Tea","3.5oz","bulk","Tea.","medium",0),
 ("Dammann Tea Breakfast Tea 96ct","Tea","96ct","bulk","Tea box.","high",0),
 ("Dammann Tea Camomile Tea 96ct","Tea","96ct","bulk","Tea box.","high",0),
 ("Soda, Sprite Can 12fl.oz","Soda","12oz","can12","GREEN Sprite can.","high",0),
 ("Soda, Coke Can 12fl.oz","Soda","12oz","can12","RED Coca-Cola can, classic.","high",0),
 ("Soda, Diet Coke Can 12fl.oz","Soda","12oz","can12","SILVER Diet Coke can.","high",0),
 ("San Pellegrino Sparkling Water Can 330ml","Water","330ml","can12","Pellegrino can, blue/green.","high",0),
 ("San Pellegrino Sparkling Water Limonata 330ml","Soda","330ml","can12","YELLOW Limonata can.","high",0),
 ("Dammann Earl Grey Yin Zhen Sachet 1sachet","Tea","1sachet","bulk","Tea.","medium",0),
 ("Ginger Ale 8fl.oz","Soda","8oz","cansm","Small ginger ale — Seagram's or Shasta.","medium",0),
 ("Acqua Panna Natural Spring Water 750ml","Water","750ml","water750","750ml glass, cream/terracotta label, TUSCANY.","high",0),
 ("San Pellegrino Spk Water Gls 750ml","Water","750ml","water750","750ml GREEN glass, red star, S.PELLEGRINO.","high",0),
 ("Club Soda 12fl.oz","Soda","12oz","can12","Club soda can.","medium",0),
 ("Red Bull Energy Drink 8.4fl.oz","Energy","8.4oz","cansm","Slim blue/silver Red Bull can.","high",0),
 ("Monster Energy Drink 16fl.oz","Energy","16oz","can12","Large black can with the green claw.","high",0),
 ("Dammann Breakfast Hot Tea 1case","Tea","1case","bulk","Tea case.","medium",0),
 ("Dammann Tea Green T W/Jsmn 96ct","Tea","96ct","bulk","Tea box.","medium",0),
 ("Dammann Tea Menthe Tea 96ct","Tea","96ct","bulk","Tea box.","medium",0),
 ("Dammann Tea Earl Grey Tea 96ct","Tea","96ct","bulk","Tea box.","medium",0),
 ("The Republic Of Tea 12fl.oz","Tea","12oz","bulk","Bottled tea.","medium",0),
 ("Tea Republic Passion Grn Tea 12fl.oz","Tea","12oz","bulk","Bottled tea.","medium",0),
 ("Tea Republic Pomegranate Green 12fl.oz","Tea","12oz","bulk","Bottled POMEGRANATE GREEN TEA — this is the labelled tea bottle seen in the coolers.","high",0),
 ("Monin Organic Agave Nectar 1L","Syrup","1L","syrup1L","Monin 1L syrup bottle, white cap.","high",0),
 ("Acqua Panna Natural Spring Water 1L","Water","1L","water750","1L Acqua Panna.","high",0),
 ("Monin Strawberry Rose Syrup 1L","Syrup","1L","syrup1L","Monin 1L, pink/red syrup.","high",0),
 ("Juice, Apple Can 7.2fl.oz","Juice","7.2oz","cansm","Small apple juice can.","medium",0),
 ("Re'al Watermelon Puree 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle, pink-red.","medium",0),
 ("Re'Al Raspberry Puree 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle, deep red.","medium",0),
 ("Q Mixers Tonic 7.5 7.5fl.oz","Mixer","7.5oz","cansm","Q Mixers slim can, YELLOW — PREMIUM TONIC WATER, CRISP & DRY.","high",0),
 ("Acqua Panna Natural Spring Water 500ml","Water","500ml","water750","500ml Acqua Panna.","high",0),
 ("Monin Syrup Watermelon 1L","Syrup","1L","syrup1L","Monin 1L, pink syrup.","medium",0),
 ("Monin Lavender Syrup 1L","Syrup","1L","syrup1L","Monin 1L, purple syrup.","medium",0),
 ("Root Beer 12fl.oz","Soda","12oz","can12","Root beer can.","medium",0),
 ("Dammann Chamomile 1each","Tea","1each","bulk","Tea.","medium",0),
 ("Pineapple Juice 6fl.oz","Juice","6oz","cansm","Small pineapple juice can.","medium",0),
 ("Blood Orange Monin 1L","Syrup","1L","syrup1L","Monin 1L, orange-red syrup.","medium",0),
 ("Illy Intenso 3kg","Coffee","3kg","bulk","Coffee bean bag, not a bottle.","high",0),
 ("Illy Medium Roast Whole Bean 3kg","Coffee","3kg","bulk","Coffee bean bag.","high",0),
 ("Fever Tree Ginger Ale 200ml","Mixer","200ml","mixer200","Small clear glass, Fever-Tree tree logo, ginger-ale colourway.","high",0),
 ("Fever Tree Sparkling Sicilian Lemonade 6.76fl.oz","Mixer","200ml","mixer200","Small clear glass, YELLOW Fever-Tree label, SICILIAN LEMONADE.","high",0),
 ("Illy Intenso Frac Pack 48 64g","Coffee","64g","bulk","Coffee pack.","medium",0),
 ("Ghiradelli Hot Chocolate 1lb","Cocoa","1lb","bulk","Cocoa tin/bag.","medium",0),
 ("Fee Brothers Cherry Bitters 1each","Bitters","1each","mixer200","Small bitters bottle, Fee Brothers label.","high",0),
 ("Rose's Grenadine 1L","Syrup","1L","syrup1L","Deep red grenadine, Rose's label.","high",0),
 ("Iced Tea Brew Black 1oz","Tea","1oz","bulk","Brew concentrate.","medium",0),
 ("Monin Ginger Syrup 1L","Syrup","1L","syrup1L","Monin 1L, amber syrup.","medium",0),
 ("Coke Zero 12oz","Soda","12oz","can12","BLACK/RED Coke Zero Sugar can.","high",0),
 ("Dammann Chamomile Sachets 84each","Tea","84each","bulk","Tea box.","medium",0),
 ("Q Mixers Ginger Beer 7.5oz","Mixer","7.5oz","cansm","Q Mixers slim can — ginger beer. Bottled version has a PURPLE crown cap.","high",0),
 ("Re'Al Guava Puree Infused Syrup 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle.","medium",0),
 ("Illy Iperespresso Mono Flowpack Decaf 3.3oz","Coffee","3.3oz","bulk","Coffee pack.","medium",0),
 ("Soda Diet Coke 2Ltr 2L","Soda","2L","bulk","2L plastic bottle.","high",0),
 ("San Pellegrino Spk Water Gls 1L","Water","1L","water750","1L green glass Pellegrino.","high",0),
 ("Illy Iper Bold Roast 30ct","Coffee","30ct","bulk","Coffee capsules.","medium",0),
]


NA2 = [
 ("Orange Juice (gal)","Juice","1gal","bulk","Foodservice jug.","medium",0),
 ("Lime Juice (fl.oz)","Juice","fl.oz","bulk","Foodservice jug or bottle.","medium",0),
 ("Lemon Juice (fl.oz)","Juice","fl.oz","bulk","Foodservice jug or bottle.","medium",0),
 ("Juice, Orange 1fl.oz","Juice","1fl.oz","cansm","Small single-serve orange juice.","medium",0),
 ("Juice - Lime 1 Gal 1gal","Juice","1gal","bulk","Gallon jug.","medium",0),
 ("Illy Wh Bean Intenso 250G Can 8839 250g","Coffee","250g","bulk","Illy pressurised tin, 250g.","high",0),
 ("Coffee, Folgers Instant Regular 8oz","Coffee","8oz","bulk","Instant coffee tub.","high",0),
 ("Illy Whole Bean Tin Decaf 1.5kg","Coffee","1.5kg","bulk","Illy tin, DECAF.","high",0),
 ("Dammann Tea Jardin Bleu Tea 96ct","Tea","96ct","bulk","Tea box.","medium",0),
 ("Dammann Chamomile Sachet 84 Ct 1each","Tea","84ct","bulk","Tea box.","medium",0),
 ("Bloody Mary Agalima Organic 1L","Mixer","1L","syrup1L","Agalima organic Bloody Mary mix, 1L.","medium",0),
 ("Fever Tree Club Soda Gls 6.8fl.oz","Mixer","200ml","mixer200","Small clear glass, Fever-Tree tree logo, CLUB SODA.","high",0),
 ("Fever Tree Club Soda 6.8fl.oz","Mixer","200ml","mixer200","Duplicate-size club soda SKU.","medium",0),
 ("Agave Nectar 1btl","Syrup","1btl","syrup1L","Agave syrup bottle.","medium",0),
 ("Apple Juice 1fl.oz","Juice","1fl.oz","cansm","Small apple juice.","medium",0),
 ("Fever Tree Tonic Gls 6.8fl.oz","Mixer","200ml","mixer200","Small clear glass, YELLOW-white Fever-Tree label, PREMIUM TONIC WATER.","high",0),
 ("Juice, Cranberry 64fl.oz","Juice","64oz","bulk","Ocean Spray foodservice bottle, red label.","high",0),
 ("Fever Tree Lime & Yuzu 1btl","Mixer","200ml","mixer200","Fever-Tree, lime and yuzu colourway.","medium",0),
 ("Fever Tree Club Soda 200ml 1each","Mixer","200ml","mixer200","Fever-Tree club soda, 200ml glass.","high",0),
 ("Fever Tree Soda 1btl","Mixer","200ml","mixer200","Generic Fever-Tree soda line item.","low",1),
 ("Fever Tree Pink Grapefruit Gls 6.8fl.oz","Mixer","200ml","mixer200","Small clear glass, PINK Fever-Tree label, GRAPEFRUIT.","high",0),
 ("Luxardo Maraschino Cherries 400g","Garnish","400g","bulk","Squat dark jar, Luxardo label. Garnish, not a drink.","high",0),
 ("Juice, Cranberry White 64fl.oz","Juice","64oz","bulk","White cranberry, foodservice bottle.","medium",0),
 ("Gatorade Glacier Frost 20fl.oz","Sports","20oz","bulk","Light blue Gatorade bottle.","high",0),
 ("Luxardo Maraschino Cherries 14fl.oz","Garnish","14oz","bulk","Smaller Luxardo jar.","high",0),
 ("Lemonade 1gal","Juice","1gal","bulk","Gallon jug.","medium",0),
 ("Q Mixers Ginger Beer Gls 6.7fl.oz","Mixer","200ml","mixer200","Q Mixers GLASS bottle, PURPLE crown cap, GINGER BEER.","high",0),
 ("Q Mixers Ginger Ale Gls 6.7fl.oz","Mixer","200ml","mixer200","Q Mixers glass bottle, ginger ale colourway.","high",0),
 ("Q Mixers Pink Grapefruit Gls 6.7fl.oz","Mixer","200ml","mixer200","Q Mixers glass bottle, pink grapefruit.","high",0),
 ("Puree Real Strawberry 16fl.oz","Puree","16oz","bulk","Re'al squeeze bottle, red.","medium",0),
 ("Q Mixers Club Soda Gls 6.7fl.oz","Mixer","200ml","mixer200","Q Mixers glass bottle, club soda.","high",0),
 ("Re'Al Strawberry Puree Infused Syrup 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle.","medium",0),
 ("Real Puree/Syrup 16fl.oz","Puree","16oz","bulk","Generic Re'al line item.","low",1),
 ("Q Mixers Tonic Gls 6.7fl.oz","Mixer","200ml","mixer200","Q Mixers GLASS bottle, tonic. Distinct from the 7.5oz can.","high",0),
 ("Re'Al Peach Puree Infused Syrup 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle.","medium",0),
 ("Re'Al Black Cherry Puree Infused Syrup 16.9fl.oz","Puree","16.9oz","bulk","Re'al squeeze bottle.","medium",0),
 ("Sparkling Sicilian Lemonade 6.7fl.oz","Mixer","200ml","mixer200","Fever-Tree Sicilian lemonade, yellow label.","high",0),
 ("Real Syrup 16.9fl.oz","Syrup","16.9oz","bulk","Generic Re'al line item.","low",1),
 ("Monin Hibiscus Syrup 1L","Syrup","1L","syrup1L","Monin 1L, deep pink-red.","medium",0),
 ("Dammann Earl Grey Blk Tea Loose 1ct","Tea","1ct","bulk","Loose tea.","medium",0),
 ("Coke Mexican Glass 355ml","Soda","355ml","water750","GLASS Coca-Cola bottle, Mexican Coke. Distinct from the cans.","high",0),
 ("Bigelow Mint Medley 1ct","Tea","1ct","bulk","Tea box.","medium",0),
 ("San Pellegrino Spk Water Gls 500ml","Water","500ml","water750","500ml green glass Pellegrino, red star.","high",0),
 ("V8 46oz","Juice","46oz","bulk","Large V8 bottle.","high",0),
 ("Q Mixers Club Soda 7.5 7.5fl.oz","Mixer","7.5oz","cansm","Q Mixers slim CAN, club soda.","high",0),
 ("Q Drinks Ginger Ale 7.5fl.oz","Mixer","7.5oz","cansm","Q Drinks can, ginger ale.","medium",0),
 ("Fever Tree Club Soda 16.9fl.oz","Mixer","500ml","water750","Larger 500ml Fever-Tree bottle.","medium",0),
 ("Coke 2L","Soda","2L","bulk","2L plastic bottle, red label.","high",0),
 ("Sprite 2L","Soda","2L","bulk","2L plastic bottle, green label.","high",0),
 ("Red Bull Energy Drink Blue 12fl.oz","Energy","12oz","can12","Red Bull BLUE EDITION can — distinct from the 8.4oz silver/blue original.","high",0),
 ("Evian Mineral Spring Water Gls 750ml","Water","750ml","water750","Clear glass Evian, pink/blue label.","high",0),
 ("Instant Coffee 19oz","Coffee","19oz","bulk","Instant coffee tub.","medium",0),
 ("Angostura Bitters 7fl.oz","Bitters","7oz","mixer200","Small bottle with an OVERSIZED yellow cap and a cream label too big for the bottle. Unmistakable.","high",0),
 ("Illy Iper Esp Intenso 50Ct Bag8831 50ct","Coffee","50ct","bulk","Illy capsule bag.","medium",0),
 ("Illy Classico Iper Capsules 30each","Coffee","30ct","bulk","Illy capsule pack.","medium",0),
 ("Illy Classico Beans 3kg","Coffee","3kg","bulk","Illy bean bag.","medium",0),
 ("Squirt Soda 12fl.oz","Soda","12oz","can12","Yellow-green Squirt can.","high",0),
 ("Coke/Diet Coke Classic 7.5fl.oz","Soda","7.5oz","cansm","Mini Coke can.","high",0),
 ("Blood Orange Juice 32fl.oz","Juice","32oz","bulk","Blood orange juice bottle.","medium",0),
 ("Filthy Bloody Mary Mix Pouch 32fl.oz","Mixer","32oz","bulk","Filthy brand pouch.","medium",0),
 ("Coffee Instant Individual Decaf 80ct","Coffee","80ct","bulk","Instant sachets.","medium",0),
 ("Dammann Breakfast Black Tea 1kg","Tea","1kg","bulk","Loose tea.","medium",0),
 ("Fever Tree Elderflower Tonic 6.76fl.oz","Mixer","200ml","mixer200","Fever-Tree, elderflower colourway.","high",0),
 ("Fever Tree Ginger Beer 200ml","Mixer","200ml","mixer200","Fever-Tree ginger beer, 200ml glass.","high",0),
 ("Agalima Bloody Mary Mix 1L","Mixer","1L","syrup1L","Agalima 1L Bloody Mary mix.","medium",0),
 ("Club Soda Dry 10fl.oz","Mixer","10oz","cansm","Dry brand club soda.","medium",0),
 ("Illy Decaf Frac Pack 192Gr 8894 192g","Coffee","192g","bulk","Illy fractional pack.","medium",0),
 ("Illy Espresso Tin 1kg","Coffee","1kg","bulk","Illy tin.","medium",0),
 ("Illy Cold Brew 7895 5L","Coffee","5L","bulk","Cold brew container.","medium",0),
 ("Illy Ipercapsule Espresso Decaf 18ct","Coffee","18ct","bulk","Illy capsules.","medium",0),
 ("Illy Cold Brew Pillow Pk 7161 1case","Coffee","1case","bulk","Cold brew case.","medium",0),
 ("Illy Wh Bean Classico 250G Can8841 250g","Coffee","250g","bulk","Illy tin, CLASSICO.","medium",0),
 ("Illy Wh Bean Decaf 250G Can 8835 250g","Coffee","250g","bulk","Illy tin, DECAF.","medium",0),
 ("Illy Iper Esp Intenso 30Ct Bag9887 30ct","Coffee","30ct","bulk","Illy capsule bag.","medium",0),
 ("Illy Intenso Frac Pack 192G 8892 192g","Coffee","192g","bulk","Illy fractional pack.","medium",0),
 ("Illy Ipercapsule Esp Classico 50C Bag8830 50ct","Coffee","50ct","bulk","Illy capsule bag.","medium",0),
 ("Illy Whole Bean Tin Med 3kg","Coffee","3kg","bulk","Illy tin, medium roast.","medium",0),
 ("Illy Whole Bean Tin Dark 3kg","Coffee","3kg","bulk","Illy tin, dark roast.","medium",0),
]


# Items appearing on the Neiman Marcus Boca Raton menu. These must be accurate;
# everything else is secondary. Matched by exact catalog name.
MENU_ITEMS = {
 # cocktails
 "Reyka Vodka 1L", "Espolon Tequila Reposado 750ml", "Campari 1L",
 "Belvedere Vodka 1L", "Belle de Brillet Pear Liqueur 750ml",
 "Dos Maderas 5 + 3 Double Aged Rum 750ml", "Glenmorangie 10 Yr 750ml",
 "Glenmorangie X 750ml", "Kahlua Coffee Liqueur 1L", "Baileys Irish Cream 1L",
 "St. Germain Elderflower 750ml", "Fiorente Elderflower Liqueur 700ml",
 "Monin Lavender Syrup 1L", "Monin Strawberry Rose Syrup 1L",
 "Agave Nectar 1btl",
 # sparkling
 "Moet Brut Imperial 750ml", "Moet Imperial 187ml",
 "Ferrari Rose 375ml", "Scharffenberger 750ml", "Bisol Jeio Prosecco 750ml",
 "Veuve Clicquot Yellow Label 750ml", "Albrecht Cremant Brut Rose 750ml",
 "Dom Perignon Luminous 750ml",
 # whites and rose
 "Whispering Angel Rose 375ml", "Whispering Angel Rose 750ml",
 "Attems Pino Grigio 750ml", "Cakebread Sauvignon Blanc 750ml",
 "Neiman Marcus Chardonnay 750ml", "Sonoma Cutrer Chardonnay 750ml",
 "Cuvaison Chardonnay 750ml", "Roseblood Rose 750ml",
 # reds
 "Belle Glos Pinot Noir 750ml", "Duckhorn Cabernet Sauvignon 18 750ml",
 # chilled / NA
 "Tea Republic Pomegranate Green 12fl.oz",
 "Acqua Panna Natural Spring Water 750ml", "San Pellegrino Spk Water Gls 750ml",
 "Wolffer Spring In A Bottle 750ml",
 "Fever Tree Club Soda 200ml 1each", "Fever Tree Ginger Beer 200ml",
 "Fever Tree Elderflower Tonic 6.76fl.oz", "Fever Tree Ginger Ale 200ml",
 "Fever Tree Sparkling Sicilian Lemonade 6.76fl.oz",
 "De Soi Purple Lune NA Aperitif", "Illy Classico Beans 3kg",
 "High West Barrel Select 1L", "Giffard Banane du Bresil 1L", "Beer",
 "Aplos Arise 1L", "Tost Sparkling 1L",
}

# On the menu but with no SKU in the Craftable list. Flagged so they are not
# silently missed at count time.
MENU_NO_SKU = []

def rows(prefix, data, cat):
    out = []
    for i, (name, sub, size, shape, cue, conf, np_) in enumerate(data, 1):
        r = {"id": f"{prefix}{i:02d}", "name": name, "cat": cat, "sub": sub,
             "size": size, "shape": shape, "cues": cue, "confidence": conf,
             "shelf": shape != "bulk"}
        if name in MENU_ITEMS:
            r["menu"] = True
        if np_:
            r["needs_photo"] = True
        out.append(r)
    return out


def collapse_liquor(items):
    """The operator counts every liquor bottle as 1L, so the 750/1L SKU pairs
    are a distinction without a difference at count time. Keep one entry per
    product, normalised to 1L, and record what it absorbed."""
    out, seen = [], {}
    for it in items:
        if it["cat"] != "liquor" or it["name"] == "Beer":
            out.append(it); continue
        base = re.sub(r"\s*\b(750ml|1L|700ml|1\.75L)\b\s*$", "", it["name"]).strip()
        key = base.lower()
        if key in seen:
            prev = seen[key]
            prev.setdefault("absorbed", []).append(it["name"])
            if it.get("menu"):
                prev["menu"] = True
            continue
        it = dict(it)
        it["name"] = base + " 1L"
        it["size"] = "1L"
        it["shape"] = "spirit1L" if it["shape"] in ("spirit750", "spirit1L") else it["shape"]
        it["cues"] = re.sub(r"\s*(Taller than the 750\.|Shorter than the 1L\.|1L is taller\.|"
                            r"Visibly taller than the 750\.|Size is the only discriminator\.|"
                            r"Size is the discriminator\.|750 is the shorter one\.|"
                            r"Same as the 1L but SHORTER\.)", "", it["cues"]).strip()
        seen[key] = it
        out.append(it)
    return out

catalog = {
    "version": "2026-09-01b",
    "note": ("Master SKU catalog transcribed from the Craftable item list — wine, liquor and "
             "NA Bev complete. 'cues' describe only what survives a bad shelf photo: bottle "
             "colour, capsule/cap colour, label colour, glass shape. Where two SKUs differ only "
             "by size, the cue says so — 1L bottles stand visibly taller than 750ml."),
    "shapes": SHAPES,
    "items": collapse_liquor(rows("W", WINE, "wine") + rows("L", LIQUOR, "liquor") + rows("N", NA + NA2, "na")),
    "menu_no_sku": MENU_NO_SKU,
}

with open("catalog.json", "w") as f:
    json.dump(catalog, f, indent=1)

print(f"wine   {len(WINE)}")
print(f"liquor {len(LIQUOR)}")
print(f"na     {len(NA)}")
print(f"TOTAL  {len(catalog['items'])} SKUs")
print(f"shelf-visible: {sum(1 for i in catalog[chr(39)+chr(39)] if 0)}") if False else None
print(f"shelf-visible: {sum(1 for i in catalog['items'] if i['shelf'])}")
print(f"back-of-house: {sum(1 for i in catalog['items'] if not i['shelf'])}")
print(f"MENU items: {sum(1 for i in catalog['items'] if i.get('menu'))}")
print(f"menu items with NO sku: {len(MENU_NO_SKU)}")
print(f"needs_photo: {sum(1 for i in catalog['items'] if i.get('needs_photo'))}")
