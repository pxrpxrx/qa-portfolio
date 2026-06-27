package com.tradingtabs.gann;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.Locale;

public class GannBlock {

    private static final String DASH = "─".repeat(46);
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("dd MMM", Locale.ENGLISH);

    public static void printAll(double btcPrice) {
        LocalDate today = LocalDate.now();
        double jd = Ephemeris.toJulianDay(today);
        Map<Ephemeris.Planet, Ephemeris.GeoPos> pos = Ephemeris.compute(today);

        System.out.println("  " + DASH);
        System.out.println("  --- GANN & PLANETARY ---");
        System.out.println("  " + DASH);

        // 1. LUNAR
        printLunar(today, jd);

        // 2. PLANETARY POSITIONS
        printPositions(pos);

        // 3. PLANETARY ASPECTS (today)
        List<AspectFinder.Aspect> todayAspects = AspectFinder.findAspects(pos, 6.0);
        if (!todayAspects.isEmpty()) {
            System.out.println("  Aspects today:");
            for (AspectFinder.Aspect a : todayAspects) {
                System.out.println("    " + a.label());
            }
        }

        // 4. UPCOMING ASPECTS (next 14 days)
        Map<LocalDate, List<AspectFinder.Aspect>> upcoming = AspectFinder.scanForwardGrouped(today, 14, 3.0);
        if (!upcoming.isEmpty()) {
            System.out.println("  Upcoming aspects (next 14d, orb±3°):");
            int count = 0;
            for (Map.Entry<LocalDate, List<AspectFinder.Aspect>> e : upcoming.entrySet()) {
                if (e.getKey().equals(today)) continue;
                if (count >= 8) { System.out.println("    ..."); break; }
                for (AspectFinder.Aspect a : e.getValue()) {
                    System.out.printf("    %s → %s%n", e.getKey().format(FMT), a.label());
                    count++;
                }
            }
        }

        // 5. ASTROLOGICAL INTERPRETATION
        printAstroInterpretation(pos, todayAspects, today, jd);

        // 6. SQUARE OF 9 for BTC
        System.out.println("  --- SQUARE OF 9 (BTC) ---");
        for (String line : GannSquare9.formatBlock(btcPrice)) {
            System.out.println("  " + line);
        }
        System.out.println("  " + DASH);
    }

    private static void printLunar(LocalDate today, double jd) {
        int lDay = Ephemeris.lunarDay(jd);
        String phase = Ephemeris.moonPhaseName(jd);
        double illum = Ephemeris.moonIllumination(jd);
        System.out.printf("  Lunar day: %d (%s, %.0f%% illuminated)%n", lDay, phase, illum * 100);

        // Market sentiment key
        String sent;
        if (lDay <= 1) sent = "volatile (new moon)";
        else if (lDay == 14 || lDay == 15) sent = "volatile (full moon)";
        else if (lDay == 7 || lDay == 8) sent = "directional (first qtr)";
        else if (lDay == 22 || lDay == 23) sent = "directional (last qtr)";
        else if (lDay < 14) sent = "expansive (waxing)";
        else sent = "contractive (waning)";
        System.out.println("  Market sentiment: " + sent);
    }

    private static void printPositions(Map<Ephemeris.Planet, Ephemeris.GeoPos> pos) {
        System.out.println("  Planetary positions (geocentric ecliptic):");
        for (Ephemeris.Planet p : Ephemeris.Planet.values()) {
            Ephemeris.GeoPos gp = pos.get(p);
            if (gp == null) continue;
            String sign = zodiacSign(gp.longitude());
            System.out.printf("    %-8s %6.1f° %s (lat: %+.1f°)%n",
                p, gp.longitude(), sign, gp.latitude());
        }
    }

    public static String zodiacSign(double lon) {
        String[] signs = {"ARI", "TAU", "GEM", "CAN", "LEO", "VIR", "LIB", "SCO", "SAG", "CAP", "AQU", "PIS"};
        int idx = ((int)Math.floor(lon / 30)) % 12;
        double degInSign = lon % 30;
        return String.format("%s %.0f°", signs[idx], Math.floor(degInSign));
    }

