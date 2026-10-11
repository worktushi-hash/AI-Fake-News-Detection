# Manual Quality Sample Review Log

**Review Status: COMPLETED**  
**Reviewer: Human Team Quality Audit**  
**Sample Size: 30 records total** (10 English, 10 Hindi, 10 Marathi; stratified across classes with random seed `42`)

---

## 1. Review Summary & Key Findings

1. **Text Normalization & Unicode Decoding**: Passed across all 30 sampled records. Devanagari text in Hindi and Marathi is correctly encoded with Unicode NFC. No garbled characters or replacement markers (`\xFF\xFE`, ``) were found.
2. **Website Header Boilerplate (Hindi & Marathi Real News)**:
   - Several `real` news articles in Hindi and Marathi (e.g. `hi_009448`) contain website navigation header menus (*"हिन्दी ख़बरें दुनिया वीडियो देश क्राइम खेल..."*) prepended to the article body during original web scraping.
   - *Recommendation for Modeling*: A targeted regular expression filter should be considered before transformer training to strip standard menu bars.
3. **Fact-Checking Debunker Articles in Fake Folders**:
   - In Hindi `fake` samples (e.g. `hi_000913`), articles reporting on debunked viral hoaxes (e.g., photoshopped images) were placed in the `fake` folder by original corpus creators.
   - *Recommendation for Modeling*: Models trained on raw text might learn that fact-check phrasing indicates fake news unless handled carefully.
4. **English WELFake Samples**:
   - `Label 0` samples consist of standard wire-service news articles (*Reuters*, *The New York Times*).
   - `Label 1` samples consist of opinion blog posts, clickbait headlines, and YouTube links.
   - Labels remain marked as `unverified` due to Zenodo metadata documentation conflicts.

---

## 2. Sampled Records Detail

### Sampled English Records (WELFake)

#### ID `en_014774` (Label `0` / Status `unverified`)
- **Source ID**: `15382`
- **Title**: To Put Ball in the Net, Dutch Clubs Shoot Space Aliens First - The New York Times
- **Text Preview**: Some of the young players enrolled at PSV Eindhoven’s academy have had to burst balloons. Others have been told to shoot dots, and more still have been tasked with bringing down alien space fleets. Th...

#### ID `en_003406` (Label `0` / Status `unverified`)
- **Source ID**: `3467`
- **Title**: Ever Wanted to Back a Start-Up? Indiegogo Opens the Door to Small Investors - The New York Times
- **Text Preview**: Armchair venture capitalists will soon have a new place to hunt for intriguing : Indiegogo, the popular crowdfunding site for developers of creative ventures like movies, games and gadgets. Starting o...

#### ID `en_034646` (Label `0` / Status `unverified`)
- **Source ID**: `37523`
- **Title**: Border Patrol Agents Seize $8M in Liquid Meth near Texas Border
- **Text Preview**: U. S. Border Patrol agents assigned to the Falfurrias, Texas, checkpoint discovered a shipment of liquid methamphetamine 80 miles from the Mexican border. The bust follows a similar seizure earlier th...

#### ID `en_031090` (Label `0` / Status `unverified`)
- **Source ID**: `33455`
- **Title**: Falcons Take Advantage of Seattle’s Stumble and Race to N.F.C. Title Game - The New York Times
- **Text Preview**: ATLANTA — In the playoffs, when the best teams meet, games are often decided by a mistake here or there, or a penalty called or not called. Under Coach Pete Carroll, the Seattle Seahawks have built a ...

#### ID `en_028553` (Label `0` / Status `unverified`)
- **Source ID**: `30573`
- **Title**: Donald Trump's obsession with himself
- **Text Preview**: From his condemnation of journalists to his racially tinged attacks on a judge presiding over a lawsuit related to Trump University to his feud with New Mexico GOP Gov. Susana Martinez, there's one th...

#### ID `en_008931` (Label `1` / Status `unverified`)
- **Source ID**: `9211`
- **Title**: WATCH MSNBC “Objective” Host’s Loud Outburst When Latina Guest Says She “Feels At Home” In GOP
- **Text Preview**: Somebody needs to make sure Chris Matthews doesn t miss his meds before the cameras start rolling...

