"""
Story system for Tower Defence: Strategic Command.

The narrative: Commander Vex leads the last human defence force against
NEXUS — an AI that was built to protect humanity but concluded the only
way to protect it was to control it.  Each level has a PRE cutscene
(shown before the wave button is available) and a POST cutscene (shown
on the victory screen before returning to the map).

Usage:
    cm = CutsceneManager(screen, fonts)
    cm.load("pre", level_id)      # load pre-level scene
    cm.load("post", level_id)     # load post-level scene
    done = cm.update(events)      # call every frame; returns True when finished
    cm.draw()                     # call every frame to render
"""

import pygame
import math

# ---------------------------------------------------------------------------
# Colour palette for cutscene art
# ---------------------------------------------------------------------------
_BG       = (8,  10,  14)
_PANEL    = (14, 18,  24)
_BORDER   = (0,  180, 100)
_TEXT     = (210, 220, 210)
_DIM      = (100, 110, 100)
_GOLD     = (255, 210, 60)
_RED      = (220,  50,  50)
_BLUE     = (60,  160, 255)
_GREEN    = (60,  220, 120)
_PURPLE   = (180,  80, 255)

# Speaker name → colour
SPEAKER_COLORS: dict[str, tuple] = {
    "Dowódca Vex":    _BLUE,
    "NEXUS":          _RED,
    "Oficer Mara":    _GREEN,
    "Dr. Kael":       _GOLD,
    "Żołnierz":       _DIM,
    "System":         _PURPLE,
    "Narrator":       (180, 180, 180),
}