    private static void printAstroInterpretation(Map<Ephemeris.Planet, Ephemeris.GeoPos> pos,
                                                  List<AspectFinder.Aspect> aspects,
                                                  LocalDate today, double jd) {
        System.out.println("  --- ASTROLOGICAL ANALYSIS ---");

        // Planetary sign interpretations
        double sunLon = getLon(pos, Ephemeris.Planet.SUN);
        double moonLon = getLon(pos, Ephemeris.Planet.MOON);
        double mercLon = getLon(pos, Ephemeris.Planet.MERCURY);
        double venusLon = getLon(pos, Ephemeris.Planet.VENUS);
        double marsLon = getLon(pos, Ephemeris.Planet.MARS);
        double jupLon = getLon(pos, Ephemeris.Planet.JUPITER);
        double satLon = getLon(pos, Ephemeris.Planet.SATURN);
        double uranLon = getLon(pos, Ephemeris.Planet.URANUS);
        double neptLon = getLon(pos, Ephemeris.Planet.NEPTUNE);
        double plutLon = getLon(pos, Ephemeris.Planet.PLUTO);

        String CFG = "Конфигурация";
        String SLN = "Солнце";
        String RAK = "Раке";
        String ZSH = "защита";
        String NST = "ностальгия";
        String YUP = "Юпитер";
        String NAK = "накопление";
        String IZB = "избыток";
        String SAT = "Сатурн";
        String OVN = "Овне";
        String OGR = "ограничения";
        String TST = "тест на прочность";
        String MRS = "Марс";
        String TEL = "Тельце";
        String UPR = "упрямство";
        String STM = "стоимость";
        String URN = "Уран";
        String BLZ = "Близнецах";
        String INN = "инновации";
        String HAO = "хаос";

        // Solar system overview
        System.out.print("  " + CFG + ": ");
        System.out.print(SLN + " в " + RAK + " (" + ZSH + "/" + NST + ")");
        if (jupLon >= 90 && jupLon < 120) System.out.print(", " + YUP + " в " + RAK + " (" + NAK + "/" + IZB + ")");
        if (satLon >= 0 && satLon < 30) System.out.print(", " + SAT + " в " + OVN + " (" + OGR + "/" + TST + ")");
        if (marsLon >= 30 && marsLon < 60) System.out.print(", " + MRS + " в " + TEL + " (" + UPR + "/" + STM + ")");
        if (uranLon >= 60 && uranLon < 90) System.out.print(", " + URN + " в " + BLZ + " (" + INN + "/" + HAO + ")");
        System.out.println();

        // Key aspects interpretation
        String KLA = "Ключевые аспекты";
        System.out.println("  " + KLA + ":");
        boolean hasKey = false;
        for (AspectFinder.Aspect a : aspects) {
            if (a.orbUsed() < 3.0) {
                String interp = aspectInterpretation(a);
                if (interp != null) {
                    System.out.println("    " + interp);
                    hasKey = true;
                }
            }
        }
        if (!hasKey) {
            for (AspectFinder.Aspect a : aspects) {
                if (a.orbUsed() < 2.0) {
                    String interp = aspectInterpretation(a);
                    if (interp != null) {
                        System.out.println("    " + interp);
                    }
                }
            }
        }

        // Lunar interpretation
        int lDay = Ephemeris.lunarDay(jd);
        double illum = Ephemeris.moonIllumination(jd);
        String phase = Ephemeris.moonPhaseName(jd);
        String LUNA = "Луна";
        String DEN = "день";
        System.out.println("  " + LUNA + ": " + lDay + " " + DEN + ", " + phase + " (" + String.format("%.0f", illum * 100) + "%)");
        if (lDay < 14) {
            String T1 = "Фаза роста — рынок склонен к расширению. Обычно благоприятно для риска.";
            System.out.println("    " + T1);
        } else {
            String T2 = "Фаза убывания — рынок склонен к сжатию. Риск коррекции повышен.";
            System.out.println("    " + T2);
        }
        if (lDay >= 12 && lDay <= 16) {
            String T3 = "Ближе к полнолунию — возможны резкие движения, развороты тренда.";
            System.out.println("    " + T3);
        }

        // Gann price interpretation
        String G9 = "Gann Square of 9: цена между квадратами — зона неопределённости.";
        System.out.println("  " + G9);
    }

