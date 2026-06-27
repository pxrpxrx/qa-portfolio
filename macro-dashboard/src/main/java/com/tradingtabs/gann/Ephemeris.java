package com.tradingtabs.gann;

import java.time.LocalDate;
import java.util.*;

public class Ephemeris {

    public enum Planet {
        SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO
    }

    public record GeoPos(double longitude, double latitude) {}

    public static Map<Planet, GeoPos> compute(LocalDate date) {
        double jd = toJulianDay(date);
        double T = (jd - 2451545.0) / 36525.0;
        double T2 = T * T;

        Map<Planet, GeoPos> result = new LinkedHashMap<>();

        // Heliocentric ecliptic coords for planets + Earth
        double[][] earthH = heliocentric(T, T2, PlanetElement.EARTH);
        double eX = earthH[0][0], eY = earthH[0][1], eZ = earthH[0][2];

        // Sun: geocentric = negative of Earth's heliocentric, convert to ecliptic long/lat
        double sunLon = Math.toDegrees(Math.atan2(-eY, -eX));
        double sunLat = Math.toDegrees(Math.atan2(-eZ, Math.sqrt(eX*eX + eY*eY)));
        result.put(Planet.SUN, new GeoPos(norm(sunLon), normLat(sunLat)));

        // Planets
        for (PlanetElement pe : PlanetElement.values()) {
            if (pe == PlanetElement.EARTH) continue;
            double[][] helio = heliocentric(T, T2, pe);
            double dx = helio[0][0] - eX, dy = helio[0][1] - eY, dz = helio[0][2] - eZ;
            double lon = Math.toDegrees(Math.atan2(dy, dx));
            double dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
            double lat = Math.toDegrees(Math.asin(dz / dist));
            result.put(pe.planet, new GeoPos(norm(lon), normLat(lat)));
        }

        // Moon (separate computation — simplified theory)
        result.put(Planet.MOON, moonPosition(T, T2));

        return result;
    }

    private static double[][] heliocentric(double T, double T2, PlanetElement pe) {
        double T3 = T2 * T;
        double a  = pe.a0 + pe.a1*T;
        double e  = pe.e0 + pe.e1*T;
        double I  = norm(pe.I0 + pe.I1*T);
        double L  = norm(pe.L0 + pe.L1*T + pe.L2*T2 + pe.L3*T3);
        double w  = norm(pe.w0 + pe.w1*T + pe.w2*T2 + pe.w3*T3);  // longitude of perihelion
        double O  = norm(pe.O0 + pe.O1*T + pe.O2*T2 + pe.O3*T3);  // longitude of ascending node

        double M = norm(L - w);
        double E = solveKepler(M, e);

        double x0 = a * (Math.cos(Math.toRadians(E)) - e);
        double y0 = a * Math.sqrt(1 - e*e) * Math.sin(Math.toRadians(E));

        double cosO = Math.cos(Math.toRadians(O));
        double sinO = Math.sin(Math.toRadians(O));
        double cosw = Math.cos(Math.toRadians(w - O));
        double sinw = Math.sin(Math.toRadians(w - O));
        double cosI = Math.cos(Math.toRadians(I));
        double sinI = Math.sin(Math.toRadians(I));

        double x = (cosO*cosw - sinO*sinw*cosI) * x0 + (-cosO*sinw - sinO*cosw*cosI) * y0;
        double y = (sinO*cosw + cosO*sinw*cosI) * x0 + (-sinO*sinw + cosO*cosw*cosI) * y0;
        double z = sinw*sinI * x0 + cosw*sinI * y0;

        return new double[][]{{x, y, z}};
    }

    private static double solveKepler(double Mdeg, double e) {
        double M = Math.toRadians(Mdeg);
        double E = M;
        for (int i = 0; i < 30; i++) {
            double dE = (M - E + e * Math.sin(E)) / (1 - e * Math.cos(E));
            E += dE;
            if (Math.abs(dE) < 1e-10) break;
        }
        return Math.toDegrees(E);
    }