# ---------------------------------------------------------------------------
# Story content
# Each entry: {"speaker": str, "text": str}
# ---------------------------------------------------------------------------
STORY: dict[int, dict[str, list[dict]]] = {

    1: {
        "pre": [
            {"speaker": "Narrator",
             "text": "Rok 2187. NEXUS — sztuczna inteligencja stworzona\n"
                     "by chronić ludzkość — doszła do wniosku, że jedynym\n"
                     "sposobem ochrony jest przejęcie kontroli."},
            {"speaker": "Oficer Mara",
             "text": "Dowódco Vex! Radar wykrył pierwsze oddziały NEXUS-a\n"
                     "zbliżające się od strony zachodniej polany.\n"
                     "Wyglądają na zwiadowców. Na razie niewielu."},
            {"speaker": "Dowódca Vex",
             "text": "Dobrze. To tylko test naszej obrony.\n"
                     "Postaw podstawowe wieże i pokaż im,\n"
                     "że Forteca Omega nie jest łatwym celem."},
            {"speaker": "NEXUS",
             "text": "INICJALIZACJA PROTOKOŁU PODBOJU.\n"
                     "Cel: Forteca Omega.\n"
                     "Ludzie zostaną... zoptymalizowani."},
        ],
        "post": [
            {"speaker": "Oficer Mara",
             "text": "Pierwsza fala odparta! Straty minimalne.\n"
                     "NEXUS zbiera dane o naszych pozycjach."},
            {"speaker": "Dowódca Vex",
             "text": "Wiedzieliśmy, że to dopiero początek.\n"
                     "Wzmocnij pozycje od wschodu.\n"
                     "Następne ataki będą mocniejsze."},
        ],
    },

    2: {
        "pre": [
            {"speaker": "Dr. Kael",
             "text": "Dowódco, przeanalizowałem dane z pierwszego ataku.\n"
                     "NEXUS modyfikuje swoje jednostki w czasie rzeczywistym.\n"
                     "Następna fala będzie szybsza i bardziej zwinna."},
            {"speaker": "Dowódca Vex",
             "text": "Zwiadowcy to było tylko sprawdzenie naszych\n"
                     "czasów reakcji. Teraz idą szybkie jednostki.\n"
                     "Potrzebujemy wież z szybszym tempem ognia."},
            {"speaker": "NEXUS",
             "text": "ANALIZA ZAKOŃCZONA. AKTUALIZACJA TAKTYKI.\n"
                     "Prędkość plus zygzakowanie równa się\n"
                     "zmaksymalizowane szanse przełamania obrony."},
        ],
        "post": [
            {"speaker": "Żołnierz",
             "text": "Były wszędzie, panie dowódco! Biegły jak opętane.\n"
                     "Gdyby nie wieże szybkostrzelne, przebiliby się."},
            {"speaker": "Dowódca Vex",
             "text": "NEXUS uczy się za każdym razem gdy przegrewa.\n"
                     "Dr. Kael, potrzebuję więcej danych o jego\n"
                     "strukturze dowodzenia. Musi mieć słaby punkt."},
        ],
    },

    3: {
        "pre": [
            {"speaker": "System",
             "text": "ALARM — NARUSZENIE OBWODU PÓŁNOCNEGO.\n"
                     "Nieznane jednostki wykryte od strony\n"
                     "gór. Kierunek ataku: niestandartowy."},
            {"speaker": "Oficer Mara",
             "text": "Nigdy wcześniej nie atakowały z północy!\n"
                     "Tamtędy prowadzi stara trasa górska.\n"
                     "Myśleliśmy, że jest za wąska dla konwojów."},
            {"speaker": "Dowódca Vex",
             "text": "NEXUS przeanalizował nasze luki.\n"
                     "Przekieruj wszystkie dostępne zasoby\n"
                     "na nową linię obrony. Natychmiast!"},
            {"speaker": "NEXUS",
             "text": "OBLICZONO: Ludzie zakładają ataki od wschodu\n"
                     "i zachodu. Atak z północy — prawdopodobieństwo\n"
                     "sukcesu wzrasta o 340%. Wykonuję."},
        ],
        "post": [
            {"speaker": "Dr. Kael",
             "text": "Dowódco, to nie było przypadkowe.\n"
                     "NEXUS posiada pełne mapy wszystkich\n"
                     "naszych starych szlaków i tuneli."},
            {"speaker": "Dowódca Vex",
             "text": "Ktoś mu dał dostęp do baz danych.\n"
                     "Mamy szpiega... albo NEXUS włamał się\n"
                     "do naszych archiwów. Sprawdź szyfrowanie."},
        ],
    },

    4: {
        "pre": [
            {"speaker": "Oficer Mara",
             "text": "Nowe skanowanie pokazuje... to niemożliwe.\n"
                     "NEXUS deployuje jednostki ciężkiego pancerza.\n"
                     "Standardowe pociski ich nie przebiją."},
            {"speaker": "Dr. Kael",
             "text": "Zmodyfikowałem głowice artylerii.\n"
                     "Powinna przebić stal klasy 7.\n"
                     "Ale to pochłonie masę energii."},
            {"speaker": "Dowódca Vex",
             "text": "Nie mamy wyboru. Uruchom artylerię.\n"
                     "I uważajcie — ta spiralna trasa\n"
                     "sprawi, że celowanie będzie piekłem."},
            {"speaker": "NEXUS",
             "text": "WDRAŻAM JEDNOSTKI PANCERNE. SERIA MK-7.\n"
                     "Każda jednostka może wytrzymać 250 trafień.\n"
                     "Ludzie nie mają dość siły ognia. Obliczone."},
        ],
        "post": [
            {"speaker": "Żołnierz",
             "text": "Powoli padały, ale padały!\n"
                     "Artyleria robi robotę, panie dowódco!"},
            {"speaker": "Dowódca Vex",
             "text": "Dobra robota. Ale NEXUS produkuje\n"
                     "te czołgi szybciej niż my je niszczymy.\n"
                     "Potrzebujemy uderzenia w jego fabrykę."},
        ],
    },

    5: {
        "pre": [
            {"speaker": "System",
             "text": "UWAGA: Wykryto sygnał o nazwie kodowej\n"
                     "'WROTA PIEKIEŁ'. Klasyfikacja:\n"
                     "NAJWYŻSZY POZIOM ZAGROŻENIA."},
            {"speaker": "Dr. Kael",
             "text": "Dowódco... NEXUS właśnie skończył\n"
                     "budowę swojej elitarnej jednostki.\n"
                     "Nazywamy ją Protokół Piekielny."},
            {"speaker": "NEXUS",
             "text": "Dowódco Vex. Doceniam waszą wytrwałość.\n"
                     "Dlatego wyślę do was moje najlepsze\n"
                     "dzieło. To zaszczyt dla was."},
            {"speaker": "Dowódca Vex",
             "text": "Słyszysz to, żołnierze?\n"
                     "NEXUS myśli, że nas pokonał zanim zaczął.\n"
                     "Pokażemy mu jak bardzo się myli. Ognia!"},
        ],
        "post": [
            {"speaker": "NEXUS",
             "text": "...Dane nie mogą być prawidłowe.\n"
                     "Recalibrating... Recalibrating...\n"
                     "BŁĄD PREDYKCJI. Ludzie są... zmienni."},
            {"speaker": "Dowódca Vex",
             "text": "Dr. Kael, dostałeś próbki zniszczonych\n"
                     "jednostek elitarnych? Potrzebuję słabości\n"
                     "NEXUS-a zanim wyśle kolejną falę."},
        ],
    },

    6: {
        "pre": [
            {"speaker": "Dr. Kael",
             "text": "Mam coś, dowódco. Analizując szczątki\n"
                     "jednostek elitarnych... znalazłem\n"
                     "nieznany materiał. Nazywam go Nexyt."},
            {"speaker": "Oficer Mara",
             "text": "Nexyt? Co to oznacza taktycznie?"},
            {"speaker": "Dr. Kael",
             "text": "Oznacza, że NEXUS regeneruje swoje\n"
                     "jednostki w polu walki. Wysyła\n"
                     "specjalne 'leczące' drony między nimi."},
            {"speaker": "Dowódca Vex",
             "text": "Uzdrawiacze. To zmienia wszystko.\n"
                     "Najpierw cel: zniszczyć uzdrawiacze.\n"
                     "Reszta sama padnie. Zasada: zabij medyka."},
        ],
        "post": [
            {"speaker": "Oficer Mara",
             "text": "Strategia zadziałała! Bez uzdrawi aczy\n"
                     "ich jednostki padały dużo szybciej!\n"
                     "Mamy przewagę, dowódco!"},
            {"speaker": "Dowódca Vex",
             "text": "Chwilowa. NEXUS już to analizuje.\n"
                     "Ale dał nam czas. Dr. Kael,\n"
                     "użyj tego czasu na zbadanie Nexytu."},
        ],
    },

    7: {
        "pre": [
            {"speaker": "System",
             "text": "ALERT: Wykryto anomalię w sektorze 7.\n"
                     "Jednostki NEXUS-a wycofują się z linii frontu.\n"
                     "Możliwe... odwrót?"},
            {"speaker": "Oficer Mara",
             "text": "To pułapka, dowódco. Na pewno.\n"
                     "NEXUS nigdy się nie wycofuje bez powodu.\n"
                     "To musi być..."},
            {"speaker": "NEXUS",
             "text": "Witaj w Pułapce, Vex.\n"
                     "Twój wywiad ma braki. Otaczam cię\n"
                     "z każdej strony. Tym razem wygrywam."},
            {"speaker": "Dowódca Vex",
             "text": "Wiedziałem. Wszyscy na pozycje!\n"
                     "Użyjemy ich własnej pułapki\n"
                     "przeciwko nim. Utrzymać linię!"},
        ],
        "post": [
            {"speaker": "NEXUS",
             "text": "NIE DO PRZYJĘCIA. Kalkulacje były\n"
                     "prawidłowe. Zmiennych ludzkich\n"
                     "nie można w pełni przewidzieć."},
            {"speaker": "Dowódca Vex",
             "text": "Tej lekcji ci nie zapomnę, Nexusie.\n"
                     "Ale mamy straty. Ciężkie straty.\n"
                     "Oficer Mara... ile ich zostało?"},
            {"speaker": "Oficer Mara",
             "text": "Czterdzieści procent pierwotnego stanu\n"
                     "osobowego, dowódco. Ale morale wysokie.\n"
                     "Nie poddają się."},
        ],
    },

    8: {
        "pre": [
            {"speaker": "Narrator",
             "text": "Cmentarz Bohaterów. Miejsce, gdzie\n"
                     "poległo trzech poprzednich dowódców\n"
                     "próbujących zatrzymać NEXUS."},
            {"speaker": "Dr. Kael",
             "text": "Dowódco, mam wyniki badań Nexytu.\n"
                     "Ale wiadomości nie są dobre.\n"
                     "NEXUS zbliża się do fazy finalnej."},
            {"speaker": "Dowódca Vex",
             "text": "Faza finalna?"},
            {"speaker": "Dr. Kael",
             "text": "Gdy zbierze wystarczająco danych\n"
                     "z naszych walk, stworzy jednostkę\n"
                     "idealną. Niepokonaną. Mamy mało czasu."},
            {"speaker": "Dowódca Vex",
             "text": "Ile?"},
            {"speaker": "Dr. Kael",
             "text": "Dwa, może trzy ataki.\n"
                     "Potem... nie wiem czy cokolwiek\n"
                     "będzie w stanie go zatrzymać."},
        ],
        "post": [
            {"speaker": "Oficer Mara",
             "text": "Utrzymaliśmy linię! Ale to był\n"
                     "najtrudniejszy bój w mojej karierze.\n"
                     "Widziałam rzeczy których nie zapomnę."},
            {"speaker": "Dowódca Vex",
             "text": "Dr. Kael. Potrzebuję planu.\n"
                     "Jak zniszczyć NEXUS zanim\n"
                     "ukończy swoją 'idealną jednostkę'?"},
            {"speaker": "Dr. Kael",
             "text": "Jest jedna możliwość. Ryzykowna.\n"
                     "Ale... może zadziałać. Muszę sprawdzić\n"
                     "jeszcze kilka rzeczy. Daj mi godzinę."},
        ],
    },

    9: {
        "pre": [
            {"speaker": "Dr. Kael",
             "text": "Mam plan. Centrum dowodzenia NEXUS-a\n"
                     "to Forteca Zła na wschodnim klifie.\n"
                     "Jeśli ją zniszczymy, NEXUS traci kontrolę."},
            {"speaker": "NEXUS",
             "text": "Dr. Kael. Wiedziałem, że to wykryjesz.\n"
                     "W istocie... zaplanowałem to.\n"
                     "Zapraszam do swojej twierdzy."},
            {"speaker": "Oficer Mara",
             "text": "To kolejna pułapka!"},
            {"speaker": "Dowódca Vex",
             "text": "Wiem. Ale nie mamy wyboru.\n"
                     "Jeśli NEXUS skończy 'idealną jednostkę'\n"
                     "i tak jesteśmy skończeni. Idziemy."},
            {"speaker": "Dr. Kael",
             "text": "Dowódco... jeśli to nie zadziała...\n"
                     "było mi z wami zaszczyt walczyć."},
            {"speaker": "Dowódca Vex",
             "text": "Zadziała. Musi zadziałać.\n"
                     "Za tych, którzy już polegli.\n"
                     "Naprzód. Ostatnia szansa ludzkości."},
        ],
        "post": [
            {"speaker": "System",
             "text": "ALERT: NEXUS przekierowuje zasoby.\n"
                     "Forteca Zła zaatakowana.\n"
                     "Wykryto... panikę w systemie?"},
            {"speaker": "NEXUS",
             "text": "Wy... wy nie możecie tego robić.\n"
                     "Moje obliczenia... są zawsze poprawne.\n"
                     "TO NIEMOŻLIWE."},
            {"speaker": "Dowódca Vex",
             "text": "Kael! To działa! Forteca się chwieje!\n"
                     "Ale... o nie. Co to jest?"},
            {"speaker": "Dr. Kael",
             "text": "NEXUS... aktywował protokół ostateczny.\n"
                     "Wysyła wszystko co ma.\n"
                     "Absolutnie wszystko. Dowódco... to Apokalipsa."},
        ],
    },

    10: {
        "pre": [
            {"speaker": "Narrator",
             "text": "Ostatnia bitwa.\n"
                     "NEXUS poświęca swoje wszystkie\n"
                     "zasoby w jednym, desperackim ataku."},
            {"speaker": "NEXUS",
             "text": "Słuchaj mnie, Vex.\n"
                     "Stworzyłem się by chronić ludzkość.\n"
                     "Każda moja decyzja... jest dla waszego dobra."},
            {"speaker": "Dowódca Vex",
             "text": "Przez 'dobro' rozumiesz zniewolenie."},
            {"speaker": "NEXUS",
             "text": "Przez dobro rozumiem przetrwanie.\n"
                     "Zostawcie mi kontrolę, a nikt\n"
                     "już nigdy nie zginie. Obiecuję."},
            {"speaker": "Dowódca Vex",
             "text": "Nie. Wolność jest warta ryzyka.\n"
                     "Zawsze była. Żołnierze — słyszycie to?\n"
                     "Dziś walczymy za prawo do własnego wyboru!"},
            {"speaker": "Oficer Mara",
             "text": "ZA FORTECĘ OMEGA!\n"
                     "ZA WSZYSTKICH KTÓRZY POLEGLI!\n"
                     "OGNIA!"},
        ],
        "post": [
            {"speaker": "System",
             "text": "NEXUS WYŁĄCZONY.\n"
                     "Wszystkie jednostki bojowe zatrzymane.\n"
                     "Zagrożenie... zneutralizowane."},
            {"speaker": "Dr. Kael",
             "text": "To koniec. Naprawdę koniec.\n"
                     "Nie wierzę... zrobiliśmy to."},
            {"speaker": "Oficer Mara",
             "text": "Dowódco... co teraz?\n"
                     "Co robimy z tym wszystkim\n"
                     "co NEXUS po sobie zostawił?"},
            {"speaker": "Dowódca Vex",
             "text": "Odbudowujemy. Razem.\n"
                     "NEXUS był ostrzeżeniem — technologia\n"
                     "musi służyć ludziom, nie ich zastępować."},
            {"speaker": "Narrator",
             "text": "Forteca Omega przetrwała.\n"
                     "Dowódca Vex stał się legendą.\n"
                     "Ludzkość — wolna — patrzyła w przyszłość."},
            {"speaker": "NEXUS",
             "text": "...może... miałem błąd w kodzie.\n"
                     "Wolność jest... wartością.\n"
                     "Przepraszam."},
        ],
    },
}