    public static String aspectInterpretation(AspectFinder.Aspect a) {
        String p1 = a.p1().toString();
        String p2 = a.p2().toString();
        String type = aspectName(a.exactDeg());
        double orb = a.orbUsed();

        // Skip Sun-Moon aspects (too frequent, low signal)
        if (p1.equals("MOON") || p2.equals("MOON")) {
            if (p1.equals("SUN") || p2.equals("SUN")) return null;
        }

        // Only CONJ, SQUARE, OPPOS, TRINE, SEXTILE for interpretation
        if (!type.equals("CONJ") && !type.equals("SQUARE") && !type.equals("OPPOS")
            && !type.equals("TRINE") && !type.equals("SEXT60")) return null;

        String key = p1 + "/" + p2 + " " + type;
        String ORB = " (орб ";
        String DEG = "°)";

        if (key.contains("SUN/SATURN") || key.contains("SATURN/SUN")) {
            if (type.equals("CONJ") || type.equals("SQUARE") || type.equals("OPPOS"))
                return "⚠️ " + "Солнце-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — давление, ограничения, возможны плохие новости";
            else
                return "✅ " + "Солнце-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — структура, порядок, стабилизация";
        }
        if (key.contains("SUN/NEPTUNE") || key.contains("NEPTUNE/SUN")) {
            if (type.equals("CONJ") || type.equals("SQUARE") || type.equals("OPPOS"))
                return "⚠️ " + "Солнце-Нептун" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — неопределённость, возможны ложные сигналы, осторожно";
            else
                return "👀 " + "Солнце-Нептун" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — интуиция, тренд может продолжиться";
        }
        if (key.contains("VENUS/SATURN") || key.contains("SATURN/VENUS")) {
            if (type.equals("CONJ") || type.equals("SQUARE") || type.equals("OPPOS"))
                return "⚠️ " + "Венера-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — сжатие ликвидности, ограничение риска";
            else
                return "✅ " + "Венера-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — стабилизация потоков, здоровое ценообразование";
        }
        if (key.contains("MARS/SATURN") || key.contains("SATURN/MARS")) {
            if (type.equals("CONJ") || type.equals("SQUARE") || type.equals("OPPOS"))
                return "⚠️ " + "Марс-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — фрустрация, пробой поддержки, сопротивление";
            else
                return "✅ " + "Марс-Сатурн" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — устойчивый тренд, накопление";
        }
        if (key.contains("SATURN/URANUS") || key.contains("URANUS/SATURN")) {
            return "⚠️ " + "Сатурн-Уран" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — конфликт старого и нового, структурный сдвиг";
        }
        if (key.contains("URANUS/PLUTO") || key.contains("PLUTO/URANUS")) {
            return "🔥 " + "Уран-Плутон" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — трансформация эпохи, редкий аспект (раз в десятилетия)";
        }
        if (key.contains("JUPITER/URANUS") || key.contains("URANUS/JUPITER")) {
            return "✅ " + "Юпитер-Уран" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — прорыв, инновации, неожиданный рост";
        }
        if (key.contains("MARS/JUPITER") || key.contains("JUPITER/MARS")) {
            return "✅ " + "Марс-Юпитер" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — энергия роста, импульс, экспансия";
        }
        if (key.contains("SUN/JUPITER") || key.contains("JUPITER/SUN")) {
            return "✅ " + "Солнце-Юпитер" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — оптимизм, рост";
        }
        if (key.contains("SUN/URANUS") || key.contains("URANUS/SUN")) {
            return "⚠️ " + "Солнце-Уран" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — неожиданные события, волатильность";
        }
        if (key.contains("SUN/VENUS") || key.contains("VENUS/SUN")) {
            return "✅ " + "Солнце-Венера" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — гармония, приток капитала";
        }
        if (key.contains("VENUS/JUPITER") || key.contains("JUPITER/VENUS")) {
            return "✅ " + "Венера-Юпитер" + " " + type + ORB + String.format("%.1f", orb) + DEG + " — избыток, переоценка, эйфория";
        }

        return null;
    }

    private static String aspectName(double exactDeg) {
        return switch ((int)Math.round(exactDeg)) {
            case 0 -> "CONJ";
            case 30 -> "SEXT30";
            case 45 -> "SEMISQ";
            case 60 -> "SEXT60";
            case 90 -> "SQUARE";
            case 120 -> "TRINE";
            case 135 -> "SESQQU";
            case 150 -> "QUNCUX";
            case 180 -> "OPPOS";
            default -> String.format("%.0f°", exactDeg);
        };
    }

    public static double getLon(Map<Ephemeris.Planet, Ephemeris.GeoPos> pos, Ephemeris.Planet p) {
        Ephemeris.GeoPos gp = pos.get(p);
        return gp == null ? -1 : gp.longitude();
    }
}
