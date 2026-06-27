package com.tradingtabs.gann;

import java.time.LocalDate;
import java.util.*;

public class AspectFinder {

    private static final double ORB = 6.0;

    public record Aspect(Ephemeris.Planet p1, Ephemeris.Planet p2, double angle, double exactDeg, double orbUsed) {
        public String label() {
            String an = switch ((int)Math.round(exactDeg)) {
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
            return String.format("%s %s %s (orb %.1f°)", p1, an, p2, orbUsed);
        }
    }

    public static List<Aspect> findAspects(Map<Ephemeris.Planet, Ephemeris.GeoPos> pos, double orb) {
        List<Aspect> out = new ArrayList<>();
        List<Ephemeris.Planet> planets = new ArrayList<>(pos.keySet());
        for (int i = 0; i < planets.size(); i++) {
            for (int j = i + 1; j < planets.size(); j++) {
                Ephemeris.Planet a = planets.get(i);
                Ephemeris.Planet b = planets.get(j);
                if (a == Ephemeris.Planet.SUN && b == Ephemeris.Planet.MOON) continue;
                if (a == Ephemeris.Planet.MOON && b == Ephemeris.Planet.SUN) continue;
                double lon1 = pos.get(a).longitude();
                double lon2 = pos.get(b).longitude();
                double diff = Math.abs(lon1 - lon2);
                if (diff > 180) diff = 360 - diff;

                for (double aspect : new double[]{0, 30, 45, 60, 90, 120, 135, 150, 180}) {
                    double orbUsed = Math.abs(diff - aspect);
                    if (orbUsed <= orb) {
                        out.add(new Aspect(a, b, diff, aspect, orbUsed));
                    }
                }
            }
        }
        return out;
    }

    public static List<Aspect> scanForward(LocalDate from, int days, double orb) {
        List<Aspect> all = new ArrayList<>();
        for (int d = 0; d <= days; d++) {
            LocalDate date = from.plusDays(d);
            Map<Ephemeris.Planet, Ephemeris.GeoPos> pos = Ephemeris.compute(date);
            List<Aspect> today = findAspects(pos, orb);
            for (Aspect a : today) {
                all.add(new Aspect(a.p1(), a.p2(), a.angle(), a.exactDeg(), a.orbUsed()));
            }
        }
        return all;
    }

    public static Map<LocalDate, List<Aspect>> scanForwardGrouped(LocalDate from, int days, double orb) {
        Map<LocalDate, List<Aspect>> grouped = new TreeMap<>();
        for (int d = 0; d <= days; d++) {
            LocalDate date = from.plusDays(d);
            Map<Ephemeris.Planet, Ephemeris.GeoPos> pos = Ephemeris.compute(date);
            List<Aspect> aspects = findAspects(pos, orb);
            if (!aspects.isEmpty()) grouped.put(date, aspects);
        }
        return grouped;
    }
}