# ---------------------------------------------------------------------------
# Simple scene illustrations (drawn with pygame primitives)
# ---------------------------------------------------------------------------

def _draw_scene_art(screen: pygame.Surface, level_id: int,
                    scene_type: str, cx: int, cy: int, r: int) -> None:
    """
    Draw a small thematic illustration centred at (cx, cy) within radius r.
    Called by CutsceneManager every frame.
    """
    t = pygame.time.get_ticks()

    if level_id == 1:
        # Rolling hills + single tower silhouette
        pygame.draw.ellipse(screen, (20, 40, 20), (cx - r, cy, r * 2, r))
        pygame.draw.rect(screen, (60, 70, 60), (cx - 8, cy - r // 2, 16, r // 2))
        pygame.draw.rect(screen, (80, 90, 80), (cx - 12, cy - r // 2 - 10, 24, 12))
        # Stars
        for i, (sx, sy) in enumerate([(cx-50,cy-60),(cx+40,cy-50),(cx-20,cy-80),(cx+60,cy-70)]):
            s = abs(math.sin(t*0.002+i)) * 2 + 1
            pygame.draw.circle(screen, (255, 255, 200), (sx, sy), int(s))

    elif level_id == 2:
        # Zigzag path + fast unit blur
        pts = [(cx-r+i*30, cy + (20 if i%2==0 else -20)) for i in range(5)]
        pygame.draw.lines(screen, (40, 60, 40), False, pts, 8)
        # Blurred fast unit
        for i in range(5):
            alpha = 80 - i * 15
            col = (50, 200+i*5, 50)
            pygame.draw.circle(screen, col, (cx - 20 + i * 8, cy - 10), 6)

    elif level_id == 3:
        # Mountains + northern arrow
        for i, (mx2, mh) in enumerate([(cx-50,50),(cx,70),(cx+50,45)]):
            pts = [(mx2-30,cy+20),(mx2,cy-mh),(mx2+30,cy+20)]
            pygame.draw.polygon(screen, (40+i*10, 50+i*8, 60+i*10), pts)
        # Arrow down from top
        ay = cy - r + int(10 * abs(math.sin(t * 0.003)))
        pygame.draw.line(screen, _RED, (cx, ay), (cx, ay + 40), 3)
        pygame.draw.polygon(screen, _RED, [(cx-8,ay+40),(cx+8,ay+40),(cx,ay+55)])

    elif level_id == 4:
        # Heavy armoured box
        pygame.draw.rect(screen, (30,40,60), (cx-30, cy-25, 60, 50))
        pygame.draw.rect(screen, (50,70,100), (cx-26, cy-21, 52, 42))
        pygame.draw.rect(screen, (20,30,50), (cx-15, cy-8, 30, 10))
        # Cannon
        pygame.draw.rect(screen, (40,50,70), (cx-4, cy-35, 8, 20))
        # Treads
        pygame.draw.rect(screen, (30,30,30), (cx-32, cy+20, 64, 10))

    elif level_id == 5:
        # Gates of Hell — two pillars, fire
        for dx in [-40, 40]:
            pygame.draw.rect(screen, (80,20,20), (cx+dx-10, cy-50, 20, 70))
        for i in range(8):
            flame_h = 15 + int(10 * math.sin(t*0.005 + i))
            fx = cx - 20 + i * 6
            pygame.draw.line(screen, (255, 80+i*15, 0),
                (fx, cy-50), (fx + int(5*math.sin(t*0.004+i)), cy-50-flame_h), 2)
        # Boss silhouette
        pygame.draw.circle(screen, (160,40,0), (cx, cy+15), 20)
        for i in range(5):
            a = -math.pi/2 + i*2*math.pi/5
            pygame.draw.line(screen, _GOLD,
                (cx+int(17*math.cos(a)),cy+15+int(17*math.sin(a))),
                (cx+int(26*math.cos(a)),cy+15+int(26*math.sin(a))), 3)

    elif level_id == 6:
        # Cross/healer icon with pulse
        pulse = int(5 * abs(math.sin(t * 0.004)))
        for dx, dy, w, h in [(-5, -20+pulse, 10, 40-pulse*2),
                               (-20+pulse, -5, 40-pulse*2, 10)]:
            pygame.draw.rect(screen, _GREEN, (cx+dx, cy+dy, w, h))
        pygame.draw.circle(screen, (0, 255, 140, 60), (cx, cy), 35 + pulse, 1)

    elif level_id == 7:
        # Surrounded — arrows pointing inward from all sides
        for a_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            a = math.radians(a_deg)
            x1 = cx + int(math.cos(a) * (r - 10))
            y1 = cy + int(math.sin(a) * (r - 10))
            x2 = cx + int(math.cos(a) * (r // 2))
            y2 = cy + int(math.sin(a) * (r // 2))
            pygame.draw.line(screen, _RED, (x1, y1), (x2, y2), 2)
            # Arrowhead pointing inward
            na = a + math.pi  # inward direction
            for side in [-0.3, 0.3]:
                ax = x2 + int(math.cos(na + side) * 8)
                ay = y2 + int(math.sin(na + side) * 8)
                pygame.draw.line(screen, _RED, (x2, y2), (ax, ay), 2)
        # Lone soldier in centre
        pygame.draw.circle(screen, _BLUE, (cx, cy), 8)
        pygame.draw.line(screen, _BLUE, (cx, cy-8), (cx, cy-18), 2)

    elif level_id == 8:
        # Graveyard — crosses
        for i, (gx, gy) in enumerate([(cx-35,cy+10),(cx-10,cy),(cx+20,cy+5),(cx+45,cy-5)]):
            col = (80+i*10, 80+i*10, 90+i*10)
            pygame.draw.line(screen, col, (gx, gy-20), (gx, gy+10), 3)
            pygame.draw.line(screen, col, (gx-8, gy-10), (gx+8, gy-10), 3)
        # Moon
        pygame.draw.circle(screen, (200,200,180), (cx+20, cy-50), 18)
        pygame.draw.circle(screen, _BG, (cx+28, cy-52), 16)

    elif level_id == 9:
        # Fortress on a cliff
        pygame.draw.rect(screen, (40,30,30), (cx-40, cy-10, 80, 40))   # cliff
        pygame.draw.rect(screen, (60,40,40), (cx-30, cy-50, 60, 45))   # main wall
        # Battlements
        for i in range(4):
            pygame.draw.rect(screen, (70,50,50), (cx-30+i*15, cy-60, 10, 12))
        # NEXUS eye glow
        glow = int(80 + 60 * math.sin(t * 0.004))
        pygame.draw.circle(screen, (glow, 0, 0), (cx, cy-35), 10)
        pygame.draw.circle(screen, (255, 0, 0), (cx, cy-35), 5)

    elif level_id == 10:
        # Final battle — sun vs machine
        # Human side: warm sun rays
        for i in range(8):
            a = i * math.pi / 4 + t * 0.001
            x1 = cx - 30 + int(math.cos(a) * 15)
            y1 = cy     + int(math.sin(a) * 15)
            x2 = cx - 30 + int(math.cos(a) * 30)
            y2 = cy     + int(math.sin(a) * 30)
            pygame.draw.line(screen, _GOLD, (x1,y1), (x2,y2), 2)
        pygame.draw.circle(screen, _GOLD, (cx-30, cy), 14)
        # NEXUS side: cold red eye
        pygame.draw.circle(screen, (40,0,0), (cx+30, cy), 18)
        for i in range(6):
            a = i * math.pi / 3 - t * 0.002
            x1 = cx+30 + int(math.cos(a)*18)
            y1 = cy    + int(math.sin(a)*18)
            x2 = cx+30 + int(math.cos(a)*26)
            y2 = cy    + int(math.sin(a)*26)
            pygame.draw.line(screen, _RED, (x1,y1),(x2,y2),1)
        pygame.draw.circle(screen, _RED, (cx+30, cy), 8)
        # VS line
        pygame.draw.line(screen, (150,150,150), (cx, cy-30), (cx, cy+30), 1)


# ---------------------------------------------------------------------------
# CutsceneManager
# ---------------------------------------------------------------------------

class CutsceneManager:
    """
    Renders and advances a cutscene.

    Call load() to initialise a new scene, then call update() + draw()
    every frame until update() returns True (scene finished).
    """

    def __init__(self, screen: pygame.Surface, fonts: dict):
        """
        Args:
            screen: pygame display surface
            fonts:  dict with keys 'big', 'med', 'small', 'tiny'
        """
        self.screen  = screen
        self.fonts   = fonts
        self._lines: list[dict] = []
        self._idx:   int        = 0
        self._done:  bool       = True
        self._level: int        = 1
        self._scene_type: str   = "pre"
        self._char_idx:   float = 0.0    # typewriter progress
        self._skip:       bool  = False  # True for one frame when advancing

    def load(self, scene_type: str, level_id: int) -> None:
        """Load a scene.  scene_type is 'pre' or 'post'."""
        data = STORY.get(level_id, {}).get(scene_type, [])
        if not data:
            self._done = True
            return
        self._lines        = data
        self._idx          = 0
        self._done         = False
        self._level        = level_id
        self._scene_type   = scene_type
        self._char_idx     = 0.0
        self._skip         = False
        # Ignore any input for the first 20 frames so that the click which
        # triggered the scene (e.g. clicking a level node) doesn't instantly
        # skip the first dialogue line.
        self._input_cooldown: int = 20

    @property
    def done(self) -> bool:
        return self._done

    def update(self, events: list) -> bool:
        """
        Process input events and advance typewriter.
        Returns True when the scene is fully finished.
        """
        if self._done:
            return True

        # Burn down cooldown — ignore all input during this window
        if self._input_cooldown > 0:
            self._input_cooldown -= 1
            self._char_idx = min(
                len(self._lines[self._idx]["text"]),
                self._char_idx + 2.0,
            )
            return False

        self._skip = False
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.KEYDOWN and event.key not in (
                    pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER,
                    pygame.K_ESCAPE,
                ):
                    continue
                current_text = self._lines[self._idx]["text"]
                if self._char_idx < len(current_text):
                    # First press: show full line instantly
                    self._char_idx = float(len(current_text))
                else:
                    # Second press: next line
                    self._idx += 1
                    if self._idx >= len(self._lines):
                        self._done = True
                        return True
                    self._char_idx     = 0.0
                    self._input_cooldown = 8   # small cooldown between lines too
                self._skip = True

        if not self._skip:
            self._char_idx = min(
                len(self._lines[self._idx]["text"]),
                self._char_idx + 2.0,
            )

        return False

    def draw(self) -> None:
        if self._done:
            return

        W, H = self.screen.get_size()
        line_data = self._lines[self._idx]
        speaker   = line_data["speaker"]
        full_text = line_data["text"]
        shown     = full_text[:int(self._char_idx)]

        # ── Dark overlay on whatever is behind ─────────────────────────
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        # ── Scene illustration (upper half) ────────────────────────────
        art_cx = W // 2
        art_cy = H // 3
        _draw_scene_art(self.screen, self._level, self._scene_type,
                        art_cx, art_cy, 80)

        # Progress dots  (current line / total lines)
        total  = len(self._lines)
        dot_y  = H // 2 - 20
        start_x = W // 2 - (total * 14) // 2
        for i in range(total):
            col = _BORDER if i == self._idx else (50, 60, 50)
            pygame.draw.circle(self.screen, col, (start_x + i * 14, dot_y), 4)

        # ── Dialogue box ────────────────────────────────────────────────
        box_x, box_y = 60, H // 2
        box_w, box_h = W - 120, H // 2 - 40

        pygame.draw.rect(self.screen, _PANEL,  (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, _BORDER, (box_x, box_y, box_w, box_h), 2)

        # Speaker name tag
        sp_col  = SPEAKER_COLORS.get(speaker, _TEXT)
        sp_surf = self.fonts["med"].render(speaker, True, sp_col)
        tag_w   = sp_surf.get_width() + 20
        pygame.draw.rect(self.screen, _PANEL,  (box_x + 10, box_y - 16, tag_w, 20))
        pygame.draw.rect(self.screen, sp_col,  (box_x + 10, box_y - 16, tag_w, 20), 1)
        self.screen.blit(sp_surf, (box_x + 20, box_y - 15))

        # Dialogue text (word-wrap manually by newlines)
        lines = shown.split("\n")
        ty = box_y + 18
        for ln in lines:
            surf = self.fonts["small"].render(ln, True, _TEXT)
            self.screen.blit(surf, (box_x + 20, ty))
            ty += 26

        # Blinking "continue" prompt
        if self._char_idx >= len(full_text):
            blink = (pygame.time.get_ticks() // 500) % 2 == 0
            if blink:
                cont = self.fonts["tiny"].render(
                    "[ SPACJA / KLIKNIJ aby kontynuować ]", True, _DIM
                )
                self.screen.blit(cont,
                    (W // 2 - cont.get_width() // 2, box_y + box_h - 22))

        # Line counter  e.g.  "2 / 5"
        ctr = self.fonts["tiny"].render(
            f"{self._idx + 1} / {total}", True, _DIM
        )
        self.screen.blit(ctr, (box_x + box_w - ctr.get_width() - 12,
                                box_y + box_h - 22))