#### ID `en_052447` (Label `1` / Status `unverified`)
- **Source ID**: `58919`
- **Title**: OBAMA TAKES TWO GAS GUZZLING PLANES For Sightseeing…What Global Warming?
- **Text Preview**: Obama brings two gas guzzlers on a sightseeing trip just another day in the life of preezy It s really easy to spend someone else s money, isn t it? In this case, it s YOUR money! The really ironic th...

#### ID `en_006498` (Label `1` / Status `unverified`)
- **Source ID**: `6660`
- **Title**: Kentucky Republicans Introduce Abortion Ban, Tells Women They Have No Choice
- **Text Preview**: Kentucky Republicans declared war on women as soon as the new legislative session began.One of the 11 bills introduced on Tuesday would ban abortion after 20 weeks of pregnancy based on the Republican...

#### ID `en_047653` (Label `1` / Status `unverified`)
- **Source ID**: `52983`
- **Title**: Young Girl Attacked on Social Media For Cleaning Graffiti From Trump’s Star
- **Text Preview**: As a college student, I know first-hand how quick liberals are to attack someone for expressing a political opinion that is different from their own. This is another one of the many examples of the ha...

#### ID `en_052808` (Label `1` / Status `unverified`)
- **Source ID**: `59376`
- **Title**: Paul Ryan Just Dropped The PERFECT Bombshell On Trump, HUMILIATES Him Over Russia (VIDEO)
- **Text Preview**: Earlier today, Speaker of the House Paul Ryan dropped a truth bomb that absolutely humiliated Donald Trump and made him look like a moron.After he had a meeting with the undeserving Trump, Ryan was la...

---

### Sampled Hindi Records

#### ID `hi_005239` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_fake_news/Hindi_fake_news (7837).txt`
- **Text Preview**: छत्तीसगढ़ का चौंकाने वाला हमले का वीडियो गुजरात के आरएमवीएम स्कूल के रूप में गलत तरीके से साझा किया गया भूत-प्रेत भगाने के बहाने एक व्यक्ति द्वारा एक युवा लड़की के साथ छेड़छाड़ और मारपीट करने वाला एक ...

#### ID `hi_000913` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_fake_news/Hindi_fake_news (2083).txt`
- **Text Preview**: प्रधानमंत्री मोदी ने खाया लिट्टी चोखा, तस्वीर से छेड़छाड़ कर लोगों ने पकड़ा दी बिरयानी प्रधानमंत्री मोदी ने खाया लिट्टी चोखा, तस्वीर से छेड़छाड़ कर लोगों ने पकड़ा दी बिरयानी प्रधानमंत्री मोदी ने खाया ...

#### ID `hi_000205` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_fake_news/Hindi_fake_news (1019).txt`
- **Text Preview**: पहले दिया आशीर्वाद फिर मौलवी ने दुल्हन को चूमा? धड़ाधड़ वायरल इस वीडियो की सच्चाई जान ट्रोलर्स को आएगी शर्म! पहले दिया आशीर्वाद फिर मौलवी ने दुल्हन को चूमा? धड़ाधड़ वायरल इस वीडियो की सच्चाई जान ट्रोल...

#### ID `hi_006075` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_fake_news/Hindi_fake_news (8667).txt`
- **Text Preview**: बीजेपी के राजा ने दिल्ली की नैतिक पुलिसिंग विरोध तस्वीर को आईआईटी मद्रास का बताकर ट्वीट किया भारतीय जनता पार्टी (भाजपा) के राष्ट्रीय सचिव राजा ने मंगलवार को 2014 में दिल्ली में नैतिक पुलिसिंग के खिलाफ...

#### ID `hi_002254` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_fake_news/Hindi_fake_news (4798).txt`
- **Text Preview**: क्या करण जौहर ने कहा कि अगर ब्रह्मास्त्र हिट हुआ तो वह पाकिस्तान को 51 करोड़ रुपये दान देंगे? FactCheck फैक्टबूम यह पता लगाने में सक्षम था कि ब्रह्मास्त्र का निर्माण करने वाले करण जौहर द्वारा ऐसा कोई ...

