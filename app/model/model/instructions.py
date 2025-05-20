class InstructionsHandler:
    def __init__(self):
        self.ate = {}
        self.atsc = {}
        self.aspe = {}
        self.aooe = {}
        self.aope = {}
        self.aoste = {}

    def load_instruction_set1(self, ):

        ################################# ATE #################################

        self.ate['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) which have an associated opinion that are extracted from the input text. In cases where there are no aspects the output should be noaspectterm.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life.
        output: battery life
        Positive example 2-
        input: I even got my teenage son one, because of the features that it offers, like, iChat, Photobooth, garage band and more!.
        output: features, iChat, Photobooth, garage band
        Now complete the following example-
        input: """

        self.ate['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) which have an associated opinion that are extracted from the input text. In cases where there are no aspects the output should be noaspectterm.
        Positive example 1-
        input: With the great variety on the menu , I eat here often and never get bored.
        output: menu
        Positive example 2- 
        input: Great food, good size menu, great service and an unpretensious setting.
        output: food, menu, service, setting
        Now complete the following example-
        input: """
        self.ate['delim_instruct'] = ''
        self.ate['eos_instruct'] = ' \noutput:'

        ################################# ATSC #################################

        self.atsc['bos_instruct1'] = """Definition: The output will be 'positive' if the aspect identified in the sentence contains a positive sentiment. If the sentiment of the identified aspect in the input is negative the answer will be 'negative'. 
        Otherwise, the output should be 'neutral'. For aspects which are classified as noaspectterm, the sentiment is none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life. The aspect is battery life.
        output: positive
        Positive example 2-
        input: I even got my teenage son one, because of the features that it offers, like, iChat, Photobooth, garage band and more!. The aspect is garage band.
        output: positive
        Now complete the following example-
        input: """
        
        self.atsc['bos_instruct2'] = """Definition: The output will be 'positive' if the aspect identified in the sentence contains a positive sentiment. If the sentiment of the identified aspect in the input is negative the answer will be 'negative'. 
        Otherwise, the output should be 'neutral'. For aspects which are classified as noaspectterm, the sentiment is none.
        Positive example 1-
        input: With the great variety on the menu , I eat here often and never get bored. The aspect is menu.
        output: positive
        Positive example 2- 
        input: Great food, good size menu, great service and an unpretensious setting. The aspect is food.
        output: positive
        Now complete the following example-
        input: """
        self.atsc['delim_instruct'] = ' The aspect is '
        self.atsc['eos_instruct'] = '.\noutput:'

        ################################# ASPE #################################

        self.aspe['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: I absolutely loved the cinematography and the soundtrack elevated every scene.
        output: cinematography:positive, soundtrack:positive,
        Positive example 2-
        input: The performances were stellar and the direction was flawless.
        output: performances:positive, direction:positive
        Now complete the following example-
        input: """
        
        self.aspe['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: The storyline was gripping and the special effects were breathtaking.
        output: storyline:positive, special effects:positive
        Positive example 2- 
        input: The pacing felt tight and the character development was superb.
        output: pacing:positive, character development:positive
        Now complete the following example-
        input: """
        self.aspe['delim_instruct'] = ''
        self.aspe['eos_instruct'] = ' \noutput:'

        ################################# AOOE #################################

        self.aooe['bos_instruct1'] = """Definition: The output will be the opinion/describing word of the aspect terms in the sentence. In cases where there are no aspects the output should be none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life . The aspect is battery life.
        output: good
        Positive example 2-
        input: it is of high quality , has a killer GUI , is extremely stable , is highly expandable , is bundled with lots of very good applications , is easy to use , and is absolutely gorgeous. The aspect is GUI.
        output: killer
        Now complete the following example-
        input: """
        
        self.aooe['bos_instruct2'] = """Definition: The output will be the opinion/describing word for the aspect term in the sentence. In cases where there are no aspects the output should be none.
        Positive example 1-
        input: Faan 's got a great concept but a little rough on the delivery . The aspect term is delivery.
        output: rough
        Positive example 2- 
        input: At the end you 're left with a mild broth with noodles that you can slurp out of a cup . The aspect term is broth with noodles.
        output: mild
        Now complete the following example-
        input: """
        self.aooe['delim_instruct'] = ' The aspect is '
        self.aooe['eos_instruct'] = '.\noutput:'

        ################################# AOPE #################################

        self.aope['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) and the corresponding opinion/describing terms. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life.
        output: battery life:good 
        Positive example 2-
        input: it is of high quality , has a killer GUI , is extremely stable , is highly expandable , is bundled with lots of very good applications , is easy to use , and is absolutely gorgeous.
        output: quality:high, GUI:killer, applications:good, use:easy 
        Now complete the following example-
        input: """
        
        self.aope['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: Faan 's got a great concept but a little rough on the delivery .
        output: delivery:rough
        Positive example 2- 
        input: I just wonder how you can have such a delicious meal for such little money .
        output: meal:delicious, money:little
        Now complete the following example-
        input: """
        self.aope['delim_instruct'] = ''
        self.aope['eos_instruct'] = ' \noutput:'

        ################################# AOSTE #################################

        self.aoste['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) the corresponding opinion/describing terms and the sentiment polarity (positive, negative, neutral) of the opinion term . In cases where there are no aspects the output should be noaspectterm:none:none.
        Positive example 1-
        input: I was absolutely captivated by the gripping plot, and the lead actor delivered a truly unforgettable performance.
        output: plot:gripping:positive, performance:unforgettable:positive
        Positive example 2-
        input: The stunning cinematography and evocative soundtrack elevated every scene, making the film a visual and auditory masterpiece.
        output: cinematography:stunning:positive, soundtrack:evocative:positive, film:masterpiece:positive
        Now complete the following example-
        input: """
        
        self.aoste['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) the corresponding opinion/describing terms and the sentiment polarity (positive, negative, neutral) of the opinion term . In cases where there are no aspects the output should be noaspectterm:none:none.
        Positive example 1-
        input: Faan 's got a great concept but a little rough on the delivery .
        output: delivery:rough:positive
        Positive example 2- 
        input: I just wonder how you can have such a delicious meal for such little money .
        output: meal:delicious:positive, money:little:positive
        Now complete the following example-
        input: """
        self.aoste['delim_instruct'] = ''
        self.aoste['eos_instruct'] = ' \noutput:'


    def load_instruction_set2(self, ):

        ################################# ATE #################################

        self.ate['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) which have an associated opinion that are extracted from the input text. In cases where there are no aspects the output should be noaspectterm.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life.
        output: battery life
        Positive example 2-
        input: I even got my teenage son one, because of the features that it offers, like, iChat, Photobooth, garage band and more!.
        output: features, iChat, Photobooth, garage band
        Negative example 1-
        input: Speaking of the browser, it too has problems.
        output: browser
        Negative example 2-
        input: The keyboard is too slick.
        output: keyboard
        Neutral example 1-
        input: I took it back for an Asus and same thing- blue screen which required me to remove the battery to reset.
        output: battery
        Neutral example 2-
        input: Nightly my computer defrags itself and runs a virus scan.
        output: virus scan
        Now complete the following example-
        input: """
        
        self.ate['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) which have an associated opinion that are extracted from the input text. In cases where there are no aspects the output should be noaspectterm.
        Positive example 1-
        input: With the great variety on the menu , I eat here often and never get bored.
        output: menu
        Positive example 2- 
        input: Great food, good size menu, great service and an unpretensious setting.
        output: food, menu, service, setting
        Negative example 1-
        input: They did not have mayonnaise, forgot our toast, left out ingredients (ie cheese in an omelet), below hot temperatures and the bacon was so over cooked it crumbled on the plate when you touched it.
        output: toast, mayonnaise, bacon, ingredients, plate
        Negative example 2-
        input: The seats are uncomfortable if you are sitting against the wall on wooden benches.
        output: seats
        Neutral example 1-
        input: I asked for seltzer with lime, no ice.
        output: seltzer with lime
        Neutral example 2-
        input: They wouldnt even let me finish my glass of wine before offering another.
        output: glass of wine
        Now complete the following example-
        input: """
        self.ate['delim_instruct'] = ''
        self.ate['eos_instruct'] = ' \noutput:'

        ################################# ATSC #################################

        self.atsc['bos_instruct1'] = """Definition: The output will be 'positive' if the aspect identified in the sentence contains a positive sentiment. If the sentiment of the identified aspect in the input is negative the answer will be 'negative'. 
        Otherwise, the output should be 'neutral'. For aspects which are classified as noaspectterm, the sentiment is none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life. The aspect is battery life.
        output: positive
        Positive example 2-
        input: I even got my teenage son one, because of the features that it offers, like, iChat, Photobooth, garage band and more!. The aspect is garage band.
        output: positive
        Negative example 1-
        input: Speaking of the browser, it too has problems. The aspect is browser.
        output: negative
        Negative example 2-
        input: The keyboard is too slick. The aspect is keyboard.
        output: negative
        Neutral example 1-
        input: I took it back for an Asus and same thing- blue screen which required me to remove the battery to reset. The aspect is battery.
        output: neutral
        Neutral example 2-
        input: Nightly my computer defrags itself and runs a virus scan. The aspect is virus scan.
        output: neutral
        Now complete the following example-
        input: """
        
        self.atsc['bos_instruct2'] = """Definition: The output will be 'positive' if the aspect identified in the sentence contains a positive sentiment. If the sentiment of the identified aspect in the input is negative the answer will be 'negative'. 
        Otherwise, the output should be 'neutral'. For aspects which are classified as noaspectterm, the sentiment is none.
        Positive example 1-
        input: With the great variety on the menu , I eat here often and never get bored. The aspect is menu.
        output: positive
        Positive example 2- 
        input: Great food, good size menu, great service and an unpretensious setting. The aspect is food.
        output: positive
        Negative example 1-
        input: They did not have mayonnaise, forgot our toast, left out ingredients (ie cheese in an omelet), below hot temperatures and the bacon was so over cooked it crumbled on the plate when you touched it. The aspect is toast.
        output: negative
        Negative example 2-
        input: The seats are uncomfortable if you are sitting against the wall on wooden benches. The aspect is seats.
        output: negative
        Neutral example 1-
        input: I asked for seltzer with lime, no ice. The aspect is seltzer with lime.
        output: neutral
        Neutral example 2-
        input: They wouldnt even let me finish my glass of wine before offering another. The aspect is glass of wine.
        output: neutral
        Now complete the following example-
        input: """
        self.atsc['delim_instruct'] = ' The aspect is '
        self.atsc['eos_instruct'] = '.\noutput:'

        ################################# ASPE #################################

        self.aspe['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: The cinematography was stunning and the score was moving.
        output: cinematography:positive, score:positive, 
        Positive example 2-
        input: I loved the performances and the dialogue felt natural.
        output: performances:positive, dialogue:positive
        Negative example 1-
        input: The acting was wooden and the script was cliché.
        output: acting:negative, script:negative
        Negative example 2-
        input: The special effects looked fake and the soundtrack was distracting.
        output: special effects:negative, soundtrack:negative
        Neutral example 1-
        input: The runtime was long but not unbearable.
        output: runtime:neutral
        Neutral example 2-
        input: The plot was average and the pacing was steady.
        output: plot:neutral, pacing:neutral
        Now complete the following example-
        input: """
        
        self.aspe['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: The visual effects were breathtaking and the score complemented every scene.
        output: visual effects:positive, score:positive
        Positive example 2- 
        input: The movie's direction, acting, soundtrack, and cinematography were all outstanding.
        output: direction:positive, acting:positive, soundtrack:positive, cinematography:positive
        Negative example 1-
        input: The pacing dragged in the middle and the dialogue was clunky.
        output: pacing:negative, dialogue:negative
        Negative example 2-
        input: The special effects looked cheap and the editing was jarring.
        output: special effects:negative, editing:negative
        Neutral example 1-
        input: The runtime was long but offered some memorable moments.
        output: runtime:neutral
        Neutral example 2-
        input: The cinematography was standard and the story was predictable.
        output: cinematography:neutral, story:neutral
        Now complete the following example-
        input: """
        self.aspe['delim_instruct'] = ''
        self.aspe['eos_instruct'] = ' \noutput:'

        ################################# AOOE #################################

        self.aooe['bos_instruct1'] = """Definition: The output will be the opinion/describing word of the aspect terms in the sentence. In cases where there are no aspects the output should be none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life . The aspect is battery life.
        output: good
        Positive example 2-
        input: it is of high quality , has a killer GUI , is extremely stable , is highly expandable , is bundled with lots of very good applications , is easy to use , and is absolutely gorgeous. The aspect is GUI.
        output: killer
        Negative example 1-
        input: One night I turned the freaking thing off after using it , the next day I turn it on , no GUI , screen all dark , power light steady , hard drive light steady and not flashing as it usually does . The aspect is GUI.
        output: no
        Negative example 2-
        input: I can barely use any usb devices because they will not stay connected properly . The aspect is usb devices.
        output: not stay connected properly
        Neutral example 1-
        input: However , the multi-touch gestures and large tracking area make having an external mouse unnecessary ( unless you 're gaming ) . The aspect is external mouse.
        output: unnecessary
        Neutral example 2-
        input: I wanted to purchase the extended warranty and they refused , because they knew it was trouble . The aspect is extended warranty.
        output: refused
        Now complete the following example-
        input: """

        self.aooe['bos_instruct2'] = """Definition: The output will be the opinion/describing word of the aspect terms in the sentence. In cases where there are no aspects the output should be none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life . The aspect is battery life.
        output: good
        Positive example 2-
        input: it is of high quality , has a killer GUI , is extremely stable , is highly expandable , is bundled with lots of very good applications , is easy to use , and is absolutely gorgeous. The aspect is GUI.
        output: killer
        Negative example 1-
        input: The menu is very limited - i think we counted 4 or 5 entrees . The aspect is menu.
        output: limited
        Negative example 2-
        input: The strong scents coming from the left and right of me negatively affected my taste buds . The aspect is scents.
        output: strong
        Neutral example 1-
        input: What came to our table was burned beyond recognition and stringy . The aspect is battery table.
        output: burned
        Neutral example 2-
        input: But , nothing stands out about the cooking . The aspect is cooking.
        output: nothing stands out
        Now complete the following example-
        input: """
        self.aooe['delim_instruct'] = ' The aspect is '
        self.aooe['eos_instruct'] = '.\noutput:'

        ################################# AOPE #################################

        self.aope['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) and the corresponding opinion/describing terms. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: I charge it at night and skip taking the cord with me because of the good battery life.
        output: battery life:good 
        Positive example 2-
        input: it is of high quality , has a killer GUI , is extremely stable , is highly expandable , is bundled with lots of very good applications , is easy to use , and is absolutely gorgeous.
        output: quality:high, GUI:killer, applications:good, use:easy
        Negative example 1-
        input: A month or so ago , the freaking motherboard just died .
        output: motherboard:freaking, motherboard:freaking
        Negative example 2-
        input: I had always used PCs and been constantly frustrated by the crashing and the poorly designed operating systems that were never very intuitive .
        output: operating systems:poorly designed, operating systems:intuitive
        Neutral example 1-
        input: It has a 10 hour battery life when you 're doing web browsing and word editing , making it perfect for the classroom or office , and in terms of gaming and movie playing it 'll have a battery life of just over 5 hours .
        output: web browsing:perfect, word editing:perfect
        Neutral example 2-
        input: no complaints with their desktop , and maybe because it just sits on your desktop , and you do n't carry it around , which could jar the hard drive , or the motherboard .
        output: hard drive:jar, motherboard:jar
        Now complete the following example-
        input: """
        
        self.aope['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) and the aspects sentiment polarity. In cases where there are no aspects the output should be noaspectterm:none.
        Positive example 1-
        input: Faan 's got a great concept but a little rough on the delivery .
        output: delivery:rough
        Positive example 2- 
        input: I just wonder how you can have such a delicious meal for such little money .
        output: meal:delicious, money:little
        Negative example 1-
        input: From the terrible service , to the bland food , not to mention the unaccommodating managers , the overall experience was horrible .
        output: service:terrible, food:bland, managers:unaccommodating
        Negative example 2- 
        input: I had the Pad Thai and the noodles were sticky .
        output: Pad Thai:sticky, noodles:sticky
        Neutral example 1-
        input: The Dim Sum was so-so , but not spectacular .
        output: Dim Sum:so-so, Dim Sum:not spectacular
        Neutral example 2- 
        input: The location and ambience is Ok but the food is what makes up for it .
        output: mlocationeal:Ok, ambience:Ok
        Now complete the following example-
        input: """
        self.aope['delim_instruct'] = ''
        self.aope['eos_instruct'] = ' \noutput:'

        ################################# AOSTE #################################

        self.aoste['bos_instruct1'] = """Definition: The output will be the aspects (both implicit and explicit) the corresponding opinion/describing terms and the sentiment polarity (positive, negative, neutral) of the opinion term . In cases where there are no aspects the output should be noaspectterm:none:none.
        Positive example 1-
        input: The film’s breathtaking visuals and seamless CGI created an immersive world I never wanted to leave.
        output: visuals:breathtaking:positive, CGI:seamless:positive, world:immersive:positive 
        Positive example 2-
        input: The lead actor’s nuanced performance and the sharp, witty dialogue kept me engaged from start to finish.
        output: performance:nuanced:positive, dialogue:sharp:positive, engagement:kept me engaged:positive
        Negative example 1-
        input: The pacing was painfully slow, and the plot felt disjointed and underdeveloped.
        output: pacing:painfully slow:negative, plot:disjointed:negative, plot:underdeveloped:negative
        Negative example 2-
        input: Despite the star-studded cast, the writing was cliché and the characters lacked any real depth.
        output: writing:cliché:negative, characters:lacked depth:negative
        Neutral example 1-
        input: The soundtrack was appropriate and the cinematography was competent, but nothing stood out as particularly memorable.
        output: soundtrack:appropriate:neutral, cinematography:competent:neutral
        Neutral example 2-
        input: It’s a serviceable thriller with a few tense moments, though it doesn’t break new ground in the genre.
        output: thriller:serviceable:neutral, moments:tense:neutral
        Now complete the following example-
        input: """
        
        self.aoste['bos_instruct2'] = """Definition: The output will be the aspects (both implicit and explicit) the corresponding opinion/describing terms and the sentiment polarity (positive, negative, neutral) of the opinion term . In cases where there are no aspects the output should be noaspectterm:none:none.
        Positive example 1-
        input: Faan 's got a great concept but a little rough on the delivery .
        output: delivery:rough:positive
        Positive example 2- 
        input: I just wonder how you can have such a delicious meal for such little money .
        output: meal:delicious:positive, money:little:positive
        Negative example 1-
        input: From the terrible service , to the bland food , not to mention the unaccommodating managers , the overall experience was horrible .
        output: service:terrible:negative, food:bland:negative, managers:unaccommodating:negative
        Negative example 2- 
        input: I had the Pad Thai and the noodles were sticky .
        output: Pad Thai:sticky:negative, noodles:sticky:negative
        Neutral example 1-
        input: The Dim Sum was so-so , but not spectacular .
        output: Dim Sum:so-so:neutral, Dim Sum:not spectacular:neutral
        Neutral example 2- 
        input: The location and ambience is Ok but the food is what makes up for it .
        output: mlocationeal:Ok:neutral, ambience:Ok:neutral
        Now complete the following example-
        input: """
        self.aoste['delim_instruct'] = ','
        self.aoste['eos_instruct'] = ' \noutput:'