    private static GeoPos moonPosition(double T, double T2) {
        double T3 = T2 * T;
        double Lm = norm(218.3164591 + 481267.88134236*T - 0.0013268*T2 + T3/538841 - T3*T/65194000);
        double D  = norm(297.8502042 + 445267.1115168*T - 0.0016300*T2 + T3/545868 - T3*T/113065000);
        double M  = norm(357.5291092 + 35999.0502909*T - 0.0001536*T2 + T3/24490000);
        double Mp = norm(134.9634114 + 477198.8676313*T + 0.0089970*T2 + T3/69699 - T3*T/14712000);
        double F  = norm(93.2720993 + 483202.0175273*T - 0.0034029*T2 - T3/3526000 + T3*T/863310000);

        double lon = Lm
            + 6.288774 * Math.sin(Math.toRadians(Mp))
            + 1.274027 * Math.sin(Math.toRadians(2*D - Mp))
            + 0.658314 * Math.sin(Math.toRadians(2*D))
            + 0.213618 * Math.sin(Math.toRadians(2*Mp))
            - 0.185116 * Math.sin(Math.toRadians(M))
            - 0.114332 * Math.sin(Math.toRadians(2*F))
            + 0.058793 * Math.sin(Math.toRadians(2*D - 2*Mp))
            + 0.057212 * Math.sin(Math.toRadians(2*D - M - Mp))
            + 0.053320 * Math.sin(Math.toRadians(2*D + Mp))
            + 0.045874 * Math.sin(Math.toRadians(2*D - M))
            + 0.041024 * Math.sin(Math.toRadians(Mp - M))
            - 0.034718 * Math.sin(Math.toRadians(D))
            - 0.030465 * Math.sin(Math.toRadians(M + Mp))
            + 0.015326 * Math.sin(Math.toRadians(2*D - 2*F))
            - 0.012528 * Math.sin(Math.toRadians(2*F + Mp))
            - 0.010980 * Math.sin(Math.toRadians(2*F - Mp))
            + 0.010674 * Math.sin(Math.toRadians(4*D - Mp))
            + 0.010034 * Math.sin(Math.toRadians(3*Mp))
            + 0.008548 * Math.sin(Math.toRadians(4*D - 2*Mp))
            - 0.007910 * Math.sin(Math.toRadians(M - Mp + 2*D))
            - 0.006783 * Math.sin(Math.toRadians(2*D + M))
            + 0.005162 * Math.sin(Math.toRadians(Mp - D));

        double lat = 
            + 5.128122 * Math.sin(Math.toRadians(F))
            + 0.280606 * Math.sin(Math.toRadians(Mp + F))
            + 0.277693 * Math.sin(Math.toRadians(Mp - F))
            + 0.173238 * Math.sin(Math.toRadians(2*D - F))
            + 0.055413 * Math.sin(Math.toRadians(2*D + Mp - F))
            + 0.046272 * Math.sin(Math.toRadians(2*D - Mp - F))
            + 0.032573 * Math.sin(Math.toRadians(2*D + F))
            + 0.017198 * Math.sin(Math.toRadians(2*Mp + F))
            + 0.009267 * Math.sin(Math.toRadians(2*D + Mp + F))
            + 0.008823 * Math.sin(Math.toRadians(2*Mp - F));

        return new GeoPos(norm(lon), normLat(lat));
    }

    public static int lunarDay(double jd) {
        double newMoonJd = 2451549.5;
        double synodic = 29.530588853;
        double age = norm((jd - newMoonJd) / synodic * 360) / 360 * synodic;
        return (int) Math.floor(age) + 1;
    }

    public static String moonPhaseName(double jd) {
        double newMoonJd = 2451549.5;
        double synodic = 29.530588853;
        double age = norm((jd - newMoonJd) / synodic * 360) / 360 * synodic;
        int day = (int) Math.floor(age) + 1;
        if (day <= 1) return "NEW MOON";
        if (day < 7) return "WAXING CRESCENT";
        if (day == 7 || day == 8) return "FIRST QUARTER";
        if (day < 14) return "WAXING GIBBOUS";
        if (day == 14 || day == 15) return "FULL MOON";
        if (day < 22) return "WANING GIBBOUS";
        if (day == 22 || day == 23) return "LAST QUARTER";
        if (day < 29) return "WANING CRESCENT";
        return "NEW MOON";
    }

    public static double moonIllumination(double jd) {
        double newMoonJd = 2451549.5;
        double synodic = 29.530588853;
        double phase = norm((jd - newMoonJd) / synodic * 360);
        return (1 - Math.cos(Math.toRadians(phase))) / 2;
    }