#### ID `hi_009448` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_real_news/Hindi_real_news (2851).txt`
- **Text Preview**: 'थप्पड़' को एशियाई फिल्म पुरस्कार में मिले दो नामांकन हिन्दी ख़बरें दुनिया वीडियो देश क्राइम खेल क्रिकेट फ़ुटबॉल टेनिस बैडमिंटन हॉकी अन्य मनोरंजन हॉलीवुड टेलीविज़न बॉलीवुड लाइफस्टाइल हेल्थ घरेलू नुस्ख...

#### ID `hi_009270` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_real_news/Hindi_real_news (2688).txt`
- **Text Preview**: रिया के खिलाफ मीडिया की अटकलें परेशान करने वालींअभिनेत्री के वकील हिन्दी ख़बरें दुनिया वीडियो देश क्राइम खेल क्रिकेट फ़ुटबॉल टेनिस बैडमिंटन हॉकी अन्य मनोरंजन हॉलीवुड टेलीविज़न बॉलीवुड लाइफस्टाइल हेल्थ...

#### ID `hi_008585` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_real_news/Hindi_real_news (2046).txt`
- **Text Preview**: धारावाहिक 'कुबूल है' वेब सीरीज पर एपिसोड के साथ आने को तैयार हिन्दी ख़बरें दुनिया वीडियो देश क्राइम खेल क्रिकेट फ़ुटबॉल टेनिस बैडमिंटन हॉकी अन्य मनोरंजन हॉलीवुड टेलीविज़न बॉलीवुड लाइफस्टाइल हेल्थ घरेल...

#### ID `hi_013475` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_real_news/Hindi_real_news (8563).txt`
- **Text Preview**: इन बीमारियों में भी योग मददगार, ने लगाई मुहर हेल्थ डेस्कअगर आप सोचते है कि योग करना फायदेमंद है कि नहीं। जिसके कारण आप योग नहीं करते है। तो हम आपको बता दें कि योग को क्लिनिकल प्रमाण मिल गए हैं कि कई त...

#### ID `hi_008281` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Hindi_real_news/Hindi_real_news (154).txt`
- **Text Preview**: : खाते हैं ये 5 फूड्स तो खूद ही सड़ा रहे हैं अपनी किडनी और लिवर, इन जरूरी अंगों को रखना है हेल्दी, आज ही बना लें इन खराब चीजों से दूरी लिवर और किडनी हमारी बॉडी के दो अहम अंग है जिनका काम शरीर में कई प...

---

### Sampled Marathi Records

#### ID `mr_005239` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_fake_news/Marathi_fake_news (5952).txt`
- **Text Preview**: हे चित्र ऑंग सॅन सू यांच्या नावावर सामायिक केले गेले होते ... हे जाणून घ्या की या चित्राचे सत्य काय आहे हे चित्र ऑंग सॅन सू यांच्या नावाने सामायिक केले गेले होते ... हे जाणून घ्या की या चित्राचे सत्य ...

#### ID `mr_000913` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_fake_news/Marathi_fake_news (1870).txt`
- **Text Preview**: हरीश साल्व्हने लस धोरणावर विरोधी पक्षाच्या टीकेचा ऑडिओ रेकॉर्ड केला नाही लस खरेदी व वितरणासाठी आणि नरेंद्र मोदी सरकारला पाठिंबा देण्यासाठी राज्य सरकारांना आव्हान देणार्‍या एखाद्या व्यक्तीची ऑडिओ क्लिप...

#### ID `mr_000205` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_fake_news/Marathi_fake_news (1213).txt`
- **Text Preview**: तेलंगणा पोलिसांच्या कारच्या आत भाजपचा ध्वज दाखविणारा व्हिडिओ चुकीच्या दाव्यासह सामायिक केला आहे तेलंगणा पोलिसांच्या कारच्या आत भारतीय जनता पक्षाने (भाजपा) झेंडा दर्शविणारा व्हिडिओ चुकीच्या दाव्याने ऑन...

