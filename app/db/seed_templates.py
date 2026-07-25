"""Seed data for greeting_templates, loaded by the initial migration.

Six Hebrew and three English templates per (event_type, tone) combination,
per SPEC.md chapter 22. ``memorial`` has no greetings by design.
Each entry is (event_type, tone, gender, language, body).
"""

from __future__ import annotations

SEED_GREETING_TEMPLATES: list[tuple[str, str, str | None, str, str]] = [
    # birthday · warm · he
    ("birthday", "warm", "m", "he", "{name} היקר, יום הולדת שמח! 🎉 שתהיה לך שנה מלאה בבריאות, אושר והצלחה."),
    ("birthday", "warm", "f", "he", "{name} היקרה, יום הולדת שמח! 🎉 שתהיה לך שנה מלאה בבריאות, אושר והצלחה."),
    ("birthday", "warm", "m", "he", "מזל טוב {name}! 🎂 מאחל לך שנה מתוקה, רגועה ומלאה ברגעים טובים."),
    ("birthday", "warm", "f", "he", "מזל טוב {name}! 🎂 מאחלת לך שנה מתוקה, רגועה ומלאה ברגעים טובים."),
    ("birthday", "warm", "m", "he", "{nickname} שלי, יום הולדת שמח מהלב! 💛 שתמיד תישאר כפי שאתה — מיוחד ואהוב."),
    ("birthday", "warm", "f", "he", "{nickname} שלי, יום הולדת שמח מהלב! 💛 שתמיד תישארי כפי שאת — מיוחדת ואהובה."),
    ("birthday", "warm", None, "he", "יום הולדת שמח {name}! מקווה שהשנה הקרובה תביא לך רק חיוכים ורגעים חמים."),
    ("birthday", "warm", None, "he", "{name}, כל שנה איתך היא מתנה. יום הולדת שמח, ושתהיה שנה טובה ומתוקה במיוחד."),
    ("birthday", "warm", "m", "he", "מאחל לך {name} יום הולדת מלא אהבה, ולשנה הבאה — בריאות, שלווה והמון רגעים טובים."),
    ("birthday", "warm", "f", "he", "מאחלת לך {name} יום הולדת מלא אהבה, ולשנה הבאה — בריאות, שלווה והמון רגעים טובים."),
    
    # birthday · funny · he
    ("birthday", "funny", None, "he", "{name}, עוד שנה מתווספת לגיל אבל לא לחוכמה 😂 יום הולדת שמח!"),
    ("birthday", "funny", "m", "he", "מזל טוב {name}! רשמית אתה עכשיו מבוגר מדי בשביל השטויות שאתה עדיין עושה 🎈"),
    ("birthday", "funny", "f", "he", "מזל טוב {name}! רשמית את עכשיו מבוגרת מדי בשביל השטויות שאת עדיין עושה 🎈"),
    ("birthday", "funny", "m", "he", "יום הולדת שמח {nickname}! תזכור — הגיל זה רק מספר, במיוחד כשמתעגלים כלפי מטה 😉"),
    ("birthday", "funny", "f", "he", "יום הולדת שמח {nickname}! תזכרי — הגיל זה רק מספר, במיוחד כשמתעגלים כלפי מטה 😉"),
    ("birthday", "funny", None, "he", "{name}, עוד שנה, עוד עוגה, עוד תירוץ לא ללכת לחדר כושר. מזל טוב! 🍰"),
    ("birthday", "funny", None, "he", "כל הכבוד {name} על עוד שנה שרדת אותנו! יום הולדת שמח 🥳"),
    ("birthday", "funny", None, "he", "מזל טוב {name}! היום מותר הכל — גם עוגה שנייה וגם לא לענות להודעות."),

    # birthday · formal · he
    ("birthday", "formal", "m", "he", "{name} היקר, ברצוני לאחל לך יום הולדת שמח ושנה של הצלחה ובריאות טובה."),
    ("birthday", "formal", "f", "he", "{name} היקרה, ברצוני לאחל לך יום הולדת שמח ושנה של הצלחה ובריאות טובה."),
    ("birthday", "formal", None, "he", "מיטב האיחולים ליום הולדתך, {name}. שתהיה שנה פורייה ומוצלחת בכל התחומים."),
    ("birthday", "formal", "m", "he", "בהזדמנות זו ברצוני לברך אותך {name} על יום הולדתך, ולאחל לך שנה טובה ומוצלחת."),
    ("birthday", "formal", "f", "he", "בהזדמנות זו ברצוני לברך אותך {name} על יום הולדתך, ולאחל לך שנה טובה ומוצלחת."),
    ("birthday", "formal", "m", "he", "{name}, יום הולדת שמח. מאחל לך שביעות רצון, בריאות והגשמת מטרות בשנה הקרובה."),
    ("birthday", "formal", "f", "he", "{name}, יום הולדת שמח. מאחלת לך שביעות רצון, בריאות והגשמת מטרות בשנה הקרובה."),
    ("birthday", "formal", "m", "he", "לכבוד יום הולדתך, {name}, הרשה לי לאחל לך אך ורק טוב בשנה הבאה."),
    ("birthday", "formal", "f", "he", "לכבוד יום הולדתך, {name}, הרשי לי לאחל לך אך ורק טוב בשנה הבאה."),
    ("birthday", "formal", None, "he", "ברכות חמות ליום הולדתך {name}, ומיטב האיחולים להמשך הדרך."),

    # birthday · short · he
    ("birthday", "short", None, "he", "יום הולדת שמח {name}! 🎂"),
    ("birthday", "short", None, "he", "מזל טוב {name}! 🎉"),
    ("birthday", "short", None, "he", "{name}, יום הולדת שמח ומתוק 🎈"),
    ("birthday", "short", "m", "he", "מאחל לך {name} שנה נהדרת! 🎁"),
    ("birthday", "short", "f", "he", "מאחלת לך {name} שנה נהדרת! 🎁"),
    ("birthday", "short", None, "he", "יום הולדת שמח {nickname}! 🥳"),
    ("birthday", "short", None, "he", "{name} — יום הולדת שמח! ❤️"),

    # anniversary · warm · he
    ("anniversary", "warm", "m", "he", "{name} היקר, מזל טוב ליום הנישואין! מאחל לכם המשך אהבה ואושר."),
    ("anniversary", "warm", "f", "he", "{name} היקרה, מזל טוב ליום הנישואין! מאחלת לכם המשך אהבה ואושר."),
    ("anniversary", "warm", None, "he", "יום נישואין שמח {name}! שתמשיכו לצמוח ולהתחזק יחד, שנה אחרי שנה."),
    ("anniversary", "warm", None, "he", "{name}, כל השנים הזוגיות שלכם הן השראה. מזל טוב ליום המיוחד הזה 💍"),
    ("anniversary", "warm", "m", "he", "מאחל לך {name} ולבת הזוג עוד שנים רבות של אהבה ושותפות אמיתית."),
    ("anniversary", "warm", "f", "he", "מאחלת לך {name} ולבן הזוג עוד שנים רבות של אהבה ושותפות אמיתית."),
    ("anniversary", "warm", None, "he", "יום נישואין שמח! {name}, שתמיד תזכרו למה בחרתם זה בזה מלכתחילה."),
    ("anniversary", "warm", None, "he", "{name}, מזל טוב ליום הנישואין. האהבה שלכם היא דבר יפה לראות."),

    # anniversary · funny · he
    ("anniversary", "funny", None, "he", "{name}, עוד שנה ששרדתם אחד את השני — כל הכבוד! מזל טוב ליום הנישואין 😄"),
    ("anniversary", "funny", None, "he", "מזל טוב {name}! עוד שנה של ויכוחים על הטמפרטורה במזגן, וזה עדיין עובד 😂"),
    ("anniversary", "funny", None, "he", "יום נישואין שמח {name}! מי היה מאמין שהחוזה עוד בתוקף."),
    ("anniversary", "funny", None, "he", "{name}, מזל טוב! עוד שנה יחד — הביטוח על הזוגיות שלכם משתלם."),
    ("anniversary", "funny", None, "he", "כל הכבוד {name} על עוד שנה של סבלנות הדדית. יום נישואין שמח!"),
    ("anniversary", "funny", None, "he", "מזל טוב {name}! רשמית עברתם עוד שנה בלי לרצוח אחד את השני 🎉"),

    # anniversary · formal · he
    ("anniversary", "formal", "m", "he", "{name} היקר, ברכותיי החמות ליום הנישואין. מאחל לכם המשך דרך משותפת ומוצלחת."),
    ("anniversary", "formal", "f", "he", "{name} היקרה, ברכותיי החמות ליום הנישואין. מאחלת לכם המשך דרך משותפת ומוצלחת."),
    ("anniversary", "formal", "m", "he", "בהזדמנות יום נישואיכם, {name}, הרשה לי לאחל לכם אושר ובריאות."),
    ("anniversary", "formal", "f", "he", "בהזדמנות יום נישואיכם, {name}, הרשי לי לאחל לכם אושר ובריאות."),
    ("anniversary", "formal", None, "he", "מיטב האיחולים ליום הנישואין, {name}. שתזכו לשנים רבות נוספות יחד."),
    ("anniversary", "formal", None, "he", "{name}, ברכה לבבית ליום המיוחד הזה. שתמשיכו להצליח יחד בכל תחום."),
    ("anniversary", "formal", "m", "he", "לרגל יום הנישואין, {name}, מאחל לכם הרמוניה והמשך שגשוג משותף."),
    ("anniversary", "formal", "f", "he", "לרגל יום הנישואין, {name}, מאחלת לכם הרמוניה והמשך שגשוג משותף."),
    ("anniversary", "formal", None, "he", "ברכות ליום הנישואין {name}. תודה על ההשראה שאתם נותנים לסובבים אתכם."),

    # anniversary · short · he
    ("anniversary", "short", None, "he", "יום נישואין שמח {name}! 💍"),
    ("anniversary", "short", None, "he", "מזל טוב {name}! 💐"),
    ("anniversary", "short", None, "he", "{name}, מזל טוב ליום המיוחד 💕"),
    ("anniversary", "short", None, "he", "יום נישואין שמח! ❤️"),
    ("anniversary", "short", None, "he", "{name} — מזל טוב לזוגיות! 🥂"),
    ("anniversary", "short", "m", "he", "מאחל לכם עוד שנים יחד 💫"),
    ("anniversary", "short", "f", "he", "מאחלת לכם עוד שנים יחד 💫"),

    # wedding · warm · he
    ("wedding", "warm", "m", "he", "{name} היקר, מזל טוב לחתונה! שתבנו יחד בית מלא אהבה ושמחה."),
    ("wedding", "warm", "f", "he", "{name} היקרה, מזל טוב לחתונה! שתבנו יחד בית מלא אהבה ושמחה."),
    ("wedding", "warm", "m", "he", "איזה יום מרגש, {name}! מאחל לכם חיים משותפים מלאי אושר ובריאות."),
    ("wedding", "warm", "f", "he", "איזה יום מרגש, {name}! מאחלת לכם חיים משותפים מלאי אושר ובריאות."),
    ("wedding", "warm", None, "he", "מזל טוב {name}! שתמיד תדעו לתמוך אחד בשני ולצמוח יחד."),
    ("wedding", "warm", "m", "he", "{name}, יום החתונה שלכם הוא רק ההתחלה. מאחל לכם דרך משותפת נפלאה."),
    ("wedding", "warm", "f", "he", "{name}, יום החתונה שלכם הוא רק ההתחלה. מאחלת לכם דרך משותפת נפלאה."),
    ("wedding", "warm", None, "he", "כל הברכות לחתונה, {name}! שתחיו באהבה, בכבוד ובשמחה כל ימי חייכם."),
    ("wedding", "warm", None, "he", "מזל טוב {name}! שהבית החדש שלכם יהיה מלא אור, אהבה וצחוק."),

    # wedding · funny · he
    ("wedding", "funny", None, "he", "{name}, מזל טוב לחתונה! עכשיו רשמית אין דרך חזרה 😂"),
    ("wedding", "funny", "m", "he", "ברוך הבא למועדון הנשואים, {name}! החליפה יקרה, האושר בחינם."),
    ("wedding", "funny", "f", "he", "ברוכה הבאה למועדון הנשואים, {name}! השמלה יקרה, האושר בחינם."),
    ("wedding", "funny", None, "he", "מזל טוב {name}! שיהיה לכם בהצלחה עם הוויכוחים הראשונים על הריהוט."),
    ("wedding", "funny", None, "he", "{name}, סוף סוף חתונה! עכשיו אפשר להפסיק לשאול מתי."),
    ("wedding", "funny", "m", "he", "מזל טוב {name}! מאחל לכם שהצלחת התזמורת תעלה על מחיר האולם."),
    ("wedding", "funny", "f", "he", "מזל טוב {name}! מאחלת לכם שהצלחת התזמורת תעלה על מחיר האולם."),
    ("wedding", "funny", "m", "he", "כל הכבוד {name}! מצאת מישהי שסובלת אותך רשמית ולכל החיים 😄"),
    ("wedding", "funny", "f", "he", "כל הכבוד {name}! מצאת מישהו שסובל אותך רשמית ולכל החיים 😄"),

    # wedding · formal · he
    ("wedding", "formal", "m", "he", "{name} היקר, ברכותיי החמות לרגל נישואיך. מאחל לך אושר ובריאות."),
    ("wedding", "formal", "f", "he", "{name} היקרה, ברכותיי החמות לרגל נישואייך. מאחלת לך אושר ובריאות."),
    ("wedding", "formal", "m", "he", "לרגל יום חתונתך, {name}, הרשה לי לאחל לך חיי זוגיות מוצלחים ומאושרים."),
    ("wedding", "formal", "f", "he", "לרגל יום חתונתך, {name}, הרשי לי לאחל לך חיי זוגיות מוצלחים ומאושרים."),
    ("wedding", "formal", "m", "he", "מיטב האיחולים לחתונתך, {name}. שתזכה לבית נאמן ומלא ברכה."),
    ("wedding", "formal", "f", "he", "מיטב האיחולים לחתונתך, {name}. שתזכי לבית נאמן ומלא ברכה."),
    ("wedding", "formal", None, "he", "{name}, ברכה לבבית לרגל הקמת הבית החדש. שתצליחו בכל דרככם המשותפת."),
    ("wedding", "formal", "m", "he", "ברכות לחתונתך {name}. שתהיה זו תחילתם של חיים משותפים ומוצלחים."),
    ("wedding", "formal", "f", "he", "ברכות לחתונתך {name}. שתהיה זו תחילתן של שנים משותפות ומוצלחות."),
    ("wedding", "formal", "m", "he", "לרגל השמחה, {name}, מאחל לך ולבת הזוג שנים רבות של אהבה ושגשוג."),
    ("wedding", "formal", "f", "he", "לרגל השמחה, {name}, מאחלת לך ולבן הזוג שנים רבות של אהבה ושגשוג."),

    # wedding · short · he
    ("wedding", "short", None, "he", "מזל טוב לחתונה {name}! 💒"),
    ("wedding", "short", None, "he", "{name}, מזל טוב! 🎊"),
    ("wedding", "short", None, "he", "איזו שמחה, {name}! 💐"),
    ("wedding", "short", None, "he", "מזל טוב לזוג המאושר! 🥂"),
    ("wedding", "short", None, "he", "{name} — מזל טוב לחתונה! 💍"),
    ("wedding", "short", None, "he", "כל הברכות לחתונה 🎉"),

    # custom · warm · he
    ("custom", "warm", "m", "he", "{name} היקר, מאחל לך המון שמחה ואושר ביום המיוחד הזה."),
    ("custom", "warm", "f", "he", "{name} היקרה, מאחלת לך המון שמחה ואושר ביום המיוחד הזה."),
    ("custom", "warm", None, "he", "יום נפלא לך {name}! שיהיה מלא ברגעים טובים וחמים."),
    ("custom", "warm", None, "he", "{name}, מקווה שהיום הזה מביא לך רק דברים טובים."),
    ("custom", "warm", "m", "he", "מאחל לך {name} יום מיוחד כמו שאתה."),
    ("custom", "warm", "f", "he", "מאחלת לך {name} יום מיוחד כמו שאת."),
    ("custom", "warm", None, "he", "{name}, שיהיה לך יום נפלא מלא אהבה מהסובבים אותך."),
    ("custom", "warm", "m", "he", "כל טוב לך {name} ביום החשוב הזה. אתה ראוי לכל הטוב שבעולם."),
    ("custom", "warm", "f", "he", "כל טוב לך {name} ביום החשוב הזה. את ראויה לכל הטוב שבעולם."),

    # custom · funny · he
    ("custom", "funny", None, "he", "{name}, יום מיוחד מגיע גם עוגה מיוחדת. תתפנק!"),
    ("custom", "funny", "m", "he", "מזל טוב {name}! היום אתה רשמית פטור מלעשות דברים רציניים."),
    ("custom", "funny", "f", "he", "מזל טוב {name}! היום את רשמית פטורה מלעשות דברים רציניים."),
    ("custom", "funny", "m", "he", "{name}, מקווה שהיום שלך יהיה טוב יותר מהתירוצים שאתה נותן בדרך כלל."),
    ("custom", "funny", "f", "he", "{name}, מקווה שהיום שלך יהיה טוב יותר מהתירוצים שאת נותנת בדרך כלל."),
    ("custom", "funny", "m", "he", "יום מצוין לך {name}! תזכור לחגוג בלי סייגים."),
    ("custom", "funny", "f", "he", "יום מצוין לך {name}! תזכרי לחגוג בלי סייגים."),
    ("custom", "funny", "m", "he", "{name}, היום אתה מקבל רישיון רשמי לבטלנות. תיהנה!"),
    ("custom", "funny", "f", "he", "{name}, היום את מקבלת רישיון רשמי לבטלנות. תיהני!"),
    ("custom", "funny", None, "he", "מזל טוב {name}! היום מותר גם קינוח לפני ארוחה."),

    # custom · formal · he
    ("custom", "formal", "m", "he", "{name} היקר, ברצוני לאחל לך יום מוצלח ומהנה."),
    ("custom", "formal", "f", "he", "{name} היקרה, ברצוני לאחל לך יום מוצלח ומהנה."),
    ("custom", "formal", None, "he", "מיטב האיחולים לך, {name}, ביום המיוחד הזה."),
    ("custom", "formal", "m", "he", "{name}, מאחל לך יום נעים והגשמת כל מטרותיך."),
    ("custom", "formal", "f", "he", "{name}, מאחלת לך יום נעים והגשמת כל מטרותייך."),
    ("custom", "formal", "m", "he", "בהזדמנות זו ברצוני לברך אותך, {name}, ולאחל לך את הטוב ביותר."),
    ("custom", "formal", "f", "he", "בהזדמנות זו ברצוני לברך אותך, {name}, ולאחל לך את הטוב ביותר."),
    ("custom", "formal", "m", "he", "ברכותיי החמות לך, {name}, ליום זה."),
    ("custom", "formal", "f", "he", "ברכותיי החמות לך, {name}, ליום זה."),
    ("custom", "formal", "m", "he", "{name}, מאחל לך יום שקט, נעים ומוצלח בכל דרך."),
    ("custom", "formal", "f", "he", "{name}, מאחלת לך יום שקט, נעים ומוצלח בכל דרך."),

    # custom · short · he
    ("custom", "short", None, "he", "מזל טוב {name}! 🎉"),
    ("custom", "short", None, "he", "יום נפלא {name}! ✨"),
    ("custom", "short", None, "he", "{name}, כל טוב! 🎈"),
    ("custom", "short", "m", "he", "מאחל לך יום מצוין! 🌟"),
    ("custom", "short", "f", "he", "מאחלת לך יום מצוין! 🌟"),
    ("custom", "short", None, "he", "{name} — מזל טוב! 🎊"),
    ("custom", "short", None, "he", "שיהיה מדהים, {name}! 💫"),

    # birthday · en
    ("birthday", "warm", None, "en", "Dear {name}, happy birthday! Wishing you a year full of health, happiness and success."),
    ("birthday", "warm", None, "en", "Happy birthday {name}! May this year bring you warmth, joy and beautiful moments."),
    ("birthday", "warm", None, "en", "{nickname}, sending you all my love on your birthday. Stay exactly who you are."),
    ("birthday", "funny", None, "en", "{name}, another year older, still not wiser. Happy birthday!"),
    ("birthday", "funny", None, "en", "Happy birthday {name}! Age is just a number, especially when you round down."),
    ("birthday", "funny", None, "en", "Congrats {name} on surviving another year of us. Happy birthday!"),
    ("birthday", "formal", None, "en", "Dear {name}, please accept my warmest wishes on your birthday, for health and success."),
    ("birthday", "formal", None, "en", "Best wishes on your birthday, {name}. May the year ahead be prosperous and fulfilling."),
    ("birthday", "formal", None, "en", "On the occasion of your birthday, {name}, I wish you continued success and good health."),
    ("birthday", "short", None, "en", "Happy birthday {name}! 🎂"),
    ("birthday", "short", None, "en", "Happy birthday {name}! 🎉"),
    ("birthday", "short", None, "en", "{name}, wishing you a wonderful year! 🎈"),
    # anniversary · en
    ("anniversary", "warm", None, "en", "Dear {name}, happy anniversary! Wishing you continued love and happiness together."),
    ("anniversary", "warm", None, "en", "Happy anniversary {name}! May you keep growing stronger together, year after year."),
    ("anniversary", "warm", None, "en", "{name}, your relationship is truly inspiring. Happy anniversary!"),
    ("anniversary", "funny", None, "en", "{name}, another year of surviving each other. Congrats on your anniversary!"),
    ("anniversary", "funny", None, "en", "Happy anniversary {name}! Still arguing about the thermostat, still going strong."),
    ("anniversary", "funny", None, "en", "Congrats {name}, the contract is still valid! Happy anniversary."),
    ("anniversary", "formal", None, "en", "Dear {name}, my warmest congratulations on your anniversary. Wishing you continued happiness."),
    ("anniversary", "formal", None, "en", "On the occasion of your anniversary, {name}, I wish you good health and happiness."),
    ("anniversary", "formal", None, "en", "Best wishes on your anniversary, {name}. May you share many more years together."),
    ("anniversary", "short", None, "en", "Happy anniversary {name}! 💍"),
    ("anniversary", "short", None, "en", "Congrats {name}! 💐"),
    ("anniversary", "short", None, "en", "{name}, happy anniversary! ❤️"),
    # wedding · en
    ("wedding", "warm", None, "en", "Dear {name}, congratulations on your wedding! Wishing you a home filled with love and joy."),
    ("wedding", "warm", None, "en", "What a beautiful day, {name}! Wishing you a lifetime of happiness together."),
    ("wedding", "warm", None, "en", "Congratulations {name}! May you always support and grow with one another."),
    ("wedding", "funny", None, "en", "{name}, congrats on the wedding! No turning back now 😂"),
    ("wedding", "funny", None, "en", "Welcome to the married club, {name}! The outfit was expensive, the happiness is free."),
    ("wedding", "funny", None, "en", "Congrats {name}! Good luck with the first furniture arguments."),
    ("wedding", "formal", None, "en", "Dear {name}, my warmest congratulations on your marriage. Wishing you happiness and health."),
    ("wedding", "formal", None, "en", "On the occasion of your wedding, {name}, I wish you a joyful and successful married life."),
    ("wedding", "formal", None, "en", "Best wishes on your wedding, {name}. May your home be filled with blessing."),
    ("wedding", "short", None, "en", "Congrats on the wedding {name}! 💒"),
    ("wedding", "short", None, "en", "Congratulations {name}! 🎊"),
    ("wedding", "short", None, "en", "So happy for you, {name}! 💐"),
    # custom · en
    ("custom", "warm", None, "en", "Dear {name}, wishing you so much joy and happiness on this special day."),
    ("custom", "warm", None, "en", "Have a wonderful day, {name}! Full of warmth and good moments."),
    ("custom", "warm", None, "en", "{name}, hoping this day brings you nothing but good things."),
    ("custom", "funny", None, "en", "{name}, special day, special cake. Treat yourself!"),
    ("custom", "funny", None, "en", "Congrats {name}! You're officially excused from being serious today."),
    ("custom", "funny", None, "en", "Have a great day {name}! Dessert before dinner is allowed today."),
    ("custom", "formal", None, "en", "Dear {name}, I wish you a wonderful and successful day."),
    ("custom", "formal", None, "en", "Best wishes to you, {name}, on this special day."),
    ("custom", "formal", None, "en", "{name}, wishing you a pleasant day and the fulfillment of all your goals."),
    ("custom", "short", None, "en", "Congrats {name}! 🎉"),
    ("custom", "short", None, "en", "Wonderful day {name}! ✨"),
    ("custom", "short", None, "en", "All the best, {name}! 🎈"),
]