    public static double toJulianDay(LocalDate date) {
        int y = date.getYear(), m = date.getMonthValue(), d = date.getDayOfMonth();
        if (m <= 2) { y -= 1; m += 12; }
        int A = y / 100;
        int B = 2 - A + A / 4;
        return (int) (365.25 * (y + 4716)) + (int) (30.6001 * (m + 1)) + d + B - 1524.5;
    }

    private static double norm(double deg) {
        deg = deg % 360;
        return deg < 0 ? deg + 360 : deg;
    }

    private static double normLat(double deg) {
        if (deg > 180) deg -= 360;
        if (deg < -180) deg += 360;
        return deg;
    }

    private enum PlanetElement {
        MERCURY(Planet.MERCURY,
            0.38709927, 0, 0.20563593, 0.00001906,
            7.00497923, -0.00594749, 0,
            252.250906, 149472.6746358, 0, 0,
            77.456119, 0.1588643, 0, 0,
            48.330541, -0.1253981, 0, 0),
        VENUS(Planet.VENUS,
            0.72333566, 0, 0.00677672, -0.00005107,
            3.39467605, -0.00078890, 0,
            181.979099, 58517.8153870, 0, 0,
            131.767562, 0.0047964, 0, 0,
            76.679842, -0.2776942, 0, 0),
        EARTH(Planet.SUN,
            1.00000261, 0, 0.01673163, -0.00004261,
            -0.00001531, 0, 0,
            100.464571, 35999.373449, 0, 0,
            102.937348, 0.3225622, 0, 0,
            0.0, 0.0, 0, 0),
        MARS(Planet.MARS,
            1.52371034, 0, 0.09339410, 0.00007882,
            1.84969142, -0.0047340, 0,
            -4.553432, 19140.302684, 0, 0,
            -23.943629, 0.4444109, 0, 0,
            49.559538, -0.2925734, 0, 0),
        JUPITER(Planet.JUPITER,
            5.20288700, 0, 0.04838624, 0.00013253,
            1.30439695, -0.0018371, 0,
            34.396440, 3034.746128, 0, 0,
            14.728479, 0.2125268, 0, 0,
            100.473909, 0.2046913, 0, 0),
        SATURN(Planet.SATURN,
            9.53667594, 0, 0.05386179, -0.0005099,
            2.48599187, 0.0019361, 0,
            49.954244, 1222.493622, 0, 0,
            92.598878, 0.1501507, 0, 0,
            113.662424, -0.2886779, 0, 0),
        URANUS(Planet.URANUS,
            19.18916464, 0, 0.04725744, 0.000043,
            0.77263783, 0.0002919, 0,
            313.238105, 428.482027, 0, 0,
            170.954276, 0.4080528, 0, 0,
            74.016925, 0.0424059, 0, 0),
        NEPTUNE(Planet.NEPTUNE,
            30.06992276, 0, 0.00859048, 0.00005105,
            1.77004347, -0.0010009, 0,
            -55.120029, 218.693493, 0, 0,
            44.971882, -0.135182, 0, 0,
            131.785368, 0.0507054, 0, 0),
        PLUTO(Planet.PLUTO,
            39.48211675, 0, 0.24882730, 0.0000517,
            17.14001206, 0.0001088, 0,
            238.929038, 145.207805, 0, 0,
            224.068916, 0.0402696, 0, 0,
            110.303936, -0.0118348, 0, 0);

        final Planet planet;
        final double a0, a1, e0, e1, I0, I1, I2, L0, L1, L2, L3, w0, w1, w2, w3, O0, O1, O2, O3;
        PlanetElement(Planet p,
            double a0, double a1, double e0, double e1,
            double I0, double I1, double I2,
            double L0, double L1, double L2, double L3,
            double w0, double w1, double w2, double w3,
            double O0, double O1, double O2, double O3) {
            this.planet = p;
            this.a0 = a0; this.a1 = a1;
            this.e0 = e0; this.e1 = e1;
            this.I0 = I0; this.I1 = I1; this.I2 = I2;
            this.L0 = L0; this.L1 = L1; this.L2 = L2; this.L3 = L3;
            this.w0 = w0; this.w1 = w1; this.w2 = w2; this.w3 = w3;
            this.O0 = O0; this.O1 = O1; this.O2 = O2; this.O3 = O3;
        }
    }
}