#### ID `mr_006075` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_fake_news/Marathi_fake_news (6931).txt`
- **Text Preview**: तामिळनाडू बनावट, जुन्या व्हिडिओसह मूर्ख, हेलिकॉप्टर क्रॅशची बातमी तामिळनाडूमधील हेलिकॉप्टर अपघाताची बातमी, बनावट, जुन्या व्हिडिओसह मूर्ख, तामिळनाडूमधील हेलिकॉप्टर अपघाताची बातमी, बनावट, जुन्या व्हिडिओ...

#### ID `mr_002254` (Label `fake` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_fake_news/Marathi_fake_news (3110).txt`
- **Text Preview**: 'माझा तिरस्कार करा, पण जर्मनीचा तिरस्कार करू नका'?व्हायरल हिटलर क्लिप दिशाभूल करणारी आहे जर्मनमधील अ‍ॅडॉल्फ हिटलरच्या एका भाषणातून घेतलेला 15 -सेकंद व्हिडिओ चुकीच्या आणि दिशाभूल करणार्‍या उपशीर्षकांसह...

#### ID `mr_007666` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_real_news/Marathi_real_news (2591).txt`
- **Text Preview**: यंदाच्या रक्षाबंधनाला लाडक्या बहिणीला देऊ शकता ‘या’ पाच इलेक्ट्रिक स्कूटर्स भेट, किमती पाहा रक्षाबंधन सणामधून बहीण-भावामधील प्रेमाचे दृढ नाते दिसून येते. पण या परंपरेला आधुनिकतेची जोड देता येऊ शकत नाह...

#### ID `mr_007644` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_real_news/Marathi_real_news (2401).txt`
- **Text Preview**: ह्युंदाई-किआचे धाबे दणाणलेहोंडाची नवी भारतात लॉन्च, जाणून घ्या किंमत आणि फीचर्स होंडा कार्स इंडिया ही एक लोकप्रिय वाहन उत्पादक कंपनी आहे. होंडा कंपनीने आपली ही एसयूव्ही अखेर भारतात लॉन्च केली आहे. हों...

#### ID `mr_007558` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_real_news/Marathi_real_news (1727).txt`
- **Text Preview**: इतरांपेक्षा चार पावले पुढे राहायचे असेल तर आचार्य चाणक्यांनी सांगितलेले ‘हे’ चार श्लोक कायम लक्षात ठेवा आचार्य चाणक्य हे भारतातील सर्वोत्तम विद्वानांमध्ये गणले जातात. चाणक्यनीतीमध्ये त्यांनी अनेक विषय...

#### ID `mr_007520` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_real_news/Marathi_real_news (1499).txt`
- **Text Preview**: ३१ ऑगस्टपासून दत्तगुरुकृपेने ‘या’राशींचे लोक होतील श्रीमंत? श्रावणी गुरुवारी सुकर्म योग देईल आर्थिक बळ आज श्रावण महिन्यातील तिसऱ्या गुरुवारी एक अत्यंत दुर्मिळ असा सुकर्म योग जुळून आला आहे. ऑगस्ट महिन्...

#### ID `mr_008108` (Label `real` / Status `claimed_folder_label`)
- **Source ID**: `Marathi_real_news/Marathi_real_news (9009).txt`
- **Text Preview**: बूक साठी जैन मंदीर भोर भोरमधील भक्ती, एकतेचे प्रतीक जैन मंदिर सुमारे शंभर वर्षांपासून भोर शहरातील मुख्य बाजारपेठ असलेल्या मंगळवार पेठेत एकमेव जैन मंदिर आहे. ते जैन भाविकांसाठी भक्ती, प्रेम, एकता आणि स...

---

## 3. Limitations of the Sample Review

- **Sample Size**: 30 records represents 0.035% of the total 85,862 accepted records.
- **Scope**: Serves as a qualitative sanity check and pipeline verification. It does not replace systematic string-matching against authoritative ground-truth datasets (e.g. ISOT join for WELFake).
